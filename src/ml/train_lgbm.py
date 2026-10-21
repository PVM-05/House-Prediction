"""
Pipeline 6 (ML 2): Gradient Boosting Regressor (LightGBM)
- Splits Gold dataset into disjoint Train (70%) / Validation (15%) / Holdout Test (15%).
- Fits imputers (medians) and OrdinalEncoder strictly on Train set.
- Uses Validation set ONLY for early_stopping and hyperparameter verification.
- Evaluates both Ridge and LightGBM on the untouched Holdout Test set (both log-price and Billion VND scales).
- Saves complete model + preprocessor + location catalog bundle to models/lgbm_model.joblib.
"""
import sys
import time
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import joblib
from sklearn.preprocessing import OrdinalEncoder
import lightgbm as lgb

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config import GOLD_DIR, MODELS_DIR, RANDOM_STATE
from src.ml.common import (
    NUM_FEATURES, BINARY_FEATURES, TEMPORAL_FEATURES, CAT_FEATURES,
    ALL_FEATURE_COLS, split_train_val_test, compute_regression_metrics,
    build_location_catalog
)


def _preprocess_split(
    df_split: pd.DataFrame,
    numeric_medians: dict,
    encoder: OrdinalEncoder,
    fit_encoder: bool = False
) -> pd.DataFrame:
    """Applies training-set medians and categorical encoding without data leakage."""
    X = df_split[ALL_FEATURE_COLS].copy()
    for col in NUM_FEATURES:
        s = pd.to_numeric(X[col], errors="coerce").fillna(numeric_medians[col])
        if col == "house_depth" and numeric_medians.get("house_depth", 0.0) > 0:
            s = s.mask(s <= 0, numeric_medians["house_depth"])
        X[col] = s
    for col in BINARY_FEATURES + TEMPORAL_FEATURES:
        X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0).astype(int)
    for col in CAT_FEATURES:
        X[col] = X[col].astype(str).fillna("Không xác định")

    if fit_encoder:
        X[CAT_FEATURES] = encoder.fit_transform(X[CAT_FEATURES])
    else:
        X[CAT_FEATURES] = encoder.transform(X[CAT_FEATURES])

    for c in CAT_FEATURES:
        X[c] = X[c].astype("category")
    return X


