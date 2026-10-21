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

import json
import hashlib
import argparse
from src.config import GOLD_DIR, POSTGRES_URL, SQLITE_URL, SQLITE_PATH, DATA_QUALITY_REPORT_PATH


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


def _compute_record_ids(df: pd.DataFrame) -> pd.Series:
    """Computes a deterministic MD5 primary/unique key from core business attributes."""
    combined = (
        df["name"].astype(str) + "|" +
        df["province_name"].astype(str) + "|" +
        df["district_name"].astype(str) + "|" +
        df["price"].astype(str) + "|" +
        df["area"].astype(str)
    )
    return combined.map(lambda x: hashlib.md5(x.encode("utf-8", errors="ignore")).hexdigest())


def load_gold_to_storage(gold_path: Path = None, chunk_size: int = 5000, mode: str = "replace"):
    """
    Loads Gold Parquet into PostgreSQL with fallback to SQLite.
    Includes transaction rollback safety, unique key indexing, and post-load row count verification.
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

    # Generate deterministic record_id and ensure uniqueness
    df["record_id"] = _compute_record_ids(df)
    before_unique = len(df)
    df = df.drop_duplicates(subset=["record_id"]).copy()
    dedup_in_loader = before_unique - len(df)
    if dedup_in_loader > 0:
        print(f"[!] Removed {dedup_in_loader:,} duplicate record_id entries prior to DB load.")

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
        "record_id", "name", "property_type_name",
        "province_name", "district_name", "ward_name",
        "province_clean", "district_clean",
        "price", "price_billion", "area", "price_per_m2",
        "floor_count", "frontage_width", "house_depth", "road_width",
        "bedroom_count", "bathroom_count", "house_direction", "balcony_direction",
        "has_so_do", "car_access", "is_frontage",
        "published_at", "published_year", "published_month", "published_quarter",
        "log_price", "log_area", "batch_id"
    ]
    existing_cols = [c for c in store_cols if c in df.columns]
    df_to_save = df[existing_cols]
    expected_rows = len(df_to_save)

    print(f"[*] Writing {expected_rows:,} records into {target_db_type} table '{table_name}' (mode={mode}, chunk_size={chunk_size})...")

    # Execute inside an atomic transaction block (automatic rollback on failure)
    try:
        with engine.begin() as conn:
            if mode == "upsert":
                # Check if table exists; if so, filter out existing record_ids before appending
                try:
                    existing_ids_df = pd.read_sql(text(f"SELECT record_id FROM {table_name}"), conn)
                    existing_set = set(existing_ids_df["record_id"].tolist())
                    new_rows = df_to_save[~df_to_save["record_id"].isin(existing_set)]
                    print(f"[*] Upsert mode: {len(new_rows):,} new records to insert ({len(existing_set):,} already present).")
                    if len(new_rows) > 0:
                        new_rows.to_sql(
                            table_name,
                            conn,
                            if_exists="append",
                            index=False,
                            chunksize=chunk_size,
                            method="multi" if target_db_type == "PostgreSQL" else None
                        )
                    expected_rows = len(existing_set) + len(new_rows)
                except Exception:
                    # Table does not exist yet, create it
                    df_to_save.to_sql(
                        table_name,
                        conn,
                        if_exists="replace",
                        index=False,
                        chunksize=chunk_size,
                        method="multi" if target_db_type == "PostgreSQL" else None
                    )
            else:
                df_to_save.to_sql(
                    table_name,
                    conn,
                    if_exists="replace",
                    index=False,
                    chunksize=chunk_size,
                    method="multi" if target_db_type == "PostgreSQL" else None
                )

            # Create unique constraint index + analytical B-Tree indexes inside the same transaction
            print(f"[*] Creating unique key and analytical B-Tree indexes...")
            conn.execute(text(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_re_record_id_unique ON {table_name} (record_id);"))
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_re_province ON {table_name} (province_name);"))
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_re_district ON {table_name} (district_name);"))
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_re_property_type ON {table_name} (property_type_name);"))
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_re_price ON {table_name} (price);"))
    except Exception as tx_err:
        print(f"[!] Database transaction failed and was safely rolled back: {tx_err}")
        raise

    # Post-load verification
    with engine.connect() as conn:
        verified_count = int(conn.execute(text(f"SELECT COUNT(*) FROM {table_name};")).scalar() or 0)

    if verified_count != expected_rows:
        raise RuntimeError(
            f"Post-load row count mismatch! Expected {expected_rows:,} rows in '{table_name}', found {verified_count:,}."
        )

    duration = time.time() - start_time
    _update_quality_report("storage_verification", {
        "target_database": target_db_type,
        "table_name": table_name,
        "load_mode": mode,
        "chunk_size": chunk_size,
        "input_gold_records": int(total_records),
        "verified_db_records": int(verified_count),
        "row_count_match": bool(verified_count == expected_rows),
        "unique_key_column": "record_id",
        "indexes_created": [
            "idx_re_record_id_unique (UNIQUE)",
            "idx_re_province",
            "idx_re_district",
            "idx_re_property_type",
            "idx_re_price"
        ],
        "duration_seconds": round(float(duration), 2)
    })

    print(f"[✓] Storage Layer Completed & Verified in {duration:.2f}s!")
    print(f"    - Target Database: {target_db_type}")
    print(f"    - Table: {table_name}")
    print(f"    - Verified Row Count: {verified_count:,} / {expected_rows:,} (MATCH)")
    return target_db_type, verified_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Gold Parquet into PostgreSQL / SQLite safely")
    parser.add_argument("--mode", choices=["replace", "upsert"], default="replace", help="Load mode: replace or upsert")
    parser.add_argument("--chunk-size", type=int, default=5000, help="Batch chunk size")
    args = parser.parse_args()
    load_gold_to_storage(chunk_size=args.chunk_size, mode=args.mode)

