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

from src.config import BRONZE_DIR, SILVER_DIR
from src.etl.spark_session import get_spark_session, save_spark_to_parquet


def run_clean_pipeline(bronze_path: Path = None, silver_path: Path = None):
    """
    Executes PySpark cleaning step from Bronze to Silver.
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
    print(f"[+] Deduplicated: removed {raw_count - dedup_count:,} duplicate listings. Remaining: {dedup_count:,}")

    # 2. Filter out records with invalid or missing price / area (price is string in raw, cast to Double)
    df_typed = df_dedup.withColumn("price_num", F.col("price").cast(DoubleType())) \
                       .withColumn("area_num", F.col("area").cast(DoubleType()))

    df_valid = df_typed.filter(
        F.col("price_num").isNotNull() & (F.col("price_num") > 0) &
        F.col("area_num").isNotNull() & (F.col("area_num") > 0)
    )
    valid_count = df_valid.count()
    print(f"[+] Filtered positive price & area: {valid_count:,} records valid")

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

    duration = time.time() - start_time
    print(f"[✓] Silver ETL Completed in {duration:.2f}s!")
    print(f"    - Output: {silver_path}")
    print(f"    - Cleaned records: {valid_count:,}")
    return silver_path, valid_count


if __name__ == "__main__":
    run_clean_pipeline()
