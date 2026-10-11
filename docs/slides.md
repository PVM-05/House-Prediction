---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #f8fafc
color: #1e293b
---

# HỆ THỐNG TÍCH HỢP VÀ PHÂN TÍCH DỮ LIỆU LỚN
## DỰ ĐOÁN GIÁ BẤT ĐỘNG SẢN VIỆT NAM (3.5 TRIỆU BẢN GHI)
**Kiến Trúc Big Data 6 Tầng (Minimal Stack) - Sprint 2 Tuần**
*Đồ Án Môn Học Tích Hợp Và Xử Lý Dữ Liệu Lớn*

---

## 1. Bối Cảnh và Thách Thức Nghiệp Vụ

- **Thị trường BĐS Việt Nam:** Biến động mạnh, thiếu minh bạch, tin đăng phân tán.
- **Nguồn dữ liệu từ Hugging Face:** `tinixai/vietnam-real-estates`
  - **3,500,744 bản ghi** (10 phân đoạn Parquet ~ 1.5 GB nén).
  - Thu thập từ 06/2025 đến 03/2026 trên toàn quốc.
- **Thách thức của dữ liệu thực tế:**
  - Định dạng giá không nhất quán, lẫn tin ảo (ngoại lai cực đoan).
  - Văn bản tự do chứa thông tin pháp lý quan trọng (sổ đỏ/hồng, ngõ ô tô).
  - Phân phối giá lệch phải cực mạnh (Extreme Right-skewed).

---

## 2. Ánh Xạ 6 Đặc Trưng Của Big Data (The 6 V's)

1. **Volume (Quy mô):** 3.5 triệu dòng, xử lý out-of-core bằng **PySpark**.
2. **Variety (Đa dạng):** Dữ liệu bảng (tabular) kết hợp văn bản tự do (unstructured).
3. **Veracity (Độ tin cậy):** Lọc outlier miền giá trị, điền khuyết thiếu trung vị.
4. **Velocity (Vận tốc/Thời gian):** Theo dõi chu kỳ đăng tin, gắn `ingested_at`, `batch_id`.
5. **Value (Giá trị):** AI định giá tự động ($R^2 = 0.82$) và Dashboard phân tích.
6. **Valence (Tính kết nối):** Phân cấp Tỉnh -> Huyện -> Xã -> Tuyến đường.

---

## 3. Kiến Trúc Hệ Thống 6 Tầng (Minimal Stack)

```
+--------------------------------------------------------+
| 1. Raw Source      : Hugging Face Hub (3.5M records)   |
+--------------------------------------------------------+
| 2. Ingestion       : Python Script -> Bronze Parquet   |
+--------------------------------------------------------+
| 3. PySpark ETL     : Clean (Silver) & Features (Gold)  |
+--------------------------------------------------------+
| 4. Storage         : PostgreSQL (Fallback SQLite)      |
+--------------------------------------------------------+
| 5. Machine Learning: Ridge Baseline & LightGBM         |
+--------------------------------------------------------+
| 6. Serving Layer   : Streamlit (Dashboard & Form AI)   |
+--------------------------------------------------------+
```
*Vận hành tự động bằng 1 lệnh duy nhất: python run_pipeline.py all*

---

## 4. Tầng Ingestion và Lưu Trữ Medallion

- **Bronze Layer (`data/bronze/`):**
  - Tải nạp theo shard, bổ sung siêu dữ liệu kiểm toán `ingested_at`, `batch_id`.
  - Định dạng Parquet nén Snappy tối ưu I/O.
- **PostgreSQL Storage Layer:**
  - Docker Compose: Khởi chạy PostgreSQL 16 container (`docker compose up -d`).
  - Bảng `real_estate_gold` với chỉ mục B-Tree trên `(province_name, district_name, price)`.
  - Tự động fallback sang SQLite nếu môi trường chưa bật Docker.

---

## 5. Tầng PySpark ETL và Kỹ Thuật Đặc Trưng

- **ETL 1 (Silver - `src/etl/clean.py`):**
  - Khử trùng lặp trên cụm phân tán (`dropDuplicates`).
  - Ép kiểu dữ liệu số thực, xử lý null thông minh.
