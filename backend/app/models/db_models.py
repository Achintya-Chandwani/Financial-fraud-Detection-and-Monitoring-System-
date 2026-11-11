"""
FraudShield AI — SQLAlchemy ORM Models
Maps Python classes to database tables.
"""
from datetime import datetime
from sqlalchemy import (
    BigInteger, Column, DateTime, Enum, Float, Integer,
    String, Text, JSON, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from backend.app.database.connection import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id                    = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_type      = Column(Enum("CASH_IN","CASH_OUT","DEBIT","PAYMENT","TRANSFER"), nullable=False)
    amount                = Column(Float, nullable=False)
    origin_account        = Column(String(50), nullable=False)
    destination_account   = Column(String(50), nullable=False)
    origin_balance_before = Column(Float, nullable=True)
    origin_balance_after  = Column(Float, nullable=True)
    dest_balance_before   = Column(Float, nullable=True)
    dest_balance_after    = Column(Float, nullable=True)
    transaction_timestamp = Column(DateTime, default=datetime.utcnow)
    created_at            = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prediction = relationship("Prediction", back_populates="transaction", uselist=False, cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"

    id                   = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_id       = Column(BigInteger, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    predicted_class      = Column(Integer, nullable=False)
    fraud_probability    = Column(Float, nullable=False)
    risk_category        = Column(Enum("Low","Medium","High"), nullable=False)
    model_version        = Column(String(20), nullable=False)
    top_features         = Column(JSON, nullable=True)
    prediction_timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    transaction  = relationship("Transaction", back_populates="prediction")
    investigation = relationship("Investigation", back_populates="prediction", uselist=False, cascade="all, delete-orphan")


class Investigation(Base):
    __tablename__ = "investigations"

    id                  = Column(BigInteger, primary_key=True, autoincrement=True)
    prediction_id       = Column(BigInteger, ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False)
    case_status         = Column(
        Enum("Open","Under Review","Escalated","Resolved","False Positive"),
        nullable=False,
        default="Open",
    )
    assigned_to         = Column(String(100), nullable=True)
    investigation_notes = Column(Text, nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prediction = relationship("Prediction", back_populates="investigation")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id               = Column(BigInteger, primary_key=True, autoincrement=True)
    model_name       = Column(String(100), nullable=False)
    model_version    = Column(String(20), nullable=False)
    training_date    = Column(DateTime, nullable=False)
    is_active        = Column(Boolean, default=False)
    precision_score  = Column(Float, nullable=True)
    recall_score     = Column(Float, nullable=True)
    f1_score         = Column(Float, nullable=True)
    roc_auc_score    = Column(Float, nullable=True)
    pr_auc_score     = Column(Float, nullable=True)
    training_samples = Column(BigInteger, nullable=True)
    test_samples     = Column(BigInteger, nullable=True)
    threshold        = Column(Float, default=0.5)
    model_params     = Column(JSON, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)
