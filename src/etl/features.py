"""
Pipeline 4 (ETL 2): Feature Engineering & Gold Layer Transformation
Reads Silver Parquet, removes outliers, normalizes addresses, extracts regex NLP features
(sổ đỏ, ngõ ô tô, mặt tiền), parses temporal features, and writes to Gold Parquet.
"""
import sys
import time
from pathlib import Path
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, DoubleType

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import re
import json
import numpy as np
from src.config import SILVER_DIR, GOLD_DIR, DATA_QUALITY_REPORT_PATH
from src.etl.spark_session import get_spark_session, save_spark_to_parquet


def normalize_province_str(val: str) -> str:
    """Shared deterministic province name normalization for ETL, Training, and Serving."""
    if not val:
        return "Chưa xác định"
    s = str(val).strip()
    s = re.sub(r"^(Thành phố|Tỉnh)\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^(TP\.|Tp\.)\s*", "", s, flags=re.IGNORECASE)
    return s.strip() or "Chưa xác định"


def normalize_district_str(val: str) -> str:
    """Shared deterministic district name normalization for ETL, Training, and Serving."""
    if not val:
        return "Chưa xác định"
    s = str(val).strip()
    s = re.sub(r"^(Quận|Huyện|Thị xã|TP\.|Thành phố)\s+", "", s, flags=re.IGNORECASE)
    return s.strip() or "Chưa xác định"


