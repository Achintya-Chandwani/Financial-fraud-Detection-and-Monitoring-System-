"""
FraudShield AI — Model service unit tests
Tests feature engineering, risk categorization, and error handling.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from backend.app.services.model_service import FraudDetectionModel, ModelNotLoadedError


SAMPLE_TX = {
    "transaction_type": "TRANSFER",
    "amount": 500000.0,
    "origin_account": "C123456789",
    "destination_account": "C987654321",
    "origin_balance_before": 500000.0,
    "origin_balance_after": 0.0,
    "dest_balance_before": 0.0,
    "dest_balance_after": 500000.0,
}


# ─── Feature Engineering ──────────────────────────────────────────────────────

class TestFeatureEngineering:
    def setup_method(self):
        self.model_svc = FraudDetectionModel()

    def test_engineer_features_shape(self):
        df = self.model_svc._engineer_features(SAMPLE_TX)
        assert df.shape == (1, 10), f"Expected (1, 10) but got {df.shape}"

    def test_balance_diff_origin_calculated(self):
        df = self.model_svc._engineer_features(SAMPLE_TX)
        # 500000 - 0 = 500000
        assert df["balance_diff_origin"].iloc[0] == pytest.approx(500000.0)

    def test_balance_diff_dest_calculated(self):
        df = self.model_svc._engineer_features(SAMPLE_TX)
        # 500000 - 0 = 500000
        assert df["balance_diff_dest"].iloc[0] == pytest.approx(500000.0)

    def test_is_large_transfer_flag(self):
        df = self.model_svc._engineer_features(SAMPLE_TX)
        assert df["is_large_transfer"].iloc[0] == 1

    def test_small_amount_not_large_transfer(self):
        small_tx = {**SAMPLE_TX, "amount": 100.0}
        df = self.model_svc._engineer_features(small_tx)
        assert df["is_large_transfer"].iloc[0] == 0

    def test_transaction_type_encoded(self):
        for tx_type, expected in [("CASH_IN",0),("CASH_OUT",1),("DEBIT",2),("PAYMENT",3),("TRANSFER",4)]:
            tx = {**SAMPLE_TX, "transaction_type": tx_type}
            df = self.model_svc._engineer_features(tx)
            assert df["transaction_type_encoded"].iloc[0] == expected

    def test_amount_to_origin_ratio(self):
        df = self.model_svc._engineer_features(SAMPLE_TX)
        # 500000 / (500000 + 1e-9) ≈ 1.0
        assert df["amount_to_origin_ratio"].iloc[0] == pytest.approx(1.0, abs=1e-6)

    def test_zero_origin_balance_no_division_error(self):
        tx = {**SAMPLE_TX, "origin_balance_before": 0.0}
        df = self.model_svc._engineer_features(tx)
        # Should not raise, ratio ~= amount / 1e-9 (large but finite)
        assert np.isfinite(df["amount_to_origin_ratio"].iloc[0])


# ─── Risk Categorization ──────────────────────────────────────────────────────

class TestRiskCategorization:
    def test_high_risk(self):
        assert FraudDetectionModel._get_risk_category(0.9) == "High"
        assert FraudDetectionModel._get_risk_category(0.7) == "High"

    def test_medium_risk(self):
        assert FraudDetectionModel._get_risk_category(0.6) == "Medium"
        assert FraudDetectionModel._get_risk_category(0.4) == "Medium"

    def test_low_risk(self):
        assert FraudDetectionModel._get_risk_category(0.1) == "Low"
        assert FraudDetectionModel._get_risk_category(0.0) == "Low"
        assert FraudDetectionModel._get_risk_category(0.39) == "Low"


# ─── Model Not Loaded ─────────────────────────────────────────────────────────

class TestModelNotLoaded:
    def setup_method(self):
        self.model_svc = FraudDetectionModel()

    def test_predict_raises_when_not_loaded(self):
        with pytest.raises(ModelNotLoadedError):
            self.model_svc.predict(SAMPLE_TX)

    def test_predict_batch_raises_when_not_loaded(self):
        with pytest.raises(ModelNotLoadedError):
            self.model_svc.predict_batch([SAMPLE_TX])

    def test_is_loaded_false_initially(self):
        assert self.model_svc.is_loaded is False

    def test_model_version_none_initially(self):
        assert self.model_svc.model_version is None


# ─── Model Loading ────────────────────────────────────────────────────────────

class TestModelLoading:
    def test_load_returns_false_if_no_file(self, tmp_path, monkeypatch):
        """Should return False gracefully when model file doesn't exist."""
        from backend.app.services.model_service import FraudDetectionModel
        from backend.app.core import config

        # Patch settings to point to a non-existent file path
        non_existent = tmp_path / "nonexistent.joblib"
        monkeypatch.setattr(config.settings, "MODEL_PATH", str(non_existent))

        # Override the model_path_abs property via a lambda on the class
        monkeypatch.setattr(
            type(config.settings),
            "model_path_abs",
            property(lambda self: non_existent),
        )

        model_svc = FraudDetectionModel()
        result = model_svc.load()
        assert result is False
        assert model_svc.is_loaded is False
