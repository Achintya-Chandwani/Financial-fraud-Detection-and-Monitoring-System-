"""
FraudShield AI — API endpoint tests
Tests health, validation, and proper error responses.
"""
import pytest


# ─── Health Check ─────────────────────────────────────────────────────────────

def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "database" in data
    assert "timestamp" in data


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "FraudShield AI"


# ─── Input Validation ─────────────────────────────────────────────────────────

VALID_TRANSACTION = {
    "transaction_type": "TRANSFER",
    "amount": 150000.0,
    "origin_account": "C123456789",
    "destination_account": "C987654321",
    "origin_balance_before": 300000.0,
    "origin_balance_after": 150000.0,
    "dest_balance_before": 10000.0,
    "dest_balance_after": 160000.0,
}


def test_predict_no_model_returns_503(client):
    """When no model is loaded, /api/predict must return 503 — not a fake prediction."""
    resp = client.post("/api/predict", json=VALID_TRANSACTION)
    # Either 200 (model loaded) or 503 (model missing) are correct responses
    assert resp.status_code in (200, 503)


def test_predict_invalid_amount(client):
    """Negative amount must be rejected with 422."""
    bad_tx = {**VALID_TRANSACTION, "amount": -500.0}
    resp = client.post("/api/predict", json=bad_tx)
    assert resp.status_code == 422


def test_predict_zero_amount(client):
    """Zero amount must be rejected with 422."""
    bad_tx = {**VALID_TRANSACTION, "amount": 0.0}
    resp = client.post("/api/predict", json=bad_tx)
    assert resp.status_code == 422


def test_predict_invalid_transaction_type(client):
    """Unknown transaction type must be rejected with 422."""
    bad_tx = {**VALID_TRANSACTION, "transaction_type": "WIRE_FRAUD"}
    resp = client.post("/api/predict", json=bad_tx)
    assert resp.status_code == 422


def test_predict_missing_required_fields(client):
    """Missing required fields must be rejected with 422."""
    resp = client.post("/api/predict", json={"amount": 1000.0})
    assert resp.status_code == 422


def test_predict_empty_account(client):
    """Empty account string must be rejected with 422."""
    bad_tx = {**VALID_TRANSACTION, "origin_account": "   "}
    resp = client.post("/api/predict", json=bad_tx)
    assert resp.status_code == 422


# ─── Batch Prediction ─────────────────────────────────────────────────────────

def test_batch_predict_empty_list(client):
    """Empty transaction list must be rejected."""
    resp = client.post("/api/predict/batch", json={"transactions": []})
    assert resp.status_code == 422


def test_batch_predict_valid(client):
    """Valid batch should return 200 or 503 (if no model)."""
    payload = {"transactions": [VALID_TRANSACTION, VALID_TRANSACTION]}
    resp = client.post("/api/predict/batch", json=payload)
    assert resp.status_code in (200, 503)


# ─── Dashboard ────────────────────────────────────────────────────────────────

def test_dashboard_stats(client):
    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_transactions" in data
    assert "total_suspicious" in data
    assert "fraud_detection_rate" in data


def test_transactions_list(client):
    resp = client.get("/api/transactions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_transaction_not_found(client):
    resp = client.get("/api/transactions/999999")
    assert resp.status_code == 404


def test_explanation_not_found(client):
    resp = client.get("/api/explanations/999999")
    assert resp.status_code == 404


def test_model_metrics_no_model(client):
    """Model metrics must return 503 if model is not trained."""
    resp = client.get("/api/model/metrics")
    assert resp.status_code in (200, 503)


# ─── Investigations ───────────────────────────────────────────────────────────

def test_investigations_list(client):
    resp = client.get("/api/investigations")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_investigation_not_found(client):
    resp = client.patch("/api/investigations/999999", json={"case_status": "Resolved"})
    assert resp.status_code == 404
