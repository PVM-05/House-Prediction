"""
Pipeline 5 Helper: Generate High-Resolution EDA Charts for Report & Slides
Produces 4 standard analytical charts in docs/images/ for the project technical report.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ensure UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config import GOLD_DIR, DOCS_DIR


def generate_all_eda_charts():
    gold_path = GOLD_DIR / "vietnam_real_estates_gold.parquet"
    img_dir = DOCS_DIR / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    if not gold_path.exists():
        raise FileNotFoundError(f"Gold dataset not found at {gold_path}. Run ETL first!")

    print(f"[*] Loading Gold dataset for EDA chart generation: {gold_path}")
    table = pq.read_table(str(gold_path))
    df = table.to_pandas()
    print(f"[+] Loaded {len(df):,} records.")

    # 1. Price Distribution (Raw vs Log-transformed)
    print(f"[*] Generating: eda_price_distribution.png ...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=150)
    
    # Subplot 1: Raw Price (capped at 50 billion for visualization)
    ax1.hist(df[df["price_billion"] <= 50]["price_billion"], bins=40, color="#1f77b4", edgecolor="black", alpha=0.7)
    ax1.set_title("Phân Phối Giá Gốc (Capped 50 Tỷ VNĐ) - Right-skewed", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Giá (Tỷ VNĐ)")
    ax1.set_ylabel("Số lượng tin đăng")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    # Subplot 2: Log Price
    ax2.hist(df["log_price"], bins=40, color="#2ca02c", edgecolor="black", alpha=0.7)
    ax2.set_title("Phân Phối Sau Biến Đổi ln(1 + Price) - Bell-shaped / Gaussian", fontsize=11, fontweight="bold")
    ax2.set_xlabel("log(Price)")
    ax2.set_ylabel("Số lượng tin đăng")
    ax2.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    chart1_path = img_dir / "eda_price_distribution.png"
    plt.savefig(chart1_path)
    plt.close()
    print(f"[+] Saved: {chart1_path}")

    # 2. Correlation Matrix Heatmap
    print(f"[*] Generating: eda_correlation_matrix.png ...")
    corr_cols = ["price_billion", "area", "floor_count", "road_width", "bedroom_count", "has_so_do", "car_access", "is_frontage"]
    corr_matrix = df[corr_cols].corr()

    fig, ax = plt.subplots(figsize=(8, 7), dpi=150)
    cax = ax.matshow(corr_matrix, cmap="Blues", vmin=-0.2, vmax=1.0)
    fig.colorbar(cax)

    ticks = range(len(corr_cols))
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels(corr_cols, rotation=45, ha="left", fontsize=9)
    ax.set_yticklabels(corr_cols, fontsize=9)

    for i in range(len(corr_cols)):
        for j in range(len(corr_cols)):
            val = corr_matrix.iloc[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", color="white" if val > 0.5 else "black", fontsize=8)

    plt.title("Ma Trận Tương Quan Các Đặc Trưng (Correlation Matrix)", fontsize=11, fontweight="bold", pad=20)
    plt.tight_layout()
    chart2_path = img_dir / "eda_correlation_matrix.png"
    plt.savefig(chart2_path)
    plt.close()
    print(f"[+] Saved: {chart2_path}")

    # 3. Top Provinces Median Price
    print(f"[*] Generating: eda_province_prices.png ...")
    top_provs = df["province_name"].value_counts().head(8).index
    prov_stats = df[df["province_name"].isin(top_provs)].groupby("province_name")["price_billion"].median().sort_values()

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    bars = ax.barh(prov_stats.index, prov_stats.values, color="#e6550d", alpha=0.85, edgecolor="black")
    ax.set_title("Giá Trung Vị Bất Động Sản Theo Top Tỉnh/Thành Phố (Tỷ VNĐ)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Giá Trung Vị (Tỷ VNĐ)")
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    for bar in bars:
        ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height()/2, f"{bar.get_width():.2f} Tỷ", va="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    chart3_path = img_dir / "eda_province_prices.png"
    plt.savefig(chart3_path)
    plt.close()
    print(f"[+] Saved: {chart3_path}")

    # 4. Property Types Comparison
    print(f"[*] Generating: eda_property_types.png ...")
    type_stats = df.groupby("property_type_name").agg(
        median_price=("price_billion", "median"),
        median_m2=("price_per_m2", lambda x: np.median(x) / 1e6)
    ).sort_values("median_price", ascending=False)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    bars = ax.bar(type_stats.index, type_stats["median_price"], color="#756bb1", alpha=0.85, edgecolor="black")
    ax.set_title("Giá Trung Vị Theo Loại Hình Bất Động Sản (Tỷ VNĐ)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Giá Trung Vị (Tỷ VNĐ)")
    plt.xticks(rotation=20, ha="right", fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, f"{bar.get_height():.2f} Tỷ", ha="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    chart4_path = img_dir / "eda_property_types.png"
    plt.savefig(chart4_path)
    plt.close()
    print(f"[+] Saved: {chart4_path}")

    print(f"\n[✓] All 4 EDA charts successfully generated in {img_dir}!")


if __name__ == "__main__":
    generate_all_eda_charts()
