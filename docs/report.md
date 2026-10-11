# Báo Cáo Kỹ Thuật: Hệ Thống Tích Hợp & Phân Tích Dữ Liệu Lớn Dự Đoán Giá Nhà Việt Nam
**Dự án:** Vietnam Real Estate Big Data Analytics & Price Prediction Platform  
**Dataset:** `tinixai/vietnam-real-estates` (3,500,744 bản ghi)  
**Thời gian hoàn thành:** Sprint 2 Tuần (Minimal Big Data Architecture)  

---

## 1. Giới Thiệu & Bài Toán Nghiệp Vụ

Thị trường bất động sản tại Việt Nam có quy mô lớn, tính biến động cao và phân tán mạnh theo vùng địa lý. Các tin đăng trực tuyến thường bị nhiễu:
- Giá trị định dạng không đồng nhất ("tỷ", "triệu", "thỏa thuận", chuỗi văn bản tự do).
- Đơn vị diện tích xen lẫn đất nông nghiệp, đất thổ cư.
- Thiếu chuẩn hóa hành chính giữa các cấp Tỉnh/Thành phố, Quận/Huyện, Phường/Xã.
- Tỷ lệ tin đăng ảo (outliers) với mức giá cực đoan hoặc diện tích phi lý.

**Mục tiêu dự án:**
Xây dựng một pipeline dữ liệu lớn chuẩn **Medallion Architecture (Bronze $\rightarrow$ Silver $\rightarrow$ Gold)** từ đầu đến cuối (End-to-End), xử lý out-of-core bằng **PySpark**, lưu trữ cơ sở dữ liệu **PostgreSQL**, huấn luyện mô hình máy học **LightGBM** có độ chính xác cao và phục vụ trực quan qua **Streamlit App**.

---

## 2. Kiến Trúc 6 Tầng Hệ Thống (Minimal Stack)

```
┌────────────────────────────────────────────────────────┐
│ TẦNG 1: RAW SOURCE (Hugging Face Hub)                  │
│ - Dataset: tinixai/vietnam-real-estates                │
│ - 3.5 triệu bản ghi, 10 phân đoạn Parquet (~1.5 GB)    │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ TẦNG 2: INGESTION BUFFER (Bronze Layer)                │
│ - Trình nạp Python đệm dữ liệu vào Parquet             │
│ - Gắn siêu dữ liệu kiểm toán: ingested_at, batch_id    │
│ - Thư mục: data/bronze/vietnam_real_estates_bronze.pq  │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ TẦNG 3: PYSPARK ETL PROCESSING (Silver & Gold Layers)  │
│ - PySpark Engine xử lý song song, chống tràn RAM:      │
│   * ETL 1 (Silver): Lọc trùng, chuẩn hoá kiểu dữ liệu, │
│     điền khuyết thiếu, tính price_per_m2.              │
│   * ETL 2 (Gold): Lọc outlier miền giá trị, chuẩn hoá  │
│     địa chính, trích xuất NLP (sổ đỏ, ngõ ô tô).       │
│ - Thư mục: data/silver/ & data/gold/                   │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ TẦNG 4: LAKEHOUSE STORAGE (PostgreSQL / SQLite)        │
│ - Bảng: real_estate_gold                               │
│ - Tạo B-Tree Indexes phục vụ truy vấn OLAP tức thì     │
│ - Hỗ trợ Docker Compose PostgreSQL + fallback SQLite   │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ TẦNG 5: MACHINE LEARNING PIPELINE                      │
│ - Biến đổi log-transformation: log_price = ln(1 + P)   │
│ - Baseline: Ridge Regression                           │
│ - Challenger: LightGBM Gradient Boosting Regressor     │
│ - Chỉ số: RMSE, MAE, R², MAPE (ghi models/metrics.json)│
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ TẦNG 6: SERVING & DASHBOARD (Streamlit Application)    │
│ - Tab 1: Form định giá nhà bằng AI theo thời gian thực │
│ - Tab 2: Dashboard phân tích thị trường & trực quan hóa│
│ - Tab 3: Bảng so sánh mô hình & sơ đồ kiến trúc        │
└────────────────────────────────────────────────────────┘
```

---

## 3. Kết Quả Thực Nghiệm & So Sánh Mô Hình

Dữ liệu được phân chia nghiêm ngặt theo tỷ lệ **80% Train - 20% Test** với cố định random seed (`random_state=42`) để loại bỏ hoàn toàn rủi ro rò rỉ dữ liệu (data leakage).

### Bảng So Sánh Chỉ Số (Holdout Test Set):

