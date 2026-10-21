"""
Pipeline 3 (ETL 1): Data Cleaning & Standardization (Silver Layer)
Reads Bronze Parquet with PySpark, performs data type casting, null handling,
deduplication, unit standardization (VND, m2), and writes to Silver Parquet.
"""
import sys
import time
from pathlib import Path
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
import numpy as np
from src.config import BRONZE_DIR, SILVER_DIR, DATA_QUALITY_REPORT_PATH
from src.etl.spark_session import get_spark_session, save_spark_to_parquet


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


def run_clean_pipeline(bronze_path: Path = None, silver_path: Path = None):
    """
    Executes PySpark cleaning step from Bronze to Silver and logs quantitative data quality metrics.
    """
    bronze_path = bronze_path or (BRONZE_DIR / "vietnam_real_estates_bronze.parquet")
    silver_path = silver_path or (SILVER_DIR / "vietnam_real_estates_silver.parquet")

    if not bronze_path.exists():
        raise FileNotFoundError(f"Bronze dataset not found at {bronze_path}. Please run ingestion first!")

    print(f"[*] Starting PySpark ETL Step 1: Cleaning & Silver Layer Ingestion...")
    start_time = time.time()

    spark = get_spark_session("VietnamRealEstate_ETL_Clean")

    # Read Bronze Parquet
    print(f"[*] Reading Bronze dataset: {bronze_path}")
    df = spark.read.parquet(str(bronze_path))
    raw_count = df.count()
    print(f"[+] Loaded raw Bronze records: {raw_count:,}")

    # 1. Deduplication on core unique identifiers
    df_dedup = df.dropDuplicates(["name", "province_name", "district_name", "price", "area"])
    dedup_count = df_dedup.count()
    duplicates_removed = raw_count - dedup_count
    print(f"[+] Deduplicated: removed {duplicates_removed:,} duplicate listings. Remaining: {dedup_count:,}")

    # 2. Filter out records with invalid or missing price / area (price is string in raw, cast to Double)
    df_typed = df_dedup.withColumn("price_num", F.col("price").cast(DoubleType())) \
                       .withColumn("area_num", F.col("area").cast(DoubleType()))

    # Measure specific defect counts on deduplicated records in a single aggregation pass
    defect_row = df_typed.agg(
        F.sum(F.when(F.col("price_num").isNull() | (F.col("price_num") <= 0), 1).otherwise(0)).alias("invalid_price"),
        F.sum(F.when(F.col("area_num").isNull() | (F.col("area_num") <= 0), 1).otherwise(0)).alias("invalid_area"),
        F.sum(F.when(F.col("floor_count").isNull(), 1).otherwise(0)).alias("null_floor"),
        F.sum(F.when(F.col("bedroom_count").isNull(), 1).otherwise(0)).alias("null_bedroom"),
        F.sum(F.when(F.col("frontage_width").isNull(), 1).otherwise(0)).alias("null_frontage"),
        F.sum(F.when(F.col("road_width").isNull(), 1).otherwise(0)).alias("null_road")
    ).collect()[0]

    invalid_price_count = int(defect_row["invalid_price"] or 0)
    invalid_area_count = int(defect_row["invalid_area"] or 0)

    df_valid = df_typed.filter(
        F.col("price_num").isNotNull() & (F.col("price_num") > 0) &
        F.col("area_num").isNotNull() & (F.col("area_num") > 0)
    )
    valid_count = df_valid.count()
    invalid_total_removed = dedup_count - valid_count
    print(f"[+] Filtered positive price & area: {valid_count:,} records valid (removed {invalid_total_removed:,} invalid price/area rows)")

    # 3. Handle nulls and standardize categorical and numeric fields
    df_cleaned = df_valid.select(
        # String columns (trimmed & null-imputed)
        F.trim(F.coalesce(F.col("name"), F.lit(""))).alias("name"),
        F.coalesce(F.col("description"), F.lit("")).alias("description"),
        F.trim(F.coalesce(F.col("property_type_name"), F.lit("Khác"))).alias("property_type_name"),
        F.trim(F.coalesce(F.col("province_name"), F.lit("Chưa xác định"))).alias("province_name"),
        F.trim(F.coalesce(F.col("district_name"), F.lit("Chưa xác định"))).alias("district_name"),
        F.trim(F.coalesce(F.col("ward_name"), F.lit("Chưa xác định"))).alias("ward_name"),
        F.trim(F.coalesce(F.col("street_name"), F.lit(""))).alias("street_name"),
        F.trim(F.coalesce(F.col("project_name"), F.lit(""))).alias("project_name"),
        
        # Directions
        F.trim(F.coalesce(F.col("house_direction"), F.lit("Không xác định"))).alias("house_direction"),
        F.trim(F.coalesce(F.col("balcony_direction"), F.lit("Không xác định"))).alias("balcony_direction"),
        
        # Numeric columns (cast to Double & fill realistic defaults)
        F.col("price_num").alias("price"),
        F.col("area_num").alias("area"),
        F.coalesce(F.col("floor_count").cast(DoubleType()), F.lit(1.0)).alias("floor_count"),
        F.coalesce(F.col("frontage_width").cast(DoubleType()), F.lit(0.0)).alias("frontage_width"),
        F.coalesce(F.col("house_depth").cast(DoubleType()), F.lit(0.0)).alias("house_depth"),
        F.coalesce(F.col("road_width").cast(DoubleType()), F.lit(0.0)).alias("road_width"),
        F.coalesce(F.col("bedroom_count").cast(DoubleType()), F.lit(1.0)).alias("bedroom_count"),
        F.coalesce(F.col("bathroom_count").cast(DoubleType()), F.lit(1.0)).alias("bathroom_count"),
        
        # Metadata
        F.col("published_at").cast(StringType()).alias("published_at"),
        F.col("ingested_at").alias("ingested_at"),
        F.col("batch_id").alias("batch_id")
    )

    # 4. Compute unit metrics: price_per_m2 (VND/m2) and price_billion (Tỷ VND)
    df_enriched = df_cleaned.withColumn(
        "price_per_m2",
        F.round(F.col("price") / F.col("area"), 2)
    ).withColumn(
        "price_billion",
        F.round(F.col("price") / 1e9, 4)
    )

    # 5. Write to Silver Parquet
    print(f"[*] Saving Silver dataset to: {silver_path}")
    save_spark_to_parquet(df_enriched, silver_path)

    # Compute Silver distribution stats (Before Outlier Removal in Gold)
    import pyarrow.parquet as pq
    pdf_silver = pq.read_table(str(silver_path), columns=["price_billion", "area", "price_per_m2"]).to_pandas()
    p_ser = pdf_silver["price_billion"].dropna()
    a_ser = pdf_silver["area"].dropna()
    pm2_ser = (pdf_silver["price_per_m2"].dropna() / 1e6)

    duration = time.time() - start_time
    _update_quality_report("silver_cleaning", {
        "input_bronze_records": int(raw_count),
        "duplicates_removed": int(duplicates_removed),
        "after_dedup_records": int(dedup_count),
        "missing_or_invalid_price_count": int(invalid_price_count),
        "missing_or_invalid_area_count": int(invalid_area_count),
        "total_invalid_price_or_area_removed": int(invalid_total_removed),
        "imputed_null_counts": {
            "floor_count": int(defect_row["null_floor"] or 0),
            "bedroom_count": int(defect_row["null_bedroom"] or 0),
            "frontage_width": int(defect_row["null_frontage"] or 0),
            "road_width": int(defect_row["null_road"] or 0)
        },
        "output_silver_records": int(valid_count),
        "retention_rate_percent": round(float(valid_count / max(raw_count, 1) * 100), 2),
        "stats_before_outlier_filter": {
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
                "max": round(float(pm2_ser.max()), 2)
            }
        },
        "duration_seconds": round(float(duration), 2)
    })

    print(f"[✓] Silver ETL Completed in {duration:.2f}s!")
    print(f"    - Output: {silver_path}")
    print(f"    - Cleaned records: {valid_count:,}")
    return silver_path, valid_count


if __name__ == "__main__":
    run_clean_pipeline()

