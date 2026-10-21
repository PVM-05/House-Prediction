"""
Pipeline 2: Ingestion & Buffer (Bronze Layer)
Downloads raw real estate listings from Hugging Face, enriches with ingestion metadata
(ingested_at, batch_id), and stores them into data/bronze/ as Bronze Parquet.
"""
import sys
import argparse
import uuid
from datetime import datetime, timezone
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow as pa
import pandas as pd
from huggingface_hub import hf_hub_download

# Support UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
from src.config import BRONZE_DIR, HF_DATASET_ID, DEFAULT_SHARDS, DATA_QUALITY_REPORT_PATH


def _update_quality_report(section_name: str, payload: dict):
    """Helper to update a section in models/data_quality_report.json."""
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


def ingest_data(shards=None, sample_size=None):
    """
    Downloads shards, enriches with ingested_at and batch_id, saves to Bronze.
    """
    shards = shards or DEFAULT_SHARDS
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    bronze_output = BRONZE_DIR / "vietnam_real_estates_bronze.parquet"
    batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    ingested_at = datetime.now(timezone.utc).isoformat()

    print(f"[*] Starting Data Ingestion Pipeline (Bronze Layer)...")
    print(f"[*] Source: Hugging Face ({HF_DATASET_ID})")
    print(f"[*] Target Shards: {shards}")
    print(f"[*] Batch ID: {batch_id}")

    tables = []
    total_records = 0
    raw_shard_records = 0

    for shard in shards:
        print(f"[*] Downloading {shard} from Hugging Face...")
        local_shard_path = hf_hub_download(
            repo_id=HF_DATASET_ID,
            filename=shard,
            repo_type="dataset"
        )
        print(f"[+] Downloaded: {local_shard_path}")
        
        # Read parquet shard
        table = pq.read_table(local_shard_path)
        raw_shard_records += table.num_rows
        if sample_size and sample_size < table.num_rows:
            table = table.slice(0, sample_size)
            print(f"[!] Sliced sample to {sample_size:,} records (out of {raw_shard_records:,} in shard).")

        # Convert to pandas or pyarrow to add metadata columns
        df = table.to_pandas()
        df["ingested_at"] = ingested_at
        df["batch_id"] = batch_id
        df["source_shard"] = shard

        arrow_table = pa.Table.from_pandas(df)
        tables.append(arrow_table)
        total_records += arrow_table.num_rows
        print(f"[+] Processed shard {shard}: {arrow_table.num_rows:,} records")

    # Combine shards
    combined_table = pa.concat_tables(tables)
    pq.write_table(combined_table, bronze_output, compression="snappy")

    output_size_mb = bronze_output.stat().st_size / (1024 * 1024)
    _update_quality_report("ingestion", {
        "dataset_id": HF_DATASET_ID,
        "source_total_shards_in_repo": 10,
        "source_total_records_in_repo": 3500744,
        "ingested_shards": list(shards),
        "downloaded_shard_total_records": int(raw_shard_records),
        "is_sampled": bool(sample_size is not None and sample_size < raw_shard_records),
        "sample_size_parameter": sample_size,
        "bronze_records": int(total_records),
        "bronze_file_size_mb": round(float(output_size_mb), 2),
        "batch_id": batch_id,
        "ingested_at": ingested_at
    })

    print(f"[✓] Bronze Ingestion Complete!")
    print(f"    - Output: {bronze_output}")
    print(f"    - Downloaded Shard Rows: {raw_shard_records:,}")
    print(f"    - Bronze Records Saved: {total_records:,}")
    print(f"    - File size: {output_size_mb:.2f} MB")
    print(f"    - Ingestion timestamp: {ingested_at}")
    return bronze_output, total_records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Vietnam Real Estate dataset into Bronze Parquet")
    parser.add_argument("--shards", nargs="+", default=DEFAULT_SHARDS, help="List of parquet shards to download")
    parser.add_argument("--sample-size", type=int, default=None, help="Sample size limit for testing")
    args = parser.parse_args()

    ingest_data(shards=args.shards, sample_size=args.sample_size)