| Chỉ Số Đánh Giá | Ridge Regression (Baseline) | LightGBM Regressor (Đề Xuất) | Mức Độ Cải Thiện |
| :--- | :---: | :---: | :---: |
| **$R^2$ Score (Độ giải thích)** | **0.6208** | **0.8227** | **+32.5%** |
| **RMSE (Thang đo $\log$)** | 0.6657 | **0.4552** | **-31.6%** (Giảm sai số mạnh) |
| **MAE (Tỷ VNĐ)** | 10.66 Tỷ | **5.05 Tỷ** | **-52.6%** (Giảm hơn một nửa) |
| **MAPE (%)** | 62.77% | **39.84%** | **-22.93%** |

**Nhận xét:**
- Mô hình tuyến tính Ridge chỉ nắm bắt được các tương quan phẳng ($R^2 \approx 0.62$), gặp khó khăn lớn với tương quan phi tuyến giữa diện tích, vị trí địa lý và các tiện ích ngõ xe hơi.
- Mô hình LightGBM nắm bắt xuất sắc các mối quan hệ phi tuyến và tương tác giữa các quận/huyện, nâng $R^2$ lên **0.8227** và giảm sai số trung bình (MAE) từ **10.66 tỷ xuống 5.05 tỷ VNĐ**.

---

## 4. Phân Tích Tầm Quan Trọng Đặc Trưng & Sai Số Khu Vực

### Top Đặc Trưng Ảnh Hưởng Lớn Nhất Đến Giá Nhà:
1. **`area` (Diện tích):** Yếu tố quyết định cơ sở đến quy mô giá trị.
2. **`district_clean` (Quận/Huyện):** Bất động sản có tính định vị cực kỳ mạnh mẽ (giá tại Hoàn Kiếm, Cầu Giấy khác biệt hoàn toàn so với Ba Vì, Mê Linh).
3. **`frontage_width` & `road_width`:** Chiều rộng mặt tiền và độ rộng đường trước nhà ảnh hưởng trực tiếp đến giá trị kinh doanh và thanh khoản.
4. **`car_access` (Ngõ ô tô vào được):** Tăng định giá trung bình của bất động sản từ 15% - 25% so với ngõ xe máy.
5. **`has_so_do` (Pháp lý sổ đỏ/hồng):** Là điều kiện tiên quyết bảo đảm an toàn giao dịch.

### Sai Số Dự Đoán Theo Vùng Địa Lý (Geographic Breakdown):
- **Hà Nội (16,266 tin):** Giá trung vị 9.0 Tỷ, Sai số tuyệt đối (MAE) 4.31 Tỷ, Trung vị sai số phần trăm (MAPE) **18.2%**.
- **TP. Hồ Chí Minh (16,171 tin):** Giá trung vị 8.5 Tỷ, MAE 6.63 Tỷ, Trung vị MAPE **23.0%**.
- **Bình Dương (2,060 tin):** Giá trung vị 2.9 Tỷ, MAE 1.29 Tỷ, Trung vị MAPE **17.9%**.
- **Hưng Yên (871 tin):** Giá trung vị 8.7 Tỷ, MAE 2.04 Tỷ, Trung vị MAPE **11.8%**.

---

## 5. Dàn Bài Slide Thuyết Trình (10 Slides Nghiệm Thu)

- **Slide 1:** Tiêu đề dự án, thành viên thực hiện, bối cảnh bài toán định giá BĐS Việt Nam trên Big Data.
- **Slide 2:** Khảo sát tập dữ liệu lớn `tinixai/vietnam-real-estates` (3.5M records, phân phối giá lệch phải, đặc thù ngôn ngữ tiếng Việt).
- **Slide 3:** Kiến trúc tổng thể 6 tầng tinh gọn (Raw $\rightarrow$ Ingestion $\rightarrow$ PySpark ETL $\rightarrow$ PostgreSQL $\rightarrow$ ML $\rightarrow$ Streamlit).
- **Slide 4:** Tầng Ingestion & Quản trị dữ liệu thô (Bronze Parquet, Ingestion Ledger, Batch Tracking).
- **Slide 5:** Tầng Xử lý PySpark ETL: Làm sạch dữ liệu, chuẩn hóa địa chính 63 tỉnh/thành, NLP bóc tách sổ đỏ và ngõ ô tô.
- **Slide 6:** Tầng Lưu trữ Medallion & Cơ sở dữ liệu phân tích PostgreSQL / Star Schema.
- **Slide 7:** Huấn luyện mô hình Machine Learning: Thiết kế chống rò rỉ dữ liệu (No Leakage), Ridge Baseline vs. LightGBM.
- **Slide 8:** Kết quả thực nghiệm: Bảng so sánh $R^2 = 0.8227$, biểu đồ Feature Importance và sai số theo từng tỉnh thành.
- **Slide 9:** Demo trực tiếp ứng dụng Streamlit: Form định giá nhà thông minh và Dashboard phân tích thị trường.
- **Slide 10:** Kết luận, bài học kinh nghiệm về kỹ thuật Big Data và hướng mở rộng tương lai (thêm bản đồ GIS, triển khai Kubernetes).
