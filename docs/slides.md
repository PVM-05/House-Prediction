---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #f8fafc
color: #1e293b
---

# HỆ THỐNG TÍCH HỢP & PHÂN TÍCH DỮ LIỆU LỚN
## BẤT ĐỘNG SẢN VIỆT NAM (KIẾN TRÚC MEDALLION LAKEHOUSE)
**Đồ Án Môn Học Tích Hợp Và Phân Tích Dữ Liệu Lớn**  
*Sinh viên thực hiện:* **Phạm Văn Minh** | *MSV:* **23010350**  
*Email:* **23010350@st.phenikaa-uni.edu.vn**  
*Đơn vị:* **Trường Công nghệ Thông tin - Trường Đại học Phenikaa**  
*Pipeline End-to-End Tự Động Hóa 6 Tầng Bằng Apache PySpark & Streamlit*

---

## 1. Bối Cảnh, Mục Tiêu & Tiêu Chí Nghiệm Thu

- **Bối cảnh nghiệp vụ:** Thị trường BĐS Việt Nam phân tán, thiếu chuẩn hóa, tin đăng chứa nhiều dữ liệu rác, trùng lặp và văn bản tự do phức tạp.
- **Nguồn dữ liệu:** `tinixai/vietnam-real-estates` trên Hugging Face Hub:
  - Toàn bộ repo: **3,500,744 bản ghi** (10 phân mảnh Parquet ~ 1.5 GB).
  - Phân mảnh nạp thực tế: `shard_0000.parquet` (**350,075 bản ghi thô**).
- **Tiêu chí nghiệm thu hệ thống (System Acceptance Criteria):**
  1. *Ingestion:* Thu nạp shard tự động, gắn siêu dữ liệu kiểm toán (`batch_id`, `ingested_at`).
  2. *ETL:* Xử lý phân tán PySpark, khử trùng lặp, lọc ngoại lệ, chuyển đổi schema.
  3. *Lưu trữ:* Nạp Lakehouse Serving DB có cam kết ACID và đánh chỉ mục B-Tree.
  4. *Dashboard:* Giao diện Streamlit 4 Tab trực quan hóa 100% số liệu thực nghiệm.
  5. *Kiểm thử:* Vượt qua 10/10 bài kiểm thử tự động (`pytest -v`).

---

## 2. Ánh Xạ 6 Đặc Trưng Dữ Liệu Lớn (The 6 V's of Big Data)

1. **Volume (Quy mô):** 350,075 dòng thô (mở rộng tối đa 3.5M dòng), xử lý song song out-of-core bằng **Apache PySpark**.
2. **Variety (Đa dạng):** Kết hợp dữ liệu thuộc tính có cấu trúc (diện tích, giá) với văn bản tự do (tiêu đề, mô tả pháp lý, ngõ ngách).
3. **Veracity (Chất lượng & Độ tin cậy):** Khử 29,686 tin trùng lặp, loại 12,932 giá null/<=0, lọc 7,162 ngoại lệ cực trị.
4. **Velocity (Thời gian & Dòng đời):** Dữ liệu thu nạp tháng 6-7/2025, gắn audit trail ISO 8601 bảo đảm khả năng tái chạy (Idempotency).
5. **Value (Giá trị mang lại):** Cung cấp công cụ AI định giá tự động và Dashboard phân tích thị trường phục vụ người dùng.
6. **Valence (Tính kết nối):** Cấu trúc phân cấp địa lý (Tỉnh/Thành $\rightarrow$ Quận/Huyện $\rightarrow$ Phường) và tương quan giữa đường vào với đơn giá.

---

