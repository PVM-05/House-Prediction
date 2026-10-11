"""
Pipeline 6 (ML 1): Baseline Ridge Regression Model
Splits Gold dataset into Train/Test, trains a baseline Ridge model predicting log(price),
evaluates RMSE, MAE, MAPE, R2 without data leakage, and persists model artifact.
"""
import sys
import time
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config import GOLD_DIR, MODELS_DIR, RANDOM_STATE, TEST_SIZE


def run_baseline_training(gold_path: Path = None, model_output_path: Path = None):
    """
    Trains and evaluates Ridge baseline model on Gold dataset.
    """
    gold_path = gold_path or (GOLD_DIR / "vietnam_real_estates_gold.parquet")
    model_output_path = model_output_path or (MODELS_DIR / "baseline_ridge.joblib")

    if not gold_path.exists():
        raise FileNotFoundError(f"Gold dataset not found at {gold_path}. Please run etl/features.py first!")

    print(f"[*] Starting Baseline Ridge Training Pipeline...")
    start_time = time.time()

    # 1. Load Gold Dataset
    print(f"[*] Loading Gold data: {gold_path}")
    table = pq.read_table(str(gold_path))
    df = table.to_pandas()
    print(f"[+] Loaded records: {len(df):,}")

    # Features selection
    num_features = [
        "area", "floor_count", "frontage_width", "house_depth",
        "road_width", "bedroom_count", "bathroom_count"
    ]
    binary_features = ["has_so_do", "car_access", "is_frontage"]
    cat_features = ["property_type_name", "province_name", "district_name"]

    all_features = num_features + binary_features + cat_features
    X = df[all_features].copy()
    y_log = df["log_price"].values
    y_raw = df["price"].values

    # 2. Strict Train/Test Split (Prevent Data Leakage)
    X_train, X_test, y_log_train, y_log_test, y_raw_train, y_raw_test = train_test_split(
        X, y_log, y_raw, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    print(f"[+] Data split: Train={len(X_train):,}, Test={len(X_test):,} (test_size={TEST_SIZE})")

    # 3. Preprocessing Pipeline
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Khác")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(transformers=[
        ("num", num_pipeline, num_features + binary_features),
        ("cat", cat_pipeline, cat_features)
    ])

    # 4. Model Pipeline (Ridge Regression)
    baseline_model = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", Ridge(alpha=10.0))
    ])

    print(f"[*] Fitting Ridge regression model...")
    baseline_model.fit(X_train, y_log_train)

    # 5. Prediction & Inverse Transformation
    print(f"[*] Evaluating on Test Set...")
    pred_log = baseline_model.predict(X_test)
    pred_raw = np.expm1(pred_log)

    # 6. Evaluation Metrics
    rmse_log = np.sqrt(mean_squared_error(y_log_test, pred_log))
    r2 = r2_score(y_log_test, pred_log)
    
    # In Billion VND scale
    y_raw_billion = y_raw_test / 1e9
    pred_raw_billion = pred_raw / 1e9
    mae_billion = mean_absolute_error(y_raw_billion, pred_raw_billion)
    rmse_billion = np.sqrt(mean_squared_error(y_raw_billion, pred_raw_billion))
    
    # MAPE (filter extreme zeros if any)
    valid_mask = y_raw_test > 0
    mape = np.mean(np.abs((y_raw_test[valid_mask] - pred_raw[valid_mask]) / y_raw_test[valid_mask])) * 100

    metrics = {
        "model": "Ridge (Baseline)",
        "rmse_log": round(float(rmse_log), 4),
        "r2_score": round(float(r2), 4),
        "mae_billion_vnd": round(float(mae_billion), 4),
        "rmse_billion_vnd": round(float(rmse_billion), 4),
        "mape_percent": round(float(mape), 2),
        "train_samples": len(X_train),
        "test_samples": len(X_test)
    }

    # 7. Persist Model
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(baseline_model, model_output_path)

    duration = time.time() - start_time
    print(f"[✓] Baseline Training Complete in {duration:.2f}s!")
    print(f"    - Model saved to: {model_output_path}")
    print(f"    - R² Score: {r2:.4f}")
    print(f"    - RMSE (log): {rmse_log:.4f}")
    print(f"    - MAE: {mae_billion:.2f} Tỷ VNĐ")
    print(f"    - MAPE: {mape:.2f}%")
    return baseline_model, metrics


if __name__ == "__main__":
    run_baseline_training()
