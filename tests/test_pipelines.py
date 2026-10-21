import sys
import json
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

from src.config import (
    BRONZE_DIR, SILVER_DIR, GOLD_DIR, MODELS_DIR,
    DOCS_DIR, SQLITE_PATH, DATA_QUALITY_REPORT_PATH
)
from src.ml.common import split_train_val_test, prepare_inference_dataframe


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
    
    expected_cols = [
        "province_clean", "district_clean",
        "has_so_do", "car_access", "is_frontage",
        "published_year", "published_month", "published_quarter",
        "log_price", "log_area"
    ]
    for col in expected_cols:
        assert col in table.column_names, f"Gold must contain '{col}'"


def test_data_quality_and_lineage_report():
    """Verify quantitative Data Quality & Lineage report exists and tracks all stages."""
    assert DATA_QUALITY_REPORT_PATH.exists(), "models/data_quality_report.json should exist"
    with open(DATA_QUALITY_REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert "ingestion" in report, "Report must contain ingestion section"
    assert "silver_cleaning" in report, "Report must contain silver_cleaning section"
    assert "gold_feature_engineering" in report, "Report must contain gold_feature_engineering section"
    assert "storage_verification" in report, "Report must contain storage_verification section"

    b_rows = report["ingestion"]["bronze_records"]
    s_rows = report["silver_cleaning"]["output_silver_records"]
    g_rows = report["gold_feature_engineering"]["output_gold_records"]
    assert b_rows >= s_rows >= g_rows > 0, "Row counts must decrease monotonically from Bronze -> Silver -> Gold"


def test_storage_database():
    """Verify PostgreSQL (or SQLite fallback) contains real_estate_gold with unique record_id."""
    from sqlalchemy import create_engine, text
    from src.config import POSTGRES_URL, SQLITE_URL

    engine = None
    try:
        pg_engine = create_engine(POSTGRES_URL, connect_args={"connect_timeout": 3})
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        engine = pg_engine
    except Exception:
        assert SQLITE_PATH.exists(), "SQLite fallback database should exist when PostgreSQL is offline"
        engine = create_engine(SQLITE_URL)

    with engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM real_estate_gold;")).scalar()
        assert count > 0, "Database table real_estate_gold should have records"
        distinct_ids = conn.execute(text("SELECT count(distinct record_id) FROM real_estate_gold;")).scalar()
        assert count == distinct_ids, "Every row in real_estate_gold must have a unique record_id"



def test_three_way_split_and_metrics_no_leakage():
    """Verify 3-way Train/Validation/Test split is strictly disjoint and both models share the exact Test set."""
    gold_file = GOLD_DIR / "vietnam_real_estates_gold.parquet"
    df = pq.read_table(str(gold_file), columns=["price", "log_price", "area"]).to_pandas()
    train_df, val_df, test_df = split_train_val_test(df)

    # Disjoint index verification
    assert set(train_df.index).isdisjoint(set(val_df.index)), "Train and Validation sets must be disjoint"
    assert set(train_df.index).isdisjoint(set(test_df.index)), "Train and Test sets must be disjoint"
    assert set(val_df.index).isdisjoint(set(test_df.index)), "Validation and Test sets must be disjoint"
    assert len(train_df) + len(val_df) + len(test_df) == len(df), "Splits must sum to total Gold records"

    metrics_file = MODELS_DIR / "metrics.json"
    assert metrics_file.exists(), "Metrics comparison JSON should exist"
    with open(metrics_file, "r", encoding="utf-8") as f:
        m_data = json.load(f)

    assert "split_protocol" in m_data, "metrics.json must document split_protocol"
    assert len(m_data["models"]) == 2, "Both Ridge and LightGBM must be evaluated"
    ridge_m, lgbm_m = m_data["models"][0], m_data["models"][1]
    assert ridge_m["test_samples"] == lgbm_m["test_samples"] == len(test_df), "Both models must evaluate on identical Holdout Test set"
    assert lgbm_m["r2_log"] > ridge_m["r2_log"], "LightGBM should outperform Ridge baseline on log R2"


def test_train_serving_consistency_and_inference():
    """Verify prepare_inference_dataframe guarantees 100% column/encoding consistency between Training and Streamlit."""
    lgbm_file = MODELS_DIR / "lgbm_model.joblib"
    bundle = joblib.load(lgbm_file)
    model = bundle["model"]
    feature_cols = bundle["feature_cols"]

    assert "numeric_medians" in bundle, "Model bundle must store training numeric_medians"
    assert "location_catalog" in bundle, "Model bundle must store cascading location_catalog"

    raw_user_input = {
        "area": 65.0,
        "floor_count": 4.0,
        "frontage_width": 4.5,
        "house_depth": 0.0,  # Should automatically impute with training median
        "road_width": 3.5,
        "bedroom_count": 3.0,
        "bathroom_count": 3.0,
        "has_so_do": 1,
        "car_access": 1,
        "is_frontage": 0,
        "property_type_name": "Nhà",
        "province_clean": "Thành phố Hà Nội",  # Should normalize to "Hà Nội"
        "district_clean": "Quận Cầu Giấy",     # Should normalize to "Cầu Giấy"
        "house_direction": "Đông Nam",
        "balcony_direction": "Không xác định"
    }

    df_in = prepare_inference_dataframe(raw_user_input, bundle)
    assert list(df_in.columns) == feature_cols, "Inference DataFrame columns must match training feature_cols order"
    assert float(df_in["house_depth"].iloc[0]) > 0.0, "Zero house_depth must be imputed with training median"

    pred_log = float(model.predict(df_in)[0])
    pred_billion = float(np.expm1(pred_log)) / 1e9
    assert 0.5 < pred_billion < 100.0, f"Predicted Hanoi house price should be realistic, got {pred_billion:.2f} tỷ"


def test_evaluation_diagnostics_and_residual_plot():
    """Verify Feature Importance and Residual Analysis plots and Holdout Test error report exist."""
    feat_img = MODELS_DIR / "feature_importance.png"
    res_img = MODELS_DIR / "residual_analysis.png"
    err_json = MODELS_DIR / "error_analysis.json"

    assert feat_img.exists(), "feature_importance.png must exist"
    assert res_img.exists(), "residual_analysis.png must exist"
    assert err_json.exists(), "error_analysis.json must exist"

    with open(err_json, "r", encoding="utf-8") as f:
        err_data = json.load(f)
    assert "residual_summary" in err_data, "error_analysis.json must include residual_summary"
    assert err_data["test_samples_count"] > 0, "Evaluation must run on Holdout Test samples"


def test_pipeline_summary_metrics_and_charts():
    """Verify that automated pipeline summary JSON/CSV and all 6 analytical charts exist."""
    json_path = MODELS_DIR / "pipeline_summary_metrics.json"
    csv_path = MODELS_DIR / "pipeline_summary_metrics.csv"
    assert json_path.exists(), "models/pipeline_summary_metrics.json must exist"
    assert csv_path.exists(), "models/pipeline_summary_metrics.csv must exist"

    with open(json_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    for section in ["scale", "quality", "etl_efficiency", "descriptive_statistics", "performance", "storage"]:
        assert section in summary, f"Summary metrics must contain '{section}'"

    csv_df = pd.read_csv(csv_path)
    assert len(csv_df) >= 15, "Summary KPI CSV should have at least 15 rows of metrics"

    img_dir = DOCS_DIR / "images"
    expected_charts = [
        "00_architecture_flowchart.png",
        "01_pipeline_funnel_retention.png",
        "02_data_quality_missing_analysis.png",
        "03_distribution_outlier_analysis.png",
        "04_market_distribution.png",
        "07_pipeline_performance_storage.png"
    ]
    for chart in expected_charts:
        chart_file = img_dir / chart
        assert chart_file.exists(), f"Analytical chart '{chart}' must exist in docs/images/"


def test_smart_query_engine():
    """Verify Smart Query & Smart Answer engine handles natural language queries and returns 5-part structure."""
    from src.serving.smart_query_engine import SmartQueryEngine
    gold_path = GOLD_DIR / "vietnam_real_estates_gold.parquet"
    summary_path = MODELS_DIR / "pipeline_summary_metrics.json"

    assert gold_path.exists(), "Gold parquet must exist for smart query engine test"
    df = pq.read_table(str(gold_path)).to_pandas()
    summary = {}
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

    engine = SmartQueryEngine(df, summary)

    # Test 1: Compare provinces
    res1 = engine.execute_smart_query("So sánh giá nhà trung vị ở Hà Nội và TP. Hồ Chí Minh")
    assert res1["status"] == "success"
    assert res1["intent"]["intent_type"] == "COMPARE_PROVINCES"
    assert len(res1["conclusion"]) > 20
    assert res1["chart_data"] is not None and len(res1["chart_data"]) == 2
    assert len(res1["follow_ups"]) >= 2
    assert res1["exec_time_ms"] < 2000, "Query must execute in under 2 seconds"

    # Test 2: Filter search
    res2 = engine.execute_smart_query("nhà dưới 5 tỷ, diện tích trên 80 m² ở Hà Nội")
    assert res2["status"] == "success"
    assert res2["intent"]["intent_type"] == "FILTER_SEARCH"
    assert "Hà Nội" in res2["intent"]["provinces"]
    assert res2["intent"]["max_price"] == 5.0
    assert res2["intent"]["min_area"] == 80.0
    assert "Tìm thấy" in res2["conclusion"]

    # Test 3: Data Quality audit
    res3 = engine.execute_smart_query("Kiểm tra chất lượng dữ liệu Gold")
    assert res3["status"] == "success"
    assert res3["intent"]["intent_type"] == "DATA_QUALITY_AUDIT"
    assert "loại bỏ an toàn" in res3["conclusion"]

    # Test 4: Contextual follow-up
    res4 = engine.execute_smart_query("còn TP. Hồ Chí Minh thì sao?", context={"last_intent": "COMPARE_PROVINCES", "last_provinces": ["Hà Nội"]})
    assert res4["status"] == "success"
    assert "Hồ Chí Minh" in res4["intent"]["provinces"]


