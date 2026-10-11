# Đặc Tả Kiến Trúc Dữ Liệu & Schema (Bronze - Silver - Gold & PostgreSQL)
**Thời gian thực hiện:** Ngày 5 (Sprint 2 Tuần)  
**Mục tiêu:** Chuẩn hoá cấu trúc dữ liệu theo Medallion Architecture và mô tả chi tiết schema bảng cơ sở dữ liệu.

---

## 1. Tổng Quan Kiến Trúc Lưu Trữ (Medallion Architecture)

```
[Hugging Face Raw]
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ 1. BRONZE LAYER (data/bronze/)                         │
│ - Định dạng: Parquet (Snappy compression)              │
│ - Dữ liệu thô nguyên bản từ Hugging Face               │
│ - Bổ sung siêu dữ liệu: ingested_at, batch_id, shard   │
└────────────────────────────────────────────────────────┘
        │
        ▼ (PySpark ETL 1: Clean, Typecast, Dedup)
┌────────────────────────────────────────────────────────┐
│ 2. SILVER LAYER (data/silver/)                         │
│ - Định dạng: Parquet (Snappy compression)              │
│ - Lọc bỏ trùng lặp (dropDuplicates)                    │
│ - Ép kiểu chuẩn: price, area, floor_count (Double)     │
│ - Điền khuyết thiếu mặc định (imputation)              │
│ - Tính toán chỉ số cơ sở: price_per_m2, price_billion  │
└────────────────────────────────────────────────────────┘
        │
        ▼ (PySpark ETL 2: Outliers, NLP, Address, Features)
┌────────────────────────────────────────────────────────┐
│ 3. GOLD LAYER (data/gold/)                             │
│ - Định dạng: Parquet (Snappy compression)              │
│ - Lọc ngoại lai: 10m² ≤ area ≤ 5000m²; 0.1 tỷ ≤ P ≤ 500 tỷ │
│ - Chuẩn hoá hành chính: province_clean, district_clean │
│ - NLP Features: has_so_do, car_access, is_frontage     │
│ - Temporal Features: published_year, month, quarter    │
│ - ML Ready: log_price, log_area                        │
└────────────────────────────────────────────────────────┘
        │
        ▼ (Storage Loader: SQLAlchemy Batch Ingest)
┌────────────────────────────────────────────────────────┐
│ 4. DATABASE SERVING (PostgreSQL / SQLite)              │
│ - Bảng: real_estate_gold                               │
│ - B-Tree Indexes: province, district, property_type    │
│ - Phục vụ: SQL Analytics, Streamlit Dashboard & Model  │
└────────────────────────────────────────────────────────┘
```

---

## 2. Chi Tiết Schema Từng Tầng

### 2.1. Bronze Layer Schema (`data/bronze/vietnam_real_estates_bronze.parquet`)
- Lưu trữ toàn bộ 19 trường thô ban đầu cùng 3 trường kiểm toán:
  - `name`: String
  - `description`: String
  - `property_type_name`: String
  - `province_name`: String
  - `district_name`: String
  - `ward_name`: String
  - `street_name`: String
  - `project_name`: String
  - `price`: String / LargeString
  - `area`: Double
  - `floor_count`: Double (nullable)
  - `frontage_width`: Double (nullable)
  - `house_depth`: Double (nullable)
  - `road_width`: Double (nullable)
  - `bedroom_count`: Double (nullable)
  - `bathroom_count`: Double (nullable)
  - `house_direction`: String (nullable)
  - `balcony_direction`: String (nullable)
  - `published_at`: String
  - **`ingested_at`**: String (ISO UTC timestamp)
  - **`batch_id`**: String (Mã lô thu nạp)
  - **`source_shard`**: String (Tên shard nguồn)

### 2.2. Silver Layer Schema (`data/silver/vietnam_real_estates_silver.parquet`)
- Dữ liệu đã làm sạch và ép kiểu số thực:
  - `price`: Double (VNĐ)
  - `area`: Double ($m^2$)
  - `price_per_m2`: Double (VNĐ/$m^2$)
  - `price_billion`: Double (Tỷ VNĐ)
  - `floor_count`: Double (mặc định = 1.0)
  - `bedroom_count`: Double (mặc định = 1.0)
  - `bathroom_count`: Double (mặc định = 1.0)
  - `frontage_width`, `house_depth`, `road_width`: Double (mặc định = 0.0)
  - `house_direction`, `balcony_direction`: String (mặc định = "Không xác định")

### 2.3. Gold Layer Schema (`data/gold/vietnam_real_estates_gold.parquet`)
- Bổ sung các đặc trưng nghiệp vụ và biến đổi máy học:
  - **`has_so_do`**: Integer (0 hoặc 1) - Có sổ đỏ/sổ hồng/pháp lý rõ ràng.
  - **`car_access`**: Integer (0 hoặc 1) - Ngõ ô tô vào được / đường rộng.
  - **`is_frontage`**: Integer (0 hoặc 1) - Nhà mặt tiền, mặt phố kinh doanh.
  - **`published_year`**: Integer - Năm đăng tin (2025, 2026).
  - **`published_month`**: Integer - Tháng đăng tin (1-12).
  - **`published_quarter`**: Integer - Quý đăng tin (1-4).
  - **`province_clean`**: String - Tên tỉnh đã loại bỏ tiền tố thừa.
  - **`district_clean`**: String - Tên quận đã loại bỏ tiền tố thừa.
  - **`log_price`**: Double - $\ln(1 + \text{price})$, biến mục tiêu huấn luyện ML.
  - **`log_area`**: Double - $\ln(1 + \text{area})$.

---

## 3. PostgreSQL Database Schema (`real_estate_gold`)

```sql
CREATE TABLE real_estate_gold (
    id SERIAL PRIMARY KEY,
    name TEXT,
    property_type_name VARCHAR(100),
    province_name VARCHAR(100),
    district_name VARCHAR(100),
    ward_name VARCHAR(100),
    price DOUBLE PRECISION,
    price_billion DOUBLE PRECISION,
    area DOUBLE PRECISION,
    price_per_m2 DOUBLE PRECISION,
    floor_count DOUBLE PRECISION,
    frontage_width DOUBLE PRECISION,
    house_depth DOUBLE PRECISION,
    road_width DOUBLE PRECISION,
    bedroom_count DOUBLE PRECISION,
    bathroom_count DOUBLE PRECISION,
    house_direction VARCHAR(50),
    balcony_direction VARCHAR(50),
    has_so_do INTEGER,
    car_access INTEGER,
    is_frontage INTEGER,
    published_at VARCHAR(50),
    published_year INTEGER,
    published_month INTEGER,
    published_quarter INTEGER,
    log_price DOUBLE PRECISION,
    log_area DOUBLE PRECISION,
    batch_id VARCHAR(100)
);

-- Chỉ mục B-Tree tối ưu hoá truy vấn
CREATE INDEX idx_re_province ON real_estate_gold (province_name);
CREATE INDEX idx_re_district ON real_estate_gold (district_name);
CREATE INDEX idx_re_property_type ON real_estate_gold (property_type_name);
CREATE INDEX idx_re_price ON real_estate_gold (price);
CREATE INDEX idx_re_year ON real_estate_gold (published_year);
```
