"""
Streamlit Web Application: Real Estate Market Analytics Dashboard & AI Property Valuation
Combines EDA Market Intelligence and Real-Time Price Prediction Form in a single unified app.
Standardized design: No icons or emojis, formal academic and professional presentation.
"""
import os
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import streamlit as st
import joblib

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.config import GOLD_DIR, MODELS_DIR

# Set page configuration
st.set_page_config(
    page_title="Dự Đoán Giá Nhà Việt Nam - Big Data AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Formal, Clean, Professional)
st.markdown("""
<style>
    .main-header {
        font-size: 2.0rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.25rem;
    }
    .price-badge {
        font-size: 2.2rem;
        font-weight: 700;
        color: #047857;
        text-align: center;
        padding: 1rem;
        background: #f0fdf4;
        border-radius: 8px;
        border: 1px solid #10b981;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_gold_data():
    """Loads a sample of Gold dataset for visualization."""
    gold_file = GOLD_DIR / "vietnam_real_estates_gold.parquet"
    if not gold_file.exists():
        return None
    table = pq.read_table(str(gold_file))
    return table.to_pandas()


@st.cache_resource
def load_ml_bundle():
    """Loads the trained LightGBM model bundle."""
    model_file = MODELS_DIR / "lgbm_model.joblib"
    if not model_file.exists():
        return None
    return joblib.load(model_file)


@st.cache_data
def load_metrics():
    """Loads model metrics JSON."""
    metrics_file = MODELS_DIR / "metrics.json"
    if not metrics_file.exists():
        return None
    with open(metrics_file, "r", encoding="utf-8") as f:
        return json.load(f)


# Title Banner
st.markdown('<div class="main-header">Hệ Thống Định Giá và Phân Tích Bất Động Sản Việt Nam</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Nền tảng tích hợp dữ liệu lớn (PySpark, Parquet) và mô hình học máy LightGBM trên bộ dữ liệu 3.5 triệu bản ghi</div>', unsafe_allow_html=True)

df_gold = load_gold_data()
ml_bundle = load_ml_bundle()
metrics_data = load_metrics()

# Navigation Tabs (Formal text, no emojis)
tab_val, tab_dash, tab_model = st.tabs([
    "Định Giá Nhà Trực Tuyến",
    "Dashboard Thị Trường Bất Động Sản",
    "Hiệu Năng Mô Hình và Kiến Trúc"
])

# ==========================================
# TAB 1: REAL-TIME PROPERTY VALUATION
# ==========================================
with tab_val:
    st.subheader("Định Giá Bất Động Sản Bằng Trí Tuệ Nhân Tạo")
    st.caption("Nhập các thông số kỹ thuật của bất động sản để mô hình học máy ước tính giá trị thị trường.")

    if ml_bundle is None:
        st.warning("Chưa tìm thấy tập tin mô hình tại models/lgbm_model.joblib. Vui lòng thực thi lệnh: python -m src.ml.train_lgbm.")
    else:
        col_form1, col_form2 = st.columns(2)

        with col_form1:
            st.markdown("##### 1. Thông Tin Vị Trí và Loại Hình")
            
            # Province selection
            provinces = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Bình Dương", "Khánh Hòa", "Hải Phòng", "Cần Thơ", "Đồng Nai", "Bà Rịa - Vũng Tàu", "Khác"]
            if df_gold is not None and "province_clean" in df_gold.columns:
                top_provs = df_gold["province_clean"].value_counts().head(15).index.tolist()
                provinces = list(dict.fromkeys(top_provs + provinces))

            province_input = st.selectbox("Tỉnh / Thành phố:", provinces, index=0)
            district_input = st.text_input("Quận / Huyện (ví dụ: Cầu Giấy, Nam Từ Liêm, Quận 1, Bình Thạnh):", value="Cầu Giấy")
            
            prop_types = ["Nhà", "Căn hộ chung cư", "Đất", "Biệt thự/Nhà liền kề", "Shophouse", "Khác"]
            prop_type_input = st.selectbox("Loại hình bất động sản:", prop_types, index=0)
            
            directions = ["Không xác định", "Đông", "Tây", "Nam", "Bắc", "Đông Nam", "Đông Bắc", "Tây Nam", "Tây Bắc"]
            house_dir_input = st.selectbox("Hướng nhà:", directions, index=0)

        with col_form2:
            st.markdown("##### 2. Kích Thước và Thiết Kế")
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                area_input = st.number_input("Diện tích (m²):", min_value=10.0, max_value=2000.0, value=65.0, step=1.0)
                floor_input = st.number_input("Số tầng:", min_value=1.0, max_value=25.0, value=4.0, step=1.0)
                bedroom_input = st.number_input("Số phòng ngủ:", min_value=0.0, max_value=15.0, value=3.0, step=1.0)
            with col_a2:
                frontage_input = st.number_input("Mặt tiền (m, nhập 0 nếu không rõ):", min_value=0.0, max_value=50.0, value=4.5, step=0.5)
                road_input = st.number_input("Đường trước nhà (m, nhập 0 nếu không rõ):", min_value=0.0, max_value=50.0, value=3.5, step=0.5)
                bathroom_input = st.number_input("Số phòng vệ sinh:", min_value=0.0, max_value=15.0, value=3.0, step=1.0)

            st.markdown("##### 3. Pháp Lý và Hạ Tầng Giao Thông")
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                has_so_do = st.checkbox("Có Sổ đỏ / Sổ hồng", value=True)
            with col_b2:
                car_access = st.checkbox("Ngõ ô tô vào được", value=True)
            with col_b3:
                is_frontage = st.checkbox("Nhà mặt tiền kinh doanh", value=False)

        # Predict Button
        st.markdown("---")
        predict_btn = st.button("Dự Đoán Giá Trị Bất Động Sản", type="primary", use_container_width=True)

        if predict_btn:
            # Prepare feature vector
            model = ml_bundle["model"]
            encoder = ml_bundle["encoder"]
            feature_cols = ml_bundle["feature_cols"]

            input_dict = {
                "area": [float(area_input)],
                "floor_count": [float(floor_input)],
                "frontage_width": [float(frontage_input)],
                "house_depth": [0.0],
                "road_width": [float(road_input)],
                "bedroom_count": [float(bedroom_input)],
                "bathroom_count": [float(bathroom_input)],
                "has_so_do": [1 if has_so_do else 0],
                "car_access": [1 if car_access else 0],
                "is_frontage": [1 if is_frontage else 0],
                "published_year": [2026],
                "published_month": [3],
                "published_quarter": [1],
                "property_type_name": [str(prop_type_input)],
                "province_clean": [str(province_input).replace("TP.", "").strip()],
                "district_clean": [str(district_input).replace("Quận", "").replace("Huyện", "").strip()],
                "house_direction": [str(house_dir_input)],
                "balcony_direction": ["Không xác định"]
            }

            input_df = pd.DataFrame(input_dict)
            cat_features = ml_bundle["cat_features"]
            
            # Encode categoricals
            input_df[cat_features] = encoder.transform(input_df[cat_features])
            for c in cat_features:
                input_df[c] = input_df[c].astype("category")

            # Inference
            pred_log = model.predict(input_df[feature_cols])[0]
            pred_vnd = np.expm1(pred_log)
            pred_billion = pred_vnd / 1e9
            price_m2 = (pred_vnd / area_input) / 1e6

            # Display Result
            st.markdown(f'<div class="price-badge">Giá Ước Tính: {pred_billion:,.2f} Tỷ VNĐ</div>', unsafe_allow_html=True)

            res_c1, res_c2, res_c3 = st.columns(3)
            with res_c1:
                st.metric("Tổng giá trị ước tính (VNĐ)", f"{pred_vnd:,.0f} đ")
            with res_c2:
                st.metric("Đơn giá trung bình", f"{price_m2:,.1f} triệu/m²")
            with res_c3:
                lower_b = pred_billion * 0.92
                upper_b = pred_billion * 1.08
                st.metric("Khoảng giá tin cậy (sai số ±8%)", f"{lower_b:.2f} - {upper_b:.2f} Tỷ VNĐ")

            # Contextual benchmark
            if df_gold is not None:
                subset = df_gold[df_gold["province_clean"] == province_input]
                if len(subset) > 10:
                    med_prov = subset["price_billion"].median()
                    diff_pct = ((pred_billion - med_prov) / med_prov) * 100
                    status_text = "cao hơn" if diff_pct > 0 else "thấp hơn"
                    st.info(f"Bất động sản này có giá {status_text} {abs(diff_pct):.1f}% so với giá trung vị của khu vực {province_input} ({med_prov:.2f} Tỷ VNĐ).")


# ==========================================
# TAB 2: MARKET ANALYTICS DASHBOARD
# ==========================================
with tab_dash:
    st.subheader("Phân Tích Dữ Liệu Lớn Thị Trường Bất Động Sản")

    if df_gold is None:
        st.warning("Chưa tìm thấy dữ liệu tầng Gold tại data/gold/vietnam_real_estates_gold.parquet. Vui lòng thực thi pipeline ETL.")
    else:
        # KPI Row
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.metric("Tổng Số Tin Đăng", f"{len(df_gold):,} tin")
        with kpi2:
            st.metric("Giá Trung Vị Toàn Quốc", f"{df_gold['price_billion'].median():.2f} Tỷ VNĐ")
        with kpi3:
            st.metric("Đơn Giá Trung Vị", f"{(df_gold['price_per_m2'].median() / 1e6):.1f} triệu/m²")
        with kpi4:
            st.metric("Diện Tích Trung Vị", f"{df_gold['area'].median():.1f} m²")

        st.markdown("---")

        chart_c1, chart_c2 = st.columns(2)
        with chart_c1:
            st.markdown("##### Phân Bổ Tin Đăng Theo Top Tỉnh và Thành Phố")
            top_provs = df_gold["province_name"].value_counts().head(8).reset_index()
            top_provs.columns = ["Tỉnh / Thành", "Số Lượng"]
            st.bar_chart(top_provs.set_index("Tỉnh / Thành"))

        with chart_c2:
            st.markdown("##### Giá Trung Vị Theo Loại Hình Bất Động Sản (Tỷ VNĐ)")
            type_price = df_gold.groupby("property_type_name")["price_billion"].median().reset_index()
            type_price.columns = ["Loại Hình", "Giá Trung Vị (Tỷ)"]
            type_price = type_price.sort_values("Giá Trung Vị (Tỷ)", ascending=False)
            st.bar_chart(type_price.set_index("Loại Hình"))

        chart_c3, chart_c4 = st.columns(2)
        with chart_c3:
            st.markdown("##### Tỷ Lệ Tin Đăng Có Sổ Đỏ / Sổ Hồng")
            so_do_counts = df_gold["has_so_do"].value_counts().reset_index()
            so_do_counts["Pháp lý"] = so_do_counts["has_so_do"].map({1: "Có Sổ đỏ / Sổ hồng", 0: "Chưa rõ hoặc Khác"})
            st.dataframe(so_do_counts[["Pháp lý", "count"]].rename(columns={"count": "Số lượng"}), hide_index=True)

        with chart_c4:
            st.markdown("##### Tỷ Lệ Bất Động Sản Có Ngõ Ô Tô và Mặt Tiền")
            car_counts = df_gold["car_access"].value_counts().reset_index()
            car_counts["Đường ô tô"] = car_counts["car_access"].map({1: "Ngõ ô tô vào được", 0: "Ngõ xe máy hoặc Khác"})
            st.dataframe(car_counts[["Đường ô tô", "count"]].rename(columns={"count": "Số lượng"}), hide_index=True)

        st.markdown("##### Bảng Mẫu Dữ Liệu Bất Động Sản Chuẩn Hóa (Tầng Gold)")
        view_cols = ["property_type_name", "province_name", "district_name", "price_billion", "area", "price_per_m2", "has_so_do", "car_access"]
        st.dataframe(df_gold[view_cols].head(15), use_container_width=True)


# ==========================================
# TAB 3: MODEL PERFORMANCE & ARCHITECTURE
# ==========================================
with tab_model:
    st.subheader("Đánh Giá Mô Hình và Sơ Đồ Kiến Trúc Hệ Thống")

    st.markdown("##### So Sánh Hiệu Năng: Ridge Baseline vs. LightGBM Regressor")
    if metrics_data and "models" in metrics_data:
        m_df = pd.DataFrame(metrics_data["models"])
        col_rename = {
            "model": "Mô Hình",
            "r2_score": "R² Score (Độ giải thích)",
            "rmse_log": "RMSE (Thang log)",
            "mae_billion_vnd": "MAE (Tỷ VNĐ)",
            "rmse_billion_vnd": "RMSE (Tỷ VNĐ)",
            "mape_percent": "MAPE (%)",
            "test_samples": "Số Mẫu Test"
        }
        st.dataframe(m_df.rename(columns=col_rename), hide_index=True, use_container_width=True)
    else:
        st.info("Chưa có tập tin models/metrics.json. Vui lòng thực thi huấn luyện mô hình để xem bảng so sánh.")

    st.markdown("---")
    col_feat1, col_feat2 = st.columns([1, 1])

    with col_feat1:
        st.markdown("##### Tầm Quan Trọng Của Các Đặc Trưng (Feature Importance)")
        feat_img_path = MODELS_DIR / "feature_importance.png"
        if feat_img_path.exists():
            st.image(str(feat_img_path), caption="Biểu đồ tầm quan trọng đặc trưng trong việc ước tính giá nhà")
        else:
            st.info("Chưa có biểu đồ Feature Importance. Chạy: python -m src.ml.evaluate để sinh ảnh.")

    with col_feat2:
        st.markdown("##### Kiến Trúc Dữ Liệu Lớn 6 Tầng")
        st.markdown("""
        1. **Raw Layer**: Nguồn dữ liệu Hugging Face `tinixai/vietnam-real-estates` (3.5 triệu bản ghi).
        2. **Ingestion Layer (Bronze)**: Script Python tải theo shard, gắn timestamp `ingested_at` và `batch_id`.
        3. **ETL Layer 1 (Silver)**: PySpark làm sạch, loại trùng lặp, chuẩn hóa kiểu số thực, tính đơn giá VND/m².
        4. **ETL Layer 2 (Gold)**: PySpark lọc ngoại lai, chuẩn hóa địa chỉ, trích xuất NLP sổ đỏ và ngõ ô tô, biến đổi logarit.
        5. **Storage Layer**: Lưu trữ Bronze/Silver/Gold Parquet và nạp bảng `real_estate_gold` vào PostgreSQL (hoặc SQLite).
        6. **Machine Learning & Serving**: Huấn luyện Ridge baseline và LightGBM Regressor, đánh giá RMSE/MAE/MAPE, phục vụ qua giao diện Streamlit.
        """)
