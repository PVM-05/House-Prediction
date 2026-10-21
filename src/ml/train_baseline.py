"""
Pipeline 6 (ML 1): Baseline Ridge Regression Model
Splits Gold dataset into Train (70%) / Validation (15%) / Holdout Test (15%),
trains a baseline Ridge model strictly on Train predicting log(1 + price),
evaluates on Validation and untouched Holdout Test sets, and persists model artifact.
"""
import sys
import time
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import joblib
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config import GOLD_DIR, MODELS_DIR
from src.ml.common import (
    NUM_FEATURES, BINARY_FEATURES, TEMPORAL_FEATURES, CAT_FEATURES,
    ALL_FEATURE_COLS, split_train_val_test, compute_regression_metrics
)


def run_baseline_training(gold_path: Path = None, model_output_path: Path = None):
    """
    Trains and evaluates Ridge baseline model on Gold dataset using strict 3-way split.
    """
    gold_path = gold_path or (GOLD_DIR / "vietnam_real_estates_gold.parquet")
    model_output_path = model_output_path or (MODELS_DIR / "baseline_ridge.joblib")
    baseline_metrics_path = MODELS_DIR / "baseline_metrics.json"

    if not gold_path.exists():
        raise FileNotFoundError(f"Gold dataset not found at {gold_path}. Please run etl/features.py first!")

    print(f"[*] Starting Baseline Ridge Training Pipeline (3-Way Split: 70% Train / 15% Val / 15% Test)...")
    start_time = time.time()

    # 1. Load Gold Dataset
    print(f"[*] Loading Gold data: {gold_path}")
    table = pq.read_table(str(gold_path))
    df = table.to_pandas()
    print(f"[+] Loaded Gold records: {len(df):,}")

    # 2. Strict 3-Way Split (Train 70% / Validation 15% / Holdout Test 15%)
    train_df, val_df, test_df = split_train_val_test(df)
    print(
        f"[+] Split complete: Train={len(train_df):,} (70%), "
        f"Validation={len(val_df):,} (15%), Holdout Test={len(test_df):,} (15%)"
    )

    X_train = train_df[ALL_FEATURE_COLS].copy()
    y_log_train = train_df["log_price"].values

    X_val = val_df[ALL_FEATURE_COLS].copy()
    y_log_val = val_df["log_price"].values
    y_raw_val = val_df["price"].values

    X_test = test_df[ALL_FEATURE_COLS].copy()
    y_log_test = test_df["log_price"].values
    y_raw_test = test_df["price"].values

    # 3. Preprocessing Pipeline (Fitted strictly on X_train)
    numeric_cols = NUM_FEATURES + BINARY_FEATURES + TEMPORAL_FEATURES
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Không xác định")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True))
    ])

    preprocessor = ColumnTransformer(transformers=[
        ("num", num_pipeline, numeric_cols),
        ("cat", cat_pipeline, CAT_FEATURES)
    ])

    # 4. Select best alpha using Validation set (never touching Test set)
    best_alpha = 10.0
    best_val_rmse = float("inf")
    best_pipeline = None

    for alpha in [1.0, 10.0, 50.0]:
        candidate = Pipeline([
            ("preprocessor", preprocessor),
            ("regressor", Ridge(alpha=alpha))
        ])
        candidate.fit(X_train, y_log_train)
        val_pred_log = candidate.predict(X_val)
        val_rmse = float(np.sqrt(np.mean((y_log_val - val_pred_log) ** 2)))
        if val_rmse < best_val_rmse:
            best_val_rmse = val_rmse
            best_alpha = alpha
            best_pipeline = candidate

    baseline_model = best_pipeline
    print(f"[+] Selected Ridge alpha={best_alpha} via Validation set (Val RMSE_log={best_val_rmse:.4f})")

    # 5. Evaluate on Validation Set and Untouched Holdout Test Set
    val_pred_log = baseline_model.predict(X_val)
    val_metrics = compute_regression_metrics(y_log_val, val_pred_log, y_raw_val)

    print(f"[*] Evaluating Ridge Baseline on untouched Holdout Test Set ({len(X_test):,} samples)...")
    test_pred_log = baseline_model.predict(X_test)
    test_metrics = compute_regression_metrics(y_log_test, test_pred_log, y_raw_test)

    metrics = {
        "model": "Hồi quy tuyến tính chuẩn hóa L2 (Ridge Baseline)",
        "selected_hyperparameters": {"alpha": best_alpha},
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "val_r2_log": val_metrics["r2_log"],
        "val_rmse_log": val_metrics["rmse_log"],
        **test_metrics
    }

    # 6. Persist Model & Baseline Metrics
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(baseline_model, model_output_path)
    with open(baseline_metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    duration = time.time() - start_time
    print(f"[✓] Baseline Training Complete in {duration:.2f}s!")
    print(f"    - Model saved to: {model_output_path}")
    print(f"    - Holdout Test R² (log scale): {metrics['r2_log']:.4f}")
    print(f"    - Holdout Test RMSE (log scale): {metrics['rmse_log']:.4f}")
    print(f"    - Holdout Test MAE (Giá gốc): {metrics['mae_billion_vnd']:.2f} Tỷ VNĐ (MedAE: {metrics['medae_billion_vnd']:.2f} Tỷ)")
    print(f"    - Holdout Test MAPE: {metrics['mape_percent']:.2f}% (MdAPE: {metrics['mdape_percent']:.2f}%)")
    return baseline_model, metrics


if __name__ == "__main__":
    run_baseline_training()

