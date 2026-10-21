"""
Shared ML utilities for Vietnam Real Estate Price Prediction:
- Deterministic 3-way split: Train (70%) / Validation (15%) / Holdout Test (15%)
- Dual-scale evaluation metrics: Log-price scale (log1p) and Original price scale (Billion VND)
- Shared Train-Serving preprocessing & inference consistency
"""
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, median_absolute_error, r2_score

from src.config import RANDOM_STATE, TRAIN_RATIO, VAL_RATIO, TEST_RATIO
from src.etl.features import normalize_province_str, normalize_district_str

NUM_FEATURES = [
    "area", "floor_count", "frontage_width", "house_depth",
    "road_width", "bedroom_count", "bathroom_count"
]
BINARY_FEATURES = ["has_so_do", "car_access", "is_frontage"]
TEMPORAL_FEATURES = ["published_year", "published_month", "published_quarter"]
CAT_FEATURES = [
    "property_type_name", "province_clean", "district_clean",
    "house_direction", "balcony_direction"
]
ALL_FEATURE_COLS = NUM_FEATURES + BINARY_FEATURES + TEMPORAL_FEATURES + CAT_FEATURES

FEATURE_VIETNAMESE_LABELS = {
    "area": "Diện tích đất/sàn (m²)",
    "district_clean": "Quận / Huyện",
    "province_clean": "Tỉnh / Thành phố",
    "frontage_width": "Chiều rộng mặt tiền (m)",
    "road_width": "Độ rộng đường trước nhà (m)",
    "bedroom_count": "Số phòng ngủ",
    "floor_count": "Số tầng",
    "bathroom_count": "Số phòng vệ sinh",
    "house_depth": "Chiều sâu thửa đất (m)",
    "property_type_name": "Loại hình bất động sản",
    "house_direction": "Hướng nhà",
    "balcony_direction": "Hướng ban công",
    "published_month": "Tháng đăng tin",
    "published_year": "Năm đăng tin",
    "published_quarter": "Quý đăng tin",
    "car_access": "Ngõ ô tô vào được",
    "has_so_do": "Có Sổ đỏ / Sổ hồng",
    "is_frontage": "Nhà mặt tiền kinh doanh"
}


