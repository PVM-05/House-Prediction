# Vietnam Real Estate Big Data Analytics & Price Prediction (2-Week Minimal Stack)

Hệ thống tích hợp và phân tích dữ liệu lớn phục vụ dự đoán giá bất động sản tại Việt Nam, dựa trên tập dữ liệu thực tế **`tinixai/vietnam-real-estates`** (hơn **3.5 triệu bản ghi** / 10 phân đoạn Parquet từ Hugging Face).

Dự án được thiết kế theo kiến trúc chuẩn **Medallion (Bronze -> Silver -> Gold)**, đảm bảo khả năng mở rộng xử lý dữ liệu lớn với **PySpark**, lưu trữ **PostgreSQL**, mô hình học máy **LightGBM**, và ứng dụng phục vụ trực quan bằng **Streamlit**.

---

## 1. Kiến Trúc 6 Tầng Hệ Thống

```
+--------------------------------------------------------+
| 1. Raw Source      : Hugging Face (3.5M records)       |
+--------------------------------------------------------+
| 2. Ingestion       : Python Script -> Bronze Parquet   |
|                      (kèm ingested_at, batch_id)       |
+--------------------------------------------------------+
| 3. ETL Processing  : PySpark Clean (Silver) &          |
|                      PySpark Feature Engineering (Gold)|
+--------------------------------------------------------+
| 4. Storage         : Bronze/Silver/Gold Parquet +      |
|                      PostgreSQL (fallback SQLite)      |
+--------------------------------------------------------+
| 5. Machine Learning: Ridge Baseline & LightGBM         |
|                      (RMSE, MAE, R², MAPE -> JSON)     |
+--------------------------------------------------------+
| 6. Serving         : Streamlit App (Dashboard + AI Form)|
+--------------------------------------------------------+
```

---

## 2. Cấu Trúc Thư Mục

```
House Prediction/
├── AGENTS.md                  # Quy tắc và lịch trình sprint 2 tuần
├── Makefile                   # Lệnh chạy tiện ích (make ingest / etl / load / train / app / all)
├── run_pipeline.py            # Trình điều phối chạy 1 lệnh đa nền tảng (Windows / Linux / macOS)
├── docker-compose.yml         # Khởi chạy PostgreSQL database
├── requirements.txt           # Danh mục dependencies tối giản
├── README.md                  # Tài liệu hướng dẫn sử dụng
├── docs/
│   ├── data_profile.md        # [Ngày 1] Khảo sát schema, nulls, phân phối giá
│   ├── schema.md              # [Ngày 5] Đặc tả schema Bronze, Silver, Gold & PostgreSQL
│   ├── report.md              # [Ngày 13] Báo cáo kỹ thuật tổng kết & dàn ý slide
│   ├── plan_bao_cao.md        # Kế hoạch chi tiết viết báo cáo và bảo vệ
│   ├── slides.md              # Dàn bài slide thuyết trình chuẩn Marp
│   └── images/                # Biểu đồ phân tích dữ liệu EDA độ phân giải cao
├── data/
│   ├── bronze/                # Parquet thô kèm metadata nạp
│   ├── silver/                # Parquet sạch, chuẩn hoá đơn vị
│   ├── gold/                  # Parquet giàu đặc trưng (NLP, outlier, địa chỉ)
│   └── real_estate.db         # SQLite database fallback (tự động)
├── models/
│   ├── baseline_ridge.joblib  # Mô hình Ridge baseline
│   ├── lgbm_model.joblib      # Mô hình LightGBM tối ưu
│   ├── metrics.json           # Bảng so sánh chỉ số đo lường
│   ├── feature_importance.png # Biểu đồ đặc trưng quan trọng
│   └── error_analysis.json    # Phân tích sai số theo vùng miền
└── src/
    ├── config.py              # Cấu hình tập trung toàn bộ dự án
    ├── ingestion/             # [Tầng 2] Nạp dữ liệu từ Hugging Face
    │   └── ingest_raw.py
    ├── etl/                   # [Tầng 3] PySpark ETL Engine
    │   ├── spark_session.py   # Cấu hình Spark local tối ưu
    │   ├── clean.py           # Làm sạch -> Silver Parquet
    │   └── features.py        # Feature Engineering -> Gold Parquet
    ├── storage/               # [Tầng 4] Nạp dữ liệu vào Database
    │   └── load_postgres.py
    ├── ml/                    # [Tầng 5] Huấn luyện & Đánh giá Model
    │   ├── train_baseline.py  # Ridge regression trên log(giá)
    │   ├── train_lgbm.py      # LightGBM Regressor
    │   └── evaluate.py        # Phân tích sai số theo tỉnh thành
    ├── analytics/             # [Tầng 5 Phụ trợ] Sinh biểu đồ EDA
    │   └── generate_eda_charts.py
    └── serving/               # [Tầng 6] Giao diện người dùng
        └── app.py             # Streamlit App: Dashboard + Form định giá
```

