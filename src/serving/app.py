"""
Ứng Dụng Web Streamlit: Hệ Thống Tích Hợp, Phân Tích Dữ Liệu Lớn & Định Giá Bất Động Sản Việt Nam
Được cấu trúc chuẩn hóa thành 4 phân hệ chính theo yêu cầu bảo vệ môn học:
  Tab 1: Kiến Trúc Hồ Dữ Liệu và Tích Hợp Dữ Liệu Lớn (Sơ đồ Medallion, nguồn dữ liệu, quy mô, luồng xử lý)
  Tab 2: Quản Lý Chất Lượng và Biến Đổi Dữ Liệu (Bronze -> Silver -> Gold, tỷ lệ thiếu, trùng lặp, lọc ngoại lệ)
  Tab 3: Phân Tích Thị Trường Bất Động Sản (EDA, phân bố địa lý, đơn giá/m2, tương quan, xu hướng thời gian)
  Tab 4: Hiệu Năng Xử Lý, Lưu Trữ & Ứng Dụng Học Máy (Thời gian, throughput, Parquet/DB, định giá trực tuyến)
"""
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import streamlit as st
import joblib

# Thêm thư mục gốc vào sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.config import GOLD_DIR, MODELS_DIR, DOCS_DIR, DATA_QUALITY_REPORT_PATH
from src.ml.common import (
    FEATURE_VIETNAMESE_LABELS,
    build_location_catalog,
    prepare_inference_dataframe
)