def _update_quality_report(section_name: str, payload: dict):
    DATA_QUALITY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {}
    if DATA_QUALITY_REPORT_PATH.exists():
        try:
            with open(DATA_QUALITY_REPORT_PATH, "r", encoding="utf-8") as f:
                report = json.load(f)
        except Exception:
            report = {}
    report[section_name] = payload
    with open(DATA_QUALITY_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def run_features_pipeline(silver_path: Path = None, gold_path: Path = None):
    """
    Executes PySpark feature engineering step from Silver to Gold and logs quality metrics.
    """
    silver_path = silver_path or (SILVER_DIR / "vietnam_real_estates_silver.parquet")
    gold_path = gold_path or (GOLD_DIR / "vietnam_real_estates_gold.parquet")

    if not silver_path.exists():
        raise FileNotFoundError(f"Silver dataset not found at {silver_path}. Please run etl/clean.py first!")

    print(f"[*] Starting PySpark ETL Step 2: Feature Engineering & Gold Layer Transformation...")
    start_time = time.time()

    spark = get_spark_session("VietnamRealEstate_ETL_Features")

    print(f"[*] Reading Silver dataset: {silver_path}")
    df = spark.read.parquet(str(silver_path))
    silver_count = df.count()
    print(f"[+] Loaded Silver records: {silver_count:,}")

    # Measure outlier counts by rule in a single aggregation pass
    outlier_stats = df.agg(
        F.sum(F.when((F.col("area") < 10.0) | (F.col("area") > 5000.0), 1).otherwise(0)).alias("area_outliers"),
        F.sum(F.when((F.col("price") < 1e8) | (F.col("price") > 5e11), 1).otherwise(0)).alias("price_outliers"),
        F.sum(F.when((F.col("price_per_m2") < 2e6) | (F.col("price_per_m2") > 1e9), 1).otherwise(0)).alias("unit_price_outliers"),
        F.sum(F.when((F.col("floor_count") > 25.0) | (F.col("bedroom_count") > 20.0), 1).otherwise(0)).alias("structure_outliers")
    ).collect()[0]

    # 1. Outlier Filtering (Domain-specific thresholds for Vietnam Real Estate)
    # - Area: 10 m2 <= area <= 5,000 m2
    # - Total Price: 100,000,000 VND (100 triệu) <= price <= 500,000,000,000 VND (500 tỷ)
    # - Price per m2: 2,000,000 VND/m2 <= price_per_m2 <= 1,000,000,000 VND/m2 (1 tỷ/m2)
    # - Realistic floor & bedroom count
    df_filtered = df.filter(
        (F.col("area") >= 10.0) & (F.col("area") <= 5000.0) &
        (F.col("price") >= 1e8) & (F.col("price") <= 5e11) &
        (F.col("price_per_m2") >= 2e6) & (F.col("price_per_m2") <= 1e9) &
        (F.col("floor_count") <= 25.0) &
        (F.col("bedroom_count") <= 20.0)
    )
    filtered_count = df_filtered.count()
    outliers_removed = silver_count - filtered_count
    print(f"[+] Outlier filtering complete: removed {outliers_removed:,} outliers. Remaining: {filtered_count:,}")

    # 2. Address Normalization (Clean province & district names)
    df_addr = df_filtered.withColumn(
        "province_clean",
        F.trim(
            F.regexp_replace(
                F.regexp_replace(F.col("province_name"), r"^(Thành phố|Tỉnh)\s+", ""),
                r"^(TP\.|Tp\.)\s*", ""
            )
        )
    ).withColumn(
        "district_clean",
        F.trim(
            F.regexp_replace(F.col("district_name"), r"^(Quận|Huyện|Thị xã|TP\.|Thành phố)\s+", "")
        )
    )

    # 3. NLP Feature Extraction from Name & Description
    df_text = df_addr.withColumn(
        "_combined_text",
        F.lower(F.concat_ws(" ", F.col("name"), F.col("description")))
    )

    # Features: Sổ đỏ/hồng, Ngõ ô tô, Nhà mặt tiền/mặt phố
    df_feats = df_text.withColumn(
        "has_so_do",
        F.when(
            F.col("_combined_text").rlike(r"(sổ đỏ|sổ hồng|pháp lý chuẩn|chính chủ|sẵn sổ)"),
            F.lit(1)
        ).otherwise(F.lit(0)).cast(IntegerType())
    ).withColumn(
        "car_access",
        F.when(
            F.col("_combined_text").rlike(r"(ô tô|oto|xe hơi|đường rộng|tránh nhau|vào tận nhà)"),
            F.lit(1)
        ).otherwise(F.lit(0)).cast(IntegerType())
    ).withColumn(
        "is_frontage",
        F.when(
            F.col("_combined_text").rlike(r"(mặt phố|mặt tiền|kinh doanh|vỉa hè)"),
            F.lit(1)
        ).otherwise(F.lit(0)).cast(IntegerType())
    ).drop("_combined_text")

    # 4. Temporal Features from published_at
    df_temporal = df_feats.withColumn(
        "published_date",
        F.to_date(F.col("published_at"))
    ).withColumn(
        "published_year",
        F.coalesce(F.year(F.col("published_date")), F.lit(2025)).cast(IntegerType())
    ).withColumn(
        "published_month",
        F.coalesce(F.month(F.col("published_date")), F.lit(6)).cast(IntegerType())
    ).withColumn(
        "published_quarter",
        F.coalesce(F.quarter(F.col("published_date")), F.lit(2)).cast(IntegerType())
    ).drop("published_date")

    # 5. ML Target and Log Transformations
    df_gold = df_temporal.withColumn(
        "log_price",
        F.round(F.log1p(F.col("price")), 6)
    ).withColumn(
        "log_area",
        F.round(F.log1p(F.col("area")), 6)
    )

    # 6. Write Gold Parquet
    print(f"[*] Saving Gold dataset to: {gold_path}")
    save_spark_to_parquet(df_gold, gold_path)

    # Compute post-cleaning stats from Gold Parquet
    import pyarrow.parquet as pq
    pdf_gold = pq.read_table(
        str(gold_path),
        columns=["price_billion", "area", "price_per_m2", "has_so_do", "car_access", "is_frontage", "province_clean", "district_clean"]
    ).to_pandas()

    p_ser = pdf_gold["price_billion"].dropna()
    a_ser = pdf_gold["area"].dropna()
    pm2_ser = (pdf_gold["price_per_m2"].dropna() / 1e6)

    duration = time.time() - start_time
    _update_quality_report("gold_feature_engineering", {
        "input_silver_records": int(silver_count),
        "outlier_breakdown": {
            "area_outside_10_to_5000_m2": int(outlier_stats["area_outliers"] or 0),
            "price_outside_100M_to_500B_vnd": int(outlier_stats["price_outliers"] or 0),
            "price_per_m2_outside_2M_to_1B_vnd": int(outlier_stats["unit_price_outliers"] or 0),
            "structure_floors_gt_25_or_bedrooms_gt_20": int(outlier_stats["structure_outliers"] or 0),
            "total_outliers_removed": int(outliers_removed)
        },
        "output_gold_records": int(filtered_count),
        "gold_to_silver_retention_percent": round(float(filtered_count / max(silver_count, 1) * 100), 2),
        "distinct_provinces": int(pdf_gold["province_clean"].nunique()),
        "distinct_districts": int(pdf_gold["district_clean"].nunique()),
        "nlp_extracted_features": {
            "has_so_do_count": int(pdf_gold["has_so_do"].sum()),
            "has_so_do_percent": round(float(pdf_gold["has_so_do"].mean() * 100), 2),
            "car_access_count": int(pdf_gold["car_access"].sum()),
            "car_access_percent": round(float(pdf_gold["car_access"].mean() * 100), 2),
            "is_frontage_count": int(pdf_gold["is_frontage"].sum()),
            "is_frontage_percent": round(float(pdf_gold["is_frontage"].mean() * 100), 2)
        },
        "stats_after_cleaning": {
            "price_billion": {
                "min": round(float(p_ser.min()), 4),
                "p10": round(float(np.percentile(p_ser, 10)), 4),
                "p25": round(float(np.percentile(p_ser, 25)), 4),
                "median": round(float(p_ser.median()), 4),
                "mean": round(float(p_ser.mean()), 4),
                "p75": round(float(np.percentile(p_ser, 75)), 4),
                "p90": round(float(np.percentile(p_ser, 90)), 4),
                "max": round(float(p_ser.max()), 2),
                "std": round(float(p_ser.std()), 4)
            },
            "area_m2": {
                "min": round(float(a_ser.min()), 2),
                "p10": round(float(np.percentile(a_ser, 10)), 2),
                "p25": round(float(np.percentile(a_ser, 25)), 2),
                "median": round(float(a_ser.median()), 2),
                "mean": round(float(a_ser.mean()), 2),
                "p75": round(float(np.percentile(a_ser, 75)), 2),
                "p90": round(float(np.percentile(a_ser, 90)), 2),
                "max": round(float(a_ser.max()), 2),
                "std": round(float(a_ser.std()), 2)
            },
            "price_per_m2_million": {
                "median": round(float(pm2_ser.median()), 2),
                "mean": round(float(pm2_ser.mean()), 2),
                "p25": round(float(np.percentile(pm2_ser, 25)), 2),
                "p75": round(float(np.percentile(pm2_ser, 75)), 2),
                "max": round(float(pm2_ser.max()), 2)
            }
        },
        "duration_seconds": round(float(duration), 2)
    })

    print(f"[✓] Gold Feature Engineering Completed in {duration:.2f}s!")
    print(f"    - Output: {gold_path}")
    print(f"    - Gold records: {filtered_count:,}")
    return gold_path, filtered_count


if __name__ == "__main__":
    run_features_pipeline()

