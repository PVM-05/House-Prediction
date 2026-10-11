"""
Configuration file for Vietnam Real Estate Big Data & ML Pipeline (2-Week Sprint)
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
MODELS_DIR = BASE_DIR / "models"
DOCS_DIR = BASE_DIR / "docs"

# Ensure essential directories exist
for directory in [BRONZE_DIR, SILVER_DIR, GOLD_DIR, MODELS_DIR, DOCS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Dataset Configuration
HF_DATASET_ID = "tinixai/vietnam-real-estates"
DEFAULT_SHARDS = ["shard_0000.parquet"] # Shard 0 contains ~350,000 listings

# Database Configuration (PostgreSQL with SQLite fallback)
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "real_estate")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")

POSTGRES_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
SQLITE_PATH = DATA_DIR / "real_estate.db"
SQLITE_URL = f"sqlite:///{SQLITE_PATH.as_posix()}"

# Machine Learning Configuration
TARGET_COL = "price"
LOG_TARGET_COL = "log_price"
CATEGORICAL_COLS = [
    "property_type_name",
    "province_name",
    "district_name",
    "house_direction",
    "balcony_direction"
]
NUMERICAL_COLS = [
    "area",
    "floor_count",
    "frontage_width",
    "house_depth",
    "road_width",
    "bedroom_count",
    "bathroom_count"
]
BINARY_FEATURE_COLS = [
    "has_so_do",
    "car_access",
    "is_frontage"
]
TEMPORAL_COLS = [
    "published_year",
    "published_month"
]

RANDOM_STATE = 42
TEST_SIZE = 0.2