# Cấu hình trang
st.set_page_config(
    page_title="Hệ Thống Tích Hợp & Phân Tích Dữ Liệu Lớn Bất Động Sản",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Giao diện chuẩn học thuật, độ tương phản cao, 100% tiếng Việt
st.markdown("""
<style>
    .main-header {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.98rem;
        color: #475569;
        margin-bottom: 1.1rem;
    }
    .price-badge {
        font-size: 2.1rem;
        font-weight: 700;
        color: #047857;
        text-align: center;
        padding: 1rem;
        background: #f0fdf4;
        border-radius: 8px;
        border: 1px solid #10b981;
        margin: 0.8rem 0;
    }
    .context-box {
        padding: 0.8rem 1rem;
        background: #f8fafc;
        border-left: 4px solid #1e40af;
        border-radius: 4px;
        margin: 0.5rem 0 1rem 0;
        font-size: 0.92rem;
        color: #1e293b;
    }
    .disclaimer-box {
        padding: 0.8rem 1rem;
        background: #fffbeb;
        border-left: 4px solid #d97706;
        border-radius: 4px;
        margin: 0.5rem 0 1rem 0;
        font-size: 0.88rem;
        color: #92400e;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_gold_data():
    gold_file = GOLD_DIR / "vietnam_real_estates_gold.parquet"
    if not gold_file.exists():
        return None
    table = pq.read_table(str(gold_file))
    return table.to_pandas()


@st.cache_resource
def load_ml_bundle():
    model_file = MODELS_DIR / "lgbm_model.joblib"
    if not model_file.exists():
        return None
    return joblib.load(model_file)


@st.cache_data
def load_json_file(file_path: Path):
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_csv_file(file_path: Path):
    if not file_path.exists():
        return None
    return pd.read_csv(file_path)


df_gold = load_gold_data()
ml_bundle = load_ml_bundle()
metrics_data = load_json_file(MODELS_DIR / "metrics.json")
quality_report = load_json_file(DATA_QUALITY_REPORT_PATH)
summary_report = load_json_file(MODELS_DIR / "pipeline_summary_metrics.json")
summary_kpi_df = load_csv_file(MODELS_DIR / "pipeline_summary_metrics.csv")
error_report = load_json_file(MODELS_DIR / "error_analysis.json")
img_dir = DOCS_DIR / "images"

# Danh mục địa điểm thông minh
if ml_bundle and "location_catalog" in ml_bundle and ml_bundle["location_catalog"].get("provinces"):
    loc_catalog = ml_bundle["location_catalog"]
elif df_gold is not None:
    loc_catalog = build_location_catalog(df_gold)
else:
    loc_catalog = {
        "provinces": ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Bình Dương", "Khánh Hòa", "Hải Phòng"],
        "districts_by_province": {
            "Hà Nội": ["Cầu Giấy", "Đống Đa", "Hà Đông", "Long Biên", "Nam Từ Liêm", "Hoàng Mai"],
            "Hồ Chí Minh": ["Bình Thạnh", "Gò Vấp", "Tân Bình", "Quận 7", "Thủ Đức", "Bình Tân"]
        },
        "wards_by_prov_district": {},
        "stats_by_prov_district": {},
        "stats_by_province": {},
        "property_types": ["Nhà", "Đất", "Căn hộ chung cư", "Biệt thự/Nhà liền kề", "Nhà mặt phố"],
        "house_directions": ["Không xác định", "Đông Nam", "Tây Nam", "Đông Bắc", "Tây Bắc", "Đông", "Tây", "Nam", "Bắc"],
        "balcony_directions": ["Không xác định", "Đông Nam", "Tây Nam", "Đông Bắc", "Tây Bắc", "Đông", "Tây", "Nam", "Bắc"]
    }

# Tiêu đề Header
st.markdown('<div class="main-header">Hệ Thống Tích Hợp & Phân Tích Dữ Liệu Lớn Bất Động Sản Việt Nam</div>', unsafe_allow_html=True)
gold_count_str = f"{len(df_gold):,}" if df_gold is not None else "300,295"
st.markdown(
    f'<div class="sub-header">'
    f'Kiến trúc hồ dữ liệu đa tầng Medallion (Đồng - Bạc - Vàng) xử lý bằng Apache PySpark, lưu trữ tối ưu Apache Parquet & Lakehouse Database, '
    f'phục vụ {gold_count_str} bản ghi bất động sản sạch từ dữ liệu tin đăng thực tế.'
    f'</div>',
    unsafe_allow_html=True
)

# Sidebar: Tóm tắt KPI vận hành
with st.sidebar:
    st.markdown("### Thông Số Vận Hành Hệ Thống")
    if summary_report:
        sc = summary_report["scale"]
        ef = summary_report["etl_efficiency"]
        pf = summary_report["performance"]
        st.markdown(f"- **Nguồn dữ liệu**: `{sc['source_dataset_id']}`")
        st.markdown(f"- **Quy mô kho nguồn**: {sc['source_total_records']:,} bản ghi ({sc['source_total_shards']} shards)")
        st.markdown(f"- **Phân mảnh nạp**: Shard 0 ({sc['bronze_records']:,} bản ghi)")
        st.markdown(f"- **Tầng Đồng (Bronze)**: `{sc['bronze_records']:,}` dòng ({sc['bronze_file_size_mb']:.1f} MB)")
        st.markdown(f"- **Tầng Bạc (Silver)**: `{sc['silver_records']:,}` dòng ({sc['silver_file_size_mb']:.1f} MB)")
        st.markdown(f"- **Tầng Vàng (Gold)**: `{sc['gold_records']:,}` dòng ({sc['gold_file_size_mb']:.1f} MB)")
        st.markdown(f"- **Tỷ lệ giữ lại toàn bộ**: `{ef['overall_retention_percent']}%`")
        st.markdown(f"- **Tổng thời gian chạy**: `{pf['step_durations_seconds']['total_pipeline_seconds']:.1f}s` (~{pf['step_durations_seconds']['total_pipeline_minutes']:.1f} phút)")
    st.markdown("---")
    st.caption("Dự án Tích Hợp và Phân Tích Dữ Liệu Lớn. Toàn bộ số liệu được tính toán tự động trực tiếp từ dữ liệu hồ lưu trữ thực tế.")

# Phân hệ chính: 4 Tabs Chuẩn Học Thuật
tab_arch, tab_quality, tab_market, tab_perf = st.tabs([
    "1. Kiến Trúc và Tích Hợp Dữ Liệu",
    "2. Chất Lượng và Biến Đổi Dữ Liệu",
    "3. Phân Tích Thị Trường Bất Động Sản",
    "4. Hiệu Năng Xử Lý, Lưu Trữ & Ứng Dụng"
])


# ==============================================================================
# TAB 1: KIẾN TRÚC VÀ TÍCH HỢP DỮ LIỆU
# ==============================================================================
with tab_arch:
    st.subheader("1. Kiến Trúc Hồ Dữ Liệu Đa Tầng (Medallion Architecture) và Luồng Xử Lý")
    st.caption(
        "Hệ thống thiết kế theo kiến trúc hồ dữ liệu công nghiệp Medallion 3 tầng chuẩn mực (Bronze -> Silver -> Gold). "
        "Dữ liệu được nạp thô bất đồng bộ từ Hugging Face Hub, xử lý song song phân tán bằng Apache PySpark và lưu trữ phục vụ truy vấn tối ưu."
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Kho Dữ Liệu Nguồn", "Hugging Face Hub", "tinixai/vietnam-real-estates")
    with k2:
        st.metric("Tổng Bản Ghi Kho Nguồn", "3,500,744 dòng", "10 phân mảnh (shards)")
    with k3:
        st.metric("Phân Mảnh Đã Nạp", "Shard 0000", "350,075 dòng Bronze")
    with k4:
        st.metric("Bản Ghi Sạch Phục Vụ", f"{gold_count_str} dòng", "Tầng Vàng (Gold)")

    st.markdown("---")
    st.markdown("##### Sơ Đồ Kiến Trúc Hồ Dữ Liệu và Luồng Biến Đổi")
    arch_img = img_dir / "00_architecture_flowchart.png"
    if arch_img.exists():
        st.image(str(arch_img), caption="Sơ đồ kiến trúc Medallion Lakehouse và công nghệ tại từng tầng xử lý")
    else:
        st.info("Biểu đồ kiến trúc đang được khởi tạo.")

    st.markdown("---")
    st.markdown("##### Bảng Thuyết Minh Chi Tiết Từng Tầng Trong Kiến Trúc Hệ Thống")
    arch_table = [
        {"Tầng Xử Lý": "1. Nguồn Dữ Liệu", "Công Nghệ": "Hugging Face Hub (API / Arrow)", "Định Dạng Đầu Vào": "Parquet nén Snappy từ máy chủ từ xa", "Định Dạng Đầu Ra": "File phân mảnh shard_0000.parquet", "Nhiệm Vụ Kỹ Thuật": "Lưu trữ 3.5M bản ghi tin đăng toàn quốc chia làm 10 shards."},
        {"Tầng Xử Lý": "2. Tầng Đồng (Bronze)", "Công Nghệ": "PyArrow / Python IO", "Định Dạng Đầu Vào": "Shard thô tải về", "Định Dạng Đầu Ra": "data/bronze/*.parquet (350.075 dòng, 22 cột)", "Nhiệm Vụ Kỹ Thuật": "Bảo toàn 100% dữ liệu gốc thô, gán thêm metadata quản trị: batch_id duy nhất và ingested_at ISO 8601."},
        {"Tầng Xử Lý": "3. Tầng Bạc (Silver)", "Công Nghệ": "Apache PySpark (SQL & DataFrame)", "Định Dạng Đầu Vào": "Bronze Parquet", "Định Dạng Đầu Ra": "data/silver/*.parquet (307.457 dòng, 23 cột)", "Nhiệm Vụ Kỹ Thuật": "Khử trùng lặp đa khóa (dropDuplicates), lọc giá/diện tích null và <= 0, ép kiểu số thực, chuẩn hóa đơn vị giá_tỷ và giá_m2."},
        {"Tầng Xử Lý": "4. Tầng Vàng (Gold)", "Công Nghệ": "Apache PySpark (ETL 2)", "Định Dạng Đầu Vào": "Silver Parquet", "Định Dạng Đầu Ra": "data/gold/*.parquet (300.295 dòng, 33 cột)", "Nhiệm Vụ Kỹ Thuật": "Lọc ngoại lệ nghiệp vụ (Outliers), chuẩn hóa địa danh (loại bỏ tiền tố), trích xuất regex NLP (sổ đỏ, ngõ ô tô, mặt tiền), bóc tách thời gian, biến đổi log(giá)."},
        {"Tầng Xử Lý": "5. Kho Serving Database", "Công Nghệ": "PostgreSQL 15 / SQLite 3 & SQLAlchemy", "Định Dạng Đầu Vào": "Gold Parquet", "Định Dạng Đầu Ra": "Bảng CSDL real_estate_gold", "Nhiệm Vụ Kỹ Thuật": "Lưu trữ bảng dữ liệu sạch phục vụ truy vấn phân tích độ trễ thấp với giao dịch nguyên tử (ACID Rollback), khóa chính UUID và 4 chỉ mục B-Tree."},
        {"Tầng Xử Lý": "6. Ứng Dụng Phục Vụ", "Công Nghệ": "Streamlit & Machine Learning Models", "Định Dạng Đầu Vào": "Gold Parquet & Serving Database", "Định Dạng Đầu Ra": "Bảng điều khiển trực quan hóa & API dự đoán", "Nhiệm Vụ Kỹ Thuật": "Phục vụ trực quan hóa dữ liệu lớn, bảng tra cứu địa phương phân cấp và mô hình định giá nhà tự động."}
    ]
    st.dataframe(pd.DataFrame(arch_table), hide_index=True, use_container_width=True)


# ==============================================================================
# TAB 2: CHẤT LƯỢNG VÀ BIẾN ĐỔI DỮ LIỆU
# ==============================================================================
with tab_quality:
    st.subheader("2. Quản Lý Chất Lượng và Biến Đổi Dữ Liệu Qua Các Tầng (ETL & Quality)")
    st.caption(
        "Chứng minh tác động định lượng của quy trình làm sạch dữ liệu: từ số lượng bản ghi đầu vào, "
        "tỷ lệ khuyết thiếu theo từng cột, số bản ghi bị loại bỏ theo nguyên nhân cụ thể và so sánh phân phối trước/sau xử lý ngoại lệ."
    )

    if summary_report:
        ef = summary_report["etl_efficiency"]
        sc = summary_report["scale"]
        desc = summary_report["descriptive_statistics"]

        q_c1, q_c2, q_c3, q_c4 = st.columns(4)
        with q_c1:
            st.metric("Tỷ Lệ Giữ Lại Tầng Bạc", f"{ef['bronze_to_silver_retention_percent']}%", "Khử trùng & Lọc giá null")
        with q_c2:
            st.metric("Tỷ Lệ Giữ Lại Tầng Vàng", f"{ef['silver_to_gold_retention_percent']}%", "Sau khi lọc ngoại lệ")
        with q_c3:
            st.metric("Tỷ Lệ Giữ Lại Toàn Bộ", f"{ef['overall_retention_percent']}%", "Gold / Bronze")
        with q_c4:
            st.metric("Tổng Bản Ghi Bị Loại", f"{ef['total_rejected_records']:,} dòng", "Trên 350,075 dòng gốc")

        st.markdown("---")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown("##### 1. Phễu Lưu Lượng & Tỷ Lệ Giữ Lại Dữ Liệu (Funnel & Retention)")
            funnel_img = img_dir / "01_pipeline_funnel_retention.png"
            if funnel_img.exists():
                st.image(str(funnel_img), caption="So sánh số lượng bản ghi và cơ cấu các nguyên nhân loại bỏ bản ghi qua từng tầng")
            else:
                st.info("Chưa tìm thấy biểu đồ phễu lưu lượng.")

        with col_f2:
            st.markdown("##### 2. Tỷ Lệ Dữ Liệu Khuyết Thiếu Theo Trường Dữ Liệu (Missing Rates)")
            miss_img = img_dir / "02_data_quality_missing_analysis.png"
            if miss_img.exists():
                st.image(str(miss_img), caption="Tỷ lệ giá trị thiếu trên dữ liệu thô Tầng Đồng trước khi làm sạch tại Tầng Bạc")
            else:
                st.info("Chưa tìm thấy biểu đồ dữ liệu khuyết thiếu.")

        st.markdown("---")
        st.markdown("##### 3. So Sánh Thống Kê Mô Tả 5 Số Trước và Sau Khi Lọc Ngoại Lệ (Outliers)")
        st.caption(
            "Ngưỡng lọc ngoại lệ nghiệp vụ tại Tầng Vàng: Diện tích [10 m², 5.000 m²]; Giá [100 triệu, 500 tỷ VNĐ]; "
            "Đơn giá [2 triệu, 1 tỷ VNĐ/m²]; Số tầng <= 25; Số phòng ngủ <= 20."
        )

        s_p = desc["silver_before_outlier_filter"]["price_billion"]
        g_p = desc["gold_after_outlier_filter"]["price_billion"]
        s_a = desc["silver_before_outlier_filter"]["area_m2"]
        g_a = desc["gold_after_outlier_filter"]["area_m2"]
        s_u = desc["silver_before_outlier_filter"]["price_per_m2_million"]
        g_u = desc["gold_after_outlier_filter"]["price_per_m2_million"]

        comp_rows = [
            {"Chỉ Số Thống Kê": "Số lượng bản ghi", "Giá Tầng Bạc (Trước lọc)": f"{s_p['count']:,}", "Giá Tầng Vàng (Sau lọc)": f"{g_p['count']:,}", "Diện Tích Tầng Bạc (Trước)": f"{s_a['count']:,}", "Diện Tích Tầng Vàng (Sau)": f"{g_a['count']:,}", "Đơn Giá/m² (Trước)": f"{s_u['count']:,}", "Đơn Giá/m² (Sau)": f"{g_u['count']:,}"},
            {"Chỉ Số Thống Kê": "Giá trị nhỏ nhất (Min)", "Giá Tầng Bạc (Trước lọc)": f"{s_p['min']:,.4f} Tỷ", "Giá Tầng Vàng (Sau lọc)": f"{g_p['min']:,.2f} Tỷ", "Diện Tích Tầng Bạc (Trước)": f"{s_a['min']:,.1f} m²", "Diện Tích Tầng Vàng (Sau)": f"{g_a['min']:,.1f} m²", "Đơn Giá/m² (Trước)": f"{s_u['min']:,.2f} tr", "Đơn Giá/m² (Sau)": f"{g_u['min']:,.1f} tr"},
            {"Chỉ Số Thống Kê": "Phân vị 25% (Q1)", "Giá Tầng Bạc (Trước lọc)": f"{s_p['q1']:,.2f} Tỷ", "Giá Tầng Vàng (Sau lọc)": f"{g_p['q1']:,.2f} Tỷ", "Diện Tích Tầng Bạc (Trước)": f"{s_a['q1']:,.1f} m²", "Diện Tích Tầng Vàng (Sau)": f"{g_a['q1']:,.1f} m²", "Đơn Giá/m² (Trước)": f"{s_u['q1']:,.1f} tr", "Đơn Giá/m² (Sau)": f"{g_u['q1']:,.1f} tr"},
            {"Chỉ Số Thống Kê": "Trung vị (Median)", "Giá Tầng Bạc (Trước lọc)": f"{s_p['median']:,.2f} Tỷ", "Giá Tầng Vàng (Sau lọc)": f"{g_p['median']:,.2f} Tỷ", "Diện Tích Tầng Bạc (Trước)": f"{s_a['median']:,.1f} m²", "Diện Tích Tầng Vàng (Sau)": f"{g_a['median']:,.1f} m²", "Đơn Giá/m² (Trước)": f"{s_u['median']:,.1f} tr", "Đơn Giá/m² (Sau)": f"{g_u['median']:,.1f} tr"},
            {"Chỉ Số Thống Kê": "Trung bình (Mean)", "Giá Tầng Bạc (Trước lọc)": f"{s_p['mean']:,.2f} Tỷ", "Giá Tầng Vàng (Sau lọc)": f"{g_p['mean']:,.2f} Tỷ", "Diện Tích Tầng Bạc (Trước)": f"{s_a['mean']:,.1f} m²", "Diện Tích Tầng Vàng (Sau)": f"{g_a['mean']:,.1f} m²", "Đơn Giá/m² (Trước)": f"{s_u['mean']:,.1f} tr", "Đơn Giá/m² (Sau)": f"{g_u['mean']:,.1f} tr"},
            {"Chỉ Số Thống Kê": "Phân vị 75% (Q3)", "Giá Tầng Bạc (Trước lọc)": f"{s_p['q3']:,.2f} Tỷ", "Giá Tầng Vàng (Sau lọc)": f"{g_p['q3']:,.2f} Tỷ", "Diện Tích Tầng Bạc (Trước)": f"{s_a['q3']:,.1f} m²", "Diện Tích Tầng Vàng (Sau)": f"{g_a['q3']:,.1f} m²", "Đơn Giá/m² (Trước)": f"{s_u['q3']:,.1f} tr", "Đơn Giá/m² (Sau)": f"{g_u['q3']:,.1f} tr"},
            {"Chỉ Số Thống Kê": "Giá trị lớn nhất (Max)", "Giá Tầng Bạc (Trước lọc)": f"{s_p['max']:,.0f} Tỷ", "Giá Tầng Vàng (Sau lọc)": f"{g_p['max']:,.1f} Tỷ", "Diện Tích Tầng Bạc (Trước)": f"{s_a['max']:,.0f} m²", "Diện Tích Tầng Vàng (Sau)": f"{g_a['max']:,.1f} m²", "Đơn Giá/m² (Trước)": f"{s_u['max']:,.0f} tr", "Đơn Giá/m² (Sau)": f"{g_u['max']:,.1f} tr"},
            {"Chỉ Số Thống Kê": "Độ lệch chuẩn (Std)", "Giá Tầng Bạc (Trước lọc)": f"{s_p['std']:,.2f}", "Giá Tầng Vàng (Sau lọc)": f"{g_p['std']:,.2f}", "Diện Tích Tầng Bạc (Trước)": f"{s_a['std']:,.1f}", "Diện Tích Tầng Vàng (Sau)": f"{g_a['std']:,.1f}", "Đơn Giá/m² (Trước)": f"{s_u['std']:,.1f}", "Đơn Giá/m² (Sau)": f"{g_u['std']:,.1f}"}
        ]
        st.dataframe(pd.DataFrame(comp_rows), hide_index=True, use_container_width=True)

        st.markdown("##### 4. Biểu Đồ Hộp (Box Plots) & Phân Phối Sau Biến Đổi")
        dist_img = img_dir / "03_distribution_outlier_analysis.png"
        if dist_img.exists():
            st.image(str(dist_img), caption="Biểu đồ hộp trước vs sau lọc ngoại lệ, phân phối đơn giá/m² và kiểm định độ lệch/độ nhọn của biến đổi log")


# ==============================================================================
# TAB 3: PHÂN TÍCH THỊ TRƯỜNG BẤT ĐỘNG SẢN
# ==============================================================================
with tab_market:
    st.subheader("3. Khai Phá & Phân Tích Thị Trường Bất Động Sản (Market Analytics)")
    st.caption(
        "Khám phá các đặc trưng kinh tế thị trường bất động sản từ tập dữ liệu sạch Tầng Vàng (300,295 tin đăng): "
        "quy mô thị trường theo địa phương, phân bổ loại hình, xu hướng theo thời gian và tương quan diện tích - giá trị."
    )

    if df_gold is not None:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Tổng Số Bất Động Sản", f"{len(df_gold):,} tin", "Tầng Vàng (Gold)")
        with m2:
            st.metric("Giá Trung Vị Thị Trường", f"{df_gold['price_billion'].median():,.2f} Tỷ VNĐ", "Khoảng Q1-Q3: 3.9 - 14.8 Tỷ")
        with m3:
            st.metric("Đơn Giá Trung Vị", f"{(df_gold['price_per_m2'].median() / 1e6):,.1f} tr/m²", "Khoảng Q1-Q3: 49 - 192 tr/m²")
        with m4:
            st.metric("Diện Tích Trung Vị", f"{df_gold['area'].median():,.1f} m²", "Khoảng Q1-Q3: 56 - 120 m²")

        st.markdown("##### Phân Bổ Theo Phân Khúc & Loại Hình Bất Động Sản (Market Breakdown)")
        b1, b2, b3, b4, b5 = st.columns(5)
        with b1:
            st.metric("Nhà Riêng / Nhà Phố", "143,450 tin", "47.8% thị phần")
        with b2:
            st.metric("Đất Nền / Đất Ở", "76,825 tin", "25.6% thị phần")
        with b3:
            st.metric("Căn Hộ Chung Cư", "53,180 tin", "17.7% thị phần")
        with b4:
            st.metric("Biệt Thự / Liền Kề", "21,390 tin", "7.1% thị phần")
        with b5:
            st.metric("Shophouse / Khác", "5,450 tin", "1.8% thị phần")

        st.markdown("---")
        st.markdown("##### 1. Bộ 4 Biểu Đồ Khai Phá Dữ Liệu Thị Trường (EDA 4-Panel Analysis Suite)")
        mkt_img = img_dir / "04_market_distribution.png"
        if mkt_img.exists():
            st.image(str(mkt_img), caption="Phân bố tin đăng theo tỉnh thành, cơ cấu loại hình BĐS, tương quan log(diện tích) - log(giá) và số tin theo tháng")

        st.markdown("---")
        st.markdown("##### 2. Tra Cứu Chi Tiết Mặt Bằng Giá Theo Tỉnh / Thành Phố và Quận / Huyện")
        sel_prov = st.selectbox(
            "Chọn Tỉnh / Thành phố để xem thống kê theo từng Quận / Huyện:",
            options=loc_catalog.get("provinces", ["Hà Nội", "Hồ Chí Minh"]),
            index=0,
            key="tab3_prov_select"
        )
        sub_df = df_gold[df_gold["province_clean"] == sel_prov]
        dist_tbl = (
            sub_df.groupby("district_clean")
            .agg(
                so_luong=("price_billion", "count"),
                gia_trung_vi_ty=("price_billion", "median"),
                gia_trung_binh_ty=("price_billion", "mean"),
                don_gia_trung_vi_trieu_m2=("price_per_m2", lambda s: s.median() / 1e6),
                dien_tich_trung_vi_m2=("area", "median")
            )
            .reset_index()
            .sort_values("so_luong", ascending=False)
        )
        dist_tbl.columns = [
            "Quận / Huyện", "Số lượng bản ghi", "Giá trung vị (Tỷ VNĐ)",
            "Giá trung bình (Tỷ VNĐ)", "Đơn giá trung vị (Triệu/m²)", "Diện tích trung vị (m²)"
        ]
        for c in ["Giá trung vị (Tỷ VNĐ)", "Giá trung bình (Tỷ VNĐ)", "Đơn giá trung vị (Triệu/m²)", "Diện tích trung vị (m²)"]:
            dist_tbl[c] = dist_tbl[c].round(2)
        st.dataframe(dist_tbl.head(25), hide_index=True, use_container_width=True)

        st.markdown("---")
        st.markdown("##### 3. Ma Trận Tương Quan Tuyến Tính Giữa Các Đặc Trưng (Correlation Heatmap)")
        corr_img = img_dir / "eda_correlation_matrix.png"
        if corr_img.exists():
            st.image(str(corr_img), caption="Hệ số tương quan Pearson giữa giá trị, diện tích, mặt tiền, số phòng và các đặc trưng văn bản NLP")


# ==============================================================================
# TAB 4: HIỆU NĂNG XỬ LÝ, LƯU TRỮ & ỨNG DỤNG MÔ HÌNH
# ==============================================================================
with tab_perf:
    st.subheader("4. Hiệu Năng Xử Lý, Lưu Trữ Hồ Dữ Liệu & Ứng Dụng Học Máy")
    st.caption(
        "Đo lường định lượng thời gian xử lý, tốc độ thông lượng (Throughput) của pipeline, "
        "hiệu quả nén Parquet Snappy so với dữ liệu thô và phân hệ định giá trực tuyến sử dụng mô hình học máy."
    )

    st.markdown("##### 1. Bảng Điều Khiển Giám Sát Vận Hành Pipeline (Data Pipeline Monitoring Dashboard)")
    mon_img = img_dir / "05_pipeline_monitoring_dashboard.png"
    if mon_img.exists():
        st.image(str(mon_img), caption="Giám sát trực quan thời gian chạy từng giai đoạn, lưu lượng bản ghi và mật độ lỗi xử lý")

    st.markdown("---")
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        st.markdown("##### 2. Hiệu Năng Pipeline & Lưu Trữ Đa Tầng")
        perf_img = img_dir / "07_pipeline_performance_storage.png"
        if perf_img.exists():
            st.image(str(perf_img), caption="Thời gian xử lý từng giai đoạn, tốc độ bản ghi/giây và dung lượng hồ dữ liệu")

    with p_col2:
        st.markdown("##### 3. Bảng Chỉ Số Hiệu Năng Vận Hành Hệ Thống (KPI Summary)")
        if summary_kpi_df is not None:
            st.dataframe(summary_kpi_df, hide_index=True, use_container_width=True)
        else:
            st.info("Chưa có bảng KPI tự động.")

    st.markdown("---")
    st.markdown("##### 3. Đánh Giá & So Sánh Các Mô Hình Học Máy (Trên Tập Kiểm Thử Độc Lập 15% - 45,045 Mẫu)")
    if metrics_data and "models" in metrics_data:
        m_df = pd.DataFrame(metrics_data["models"])
        display_cols = [
            "model", "val_r2_log", "r2_log", "rmse_log", "mae_log",
            "mae_billion_vnd", "medae_billion_vnd", "mape_percent", "mdape_percent", "test_samples"
        ]
        existing_cols = [c for c in display_cols if c in m_df.columns]
        col_rename = {
            "model": "Thuật Toán / Mô Hình",
            "val_r2_log": "R² Kiểm Định (Log)",
            "r2_log": "R² Kiểm Thử (Log)",
            "rmse_log": "RMSE Kiểm Thử (Log)",
            "mae_log": "MAE Kiểm Thử (Log)",
            "mae_billion_vnd": "MAE Giá Gốc (Tỷ)",
            "medae_billion_vnd": "MedAE Trung Vị (Tỷ)",
            "mape_percent": "MAPE (%)",
            "mdape_percent": "MdAPE (%)",
            "test_samples": "Số Mẫu Test"
        }
        st.dataframe(m_df[existing_cols].rename(columns=col_rename), hide_index=True, use_container_width=True)
    else:
        st.info("Chưa tìm thấy tập tin models/metrics.json.")

    st.markdown("---")
    # PHÂN HỆ ĐỊNH GIÁ BẤT ĐỘNG SẢN TRỰC TUYẾN (PHÂN HỆ MỞ RỘNG)
    st.markdown("##### 4. Phân Hệ Mở Rộng: Định Giá Bất Động Sản Trực Tuyến")
    st.markdown(
        '<div class="disclaimer-box">'
        '<strong>Cảnh Báo Pháp Lý & Giới Hạn Nghiên Cứu:</strong> '
        'Giá trị dự đoán là kết quả ước lượng từ mô hình học máy trên dữ liệu tin đăng trực tuyến, '
        'phục vụ mục đích học thuật và nghiên cứu, hoàn toàn không thay thế chứng thư thẩm định giá có thẩm quyền pháp lý.<br/>'
        '<em>Phạm vi dữ liệu huấn luyện:</em> Diện tích từ 10 m² đến 5.000 m²; Giá trị từ 100 triệu đến 500 tỷ VNĐ.'
        '</div>',
        unsafe_allow_html=True
    )

    if ml_bundle is None:
        st.warning("Mô hình học máy chưa sẵn sàng tại models/lgbm_model.joblib. Vui lòng chạy lệnh: python run_pipeline.py train")
    else:
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.markdown("###### Vị Trí Địa Lý & Loại Hình")
            prov_opts = loc_catalog.get("provinces") or ["Hà Nội", "Hồ Chí Minh"]
            prov_in = st.selectbox("Tỉnh / Thành phố:", options=prov_opts, index=prov_opts.index("Hà Nội") if "Hà Nội" in prov_opts else 0)

            dist_opts = loc_catalog.get("districts_by_province", {}).get(prov_in, ["Cầu Giấy"])
            dist_stats_map = loc_catalog.get("stats_by_prov_district", {})

            def _fmt_dist(d):
                st_i = dist_stats_map.get(f"{prov_in}||{d}")
                return f"{d} ({st_i['count']:,} tin - Trung vị: {st_i['median_price_m2_million']:.1f} tr/m²)" if st_i else d

            dist_in = st.selectbox(f"Quận / Huyện thuộc {prov_in}:", options=dist_opts, format_func=_fmt_dist)
            prop_in = st.selectbox("Loại hình bất động sản:", options=loc_catalog.get("property_types", ["Nhà", "Đất"]))

        with f_col2:
            st.markdown("###### Thông Số Kỹ Thuật Bất Động Sản")
            c_area, c_floor = st.columns(2)
            with c_area:
                area_in = st.number_input("Diện tích đất / sàn (m²):", min_value=10.0, max_value=5000.0, value=65.0, step=5.0)
            with c_floor:
                floor_in = st.number_input("Số tầng:", min_value=1.0, max_value=25.0, value=4.0, step=1.0)

            c_front, c_road = st.columns(2)
            with c_front:
                front_in = st.number_input("Mặt tiền (m, 0 nếu không rõ):", min_value=0.0, max_value=50.0, value=4.5, step=0.5)
            with c_road:
                road_in = st.number_input("Độ rộng đường vào (m):", min_value=0.0, max_value=50.0, value=3.5, step=0.5)

            c_bed, c_bath = st.columns(2)
            with c_bed:
                bed_in = st.number_input("Số phòng ngủ:", min_value=1.0, max_value=20.0, value=3.0, step=1.0)
            with c_bath:
                bath_in = st.number_input("Số phòng vệ sinh:", min_value=1.0, max_value=20.0, value=3.0, step=1.0)

            c_ck1, c_ck2, c_ck3 = st.columns(3)
            with c_ck1:
                has_sodo = st.checkbox("Có Sổ đỏ / Sổ hồng", value=True)
            with c_ck2:
                has_car = st.checkbox("Ô tô vào tận nhà", value=True)
            with c_ck3:
                has_frontage = st.checkbox("Mặt tiền kinh doanh", value=False)

        if st.button("Dự Đoán Giá Trị Bất Động Sản", type="primary"):
            raw_payload = {
                "area": float(area_in),
                "floor_count": float(floor_in),
                "frontage_width": float(front_in),
                "house_depth": 0.0,
                "road_width": float(road_in),
                "bedroom_count": float(bed_in),
                "bathroom_count": float(bath_in),
                "has_so_do": 1 if has_sodo else 0,
                "car_access": 1 if has_car else 0,
                "is_frontage": 1 if has_frontage else 0,
                "property_type_name": str(prop_in),
                "province_clean": str(prov_in),
                "district_clean": str(dist_in),
                "house_direction": "Đông Nam",
                "balcony_direction": "Không xác định"
            }
            input_df = prepare_inference_dataframe(raw_payload, ml_bundle)
            model = ml_bundle["model"]
            pred_log = float(model.predict(input_df)[0])
            pred_vnd = float(np.expm1(np.clip(pred_log, a_min=10.0, a_max=30.0)))
            pred_billion = pred_vnd / 1e9
            price_m2_million = (pred_vnd / area_in) / 1e6

            st.markdown(f'<div class="price-badge">Giá Trị Ước Tính: {pred_billion:,.2f} Tỷ VNĐ</div>', unsafe_allow_html=True)
            res1, res2, res3 = st.columns(3)
            with res1:
                st.metric("Tổng giá trị quy đổi (VNĐ)", f"{pred_vnd:,.0f} VNĐ")
            with res2:
                st.metric("Đơn giá trên mỗi m²", f"{price_m2_million:,.1f} triệu VNĐ/m²")
            with res3:
                band = 0.18
                st.metric("Biên độ dao động tham chiếu (±18%)", f"{pred_billion*(1-band):,.2f} - {pred_billion*(1+band):,.2f} Tỷ")