def split_train_val_test(
    df: pd.DataFrame,
    random_state: int = RANDOM_STATE
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits Gold DataFrame into strictly disjoint Train (70%), Validation (15%), and Holdout Test (15%).
    - Train: Used strictly for fitting preprocessors, imputers, encoders, and model weights.
    - Validation: Used strictly for hyperparameter selection and LightGBM early_stopping.
    - Test: Untouched holdout set used ONLY for final model evaluation and diagnostics.
    """
    holdout_total = VAL_RATIO + TEST_RATIO  # 0.30
    train_df, temp_df = train_test_split(
        df,
        test_size=holdout_total,
        random_state=random_state
    )
    relative_test_ratio = TEST_RATIO / holdout_total  # 0.50 of 0.30 = 0.15
    val_df, test_df = train_test_split(
        temp_df,
        test_size=relative_test_ratio,
        random_state=random_state
    )
    return train_df.copy(), val_df.copy(), test_df.copy()


def compute_regression_metrics(
    y_log_true: np.ndarray,
    y_log_pred: np.ndarray,
    y_raw_true: np.ndarray
) -> Dict[str, float]:
    """
    Computes comprehensive evaluation metrics on both:
    1. Log-transformed target scale: log(1 + price_vnd)
    2. Original price scale: Billion VND (Tỷ VNĐ) via inverse transform expm1(y_log_pred)
    """
    # Clip extreme log predictions to prevent numerical overflow during expm1
    y_log_pred_safe = np.clip(y_log_pred, a_min=10.0, a_max=30.0)
    pred_raw = np.expm1(y_log_pred_safe)

    # 1. Log-scale metrics
    rmse_log = float(np.sqrt(mean_squared_error(y_log_true, y_log_pred_safe)))
    mae_log = float(mean_absolute_error(y_log_true, y_log_pred_safe))
    r2_log = float(r2_score(y_log_true, y_log_pred_safe))

    # 2. Original scale metrics (in Tỷ VNĐ = 10^9 VND)
    y_true_billion = y_raw_true / 1e9
    y_pred_billion = pred_raw / 1e9

    mae_billion = float(mean_absolute_error(y_true_billion, y_pred_billion))
    medae_billion = float(median_absolute_error(y_true_billion, y_pred_billion))
    rmse_billion = float(np.sqrt(mean_squared_error(y_true_billion, y_pred_billion)))

    valid_mask = y_raw_true > 0
    ape_pct = np.abs((y_raw_true[valid_mask] - pred_raw[valid_mask]) / y_raw_true[valid_mask]) * 100.0
    mape_pct = float(np.mean(ape_pct))
    mdape_pct = float(np.median(ape_pct))

    return {
        "r2_score": round(r2_log, 4),
        "r2_log": round(r2_log, 4),
        "rmse_log": round(rmse_log, 4),
        "mae_log": round(mae_log, 4),
        "mae_billion_vnd": round(mae_billion, 4),
        "medae_billion_vnd": round(medae_billion, 4),
        "rmse_billion_vnd": round(rmse_billion, 4),
        "mape_percent": round(mape_pct, 2),
        "mdape_percent": round(mdape_pct, 2)
    }


def build_location_catalog(df_gold: pd.DataFrame) -> Dict[str, Any]:
    """
    Builds a hierarchical catalog of Provinces -> Districts -> Wards with listing counts
    and median prices from the Gold dataset to power smart cascading selection in Streamlit.
    """
    catalog = {
        "provinces": [],
        "districts_by_province": {},
        "wards_by_prov_district": {},
        "stats_by_prov_district": {},
        "stats_by_province": {},
        "property_types": [],
        "house_directions": [],
        "balcony_directions": []
    }

    if df_gold is None or len(df_gold) == 0:
        return catalog

    # Top provinces sorted by count
    prov_counts = df_gold["province_clean"].value_counts()
    catalog["provinces"] = [p for p in prov_counts.index.tolist() if p and p != "Chưa xác định"]

    # Province stats
    prov_grp = df_gold.groupby("province_clean").agg(
        count=("price_billion", "count"),
        median_price_billion=("price_billion", "median"),
        median_price_m2_million=("price_per_m2", lambda s: float(s.median() / 1e6))
    )
    for prov, row in prov_grp.iterrows():
        catalog["stats_by_province"][str(prov)] = {
            "count": int(row["count"]),
            "median_price_billion": round(float(row["median_price_billion"]), 2),
            "median_price_m2_million": round(float(row["median_price_m2_million"]), 1)
        }

    # Districts per province sorted by listing count
    dist_grp = (
        df_gold.groupby(["province_clean", "district_clean"])
        .agg(
            count=("price_billion", "count"),
            median_price_billion=("price_billion", "median"),
            median_price_m2_million=("price_per_m2", lambda s: float(s.median() / 1e6)),
            median_area=("area", "median")
        )
        .reset_index()
        .sort_values(["province_clean", "count"], ascending=[True, False])
    )

    for prov, group in dist_grp.groupby("province_clean", sort=False):
        dists = [str(d) for d in group["district_clean"].tolist() if d and str(d) != "Chưa xác định"]
        catalog["districts_by_province"][str(prov)] = dists
        for _, r in group.iterrows():
            key = f"{prov}||{r['district_clean']}"
            catalog["stats_by_prov_district"][key] = {
                "count": int(r["count"]),
                "median_price_billion": round(float(r["median_price_billion"]), 2),
                "median_price_m2_million": round(float(r["median_price_m2_million"]), 1),
                "median_area": round(float(r["median_area"]), 1)
            }

    # Wards per (province, district) — top 25 per district
    if "ward_name" in df_gold.columns:
        ward_grp = (
            df_gold[df_gold["ward_name"] != "Chưa xác định"]
            .groupby(["province_clean", "district_clean", "ward_name"])
            .size()
            .reset_index(name="cnt")
            .sort_values(["province_clean", "district_clean", "cnt"], ascending=[True, True, False])
        )
        for (prov, dist), group in ward_grp.groupby(["province_clean", "district_clean"], sort=False):
            key = f"{prov}||{dist}"
            catalog["wards_by_prov_district"][key] = group["ward_name"].head(25).astype(str).tolist()

    catalog["property_types"] = df_gold["property_type_name"].value_counts().index.astype(str).tolist()
    catalog["house_directions"] = df_gold["house_direction"].value_counts().index.astype(str).tolist()
    catalog["balcony_directions"] = df_gold["balcony_direction"].value_counts().index.astype(str).tolist()
    return catalog


def prepare_inference_dataframe(raw_input: Dict[str, Any], bundle: Dict[str, Any]) -> pd.DataFrame:
    """
    Transforms a raw user input dictionary into an encoded DataFrame matching
    the exact column order, training medians, address normalization, and categorical dtypes
    used when training the LightGBM model.
    """
    feature_cols = bundle["feature_cols"]
    num_features = bundle["num_features"]
    binary_features = bundle["binary_features"]
    temporal_features = bundle["temporal_features"]
    cat_features = bundle["cat_features"]
    encoder = bundle["encoder"]
    numeric_medians = bundle.get("numeric_medians", {})
    default_temporal = bundle.get("default_temporal", {
        "published_year": 2025,
        "published_month": 6,
        "published_quarter": 2
    })

    row = {}

    # 1. Numeric features (use training median if missing or None; keep explicit user value otherwise)
    for col in num_features:
        val = raw_input.get(col, None)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            row[col] = float(numeric_medians.get(col, 0.0))
        else:
            fval = float(val)
            # If user left house_depth as 0 (unknown), use training median if available
            if col == "house_depth" and fval <= 0.0 and numeric_medians.get("house_depth", 0.0) > 0:
                row[col] = float(numeric_medians["house_depth"])
            else:
                row[col] = fval

    # 2. Binary features
    for col in binary_features:
        row[col] = int(bool(raw_input.get(col, 0)))

    # 3. Temporal features
    for col in temporal_features:
        row[col] = int(raw_input.get(col, default_temporal.get(col, 2025)))

    # 4. Categorical features with exact ETL address normalization
    row["property_type_name"] = str(raw_input.get("property_type_name", "Nhà")).strip() or "Nhà"
    row["province_clean"] = normalize_province_str(
        raw_input.get("province_clean") or raw_input.get("province_name") or "Hà Nội"
    )
    row["district_clean"] = normalize_district_str(
        raw_input.get("district_clean") or raw_input.get("district_name") or "Cầu Giấy"
    )
    row["house_direction"] = str(raw_input.get("house_direction", "Không xác định")).strip() or "Không xác định"
    row["balcony_direction"] = str(raw_input.get("balcony_direction", "Không xác định")).strip() or "Không xác định"

    df_in = pd.DataFrame([row])[feature_cols]
    df_in[cat_features] = encoder.transform(df_in[cat_features])
    for c in cat_features:
        df_in[c] = df_in[c].astype("category")

    return df_in
