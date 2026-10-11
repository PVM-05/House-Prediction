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

from src.config import SILVER_DIR, GOLD_DIR
from src.etl.spark_session import get_spark_session, save_spark_to_parquet


def run_features_pipeline(silver_path: Path = None, gold_path: Path = None):
    """
    Executes PySpark feature engineering step from Silver to Gold.
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
    print(f"[+] Outlier filtering complete: removed {silver_count - filtered_count:,} outliers. Remaining: {filtered_count:,}")

    # 2. Address Normalization (Clean province & district names)
    df_addr = df_filtered.withColumn(
        "province_clean",
        F.regexp_replace(
            F.regexp_replace(F.col("province_name"), r"^(Thành phố|Tỉnh)\s+", ""),
            r"^(TP\.|Tp\.)\s*", ""
        )
    ).withColumn(
        "district_clean",
        F.regexp_replace(F.col("district_name"), r"^(Quận|Huyện|Thị xã|TP\.|Thành phố)\s+", "")
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

    duration = time.time() - start_time
    print(f"[✓] Gold Feature Engineering Completed in {duration:.2f}s!")
    print(f"    - Output: {gold_path}")
    print(f"    - Gold records: {filtered_count:,}")
    return gold_path, filtered_count


if __name__ == "__main__":
    run_features_pipeline()
