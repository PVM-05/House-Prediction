"""
Pipeline 5 (Storage Layer): Load Gold Data into PostgreSQL
Reads Gold Parquet and loads into PostgreSQL database (with automatic SQLite fallback).
Creates necessary indices for low-latency queries and reporting.
"""
import sys
import time
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
from sqlalchemy import create_engine, text

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config import GOLD_DIR, POSTGRES_URL, SQLITE_URL, SQLITE_PATH


def load_gold_to_storage(gold_path: Path = None, chunk_size: int = 5000):
    """
    Loads Gold Parquet into PostgreSQL with fallback to SQLite.
    """
    gold_path = gold_path or (GOLD_DIR / "vietnam_real_estates_gold.parquet")
    if not gold_path.exists():
        raise FileNotFoundError(f"Gold dataset not found at {gold_path}. Please run etl/features.py first!")

    print(f"[*] Starting Storage Ingestion Pipeline (Gold Layer)...")
    print(f"[*] Source: {gold_path}")

    # Read Gold data
    table = pq.read_table(str(gold_path))
    df = table.to_pandas()
    total_records = len(df)
    print(f"[+] Loaded Gold records: {total_records:,}")

    # Try connecting to PostgreSQL
    engine = None
    target_db_type = "PostgreSQL"
    
    try:
        pg_engine = create_engine(POSTGRES_URL, connect_args={"connect_timeout": 3})
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        engine = pg_engine
        print(f"[+] Successfully connected to PostgreSQL at {POSTGRES_URL}")
    except Exception as e:
        print(f"[!] PostgreSQL connection unavailable ({e}).")
        print(f"[!] Falling back seamlessly to SQLite database at {SQLITE_PATH}")
        print(f"    (Tip: Run 'docker compose up -d' to start the local PostgreSQL service)")
        SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(SQLITE_URL)
        target_db_type = "SQLite"

    start_time = time.time()
    table_name = "real_estate_gold"

    # Select columns to store
    store_cols = [
        "name", "property_type_name", "province_name", "district_name", "ward_name",
        "price", "price_billion", "area", "price_per_m2",
        "floor_count", "frontage_width", "house_depth", "road_width",
        "bedroom_count", "bathroom_count", "house_direction", "balcony_direction",
        "has_so_do", "car_access", "is_frontage",
        "published_at", "published_year", "published_month", "published_quarter",
        "log_price", "log_area", "batch_id"
    ]
    existing_cols = [c for c in store_cols if c in df.columns]
    df_to_save = df[existing_cols]

    print(f"[*] Writing {len(df_to_save):,} records into {target_db_type} table '{table_name}'...")
    df_to_save.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False,
        chunksize=chunk_size,
        method="multi" if target_db_type == "PostgreSQL" else None
    )

    # Create indexes for fast query performance
    print(f"[*] Creating database indexes for analytical queries...")
    with engine.connect() as conn:
        try:
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_re_province ON {table_name} (province_name);"))
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_re_district ON {table_name} (district_name);"))
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_re_property_type ON {table_name} (property_type_name);"))
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_re_price ON {table_name} (price);"))
            conn.commit()
            print(f"[+] Indexes created successfully.")
        except Exception as idx_err:
            print(f"[!] Index creation note: {idx_err}")

    duration = time.time() - start_time
    print(f"[✓] Storage Layer Completed in {duration:.2f}s!")
    print(f"    - Target Database: {target_db_type}")
    print(f"    - Table: {table_name}")
    print(f"    - Records stored: {len(df_to_save):,}")
    return target_db_type, len(df_to_save)


if __name__ == "__main__":
    load_gold_to_storage()