---

## 3. Hướng Dẫn Cài Đặt & Sử Dụng

### 3.1. Cài Đặt Môi Trường
Yêu cầu Python 3.10+ và Java (để chạy PySpark local).
```bash
pip install -r requirements.txt
```

### 3.2. (Tùy chọn) Bật PostgreSQL bằng Docker
```bash
docker compose up -d
```
*(Nếu không bật Docker, hệ thống tự động fallback sang SQLite tại data/real_estate.db mà không gặp bất kỳ lỗi nào).*

### 3.3. Chạy Toàn Bộ Pipeline 6 Tầng (1 Lệnh Duy Nhất)
Sử dụng Makefile (Linux/macOS) hoặc Python runner (Windows):
```bash
# Bằng Makefile
make all

# Hoặc bằng Python Runner
python run_pipeline.py all
```

Bạn cũng có thể chạy độc lập từng tầng:
- `python run_pipeline.py ingest` : Tải nạp dữ liệu từ Hugging Face về Bronze
- `python run_pipeline.py etl`    : Chạy PySpark Clean (Silver) và Features (Gold)
- `python run_pipeline.py load`   : Nạp Gold vào PostgreSQL / SQLite
- `python run_pipeline.py train`  : Huấn luyện Baseline Ridge & LightGBM
- `python run_pipeline.py evaluate`: Xuất biểu đồ Feature Importance & Sai số vùng miền

### 3.4. Khởi Chạy Ứng Dụng Web Streamlit
```bash
streamlit run src/serving/app.py
```
Truy cập trình duyệt tại: `http://localhost:8501` để trải nghiệm:
- **Tab 1: Định Giá Nhà Trực Tuyến:** Chọn tỉnh thành, quận huyện, diện tích, số tầng, số phòng, mặt tiền -> Dự đoán ngay giá trị nhà (Tỷ VNĐ) với khoảng tin cậy ±8%.
- **Tab 2: Dashboard Thị Trường BĐS:** Thống kê phân bổ tin đăng theo tỉnh thành, loại hình BĐS, tỷ lệ sổ đỏ/hồng, ngõ ô tô.
- **Tab 3: Hiệu Năng Mô Hình:** Xem bảng so sánh chỉ số đo lường thực tế và tầm quan trọng của các biến.

---

## 4. Kết Quả Thực Nghiệm

| Chỉ số đánh giá | Ridge Baseline | LightGBM Regressor | Nhận xét |
| :--- | :---: | :---: | :--- |
| **R² Score** | 0.6208 | **0.8227** | Cải thiện **+32.5%** độ giải thích dữ liệu |
| **RMSE (thang log)** | 0.6657 | **0.4552** | Sai số thang log giảm mạnh |
| **MAE (Tỷ VNĐ)** | 10.66 Tỷ | **5.05 Tỷ** | Sai số trung bình giảm hơn 50% |
| **MAPE (%)** | 62.77% | **39.84%** | Sai số phần trăm tương đối giảm đáng kể |
