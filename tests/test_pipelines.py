import sys
import pytest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import joblib

from src.config import BRONZE_DIR, SILVER_DIR, GOLD_DIR, MODELS_DIR, SQLITE_PATH


def test_directories_exist():
    """Verify that all pipeline artifact directories exist."""
    assert BRONZE_DIR.exists(), "Bronze directory should exist"
    assert SILVER_DIR.exists(), "Silver directory should exist"
    assert GOLD_DIR.exists(), "Gold directory should exist"
    assert MODELS_DIR.exists(), "Models directory should exist"


def test_bronze_parquet():
    """Verify Bronze Parquet exists and contains required metadata."""
    bronze_file = BRONZE_DIR / "vietnam_real_estates_bronze.parquet"
    assert bronze_file.exists(), "Bronze parquet file should exist"
    
    table = pq.read_table(str(bronze_file))
    assert table.num_rows > 0, "Bronze dataset should not be empty"
    assert "ingested_at" in table.column_names, "Bronze must contain 'ingested_at'"
    assert "batch_id" in table.column_names, "Bronze must contain 'batch_id'"


def test_silver_parquet():
    """Verify Silver Parquet contains cleaned numeric columns."""
    silver_file = SILVER_DIR / "vietnam_real_estates_silver.parquet"
    assert silver_file.exists(), "Silver parquet file should exist"
    
    table = pq.read_table(str(silver_file))
    assert table.num_rows > 0, "Silver dataset should not be empty"
    assert "price_per_m2" in table.column_names, "Silver must contain 'price_per_m2'"
    assert "price_billion" in table.column_names, "Silver must contain 'price_billion'"


def test_gold_parquet():
    """Verify Gold Parquet contains engineered features and target transformations."""
    gold_file = GOLD_DIR / "vietnam_real_estates_gold.parquet"
    assert gold_file.exists(), "Gold parquet file should exist"
    
    table = pq.read_table(str(gold_file))
    assert table.num_rows > 0, "Gold dataset should not be empty"
    
    expected_cols = ["has_so_do", "car_access", "is_frontage", "published_year", "log_price", "log_area"]
    for col in expected_cols:
        assert col in table.column_names, f"Gold must contain '{col}'"


def test_storage_database():
    """Verify SQLite database exists and contains records in real_estate_gold."""
    assert SQLITE_PATH.exists(), "SQLite fallback database should exist"
    from sqlalchemy import create_engine, text
    engine = create_engine(f"sqlite:///{SQLITE_PATH.as_posix()}")
    with engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM real_estate_gold;")).scalar()
        assert count > 0, "Database table real_estate_gold should have records"


def test_models_and_metrics():
    """Verify ML models are saved and metrics comparison is logged."""
    baseline_file = MODELS_DIR / "baseline_ridge.joblib"
    lgbm_file = MODELS_DIR / "lgbm_model.joblib"
    metrics_file = MODELS_DIR / "metrics.json"

    assert baseline_file.exists(), "Baseline Ridge model should exist"
    assert lgbm_file.exists(), "LightGBM model should exist"
    assert metrics_file.exists(), "Metrics comparison JSON should exist"

    # Test LightGBM inference
    bundle = joblib.load(lgbm_file)
    assert "model" in bundle and "encoder" in bundle
    model = bundle["model"]
    assert hasattr(model, "predict"), "Loaded LightGBM should have predict method"


def test_single_prediction_inference():
    """Test inference logic with an example property in Hanoi."""
    lgbm_file = MODELS_DIR / "lgbm_model.joblib"
    bundle = joblib.load(lgbm_file)
    model = bundle["model"]
    encoder = bundle["encoder"]
    feature_cols = bundle["feature_cols"]
    cat_features = bundle["cat_features"]

    input_data = pd.DataFrame({
        "area": [60.0],
        "floor_count": [4.0],
        "frontage_width": [4.5],
        "house_depth": [0.0],
        "road_width": [3.5],
        "bedroom_count": [3.0],
        "bathroom_count": [3.0],
        "has_so_do": [1],
        "car_access": [1],
        "is_frontage": [0],
        "published_year": [2026],
        "published_month": [3],
        "published_quarter": [1],
        "property_type_name": ["Nhà"],
        "province_clean": ["Hà Nội"],
        "district_clean": ["Cầu Giấy"],
        "house_direction": ["Đông Nam"],
        "balcony_direction": ["Không xác định"]
    })

    input_data[cat_features] = encoder.transform(input_data[cat_features])
    for c in cat_features:
        input_data[c] = input_data[c].astype("category")

    pred_log = model.predict(input_data[feature_cols])[0]
    pred_vnd = np.expm1(pred_log)
    pred_billion = pred_vnd / 1e9

    assert pred_billion > 0.5, "House price should be realistic (> 0.5 tỷ)"
    assert pred_billion < 100.0, "House price should be realistic (< 100 tỷ)"
