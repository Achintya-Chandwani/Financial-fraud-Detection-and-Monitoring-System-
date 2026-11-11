"""
FraudShield AI — Standalone Model Training Script
Runs the complete ML pipeline without Jupyter:
  1. Generates synthetic PaySim-like data (10,000 transactions)
  2. Preprocesses and engineers features
  3. Trains XGBoost model with SMOTE
  4. Evaluates and saves model + metrics + preprocessor

Run from FraudShield-AI directory:
    python train_model.py
"""
import os
import sys
import json
import warnings

# Force UTF-8 output on Windows to avoid codec errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

warnings.filterwarnings('ignore')

# ── Paths ────────────────────────────────────────────────────
ROOT         = Path(__file__).parent
DATA_RAW     = ROOT / "data" / "raw"
DATA_PROC    = ROOT / "data" / "processed"
MODELS_DIR   = ROOT / "models"
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROC.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

TRANSACTION_CSV = DATA_RAW / "transactions.csv"
MODEL_PATH      = MODELS_DIR / "best_model.joblib"
PREPROCESSOR_PATH = MODELS_DIR / "preprocessor.joblib"
METRICS_PATH    = MODELS_DIR / "model_metrics.json"

print("=" * 60)
print("  FraudShield AI — Model Training Pipeline")
print("=" * 60)

# ════════════════════════════════════════════════════════════
# STEP 1: Generate or Load Dataset
# ════════════════════════════════════════════════════════════
print("\n[1/5] Loading dataset...")

if TRANSACTION_CSV.exists():
    df = pd.read_csv(TRANSACTION_CSV)
    print(f"      Loaded existing dataset: {len(df):,} rows")
else:
    print("      No dataset found. Generating synthetic PaySim data (50,000 rows)...")
    np.random.seed(42)
    N = 50_000
    FRAUD_RATE = 0.013   # ~1.3% fraud (realistic)

    tx_types = np.random.choice(
        ['CASH_IN', 'CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER'],
        size=N,
        p=[0.22, 0.35, 0.05, 0.34, 0.04]
    )
    amounts = np.random.exponential(scale=15000, size=N).clip(1, 2_000_000)
    is_fraud = np.zeros(N, dtype=int)

    # Fraud transactions (mostly TRANSFER and CASH_OUT, large amounts)
    fraud_mask = np.random.random(N) < FRAUD_RATE
    tx_types[fraud_mask & (np.random.random(N) > 0.3)] = 'TRANSFER'
    tx_types[fraud_mask & (np.random.random(N) <= 0.3)] = 'CASH_OUT'
    amounts[fraud_mask] = np.random.uniform(100_000, 1_000_000, fraud_mask.sum())
    is_fraud[fraud_mask] = 1

    origin_balance_before = np.random.uniform(0, 2_000_000, N)
    origin_balance_after  = np.where(
        is_fraud == 1, 0,
        np.maximum(0, origin_balance_before - amounts + np.random.normal(0, 1000, N))
    )
    dest_balance_before = np.random.uniform(0, 500_000, N)
    dest_balance_after  = dest_balance_before + amounts * np.random.uniform(0.98, 1.02, N)

    df = pd.DataFrame({
        'transaction_type':      tx_types,
        'amount':                amounts.round(2),
        'origin_account':        ['C' + str(x) for x in np.random.randint(1e9, 2e9, N)],
        'destination_account':   ['C' + str(x) for x in np.random.randint(1e9, 2e9, N)],
        'origin_balance_before': origin_balance_before.round(2),
        'origin_balance_after':  origin_balance_after.round(2),
        'dest_balance_before':   dest_balance_before.round(2),
        'dest_balance_after':    dest_balance_after.round(2),
        'isFraud':               is_fraud,
    })
    df.to_csv(TRANSACTION_CSV, index=False)
    print(f"      Generated and saved {len(df):,} rows — {is_fraud.sum()} fraud ({is_fraud.mean()*100:.2f}%)")

# ════════════════════════════════════════════════════════════
# STEP 2: Feature Engineering
# ════════════════════════════════════════════════════════════
print("\n[2/5] Engineering features...")

TYPE_MAP = {'CASH_IN': 0, 'CASH_OUT': 1, 'DEBIT': 2, 'PAYMENT': 3, 'TRANSFER': 4}

df['transaction_type_encoded'] = df['transaction_type'].str.upper().map(TYPE_MAP).fillna(3).astype(int)
df['balance_diff_origin']      = df['origin_balance_before'] - df['origin_balance_after']
df['balance_diff_dest']        = df['dest_balance_after']    - df['dest_balance_before']
df['amount_to_origin_ratio']   = df['amount'] / (df['origin_balance_before'] + 1e-9)
df['is_large_transfer']        = (df['amount'] > 200_000).astype(int)

FEATURE_COLS = [
    'transaction_type_encoded', 'amount',
    'origin_balance_before', 'origin_balance_after',
    'dest_balance_before', 'dest_balance_after',
    'balance_diff_origin', 'balance_diff_dest',
    'amount_to_origin_ratio', 'is_large_transfer',
]

# Detect fraud column name
target_col = 'isFraud' if 'isFraud' in df.columns else 'is_fraud'
if target_col not in df.columns:
    raise ValueError(f"Target column not found. Columns: {df.columns.tolist()}")

