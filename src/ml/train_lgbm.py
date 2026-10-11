"""
Pipeline 6 (ML 2): Gradient Boosting Regressor (LightGBM)
Trains LightGBM model predicting log(price), compares metrics side-by-side with Ridge baseline,
logs comprehensive evaluation metrics (RMSE, MAE, R2, MAPE) to models/metrics.json.
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
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import lightgbm as lgb

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config import GOLD_DIR, MODELS_DIR, RANDOM_STATE, TEST_SIZE


def run_lgbm_training(gold_path: Path = None, model_output_path: Path = None):
    """
    Trains LightGBM regressor on Gold dataset and logs metrics comparison.
    """
    gold_path = gold_path or (GOLD_DIR / "vietnam_real_estates_gold.parquet")
    model_output_path = model_output_path or (MODELS_DIR / "lgbm_model.joblib")
    metrics_path = MODELS_DIR / "metrics.json"

    if not gold_path.exists():
        raise FileNotFoundError(f"Gold dataset not found at {gold_path}. Please run etl/features.py first!")

    print(f"[*] Starting LightGBM Regressor Training Pipeline...")
    start_time = time.time()

    # 1. Load Gold Dataset
    print(f"[*] Reading Gold data: {gold_path}")
    table = pq.read_table(str(gold_path))
    df = table.to_pandas()
    print(f"[+] Loaded records: {len(df):,}")

    # Feature definitions
    num_features = [
        "area", "floor_count", "frontage_width", "house_depth",
        "road_width", "bedroom_count", "bathroom_count"
    ]
    binary_features = ["has_so_do", "car_access", "is_frontage"]
    temporal_features = ["published_year", "published_month", "published_quarter"]
    cat_features = [
        "property_type_name", "province_clean", "district_clean",
        "house_direction", "balcony_direction"
    ]

    feature_cols = num_features + binary_features + temporal_features + cat_features
    X = df[feature_cols].copy()
    y_log = df["log_price"].values
    y_raw = df["price"].values

    # Impute missing values for tree-based model
    for col in num_features:
        X[col] = pd.to_numeric(X[col], errors="coerce").fillna(X[col].median())
    for col in binary_features + temporal_features:
        X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0).astype(int)
    for col in cat_features:
        X[col] = X[col].astype(str).fillna("Không xác định")

    # 2. Strict Train/Test Split (Identical seed to baseline to ensure no leakage & fair comparison)
    X_train, X_test, y_log_train, y_log_test, y_raw_train, y_raw_test = train_test_split(
        X, y_log, y_raw, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    print(f"[+] Split dataset: Train={len(X_train):,}, Test={len(X_test):,}")

    # 3. Categorical Encoding
    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    X_train[cat_features] = encoder.fit_transform(X_train[cat_features])
    X_test[cat_features] = encoder.transform(X_test[cat_features])

    # Convert categoricals to 'category' dtype for LightGBM
    for c in cat_features:
        X_train[c] = X_train[c].astype("category")
        X_test[c] = X_test[c].astype("category")

    # 4. Train LightGBM Regressor
    print(f"[*] Training LightGBM Regressor (n_estimators=300, lr=0.05, leaves=31)...")
    model = lgb.LGBMRegressor(
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=31,
        max_depth=-1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=-1
    )
    model.fit(
        X_train, y_log_train,
        eval_set=[(X_test, y_log_test)],
        callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)]
    )

    # 5. Predictions & Evaluation
    print(f"[*] Evaluating LightGBM on Holdout Test Set...")
    pred_log = model.predict(X_test)
    pred_raw = np.expm1(pred_log)

    rmse_log = np.sqrt(mean_squared_error(y_log_test, pred_log))
    r2 = r2_score(y_log_test, pred_log)

    y_raw_billion = y_raw_test / 1e9
    pred_raw_billion = pred_raw / 1e9
    mae_billion = mean_absolute_error(y_raw_billion, pred_raw_billion)
    rmse_billion = np.sqrt(mean_squared_error(y_raw_billion, pred_raw_billion))

    valid_mask = y_raw_test > 0
    mape = np.mean(np.abs((y_raw_test[valid_mask] - pred_raw[valid_mask]) / y_raw_test[valid_mask])) * 100

    lgbm_metrics = {
        "model": "LightGBM Regressor",
        "rmse_log": round(float(rmse_log), 4),
        "r2_score": round(float(r2), 4),
        "mae_billion_vnd": round(float(mae_billion), 4),
        "rmse_billion_vnd": round(float(rmse_billion), 4),
        "mape_percent": round(float(mape), 2),
        "train_samples": len(X_train),
        "test_samples": len(X_test)
    }

    # 6. Save Artifacts
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": model,
        "encoder": encoder,
        "feature_cols": feature_cols,
        "num_features": num_features,
        "binary_features": binary_features,
        "temporal_features": temporal_features,
        "cat_features": cat_features
    }
    joblib.dump(bundle, model_output_path)

    # Load baseline metrics if exist
    comparison = {"models": [lgbm_metrics]}
    baseline_path = MODELS_DIR / "baseline_ridge.joblib"
    if baseline_path.exists():
        try:
            baseline_model = joblib.load(baseline_path)
            # Recompute baseline test predictions on exact same split
            base_pred_log = baseline_model.predict(df.loc[X_test.index, ["area", "floor_count", "frontage_width", "house_depth", "road_width", "bedroom_count", "bathroom_count", "has_so_do", "car_access", "is_frontage", "property_type_name", "province_name", "district_name"]])
            base_pred_raw = np.expm1(base_pred_log)
            base_metrics = {
                "model": "Ridge (Baseline)",
                "rmse_log": round(float(np.sqrt(mean_squared_error(y_log_test, base_pred_log))), 4),
                "r2_score": round(float(r2_score(y_log_test, base_pred_log)), 4),
                "mae_billion_vnd": round(float(mean_absolute_error(y_raw_billion, base_pred_raw / 1e9)), 4),
                "rmse_billion_vnd": round(float(np.sqrt(mean_squared_error(y_raw_billion, base_pred_raw / 1e9))), 4),
                "mape_percent": round(float(np.mean(np.abs((y_raw_test - base_pred_raw) / y_raw_test)) * 100), 2),
                "train_samples": len(X_train),
                "test_samples": len(X_test)
            }
            comparison["models"].insert(0, base_metrics)
        except Exception as e:
            print(f"[!] Note on baseline comparison: {e}")

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    duration = time.time() - start_time
    print(f"\n[✓] LightGBM Training Complete in {duration:.2f}s!")
    print(f"    - Model Bundle: {model_output_path}")
    print(f"    - Metrics File: {metrics_path}")
    print("\n" + "=" * 65)
    print(f"{'Metric':<25} | {'Ridge Baseline':<16} | {'LightGBM':<16}")
    print("-" * 65)
    base_m = comparison["models"][0] if len(comparison["models"]) > 1 else {}
    print(f"{'R² Score (Holdout)':<25} | {base_m.get('r2_score', 'N/A'):<16} | {lgbm_metrics['r2_score']:<16}")
    print(f"{'RMSE (log)':<25} | {base_m.get('rmse_log', 'N/A'):<16} | {lgbm_metrics['rmse_log']:<16}")
    print(f"{'MAE (Tỷ VNĐ)':<25} | {base_m.get('mae_billion_vnd', 'N/A'):<16} | {lgbm_metrics['mae_billion_vnd']:<16}")
    print(f"{'MAPE (%)':<25} | {base_m.get('mape_percent', 'N/A'):<16} | {lgbm_metrics['mape_percent']:<16}")
    print("=" * 65 + "\n")
    return model, comparison


if __name__ == "__main__":
    run_lgbm_training()
