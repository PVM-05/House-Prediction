from sympy import python


python
from pathlib import Path

import pandas as pd
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import streamlit as st

# Thư mục gốc của dự án
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

LAYERS = {
    "Bronze - Dữ liệu thô": DATA_DIR / "bronze",
    "Silver - Dữ liệu đã làm sạch": DATA_DIR / "silver",
    "Gold - Dữ liệu phục vụ mô hình": DATA_DIR / "gold",
}

st.set_page_config(
    page_title="Real Estate Data Explorer",
    page_icon="🏠",
    layout="wide",
)

st.title("🏠 KHÁM PHÁ DỮ LIỆU BẤT ĐỘNG SẢN")
st.caption("Big Data Pipeline — Medallion Architecture")

layer_name = st.selectbox(
    "Chọn tầng dữ liệu",
    list(LAYERS.keys()),
)

folder = LAYERS[layer_name]

if not folder.exists():
    st.error(f"Không tìm thấy thư mục: {folder}")
    st.stop()

files = sorted(folder.rglob("*.parquet"))

if not files:
    st.warning("Thư mục này chưa có file Parquet.")
    st.stop()

try:
    dataset = ds.dataset(
        [str(file) for file in files],
        format="parquet",
    )

    # Đếm bản ghi dựa trên metadata của từng file
    total_rows = sum(
        pq.ParquetFile(file).metadata.num_rows
        for file in files
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng số bản ghi", f"{total_rows:,}")
    col2.metric("Số cột", str(len(dataset.schema)))
    col3.metric("Số file Parquet", str(len(files)))

    st.subheader("📁 Danh sách file")
    st.write([str(f.relative_to(folder)) for f in files])

    st.subheader("🔎 Cấu trúc dữ liệu")
    schema_df = pd.DataFrame({
        "Tên cột": dataset.schema.names,
        "Kiểu dữ liệu": [
            str(field.type) for field in dataset.schema
        ],
    })
    st.dataframe(schema_df, use_container_width=True)

    st.subheader("📊 Xem trước dữ liệu")

    preview_size = st.selectbox(
        "Số bản ghi muốn xem",
        [10, 20, 50, 100],
        index=1,
    )

    preview = dataset.head(preview_size).to_pandas()
    st.dataframe(preview, use_container_width=True)

    st.download_button(
        "Tải bản xem trước CSV",
        data=preview.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{folder.name}_preview.csv",
        mime="text/csv",
    )

except Exception as e:
    st.error(f"Không thể đọc dữ liệu: {e}")

