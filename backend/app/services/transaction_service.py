"""
FraudShield AI — Transaction & Prediction Database Service
Handles CRUD operations for transactions, predictions, and investigations.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from loguru import logger

from backend.app.models.db_models import Transaction, Prediction, Investigation, ModelVersion
from backend.app.schemas.schemas import (
    TransactionInput, InvestigationCreate, InvestigationUpdate
)


# ─── Transaction CRUD ─────────────────────────────────────────────────────────

def create_transaction(db: Session, data: TransactionInput) -> Transaction:
    """Persist a new transaction record."""
    tx = Transaction(
        transaction_type      = data.transaction_type,
        amount                = data.amount,
        origin_account        = data.origin_account,
        destination_account   = data.destination_account,
        origin_balance_before = data.origin_balance_before,
        origin_balance_after  = data.origin_balance_after,
        dest_balance_before   = data.dest_balance_before,
        dest_balance_after    = data.dest_balance_after,
        transaction_timestamp = datetime.utcnow(),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    logger.debug("Transaction created: id={}", tx.id)
    return tx


def get_transaction(db: Session, transaction_id: int) -> Optional[Transaction]:
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def get_transactions(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    risk_category: Optional[str] = None,
) -> List[Transaction]:
    """Get paginated transactions, optionally filtered by risk category."""
    q = (
        db.query(Transaction)
        .join(Prediction, isouter=True)
        .order_by(desc(Transaction.created_at))
    )
    if risk_category:
        q = q.filter(Prediction.risk_category == risk_category)
    return q.offset(skip).limit(limit).all()


# ─── Prediction CRUD ──────────────────────────────────────────────────────────

def create_prediction(
    db: Session,
    transaction_id: int,
    result: Dict[str, Any],
) -> Prediction:
    """Persist a prediction result and auto-create investigation for suspicious ones."""
    top_features = None
    if result.get("top_features"):
        top_features = [f.model_dump() for f in result["top_features"]]

    pred = Prediction(
        transaction_id       = transaction_id,
        predicted_class      = result["predicted_class"],
        fraud_probability    = result["fraud_probability"],
        risk_category        = result["risk_category"],
        model_version        = result["model_version"],
        top_features         = top_features,
        prediction_timestamp = datetime.utcnow(),
    )
    db.add(pred)
    db.flush()  # get pred.id before committing

    # Auto-create investigation case for suspicious (Medium or High risk) predictions
    if result["risk_category"] in ("Medium", "High"):
        inv = Investigation(
            prediction_id = pred.id,
            case_status   = "Open",
        )
        db.add(inv)

    db.commit()
    db.refresh(pred)
    logger.debug(
        "Prediction saved: id={}, class={}, prob={:.3f}, risk={}",
        pred.id, pred.predicted_class, pred.fraud_probability, pred.risk_category,
    )
    return pred


def get_prediction(db: Session, prediction_id: int) -> Optional[Prediction]:
    return db.query(Prediction).filter(Prediction.id == prediction_id).first()


def get_prediction_by_transaction(db: Session, transaction_id: int) -> Optional[Prediction]:
    return db.query(Prediction).filter(Prediction.transaction_id == transaction_id).first()


# ─── Dashboard Stats ──────────────────────────────────────────────────────────

def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Aggregate statistics for the dashboard overview."""
    total         = db.query(func.count(Prediction.id)).scalar() or 0
    suspicious    = db.query(func.count(Prediction.id)).filter(Prediction.predicted_class == 1).scalar() or 0
    legitimate    = total - suspicious
    avg_risk      = db.query(func.avg(Prediction.fraud_probability)).scalar() or 0.0
    high_risk     = db.query(func.count(Prediction.id)).filter(Prediction.risk_category == "High").scalar() or 0
    medium_risk   = db.query(func.count(Prediction.id)).filter(Prediction.risk_category == "Medium").scalar() or 0
    low_risk      = db.query(func.count(Prediction.id)).filter(Prediction.risk_category == "Low").scalar() or 0
    detection_rate = round((suspicious / total * 100) if total > 0 else 0.0, 2)

    return {
        "total_transactions":   total,
        "total_suspicious":     suspicious,
        "total_legitimate":     legitimate,
        "fraud_detection_rate": detection_rate,
        "average_risk_score":   round(float(avg_risk), 4),
        "high_risk_count":      high_risk,
        "medium_risk_count":    medium_risk,
        "low_risk_count":       low_risk,
        "last_updated":         datetime.utcnow(),
    }


