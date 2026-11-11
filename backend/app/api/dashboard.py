"""
FraudShield AI — Dashboard & Transaction API Endpoints
GET /api/dashboard/stats       — Dashboard summary statistics
GET /api/transactions          — List transactions
GET /api/transactions/{id}     — Single transaction detail
GET /api/model/metrics         — Model performance metrics
GET /api/health                — Health check
"""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from loguru import logger

from backend.app.database.connection import get_db, check_db_connection
from backend.app.schemas.schemas import (
    DashboardStats, TransactionResponse, ModelMetricsResponse,
    HealthResponse, InvestigationResponse, InvestigationUpdate,
)
from backend.app.services import transaction_service as ts
from backend.app.services.model_service import fraud_model
from backend.app.core.config import settings

router = APIRouter(prefix="/api", tags=["Dashboard & Transactions"])


# ─── Health Check ─────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check backend and model health",
    tags=["Health"],
)
async def health_check(db: Session = Depends(get_db)):
    db_ok = check_db_connection()
    return HealthResponse(
        status        = "healthy" if db_ok else "degraded",
        database      = "connected" if db_ok else "disconnected",
        model_loaded  = fraud_model.is_loaded,
        model_version = fraud_model.model_version,
        timestamp     = datetime.utcnow(),
    )


# ─── Dashboard ────────────────────────────────────────────────────────────────

@router.get(
    "/dashboard/stats",
    response_model=DashboardStats,
    summary="Dashboard summary statistics",
)
async def dashboard_stats(db: Session = Depends(get_db)):
    stats = ts.get_dashboard_stats(db)
    return DashboardStats(**stats)


@router.get(
    "/dashboard/recent-suspicious",
    summary="Recent suspicious transactions for dashboard table",
)
async def recent_suspicious(
    limit: int = Query(10, ge=1, le=50),
    db: Session  = Depends(get_db),
):
    return ts.get_recent_suspicious(db, limit=limit)


@router.get(
    "/dashboard/trend",
    summary="Daily transaction and fraud trend data for charts",
)
async def trend_data(
    days: int = Query(7, ge=1, le=30),
    db: Session  = Depends(get_db),
):
    return ts.get_trend_data(db, days=days)


# ─── Transactions ─────────────────────────────────────────────────────────────

@router.get(
    "/transactions",
    summary="Paginated list of all transactions",
)
async def list_transactions(
    skip:          int           = Query(0, ge=0),
    limit:         int           = Query(50, ge=1, le=200),
    risk_category: Optional[str] = Query(None, description="Filter by risk: Low, Medium, High"),
    db:            Session       = Depends(get_db),
):
    txs = ts.get_transactions(db, skip=skip, limit=limit, risk_category=risk_category)
    return txs


@router.get(
    "/transactions/{transaction_id}",
    summary="Get full details for one transaction including prediction",
)
async def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = ts.get_transaction(db, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found.")
    pred = ts.get_prediction_by_transaction(db, transaction_id)
    return {
        "transaction": tx,
        "prediction":  pred,
    }


# ─── Model Metrics ────────────────────────────────────────────────────────────

@router.get(
    "/model/metrics",
    summary="Return trained model performance metrics",
)
async def model_metrics(db: Session = Depends(get_db)):
    if not fraud_model.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Model not trained",
                "message": (
                    "Model metrics are not available because no model has been trained yet. "
                    "Please run the Jupyter notebooks (04 and 05) to train and evaluate the model."
                ),
            },
        )

    metrics = fraud_model.metrics
    active_mv = ts.get_active_model_version(db)

    # Try to load confusion matrix from metrics file
    conf_matrix = metrics.get("confusion_matrix")

    # Compile comparison data for all models
    all_models = metrics.get("all_models", [])

    return {
        "model_name":       metrics.get("model_name", "Unknown"),
        "model_version":    metrics.get("model_version", settings.MODEL_VERSION),
        "training_date":    active_mv.training_date.isoformat() if active_mv else None,
        "is_active":        True,
        "precision_score":  metrics.get("precision"),
        "recall_score":     metrics.get("recall"),
        "f1_score":         metrics.get("f1"),
        "roc_auc_score":    metrics.get("roc_auc"),
        "pr_auc_score":     metrics.get("pr_auc"),
        "training_samples": metrics.get("training_samples"),
        "test_samples":     metrics.get("test_samples"),
        "threshold":        metrics.get("threshold", 0.5),
        "confusion_matrix": conf_matrix,
        "all_models":       all_models,
        "shap_feature_importance": metrics.get("shap_feature_importance"),
    }


# ─── Investigations ───────────────────────────────────────────────────────────

@router.get(
    "/investigations",
    summary="List investigation cases",
)
async def list_investigations(
    skip:          int           = Query(0, ge=0),
    limit:         int           = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    risk_category: Optional[str] = Query(None),
    db:            Session       = Depends(get_db),
):
    invs = ts.get_investigations(
        db, skip=skip, limit=limit,
        status=status_filter, risk_category=risk_category
    )
    # Enrich with transaction and prediction info
    result = []
    for inv in invs:
        pred = inv.prediction
        tx   = pred.transaction if pred else None
        result.append({
            "id":                  inv.id,
            "prediction_id":       inv.prediction_id,
            "case_status":         inv.case_status,
            "assigned_to":         inv.assigned_to,
            "investigation_notes": inv.investigation_notes,
            "created_at":          inv.created_at,
            "updated_at":          inv.updated_at,
            "risk_category":       pred.risk_category if pred else None,
            "fraud_probability":   pred.fraud_probability if pred else None,
            "amount":              tx.amount if tx else None,
            "transaction_type":    tx.transaction_type if tx else None,
            "origin_account":      tx.origin_account if tx else None,
        })
    return result


@router.patch(
    "/investigations/{investigation_id}",
    summary="Update investigation case status or notes",
)
async def update_investigation(
    investigation_id: int,
    update:           InvestigationUpdate,
    db:               Session = Depends(get_db),
):
    inv = ts.update_investigation(db, investigation_id, update)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found.")
    return inv