- **ETL 2 (Gold - `src/etl/features.py`):**
  - **Lọc ngoại lai:** $10 \le \text{area} \le 5000\text{ m}^2$, $0.1 \le \text{price} \le 500\text{ tỷ VNĐ}$.
  - **Khai phá văn bản (NLP Regex):**
    - `has_so_do`: Sổ đỏ, sổ hồng, pháp lý chuẩn (0/1).
    - `car_access`: Ngõ ô tô vào được, đường rộng (0/1).
    - `is_frontage`: Nhà mặt tiền kinh doanh (0/1).
  - **Biến đổi mục tiêu:** $\log(1 + \text{price})$ ổn định phương sai.

---

## 6. Kết Quả Khảo Sát và Phân Phối Dữ Liệu (EDA)

- **Phân phối giá gốc:** Lệch phải cực đại (Median: 7.25 Tỷ, Max: 881,020 Tỷ).
- **Sau biến đổi log:** Phân phối tiệm cận phân phối chuẩn Gauss, giúp mô hình hội tụ tốt.
- **Top tỉnh thành tập trung:** Hà Nội (~35%) và TP.HCM (~34%) chiếm gần 70% thanh khoản.
- **Tương quan:** Diện tích, độ rộng đường, mặt tiền và cờ sổ đỏ tương quan thuận với giá trị nhà.

*(Minh họa biểu đồ: docs/images/eda_price_distribution.png và eda_correlation_matrix.png)*

---

## 7. Thiết Kế và Huấn Luyện Machine Learning

- **Nguyên tắc No Data Leakage:**
  - Chia độc lập 80% Train - 20% Test cố định seed 42.
  - Bộ mã hóa OrdinalEncoder và Scaler chỉ Fit trên tập Train.
- **Mô hình đối chứng:**
  - **Baseline:** L2-Regularized Linear Regression (Ridge, alpha = 10.0).
  - **Challenger:** LightGBM Regressor (Histogram-based, Leaf-wise tree growth).
- **Hàm mất mát và Đánh giá:** Dự đoán $\log(\text{giá})$, chuyển đổi ngược $\exp(y) - 1$ để tính sai số VNĐ.

---

## 8. Kết Quả Đo Lường và So Sánh Hiệu Năng

| Chỉ Số Đánh Giá | Ridge Baseline | LightGBM Regressor | Mức Cải Thiện |
| :--- | :---: | :---: | :---: |
| **R² Score (Holdout)** | 0.6208 | **0.8227** | **+32.5%** |
| **RMSE (thang log)** | 0.6657 | **0.4552** | **-31.6%** |
| **MAE (Sai số TB)** | 10.66 Tỷ VNĐ | **5.05 Tỷ VNĐ** | **-52.6%** (Giảm > 1/2) |
| **MAPE (%)** | 62.77% | **39.84%** | Giảm mạnh |

- **Top đặc trưng quan trọng:** `area` (Diện tích), `district_clean` (Vị trí Quận), `road_width` (Đường vào), `car_access` (Ngõ ô tô).
- **Sai số theo khu vực:** Hà Nội (MAPE 18.2%), TP.HCM (23.0%), Hưng Yên (11.8%).

---

## 9. Trực Quan Hóa và Demo Ứng Dụng Streamlit

- **Tab 1: Định Giá Bất Động Sản Trực Tuyến**
  - Form nhập thông số kỹ thuật (Vị trí, Loại nhà, Diện tích, Số tầng, Mặt tiền, Tiện ích).
  - Trả về: Giá ước tính (Tỷ VNĐ), khoảng tin cậy sai số ±8%, so sánh với giá trung vị khu vực.
- **Tab 2: Dashboard Thị Trường BĐS**
  - Chỉ số toàn quốc (Tổng tin, Giá trung vị, Đơn giá/m²).
  - Biểu đồ phân bổ giá theo phân khúc và tỷ lệ tiện ích.
- **Tab 3: Hiệu Năng và Kiến Trúc Hệ Thống**

---

## 10. Kết Luận và Hướng Phát Triển

### Kết quả đạt được:
- Hoàn thành đầy đủ 6 tầng Big Data trong 2 tuần đúng cam kết.
- Mô hình đạt độ tin cậy cao (R² > 0.82), pipeline chạy 1 lệnh.
- 100% test case tự động vượt qua (7/7 passed).

### Hướng mở rộng:
- Tích hợp tọa độ GIS và bản đồ nhiệt không gian.
- Mở rộng xử lý Streaming với Apache Kafka khi tin đăng phát sinh liên tục.

**CẢM ƠN THẦY CÔ VÀ CÁC BẠN ĐÃ THEO DÕI (Q&A)**
