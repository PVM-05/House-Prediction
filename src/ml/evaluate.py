"""
Pipeline 6 (ML 3): Model Diagnostics, Feature Importance & Geographic Error Analysis
Analyzes feature importances, computes regional error distributions (Hà Nội, TP.HCM, etc.),
generates visualizations and exports diagnostics to models/error_analysis.json.
"""
import sys
import time
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config import GOLD_DIR, MODELS_DIR


def run_evaluation(gold_path: Path = None, model_path: Path = None):
    """
    Evaluates LightGBM model, plots feature importance and performs regional error breakdown.
    """
    gold_path = gold_path or (GOLD_DIR / "vietnam_real_estates_gold.parquet")
    model_path = model_path or (MODELS_DIR / "lgbm_model.joblib")
    fig_path = MODELS_DIR / "feature_importance.png"
    report_path = MODELS_DIR / "error_analysis.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run train_lgbm.py first!")

    print(f"[*] Starting Model Evaluation & Error Diagnostics Pipeline...")
    start_time = time.time()

    # 1. Load model bundle
    bundle = joblib.load(model_path)
    model = bundle["model"]
    encoder = bundle["encoder"]
    feature_cols = bundle["feature_cols"]
    num_features = bundle["num_features"]
    binary_features = bundle["binary_features"]
    temporal_features = bundle["temporal_features"]
    cat_features = bundle["cat_features"]

    # 2. Load Gold dataset
    table = pq.read_table(str(gold_path))
    df = table.to_pandas()

    # Prepare features
    X = df[feature_cols].copy()
    for col in num_features:
        X[col] = pd.to_numeric(X[col], errors="coerce").fillna(X[col].median())
    for col in binary_features + temporal_features:
        X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0).astype(int)
    for col in cat_features:
        X[col] = X[col].astype(str).fillna("Không xác định")

    X[cat_features] = encoder.transform(X[cat_features])
    for c in cat_features:
        X[c] = X[c].astype("category")

    # 3. Predict prices
    print(f"[*] Running predictions across {len(df):,} listings...")
    pred_log = model.predict(X)
    pred_raw = np.expm1(pred_log)
    df["predicted_price"] = pred_raw
    df["predicted_price_billion"] = pred_raw / 1e9
    df["abs_error_billion"] = np.abs(df["price_billion"] - df["predicted_price_billion"])
    df["ape_percent"] = (df["abs_error_billion"] / df["price_billion"]) * 100

    # 4. Feature Importance
    print(f"[*] Computing feature importances...")
    importances = model.feature_importances_
    feat_imp = pd.DataFrame({
        "feature": feature_cols,
        "importance": importances
    }).sort_values("importance", ascending=True)

    # Plot & Save
    plt.figure(figsize=(10, 6), dpi=150)
    plt.barh(feat_imp["feature"], feat_imp["importance"], color="#2b5c8f")
    plt.title("LightGBM Feature Importance (Vietnam Real Estate Price Prediction)", fontsize=12, fontweight="bold")
    plt.xlabel("Importance (Split count)")
    plt.tight_layout()
    plt.savefig(fig_path)
    plt.close()
    print(f"[+] Saved feature importance plot to: {fig_path}")

    # 5. Geographic Error Analysis by Province
    print(f"[*] Analyzing prediction error by geographic province...")
    prov_analysis = df.groupby("province_name").agg(
        listing_count=("price", "count"),
        median_actual_billion=("price_billion", "median"),
        median_pred_billion=("predicted_price_billion", "median"),
        mae_billion=("abs_error_billion", "mean"),
        mape_percent=("ape_percent", "median")
    ).reset_index()

    prov_top = prov_analysis[prov_analysis["listing_count"] >= 50].sort_values("listing_count", ascending=False)

    print("\n" + "=" * 80)
    print(f"{'Province':<22} | {'Listings':<10} | {'Med. Price (B)':<15} | {'MAE (B)':<10} | {'Med. MAPE (%)':<12}")
    print("-" * 80)
    for _, row in prov_top.head(8).iterrows():
        print(f"{row['province_name']:<22} | {int(row['listing_count']):<10} | {row['median_actual_billion']:<15.2f} | {row['mae_billion']:<10.2f} | {row['mape_percent']:<12.1f}")
    print("=" * 80 + "\n")

    # Export report
    report = {
        "overall_median_mape": round(float(df["ape_percent"].median()), 2),
        "overall_mean_mae_billion": round(float(df["abs_error_billion"].mean()), 2),
        "top_features": feat_imp.sort_values("importance", ascending=False).to_dict(orient="records"),
        "top_provinces_error": prov_top.to_dict(orient="records")
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[+] Exported error diagnostics to: {report_path}")

    duration = time.time() - start_time
    print(f"[✓] Evaluation complete in {duration:.2f}s!")
    return report


if __name__ == "__main__":
    run_evaluation()
