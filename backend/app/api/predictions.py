"""
FraudShield AI — Prediction API Endpoints
POST /api/predict        — Single transaction prediction
POST /api/predict/batch  — Batch prediction
GET  /api/explanations/{id} — SHAP explanation for a prediction
"""
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from backend.app.database.connection import get_db
from backend.app.schemas.schemas import (
    TransactionInput, PredictionResponse, BatchTransactionInput,
    BatchPredictionResponse, FeatureImportance,
)
from backend.app.services.model_service import fraud_model, ModelNotLoadedError
from backend.app.services.transaction_service import (
    create_transaction, create_prediction, get_prediction
)

router = APIRouter(prefix="/api", tags=["Predictions"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict fraud risk for a single transaction",
    description=(
        "Accepts transaction details and returns fraud risk probability, "
        "risk category, and SHAP feature importance. "
        "Results are stored in the database for audit purposes."
    ),
)
async def predict_single(
    transaction: TransactionInput,
    db: Session = Depends(get_db),
):
    """Single transaction fraud prediction endpoint."""
    logger.info(
        "Predict request: type={}, amount={}", transaction.transaction_type, transaction.amount
    )

    # Check model availability
    if not fraud_model.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Model not available",
                "message": (
                    "No trained model is loaded. "
                    "Please run the Jupyter notebooks in order: "
                    "04_Model_Training.ipynb then 05_Model_Evaluation.ipynb, "
                    "then restart the backend server."
                ),
            },
        )

    try:
        result = fraud_model.predict(transaction.model_dump())
    except ModelNotLoadedError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error("Prediction error: {}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )

    # Persist to database
    tx   = create_transaction(db, transaction)
    pred = create_prediction(db, tx.id, result)

    return PredictionResponse(
        transaction_id       = tx.id,
        predicted_class      = pred.predicted_class,
        label                = "Suspicious" if pred.predicted_class == 1 else "Legitimate",
        fraud_probability    = pred.fraud_probability,
        risk_category        = pred.risk_category,
        model_version        = pred.model_version,
        prediction_timestamp = pred.prediction_timestamp,
        top_features         = result.get("top_features"),
    )


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    summary="Predict fraud risk for a batch of transactions",
)
async def predict_batch(
    batch: BatchTransactionInput,
    db: Session = Depends(get_db),
):
    """Batch prediction — up to 1000 transactions per request."""
    if not fraud_model.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Model not available",
                "message": "Train the model using the Jupyter notebooks before submitting predictions.",
            },
        )

    try:
        raw_list = [t.model_dump() for t in batch.transactions]
        results  = fraud_model.predict_batch(raw_list)
    except ModelNotLoadedError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.error("Batch prediction error: {}", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    prediction_responses = []
    for tx_input, result in zip(batch.transactions, results):
        tx   = create_transaction(db, tx_input)
        pred = create_prediction(db, tx.id, result)
        prediction_responses.append(PredictionResponse(
            transaction_id       = tx.id,
            predicted_class      = pred.predicted_class,
            label                = "Suspicious" if pred.predicted_class == 1 else "Legitimate",
            fraud_probability    = pred.fraud_probability,
            risk_category        = pred.risk_category,
            model_version        = pred.model_version,
            prediction_timestamp = pred.prediction_timestamp,
            top_features         = None,
        ))

    flagged = sum(1 for r in prediction_responses if r.predicted_class == 1)

    return BatchPredictionResponse(
        total        = len(prediction_responses),
        flagged      = flagged,
        results      = prediction_responses,
        batch_id     = str(uuid.uuid4()),
        processed_at = datetime.utcnow(),
    )


@router.get(
    "/explanations/{prediction_id}",
    summary="Get SHAP explanation for a specific prediction",
)
async def get_explanation(prediction_id: int, db: Session = Depends(get_db)):
    """Return SHAP feature importance for a stored prediction."""
    pred = get_prediction(db, prediction_id)
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction {prediction_id} not found.",
        )
    return {
        "prediction_id":    pred.id,
        "transaction_id":   pred.transaction_id,
        "risk_category":    pred.risk_category,
        "fraud_probability": pred.fraud_probability,
        "top_features":     pred.top_features,
        "disclaimer": (
            "SHAP values indicate feature contributions to the model's prediction. "
            "They do not constitute proof of fraud."
        ),
    }
