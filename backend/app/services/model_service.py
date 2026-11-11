"""
FraudShield AI — ML Model Service
Loads the trained model and preprocessor, runs predictions,
and generates SHAP-based explanations.

Heavy ML libraries (numpy, pandas, joblib, shap) are imported lazily
inside methods so the backend starts cleanly without requiring the full
ML stack at import time (useful for lightweight deployments and testing).
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from loguru import logger

from backend.app.core.config import settings
from backend.app.schemas.schemas import FeatureImportance, RiskCategory


# ─── Feature definitions (must match training order exactly) ──────────────────

FEATURE_COLUMNS = [
    "transaction_type_encoded",
    "amount",
    "origin_balance_before",
    "origin_balance_after",
    "dest_balance_before",
    "dest_balance_after",
    "balance_diff_origin",   # engineered
    "balance_diff_dest",     # engineered
    "amount_to_origin_ratio",  # engineered
    "is_large_transfer",     # engineered
]

TRANSACTION_TYPE_MAP = {
    "CASH_IN":  0,
    "CASH_OUT": 1,
    "DEBIT":    2,
    "PAYMENT":  3,
    "TRANSFER": 4,
}


class ModelNotLoadedError(Exception):
    """Raised when a prediction is requested but no model is loaded."""
    pass


class FraudDetectionModel:
    """
    Wrapper for the trained fraud detection model.
    Handles loading, preprocessing, prediction, and explanation.
    """

    def __init__(self):
        self._model       = None
        self._preprocessor = None
        self._explainer   = None
        self._metrics: Dict = {}
        self._is_loaded   = False
        self._model_version: Optional[str] = None
        self._threshold: float = 0.5

    # ─── Loading ──────────────────────────────────────────────────────────────

    def load(self) -> bool:
        """
        Load model and preprocessor from disk.
        Returns True if successful, False otherwise.
        """
        model_path       = settings.model_path_abs
        preprocessor_path = settings.preprocessor_path_abs
        metrics_path      = settings.metrics_path_abs

        if not model_path.exists():
            logger.warning(
                "Model file not found at '{}'. "
                "Run the notebooks (04_Model_Training, 05_Model_Evaluation) to train and save the model.",
                model_path,
            )
            return False

        if not preprocessor_path.exists():
            logger.warning(
                "Preprocessor not found at '{}'. Please retrain the model.",
                preprocessor_path,
            )
            return False

        try:
            import joblib  # lazy import — only needed when model exists
            self._model        = joblib.load(model_path)
            self._preprocessor = joblib.load(preprocessor_path)
            logger.info("Model loaded from: {}", model_path)
            logger.info("Preprocessor loaded from: {}", preprocessor_path)

            # Load metrics if available
            if metrics_path.exists():
                with open(metrics_path, "r") as f:
                    self._metrics = json.load(f)
                self._threshold      = self._metrics.get("threshold", 0.5)
                self._model_version  = self._metrics.get("model_version", settings.MODEL_VERSION)
                logger.info("Model metrics loaded. Threshold={}", self._threshold)

            self._is_loaded = True

            # Initialize SHAP explainer (TreeExplainer for tree-based models)
            self._init_explainer()
            return True

        except Exception as e:
            logger.error("Failed to load model: {}", e)
            return False

    def _init_explainer(self) -> None:
        """Initialize SHAP explainer appropriate for the loaded model type."""
        try:
            import shap  # lazy import
            model_type = type(self._model).__name__
            if model_type in ("XGBClassifier", "RandomForestClassifier",
                              "GradientBoostingClassifier"):
                self._explainer = shap.TreeExplainer(self._model)
                logger.info("SHAP TreeExplainer initialized for {}", model_type)
            else:
                # Fallback: LinearExplainer or KernelExplainer
                self._explainer = None
                logger.info("SHAP explainer not initialized for {} (unsupported type)", model_type)
        except Exception as e:
            logger.warning("SHAP explainer initialization failed: {}", e)
            self._explainer = None

    # ─── Feature Engineering ─────────────────────────────────────────────────

    def _engineer_features(self, raw: Dict) -> Any:
        """
        Apply the same feature engineering used during training.
        Input: raw transaction dict.
        Output: DataFrame with engineered features.
        """
        import pandas as pd  # lazy import
        t_type = raw.get("transaction_type", "PAYMENT")
        if isinstance(t_type, str):
            t_type = t_type.upper()

        amount   = float(raw.get("amount", 0))
        ob_before = float(raw.get("origin_balance_before", 0))
        ob_after  = float(raw.get("origin_balance_after", 0))
        db_before = float(raw.get("dest_balance_before", 0))
        db_after  = float(raw.get("dest_balance_after", 0))

        balance_diff_origin = ob_before - ob_after
        balance_diff_dest   = db_after - db_before
        amount_to_origin    = amount / (ob_before + 1e-9)
        is_large_transfer   = int(amount > 200_000)

        features = {
            "transaction_type_encoded": TRANSACTION_TYPE_MAP.get(t_type, 3),
            "amount":                   amount,
            "origin_balance_before":    ob_before,
            "origin_balance_after":     ob_after,
            "dest_balance_before":      db_before,
            "dest_balance_after":       db_after,
            "balance_diff_origin":      balance_diff_origin,
            "balance_diff_dest":        balance_diff_dest,
            "amount_to_origin_ratio":   amount_to_origin,
            "is_large_transfer":        is_large_transfer,
        }
        return pd.DataFrame([features])

    # ─── Prediction ───────────────────────────────────────────────────────────

    def predict(self, transaction_data: Dict) -> Dict[str, Any]:
        """
        Run prediction for a single transaction.
        Returns a dict with probability, class, risk category, and SHAP explanation.
        Raises ModelNotLoadedError if model is not available.
        """
        if not self._is_loaded or self._model is None:
            raise ModelNotLoadedError(
                "No trained model is loaded. "
                "Please run notebooks 04_Model_Training.ipynb and 05_Model_Evaluation.ipynb "
                "to train and save the model, then restart the backend."
            )

        # Build feature DataFrame
        X = self._engineer_features(transaction_data)

        # Apply preprocessor scaling (if present)
        if self._preprocessor is not None:
            try:
                X_scaled = self._preprocessor.transform(X)
            except Exception:
                X_scaled = X.values
        else:
            X_scaled = X.values

        # Get probability
        prob = float(self._model.predict_proba(X_scaled)[0][1])
        predicted_class = int(prob >= self._threshold)

        risk_category = self._get_risk_category(prob)
        top_features  = self._explain(X, X_scaled)

        return {
            "fraud_probability": round(prob, 4),
            "predicted_class":   predicted_class,
            "risk_category":     risk_category,
            "model_version":     self._model_version or settings.MODEL_VERSION,
            "top_features":      top_features,
        }

    def predict_batch(self, transactions: List[Dict]) -> List[Dict[str, Any]]:
        """Run predictions for a batch of transactions."""
        if not self._is_loaded or self._model is None:
            raise ModelNotLoadedError(
                "No trained model is loaded. Train the model first."
            )

        feature_rows = [self._engineer_features(t) for t in transactions]
        import pandas as pd  # lazy import
        X = pd.concat(feature_rows, ignore_index=True)

        if self._preprocessor is not None:
            try:
                X_scaled = self._preprocessor.transform(X)
            except Exception:
                X_scaled = X.values
        else:
            X_scaled = X.values

        probs = self._model.predict_proba(X_scaled)[:, 1]
        results = []
        for i, prob in enumerate(probs):
            prob = float(prob)
            results.append({
                "fraud_probability": round(prob, 4),
                "predicted_class":   int(prob >= self._threshold),
                "risk_category":     self._get_risk_category(prob),
                "model_version":     self._model_version or settings.MODEL_VERSION,
                "top_features":      None,  # Skip SHAP for batch (performance)
            })
        return results

    # ─── SHAP Explanation ─────────────────────────────────────────────────────

    def _explain(self, X_df: Any, X_scaled: Any) -> Optional[List[FeatureImportance]]:
        """
        Generate SHAP feature importance for a single prediction.
        Returns list of FeatureImportance objects, or None if unavailable.
        """
        if self._explainer is None:
            return None

        try:
            import numpy as np  # lazy import
            shap_values = self._explainer.shap_values(X_scaled)

            # For binary classifiers, shap_values may be [class0, class1]
            if isinstance(shap_values, list):
                sv = shap_values[1][0]
            else:
                sv = shap_values[0]

            feature_names = FEATURE_COLUMNS
            importances = []
            for fname, fval, shap_val in zip(feature_names, X_df.iloc[0].values, sv):
                importances.append(FeatureImportance(
                    feature=fname,
                    value=round(float(fval), 4),
                    importance=round(float(shap_val), 4),
                    direction="increases_risk" if shap_val > 0 else "decreases_risk",
                ))

            # Sort by absolute importance descending
            importances.sort(key=lambda x: abs(x.importance), reverse=True)
            return importances[:6]  # Return top 6

        except Exception as e:
            logger.warning("SHAP explanation failed: {}", e)
            return None

    # ─── Risk Categorization ─────────────────────────────────────────────────

    @staticmethod
    def _get_risk_category(prob: float) -> str:
        if prob >= 0.7:
            return RiskCategory.HIGH.value
        elif prob >= 0.4:
            return RiskCategory.MEDIUM.value
        else:
            return RiskCategory.LOW.value

    # ─── Properties ───────────────────────────────────────────────────────────

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def metrics(self) -> Dict:
        return self._metrics

    @property
    def model_version(self) -> Optional[str]:
        return self._model_version


# ─── Singleton ────────────────────────────────────────────────────────────────
# This instance is imported throughout the backend to avoid reloading the model.
fraud_model = FraudDetectionModel()
