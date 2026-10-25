"""
Pipeline 6 (ML 3): Model Diagnostics, Feature Importance, Residual Analysis & Geographic Error Breakdown
- Evaluates strictly on the untouched 15% Holdout Test set (zero data leakage).
- Generates Feature Importance chart (models/feature_importance.png & docs/images/05_feature_importance.png).
- Generates Actual vs. Predicted & Residual Distribution chart (models/residual_analysis.png & docs/images/06_residual_analysis.png).
- Computes regional error breakdown on Holdout Test set and exports to models/error_analysis.json.
"""
import sys
import time
import json
import shutil
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

from src.config import GOLD_DIR, MODELS_DIR, DOCS_DIR, RANDOM_STATE
from src.ml.common import (
    FEATURE_VIETNAMESE_LABELS, split_train_val_test, compute_regression_metrics
)
from src.ml.train_lgbm import _preprocess_split


def run_evaluation(gold_path: Path = None, model_path: Path = None):
    """
    Evaluates LightGBM model strictly on Holdout Test Set, plots feature importance + residual diagnostics,
    and performs regional error breakdown.
    """
    gold_path = gold_path or (GOLD_DIR / "vietnam_real_estates_gold.parquet")
    model_path = model_path or (MODELS_DIR / "lgbm_model.joblib")
    fig_imp_path = MODELS_DIR / "feature_importance.png"
    fig_res_path = MODELS_DIR / "residual_analysis.png"
    report_path = MODELS_DIR / "error_analysis.json"
    docs_img_dir = DOCS_DIR / "images"
    docs_img_dir.mkdir(parents=True, exist_ok=True)

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run train_lgbm.py first!")

    print(f"[*] Starting Model Evaluation & Diagnostics Pipeline (Holdout Test Set ONLY)...")
    start_time = time.time()

    # 1. Load model bundle
    bundle = joblib.load(model_path)
    model = bundle["model"]
    encoder = bundle["encoder"]
    feature_cols = bundle["feature_cols"]
    numeric_medians = bundle.get("numeric_medians", {})

    # 2. Load Gold dataset and extract ONLY the untouched 15% Holdout Test split
    table = pq.read_table(str(gold_path))
    df_all = table.to_pandas()
    train_df, val_df, test_df = split_train_val_test(df_all, random_state=RANDOM_STATE)
    print(
        f"[+] Extracted untouched Holdout Test Set: {len(test_df):,} records "
        f"(excluded {len(train_df):,} Train and {len(val_df):,} Validation records)"
    )

    # 3. Preprocess Holdout Test Set using Training medians and encoder
    X_test = _preprocess_split(test_df, numeric_medians, encoder, fit_encoder=False)
    y_log_test = test_df["log_price"].values
    y_raw_test = test_df["price"].values

    # 4. Predict on Holdout Test Set
    print(f"[*] Running predictions on {len(test_df):,} Holdout Test listings...")
    pred_log = model.predict(X_test)
    pred_log_safe = np.clip(pred_log, a_min=10.0, a_max=30.0)
    pred_raw = np.expm1(pred_log_safe)

    test_df = test_df.copy()
    test_df["predicted_log_price"] = pred_log_safe
    test_df["residual_log"] = pred_log_safe - y_log_test
    test_df["predicted_price"] = pred_raw
    test_df["predicted_price_billion"] = pred_raw / 1e9
    test_df["abs_error_billion"] = np.abs(test_df["price_billion"] - test_df["predicted_price_billion"])
    test_df["ape_percent"] = (test_df["abs_error_billion"] / test_df["price_billion"].clip(lower=1e-4)) * 100.0

    overall_test_metrics = compute_regression_metrics(y_log_test, pred_log_safe, y_raw_test)

    # 5. Plot 1: Feature Importance (Vietnamese labels)
    print(f"[*] Generating Feature Importance chart...")
    importances = model.feature_importances_
    feat_imp = pd.DataFrame({
        "feature": feature_cols,
        "feature_vi": [FEATURE_VIETNAMESE_LABELS.get(f, f) for f in feature_cols],
        "importance": [int(x) for x in importances]
    }).sort_values("importance", ascending=True)

    plt.figure(figsize=(10, 6.5), dpi=150)
    bars = plt.barh(feat_imp["feature_vi"], feat_imp["importance"], color="#1e40af", edgecolor="#1e3a8a")
    plt.title("Mức Độ Quan Trọng Của Các Đặc Trưng (Mô Hình LightGBM)", fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("Số lần phân nhánh tối ưu trên cây quyết định", fontsize=10)
    plt.grid(axis="x", linestyle="--", alpha=0.4)
    for bar in bars:
        width = bar.get_width()
        plt.text(width + max(feat_imp["importance"]) * 0.01, bar.get_y() + bar.get_height() / 2,
                 f"{int(width)}", va="center", ha="left", fontsize=8.5, color="#1e293b")
    plt.xlim(0, max(feat_imp["importance"]) * 1.12)
    plt.tight_layout()
    plt.savefig(fig_imp_path)
    plt.close()
    shutil.copy2(fig_imp_path, docs_img_dir / "05_feature_importance.png")
    print(f"[+] Saved Feature Importance plot to: {fig_imp_path}")

    # 6. Plot 2: Actual vs. Predicted & Residual Distribution (on Holdout Test Set)
    print(f"[*] Generating Actual vs. Predicted and Residual Distribution plots...")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), dpi=150)

    # Panel A: Actual vs Predicted (Log scale with Billion VND secondary reference)
    ax1 = axes[0]
    sample_n = min(5000, len(test_df))
    sample_plot = test_df.sample(n=sample_n, random_state=RANDOM_STATE)
    ax1.scatter(
        sample_plot["log_price"],
        sample_plot["predicted_log_price"],
        alpha=0.25,
        s=12,
        color="#0284c7",
        label=f"Mẫu kiểm thử (n={sample_n:,})"
    )
    min_v = float(min(sample_plot["log_price"].min(), sample_plot["predicted_log_price"].min()))
    max_v = float(max(sample_plot["log_price"].max(), sample_plot["predicted_log_price"].max()))
    ax1.plot([min_v, max_v], [min_v, max_v], color="#dc2626", linestyle="--", linewidth=1.8, label="Đường lý tưởng (Dự đoán = Thực tế)")
    ax1.set_title(
        f"Giá Thực Tế vs. Giá Dự Đoán (Tập Kiểm Thử Độc Lập)\n"
        f"R² = {overall_test_metrics['r2_log']:.4f} | RMSE(log) = {overall_test_metrics['rmse_log']:.4f}",
        fontsize=11, fontweight="bold"
    )
    ax1.set_xlabel("Log(1 + Giá thực tế VNĐ)", fontsize=10)
    ax1.set_ylabel("Log(1 + Giá dự đoán VNĐ)", fontsize=10)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.35)

    # Panel B: Residual Histogram (pred_log - actual_log)
    ax2 = axes[1]
    residuals = test_df["residual_log"].clip(lower=-2.5, upper=2.5)
    mean_res = float(test_df["residual_log"].mean())
    median_res = float(test_df["residual_log"].median())
    ax2.hist(residuals, bins=60, color="#059669", edgecolor="white", alpha=0.85)
    ax2.axvline(0.0, color="#dc2626", linestyle="--", linewidth=1.8, label="Sai số = 0")
    ax2.axvline(mean_res, color="#1d4ed8", linestyle=":", linewidth=1.5, label=f"Trung bình sai số = {mean_res:+.4f}")
    ax2.set_title(
        f"Phân Phối Sai Số Phần Dư (Sai số phần dư = Log Dự Đoán - Log Thực Tế)\n"
        f"Trung vị sai số = {median_res:+.4f} | MdAPE = {overall_test_metrics['mdape_percent']:.2f}%",
        fontsize=11, fontweight="bold"
    )
    ax2.set_xlabel("Sai số phần dư trên thang logarit", fontsize=10)
    ax2.set_ylabel("Số lượng bất động sản kiểm thử", fontsize=10)
    ax2.legend(loc="upper right", fontsize=9)
    ax2.grid(True, linestyle="--", alpha=0.35)

    plt.tight_layout()
    plt.savefig(fig_res_path)
    plt.close()
    shutil.copy2(fig_res_path, docs_img_dir / "06_residual_analysis.png")
    print(f"[+] Saved Residual Analysis plot to: {fig_res_path}")

    # 7. Geographic Error Analysis by Province (Strictly on Holdout Test Set)
    print(f"[*] Analyzing prediction error by geographic province on Holdout Test Set...")
    prov_analysis = test_df.groupby("province_clean").agg(
        listing_count=("price", "count"),
        median_actual_billion=("price_billion", "median"),
        median_pred_billion=("predicted_price_billion", "median"),
        mae_billion=("abs_error_billion", "mean"),
        medae_billion=("abs_error_billion", "median"),
        mape_percent=("ape_percent", "mean"),
        mdape_percent=("ape_percent", "median")
    ).reset_index().rename(columns={"province_clean": "province_name"})

    min_count_threshold = max(10, int(len(test_df) * 0.003))
    prov_top = prov_analysis[prov_analysis["listing_count"] >= min_count_threshold].sort_values("listing_count", ascending=False)
    for col_round in ["median_actual_billion", "median_pred_billion", "mae_billion", "medae_billion", "mape_percent", "mdape_percent"]:
        prov_top[col_round] = prov_top[col_round].round(2)

    print("\n" + "=" * 88)
    print(f"{'Tỉnh / Thành (Tập Test)':<24} | {'Số mẫu Test':<11} | {'Giá TV (Tỷ)':<12} | {'MedAE (Tỷ)':<11} | {'MdAPE (%)':<11}")
    print("-" * 88)
    for _, row in prov_top.head(10).iterrows():
        print(
            f"{str(row['province_name']):<24} | {int(row['listing_count']):<11} | "
            f"{row['median_actual_billion']:<12.2f} | {row['medae_billion']:<11.2f} | {row['mdape_percent']:<11.2f}"
        )
    print("=" * 88 + "\n")

    # Export report
    report = {
        "evaluation_dataset": "Tập Kiểm Thử Độc Lập (Holdout Test Set - 15%)",
        "test_samples_count": int(len(test_df)),
        "overall_metrics": overall_test_metrics,
        "residual_summary": {
            "mean_log_residual": round(float(test_df["residual_log"].mean()), 5),
            "median_log_residual": round(float(test_df["residual_log"].median()), 5),
            "std_log_residual": round(float(test_df["residual_log"].std()), 4),
            "within_20_percent_error_rate": round(float((test_df["ape_percent"] <= 20.0).mean() * 100), 2),
            "within_30_percent_error_rate": round(float((test_df["ape_percent"] <= 30.0).mean() * 100), 2)
        },
        "overall_median_mape": overall_test_metrics["mdape_percent"],
        "overall_mean_mae_billion": overall_test_metrics["mae_billion_vnd"],
        "top_features": feat_imp.sort_values("importance", ascending=False).to_dict(orient="records"),
        "top_provinces_error": prov_top.to_dict(orient="records")
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[+] Exported Holdout Test diagnostics to: {report_path}")

    duration = time.time() - start_time
    print(f"[✓] Evaluation complete in {duration:.2f}s!")
    return report


if __name__ == "__main__":
    run_evaluation()