## 3. Kiến Trúc Hồ Dữ Liệu 6 Tầng Medallion (Data Flow)

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Raw Source      : Hugging Face Hub (tinixai, 10 shards)   │
├──────────────────────────────────────────────────────────────┤
│ 2. Bronze Zone     : Parquet Snappy (350,075 dòng, 153.9 MB) │
├──────────────────────────────────────────────────────────────┤
│ 3. PySpark Clean   : Silver Parquet (307,457 dòng, 130.0 MB) │
├──────────────────────────────────────────────────────────────┤
│ 4. PySpark Features: Gold Parquet   (300,295 dòng, 128.2 MB) │
├──────────────────────────────────────────────────────────────┤
│ 5. Serving Storage : PostgreSQL / SQLite (300,295 dòng khớp) │
├──────────────────────────────────────────────────────────────┤
│ 6. Serving Layer   : Streamlit 4-Tab Dashboard & ML Model    │
└──────────────────────────────────────────────────────────────┘
```
*Vận hành tự động bằng 1 lệnh duy nhất: `python run_pipeline.py all`*  
*Minh họa trực quan:* `docs/images/00_architecture_flowchart.png`

---

## 4. Quản Lý Chất Lượng Dữ Liệu Trước và Sau Làm Sạch (ETL)

| Chỉ Số Chất Lượng | Tầng Đồng Tầng Đồng | Tầng Bạc Tầng Bạc | Tầng Vàng Tầng Vàng | Biện Pháp Kỹ Thuật |
| :--- | :---: | :---: | :---: | :--- |
| **Số lượng bản ghi** | **350,075** | **307,457** | **300,295** | Khử trùng, lọc giá null, lọc ngoại lệ |
| **Tỷ lệ giữ lại (%)** | 100.00% | **87.83%** | **97.67%** | Tỷ lệ giữ lại toàn quy trình: **85.78%** |
| **Tin trùng lặp** | 29,686 dòng | **0 dòng** | 0 dòng | `dropDuplicates()` trên 5 thuộc tính |
| **Giá null hoặc <= 0** | 12,932 dòng | **0 dòng** | 0 dòng | Lọc ép kiểu Double dương |
| **Ngoại lệ nghiệp vụ** | Tiềm ẩn | 7,162 dòng | **0 dòng** | Lọc theo 4 quy tắc miền giá trị |
| **Độ lệch chuẩn Giá** | - | 2,006.6 Tỷ | **25.98 Tỷ** | **Giảm phương sai nhiễu 77 lần** |

*Minh họa phễu & khuyết thiếu:* `docs/images/01_pipeline_funnel_retention.png` & `02_data_quality_missing_analysis.png`

---

## 5. Phân Tích Thống Kê Thị Trường Bất Động Sản (EDA Suite)

- **Toàn cảnh thị trường Tầng Vàng (300,295 tin đăng sạch):**
  - **Giá trung vị:** **7.30 Tỷ VNĐ** *(Giá trung bình: 14.57 Tỷ - Lệch phải cực đoan)*
  - **Đơn giá trung vị:** **94.2 Triệu VNĐ/m²** *(Khoảng Q1-Q3: 49.0 - 191.7 tr/m²)*
  - **Diện tích trung vị:** **80.0 m²** *(Khoảng Q1-Q3: 56.0 - 120.0 m²)*
- **Cơ cấu thị phần theo loại hình:**
  - Nhà riêng / Nhà phố: **143,450 tin (47.8%)**
  - Đất nền / Đất ở: **76,825 tin (25.6%)**
  - Căn hộ chung cư: **53,180 tin (17.7%)**
  - Biệt thự / Liền kề: **21,390 tin (7.1%)**
- **Đặc trưng pháp lý & tiếp cận:**
  - Có sổ đỏ/sổ hồng: **56.87%** | Ngõ ô tô vào được: **36.16%** | Mặt tiền: **50.84%**

*Minh họa 4-Panel EDA:* `docs/images/04_market_distribution.png`

---

## 6. Đánh Giá Hiệu Năng Pipeline & Lưu Trữ Đa Tầng

*Môi trường đo đạc thực tế: Intel Core i5-12500H (12 cores, 16 threads), 16 GB RAM, PySpark 3.5, Python 3.12*

| Giai Đoạn Pipeline | Thời Gian (s) | Số Dòng Xử Lý | Tốc Độ (Dòng/s) | Dung Lượng Lưu Trữ |
| :--- | :---: | :---: | :---: | :---: |
| **1. Raw Ingestion** | 35.00 s | 350,075 | 10,002 dòng/s | 153.89 MB (Bronze Parquet) |
| **2. PySpark Clean** | 50.33 s | 350,075 | 6,956 dòng/s | 130.04 MB (Silver Parquet) |
| **3. PySpark Features**| 76.67 s | 307,457 | 4,010 dòng/s | 128.20 MB (Gold Parquet) |
| **4. Database Storage** | 289.43 s | 300,295 | 1,038 dòng/s | 17.40 MB (SQLite Serving) |
| **Tổng Thời Gian ETL** | **451.43 s (~7.5 phút)** | - | **775 dòng/s** | **Tiết kiệm 29% đĩa (Nén 1.4x)** |

*Minh họa Dashboard Giám sát:* `docs/images/05_pipeline_monitoring_dashboard.png`

---

## 7. Ứng Dụng Học Máy Định Giá (Downstream Machine Learning)

- **Quy trình chia 3 tập nghiêm ngặt (Zero Data Leakage):**
  - Train: **70% (210,206 mẫu)** | Validation: **15% (45,044 mẫu)** | Holdout Test: **15% (45,045 mẫu)**
- **Kết quả đối sánh trên Tập Kiểm Thử Độc Lập (45,045 mẫu):**

| Tiêu Chí Đánh Giá | Hồi Quy Tuyến Tính (Hồi quy Ridge cơ sở) | Cây Quyết Định (Mô hình LightGBM) | Mức Cải Thiện |
| :--- | :---: | :---: | :---: |
| **$R^2$ Score (Thang log)** | **0.6266** | **0.8537** | **+36.24%** |
| **RMSE (Thang log)** | 0.6556 | **0.4104** | **-37.40%** |
| **MAE (Giá gốc - Tỷ VNĐ)** | 10.18 Tỷ | **4.64 Tỷ** | **-54.37%** |
| **MdAPE (Phần trăm trung vị)** | 37.28% | **20.47%** | **-16.81 điểm %** |

*Biểu đồ sai số & Feature Importance:* `docs/images/05_feature_importance.png` & `06_residual_analysis.png`

---

## 8. Ứng Dụng Phục Vụ & Bảng Điều Khiển Streamlit (4 Tabs)

- **Tab 1: Kiến Trúc & Tích Hợp Dữ Liệu:** Sơ đồ Medallion, thẻ KPI kho nguồn Hugging Face, bảng thuyết minh công nghệ.
- **Tab 2: Chất Lượng & Biến Đổi Dữ Liệu:** Đo lường tỷ lệ giữ lại 85.8%, biểu đồ phễu, biểu đồ khuyết thiếu, bảng thống kê 5 số trước/sau lọc ngoại lệ.
- **Tab 3: Phân Tích Thị Trường Bất Động Sản:** Bộ 4 biểu đồ EDA, tra cứu mặt bằng giá phân cấp Tỉnh/Thành $\rightarrow$ Quận/Huyện, ma trận tương quan.
- **Tab 4: Hiệu Năng, Giám Sát & Định Giá:**
  - Bảng điều khiển giám sát Dark Theme (`05_pipeline_monitoring_dashboard.png`).
  - Bảng KPI xuất tự động từ `pipeline_summary_metrics.csv`.
  - Bảng so sánh mô hình và Form định giá trực tuyến thông minh (kèm cảnh báo pháp lý).

---

## 9. Kiểm Thử Hệ Thống & Độ Tin Cậy (Quality Assurance)

- **Bộ kiểm thử tự động `pytest -v` gồm 10 bài test độc lập đạt 100% Passed:**
  1. `test_directories_exist`: Kiểm tra cấu trúc thư mục dữ liệu và mô hình.
  2. `test_bronze_parquet`: Kiểm tra schema và metadata `batch_id`, `ingested_at`.
  3. `test_silver_parquet`: Kiểm tra cột chuẩn hóa `price_billion`, `price_per_m2`.
  4. `test_gold_parquet`: Kiểm tra 33 cột đặc trưng NLP và biến đổi log.
  5. `test_data_quality_and_lineage_report`: Kiểm tra tính đơn điệu của phễu lọc.
  6. `test_storage_database`: Kiểm tra CSDL khớp 300,295 dòng, khóa chính UUID duy nhất.
  7. `test_three_way_split_and_metrics_no_leakage`: Kiểm tra 3 tập rời nhau tuyệt đối.
  8. `test_train_serving_consistency_and_inference`: Kiểm tra đồng nhất Train - Serving.
  9. `test_evaluation_diagnostics_and_residual_plot`: Kiểm tra tệp chẩn đoán sai số.
  10. `test_pipeline_summary_metrics_and_charts`: Kiểm tra sự tồn tại của 6 tệp biểu đồ và file CSV KPI.

---

## 10. Kết Luận, Hạn Chế Minh Bạch & Hướng Mở Rộng

- **Kết quả đạt được:**
  - Xây dựng thành công pipeline dữ liệu lớn 6 tầng chuẩn Medallion vận hành tự động.
  - Xử lý sạch và làm giàu **300,295 bản ghi bất động sản** có chất lượng cao.
  - Nâng hệ số giải thích $R^2$ từ 0.626 lên **0.8537**, giảm sai số trung bình hơn 54%.
- **Hạn chế thực nghiệm (Minh bạch học thuật):**
  - Môi trường thử nghiệm xử lý **1 phân mảnh đầy đủ (350,075 bản ghi thô)** để tối ưu thời gian chạy trên máy cá nhân (~7.5 phút), chưa nạp trọn vẹn 10 phân mảnh (3.5M dòng).
  - Chưa tích hợp tọa độ không gian GIS (kinh độ, vĩ độ) do nguồn dữ liệu web hạn chế.
- **Khả năng mở rộng:** Kiến trúc phân tán PySpark sẵn sàng mở rộng xử lý toàn bộ 10 shards hoặc kết nối Apache Kafka streaming khi triển khai trên cụm điện toán đám mây.

---
# XIN CẢM ƠN THẦY CÔ VÀ HỘI ĐỒNG!
*Hệ Thống Tích Hợp & Phân Tích Dữ Liệu Lớn Bất Động Sản Việt Nam*  
**Q&A - Câu Hỏi Phản Biện**