def get_recent_suspicious(db: Session, limit: int = 10) -> List[Dict]:
    """Get recent suspicious transactions for dashboard table."""
    rows = (
        db.query(Transaction, Prediction)
        .join(Prediction)
        .filter(Prediction.predicted_class == 1)
        .order_by(desc(Prediction.prediction_timestamp))
        .limit(limit)
        .all()
    )
    result = []
    for tx, pred in rows:
        result.append({
            "transaction_id":    tx.id,
            "amount":            tx.amount,
            "transaction_type":  tx.transaction_type,
            "origin_account":    tx.origin_account,
            "risk_category":     pred.risk_category,
            "fraud_probability": pred.fraud_probability,
            "timestamp":         pred.prediction_timestamp.isoformat(),
        })
    return result


def get_trend_data(db: Session, days: int = 7) -> List[Dict]:
    """Return daily transaction and fraud counts for trend charts."""
    from sqlalchemy import cast, Date
    rows = (
        db.query(
            cast(Prediction.prediction_timestamp, Date).label("date"),
            func.count(Prediction.id).label("total"),
            func.sum(Prediction.predicted_class).label("flagged"),
        )
        .group_by("date")
        .order_by("date")
        .limit(days)
        .all()
    )
    return [{"date": str(r.date), "total": r.total, "flagged": int(r.flagged or 0)} for r in rows]


# ─── Investigation CRUD ───────────────────────────────────────────────────────

def get_investigations(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    risk_category: Optional[str] = None,
) -> List[Investigation]:
    q = (
        db.query(Investigation)
        .join(Prediction)
        .order_by(desc(Investigation.created_at))
    )
    if status:
        q = q.filter(Investigation.case_status == status)
    if risk_category:
        q = q.filter(Prediction.risk_category == risk_category)
    return q.offset(skip).limit(limit).all()


def update_investigation(
    db: Session,
    investigation_id: int,
    update_data: InvestigationUpdate,
) -> Optional[Investigation]:
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        return None
    for field, val in update_data.model_dump(exclude_none=True).items():
        setattr(inv, field, val)
    inv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(inv)
    return inv


# ─── Model Versions ───────────────────────────────────────────────────────────

def get_active_model_version(db: Session) -> Optional[ModelVersion]:
    return db.query(ModelVersion).filter(ModelVersion.is_active == True).first()  # noqa: E712


def upsert_model_version(db: Session, metrics: Dict[str, Any]) -> ModelVersion:
    """Insert or update the active model record from training metrics."""
    # Deactivate all existing active models
    db.query(ModelVersion).filter(ModelVersion.is_active == True).update({"is_active": False})  # noqa: E712

    mv = ModelVersion(
        model_name       = metrics.get("model_name", "Unknown"),
        model_version    = metrics.get("model_version", "1.0.0"),
        training_date    = datetime.utcnow(),
        is_active        = True,
        precision_score  = metrics.get("precision"),
        recall_score     = metrics.get("recall"),
        f1_score         = metrics.get("f1"),
        roc_auc_score    = metrics.get("roc_auc"),
        pr_auc_score     = metrics.get("pr_auc"),
        training_samples = metrics.get("training_samples"),
        test_samples     = metrics.get("test_samples"),
        threshold        = metrics.get("threshold", 0.5),
        model_params     = metrics.get("params"),
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    return mv