def run_lgbm_training(gold_path: Path = None, model_output_path: Path = None):
    """
    Trains LightGBM regressor on Gold dataset with strict Train/Val/Test separation.
    """
    gold_path = gold_path or (GOLD_DIR / "vietnam_real_estates_gold.parquet")
    model_output_path = model_output_path or (MODELS_DIR / "lgbm_model.joblib")
    metrics_path = MODELS_DIR / "metrics.json"

    if not gold_path.exists():
        raise FileNotFoundError(f"Gold dataset not found at {gold_path}. Please run etl/features.py first!")

    print(f"[*] Starting LightGBM Regressor Training Pipeline (Strict 3-Way Split)...")
    start_time = time.time()

    # 1. Load Gold Dataset
    print(f"[*] Reading Gold data: {gold_path}")
    table = pq.read_table(str(gold_path))
    df = table.to_pandas()
    print(f"[+] Loaded Gold records: {len(df):,}")

    # 2. Deterministic 3-Way Split: Train (70%), Validation (15%), Holdout Test (15%)
    train_df, val_df, test_df = split_train_val_test(df, random_state=RANDOM_STATE)
    print(
        f"[+] Split dataset: Train={len(train_df):,} (70%), "
        f"Validation={len(val_df):,} (15%), Holdout Test={len(test_df):,} (15%)"
    )

    # 3. Compute Imputation Statistics & Fit Categorical Encoder STRICTLY on Train Set
    numeric_medians = {}
    for col in NUM_FEATURES:
        s = pd.to_numeric(train_df[col], errors="coerce")
        if col == "house_depth":
            pos_s = s[s > 0]
            numeric_medians[col] = float(pos_s.median()) if len(pos_s) > 0 else 0.0
        else:
            numeric_medians[col] = float(s.median()) if not np.isnan(s.median()) else 0.0

    default_temporal = {
        "published_year": int(pd.to_numeric(train_df["published_year"], errors="coerce").median() or 2025),
        "published_month": int(pd.to_numeric(train_df["published_month"], errors="coerce").median() or 6),
        "published_quarter": int(pd.to_numeric(train_df["published_quarter"], errors="coerce").median() or 2)
    }

    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    X_train = _preprocess_split(train_df, numeric_medians, encoder, fit_encoder=True)
    X_val = _preprocess_split(val_df, numeric_medians, encoder, fit_encoder=False)
    X_test = _preprocess_split(test_df, numeric_medians, encoder, fit_encoder=False)

    y_log_train = train_df["log_price"].values
    y_log_val = val_df["log_price"].values
    y_raw_val = val_df["price"].values
    y_log_test = test_df["log_price"].values
    y_raw_test = test_df["price"].values

    # 4. Train LightGBM Regressor using Validation Set ONLY for early stopping
    print(f"[*] Training LightGBM Regressor (early_stopping monitored on Validation set ONLY)...")
    model = lgb.LGBMRegressor(
        n_estimators=500,
        learning_rate=0.05,
        num_leaves=63,
        max_depth=-1,
        min_child_samples=25,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=-1
    )
    model.fit(
        X_train, y_log_train,
        eval_set=[(X_val, y_log_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)]
    )
    best_iter = int(getattr(model, "best_iteration_", model.n_estimators) or model.n_estimators)
    print(f"[+] LightGBM converged at best_iteration={best_iter} (monitored on Validation set)")

    # 5. Evaluate on Validation Set and Untouched Holdout Test Set
    val_pred_log = model.predict(X_val)
    val_metrics = compute_regression_metrics(y_log_val, val_pred_log, y_raw_val)

    print(f"[*] Evaluating LightGBM on untouched Holdout Test Set ({len(X_test):,} samples)...")
    test_pred_log = model.predict(X_test)
    test_metrics = compute_regression_metrics(y_log_test, test_pred_log, y_raw_test)

    lgbm_metrics = {
        "model": "Cây quyết định tăng cường độ dốc (LightGBM Regressor)",
        "selected_hyperparameters": {
            "n_estimators": 500,
            "best_iteration": best_iter,
            "learning_rate": 0.05,
            "num_leaves": 63,
            "min_child_samples": 25
        },
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "val_r2_log": val_metrics["r2_log"],
        "val_rmse_log": val_metrics["rmse_log"],
        **test_metrics
    }

    # 6. Build Location Catalog & Save Complete Artifact Bundle
    print(f"[*] Building cascading location catalog for Train-Serving consistency...")
    location_catalog = build_location_catalog(df)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": model,
        "encoder": encoder,
        "feature_cols": ALL_FEATURE_COLS,
        "num_features": NUM_FEATURES,
        "binary_features": BINARY_FEATURES,
        "temporal_features": TEMPORAL_FEATURES,
        "cat_features": CAT_FEATURES,
        "numeric_medians": numeric_medians,
        "default_temporal": default_temporal,
        "location_catalog": location_catalog,
        "test_r2_log": test_metrics["r2_log"],
        "test_mdape_percent": test_metrics["mdape_percent"]
    }
    joblib.dump(bundle, model_output_path)

    # 7. Compare Side-by-Side with Ridge Baseline on the EXACT Same Holdout Test Set
    comparison = {
        "split_protocol": {
            "total_gold_records": len(df),
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "test_samples": len(X_test),
            "split_ratios": "70% Huấn luyện (Train) / 15% Kiểm định (Validation) / 15% Kiểm thử độc lập (Test)",
            "random_state": RANDOM_STATE,
            "early_stopping_set": "Tập Kiểm định (Validation 15%)",
            "final_evaluation_set": "Tập Kiểm thử độc lập (Holdout Test 15%)",
            "target_transformation": "log1p(price_vnd) -> dự báo -> expm1(pred_log)"
        },
        "models": []
    }

    baseline_path = MODELS_DIR / "baseline_ridge.joblib"
    if baseline_path.exists():
        try:
            baseline_model = joblib.load(baseline_path)
            base_val_pred_log = baseline_model.predict(val_df[ALL_FEATURE_COLS])
            base_val_m = compute_regression_metrics(y_log_val, base_val_pred_log, y_raw_val)

            base_test_pred_log = baseline_model.predict(test_df[ALL_FEATURE_COLS])
            base_test_m = compute_regression_metrics(y_log_test, base_test_pred_log, y_raw_test)

            base_metrics = {
                "model": "Hồi quy tuyến tính chuẩn hóa L2 (Ridge Baseline)",
                "train_samples": len(X_train),
                "val_samples": len(X_val),
                "test_samples": len(X_test),
                "val_r2_log": base_val_m["r2_log"],
                "val_rmse_log": base_val_m["rmse_log"],
                **base_test_m
            }
            comparison["models"].append(base_metrics)
        except Exception as e:
            print(f"[!] Note on baseline comparison: {e}")

    comparison["models"].append(lgbm_metrics)

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    duration = time.time() - start_time
    print(f"\n[✓] LightGBM Training Complete in {duration:.2f}s!")
    print(f"    - Model Bundle: {model_output_path}")
    print(f"    - Metrics File: {metrics_path}")
    print("\n" + "=" * 78)
    print(f"{'Chỉ số (Trên Tập Kiểm Thử Độc Lập 15%)':<38} | {'Ridge Baseline':<17} | {'LightGBM':<17}")
    print("-" * 78)
    base_m = comparison["models"][0] if len(comparison["models"]) > 1 else {}
    print(f"{'Hệ số xác định R² (Thang log)':<38} | {base_m.get('r2_log', 'N/A'):<17} | {lgbm_metrics['r2_log']:<17}")
    print(f"{'Sai số RMSE (Thang log)':<38} | {base_m.get('rmse_log', 'N/A'):<17} | {lgbm_metrics['rmse_log']:<17}")
    print(f"{'Sai số MAE (Giá gốc - Tỷ VNĐ)':<38} | {base_m.get('mae_billion_vnd', 'N/A'):<17} | {lgbm_metrics['mae_billion_vnd']:<17}")
    print(f"{'Sai số trung vị MedAE (Tỷ VNĐ)':<38} | {base_m.get('medae_billion_vnd', 'N/A'):<17} | {lgbm_metrics['medae_billion_vnd']:<17}")
    print(f"{'Sai số phần trăm MAPE (%)':<38} | {base_m.get('mape_percent', 'N/A'):<17} | {lgbm_metrics['mape_percent']:<17}")
    print(f"{'Sai số phần trăm trung vị MdAPE (%)':<38} | {base_m.get('mdape_percent', 'N/A'):<17} | {lgbm_metrics['mdape_percent']:<17}")
    print("=" * 78 + "\n")
    return model, comparison


if __name__ == "__main__":
    run_lgbm_training()