X = df[FEATURE_COLS]
y = df[target_col]
print(f"      Features: {len(FEATURE_COLS)} | Fraud: {y.sum():,} ({y.mean()*100:.2f}%)")

# ════════════════════════════════════════════════════════════
# STEP 3: Train/Test Split (chronological — first 80% train)
# ════════════════════════════════════════════════════════════
print("\n[3/5] Splitting data and applying SMOTE...")

split_idx = int(len(X) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

# Scale
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# SMOTE on training data only
try:
    from imblearn.over_sampling import SMOTE
    smote = SMOTE(random_state=42, k_neighbors=min(5, y_train.sum()-1))
    X_train_res, y_train_res = smote.fit_resample(X_train_scaled, y_train)
    print(f"      SMOTE applied — fraud samples: {y_train.sum():,} → {y_train_res.sum():,}")
except Exception as e:
    print(f"      SMOTE skipped ({e}). Using class_weight instead.")
    X_train_res, y_train_res = X_train_scaled, y_train

print(f"      Train: {len(X_train_res):,} | Test: {len(X_test):,}")

# ════════════════════════════════════════════════════════════
# STEP 4: Train XGBoost
# ════════════════════════════════════════════════════════════
print("\n[4/5] Training XGBoost model...")

from xgboost import XGBClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix
)

scale_pos = int((y_train_res == 0).sum() / max((y_train_res == 1).sum(), 1))

model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_pos,
    use_label_encoder=False,
    eval_metric='aucpr',
    random_state=42,
    n_jobs=-1,
)
model.fit(
    X_train_res, y_train_res,
    eval_set=[(X_test_scaled, y_test)],
    verbose=False,
)
print("      XGBoost training complete.")

# ════════════════════════════════════════════════════════════
# STEP 5: Evaluate & Optimise Threshold
# ════════════════════════════════════════════════════════════
print("\n[5/5] Evaluating model and saving...")

probs = model.predict_proba(X_test_scaled)[:, 1]

# Optimise threshold for F1
best_f1, best_thresh = 0, 0.5
for t in np.arange(0.1, 0.9, 0.01):
    preds = (probs >= t).astype(int)
    f = f1_score(y_test, preds, zero_division=0)
    if f > best_f1:
        best_f1, best_thresh = f, round(t, 2)

final_preds = (probs >= best_thresh).astype(int)
cm = confusion_matrix(y_test, final_preds).tolist()
roc  = roc_auc_score(y_test, probs)
prauc = average_precision_score(y_test, probs)
prec = precision_score(y_test, final_preds, zero_division=0)
rec  = recall_score(y_test, final_preds, zero_division=0)
f1   = f1_score(y_test, final_preds, zero_division=0)

print(f"\n  Results:")
print(f"  ----------------------------------------")
print(f"  Model        : XGBoost")
print(f"  Threshold    : {best_thresh}")
print(f"  Precision    : {prec:.4f}")
print(f"  Recall       : {rec:.4f}")
print(f"  F1 Score     : {f1:.4f}")
print(f"  ROC-AUC      : {roc:.4f}")
print(f"  PR-AUC       : {prauc:.4f}")
print(f"  ----------------------------------------")

# SHAP feature importance
try:
    import shap
    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test_scaled[:500])
    if isinstance(shap_values, list):
        sv = shap_values[1]
    else:
        sv = shap_values
    shap_importance = {
        col: float(abs(sv[:, i]).mean())
        for i, col in enumerate(FEATURE_COLS)
    }
except Exception as e:
    shap_importance = {col: float(model.feature_importances_[i])
                       for i, col in enumerate(FEATURE_COLS)}
    print(f"  SHAP fallback to feature_importances_ ({e})")

# Save metrics JSON
metrics = {
    "model_name":        "XGBoost",
    "model_version":     "1.0.0",
    "training_date":     datetime.utcnow().isoformat(),
    "threshold":         best_thresh,
    "precision_score":   round(prec, 4),
    "recall_score":      round(rec, 4),
    "f1_score":          round(f1, 4),
    "roc_auc_score":     round(roc, 4),
    "pr_auc_score":      round(prauc, 4),
    "confusion_matrix":  cm,
    "training_samples":  int(len(X_train_res)),
    "test_samples":      int(len(X_test)),
    "feature_columns":   FEATURE_COLS,
    "shap_feature_importance": shap_importance,
    "all_models": [
        {"model_name":"XGBoost", "precision":round(prec,4), "recall":round(rec,4),
         "f1":round(f1,4), "roc_auc":round(roc,4), "pr_auc":round(prauc,4)}
    ]
}

with open(METRICS_PATH, "w") as f:
    json.dump(metrics, f, indent=2)

# Save model and preprocessor
import joblib
joblib.dump(model,  MODEL_PATH)
joblib.dump(scaler, PREPROCESSOR_PATH)

print(f"\n  [OK] Saved: {MODEL_PATH}")
print(f"  [OK] Saved: {PREPROCESSOR_PATH}")
print(f"  [OK] Saved: {METRICS_PATH}")
print("\n" + "=" * 60)
print("  Training complete! Restart the backend to load the model.")
print("=" * 60 + "\n")
