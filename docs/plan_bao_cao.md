# Kế Hoạch & Khung Sườn Báo Cáo Kỹ Thuật (Project Report Plan)
**Đề tài:** Hệ Thống Tích Hợp & Phân Tích Dữ Liệu Lớn Dự Đoán Giá Nhà Ở Việt Nam  
**Dataset:** `tinixai/vietnam-real-estates` (3,500,744 bản ghi)  
**Thời gian thực hiện:** Sprint 2 Tuần (Minimal Big Data Architecture)  

---

Tài liệu này cung cấp **kế hoạch toàn diện và khung nội dung chi tiết** giúp bạn viết Báo cáo Kỹ thuật (Technical Report / Đồ án môn học) và chuẩn bị Slide bảo vệ trước giảng viên/hội đồng.

---

# PHẦN 1: DÀN Ý CHI TIẾT BÁO CÁO BẢN ĐẦY ĐỦ (WORD / LATEX / PDF)

## TRANG BÌA & THÔNG TIN CHUNG
- Tên trường, khoa (Công nghệ thông tin / Khoa học dữ liệu).
- Tên đề tài: **"Nghiên Cứu, Xây Dựng Pipeline Tích Hợp & Phân Tích Dữ Liệu Lớn Định Giá Bất Động Sản Việt Nam"**.
- Tên sinh viên, MSSV, Giảng viên hướng dẫn.
- Ngày tháng năm hoàn thành.

---

## TÓM TẮT ĐỒ ÁN (EXECUTIVE SUMMARY)
- **Bối cảnh:** Thị trường bất động sản Việt Nam có khối lượng giao dịch lớn nhưng dữ liệu phi tập trung, nhiễu và thiếu chuẩn hóa.
- **Nguồn dữ liệu:** Bộ dữ liệu thực tế lớn gồm **3.5 triệu tin đăng** từ Hugging Face (`tinixai/vietnam-real-estates`).
- **Phương pháp tiếp cận:** Triển khai đủ 6 tầng kiến trúc Big Data chuẩn Medallion (Bronze $\rightarrow$ Silver $\rightarrow$ Gold) sử dụng **PySpark** cho xử lý dữ liệu lớn, **PostgreSQL** lưu trữ phân tích, **LightGBM** dự đoán giá trên thang đo logarit, và **Streamlit** phục vụ ứng dụng trực quan.
- **Kết quả cốt lõi:** Mô hình LightGBM đạt **$R^2 = 0.8227$** (tăng 32.5% so với mô hình baseline Ridge), giảm sai số tuyệt đối trung bình (MAE) xuống **5.05 Tỷ VNĐ** (giảm hơn 50%), hệ thống chạy tự động toàn trình end-to-end chỉ với 1 lệnh.

---

## CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI & ĐẶC TRƯNG DỮ LIỆU LỚN

### 1.1. Tính cấp thiết của đề tài
- Nhu cầu định giá nhà đất minh bạch, giảm thiểu rủi ro cho người mua và ngân hàng thẩm định.
- Thách thức của dữ liệu BĐS Việt Nam: Ngôn ngữ tự nhiên phức tạp ("sổ đỏ", "ô tô đỗ cửa", "nở hậu"), giá tiền biến động từ trăm triệu tới hàng trăm tỷ, phân phối lệch phải cực đoan.

### 1.2. Ánh xạ 6 đặc trưng Big Data (The 6 V's of Big Data) vào bài toán
*(Dựa trên kiến thức khóa UCSD - Introduction to Big Data)*
1. **Volume (Quy mô):** 3,500,744 dòng dữ liệu, 10 phân đoạn Parquet (~1.5 GB nén), không thể dùng công cụ tính toán bộ nhớ đơn thuần.
2. **Variety (Đa dạng):** Dữ liệu có cấu trúc (diện tích, giá, số phòng) kết hợp dữ liệu phi cấu trúc (văn bản tiêu đề, mô tả pháp lý, ngõ ngách).
3. **Veracity (Độ tin cậy & Nhiễu):** Tỷ lệ tin ảo cao (giá 881.000 tỷ, đơn giá < 2 triệu/m²), trường dữ liệu khuyết thiếu nhiều (số tầng null 85%, số phòng null 50%).
4. **Velocity (Vận tốc & Thời gian):** Dữ liệu trải dài từ 2025 đến 2026, áp dụng cơ chế đánh dấu thời điểm nạp `ingested_at` và `batch_id` để kiểm soát dòng đời dữ liệu.
5. **Value (Giá trị):** Cung cấp công cụ AI định giá tự động và Dashboard thống kê thị trường cho cộng đồng.
6. **Valence (Tính liên kết):** Mối quan hệ cấu trúc phân cấp địa lý (Tỉnh/Thành $\rightarrow$ Quận/Huyện $\rightarrow$ Phường) và tương quan giữa chiều rộng đường với đơn giá đất.

---

## CHƯƠNG 2: CƠ SỞ LÝ THUYẾT & CÔNG NGHỆ SỬ DỤNG

### 2.1. Quy trình Khoa học Dữ liệu 5 bước (Steps in Data Science Process)
- Phân tích chu trình: Acquiring Data $\rightarrow$ Exploring Data $\rightarrow$ Pre-processing $\rightarrow$ Analyzing $\rightarrow$ Communicating Results & Action.

### 2.2. Kiến trúc Hồ Dữ liệu Medallion (Data Lakehouse)
- Khái niệm Bronze, Silver, Gold Layers.
- So sánh định dạng hàng (CSV) với định dạng cột (Apache Parquet với nén Snappy).

### 2.3. Khung tính toán phân tán Apache Spark & PySpark
- Kiến trúc Driver - Worker, cơ chế Lazy Evaluation (Transformations vs Actions).
- Tối ưu hóa xử lý song song với PySpark DataFrame.

### 2.4. Thuật toán Học máy & Đánh giá
- **Ridge Regression:** Cơ sở toán học L2-regularization, làm chuẩn tham chiếu (baseline).
- **LightGBM:** Gradient Boosted Decision Trees, thuật toán Histogram-based và cơ chế phát triển cây theo lá (Leaf-wise Tree Growth).
- **Kỹ thuật biến đổi:** Phép biến đổi $\log(1 + \text{price})$ xử lý phân phối lệch phải (Right-skewed distribution).
- **Các hàm đo lường:** $R^2$, RMSE, MAE, MAPE.

---

## CHƯƠNG 3: THIẾT KẾ & TRIỂN KHAI KIẾN TRÚC 6 TẦNG

```
Hugging Face (Raw) ──► Bronze Parquet ──► PySpark ETL (Silver/Gold) ──► PostgreSQL ──► LightGBM ──► Streamlit App
```

### 3.1. Tầng 1 & 2: Raw Source & Ingestion Buffer (Bronze Layer)
- Tải nạp theo lô từ Hugging Face Hub (`src/ingestion/ingest_raw.py`).
- Quản trị dữ liệu: bổ sung `ingested_at`, `batch_id`, lưu vào `data/bronze/`.

### 3.2. Tầng 3: PySpark ETL & Xử lý Dữ liệu Lớn (Silver & Gold Layers)
- **ETL 1 (Silver - `src/etl/clean.py`):**
  - Khử trùng lặp trên composite key (`dropDuplicates`).
  - Ép kiểu số thực (cast `price` từ chuỗi sang Double).
  - Điền giá trị khuyết thiếu (Imputation) thông minh.
  - Tính toán chỉ số dẫn xuất: `price_per_m2` và `price_billion`.
- **ETL 2 (Gold - `src/etl/features.py`):**
  - Lọc ngoại lai miền giá trị: $10 \le \text{area} \le 5000\text{ m}^2$, $0.1 \le \text{price} \le 500\text{ tỷ VNĐ}$, $2 \le \text{price/m}^2 \le 1000\text{ triệu/m}^2$.
  - Chuẩn hóa địa chính: loại bỏ tiền tố thừa của 63 tỉnh thành (`province_clean`, `district_clean`).
  - Trích xuất đặc trưng NLP Regex: `has_so_do` (pháp lý), `car_access` (ngõ ô tô), `is_frontage` (mặt tiền).
  - Trích xuất đặc trưng thời gian và biến đổi $\log(1 + \text{price})$.

### 3.3. Tầng 4: Lưu trữ Cơ sở Dữ liệu Phân tích (Storage Layer)
- Cấu hình PostgreSQL qua `docker-compose.yml` (kèm cơ chế tự động fallback SQLite).
- Bảng `real_estate_gold` và chiến lược đánh chỉ mục B-Tree (Indexes) trên `province_name`, `district_name`, `price`.

### 3.4. Tầng 5: Pipeline Học máy & Đánh giá (Machine Learning)
- Phân chia dữ liệu nghiêm ngặt 80% Train - 20% Test (Seed 42, chống rò rỉ dữ liệu).
- Huấn luyện Ridge Baseline (`src/ml/train_baseline.py`).
- Huấn luyện LightGBM Regressor (`src/ml/train_lgbm.py`), lưu kết quả vào `models/metrics.json`.
- Phân tích chẩn đoán sai số theo vùng miền (`src/ml/evaluate.py`).

### 3.5. Tầng 6: Phục vụ Người dùng (Serving Layer)
- Xây dựng ứng dụng Streamlit (`src/serving/app.py`):
  - Form AI định giá nhà trực tuyến theo thời gian thực (với khoảng tin cậy $\pm 8\%$).
  - Dashboard phân tích thị trường BĐS.

### 3.6. Tự động hóa Pipeline (Workflow Orchestration)
- Tự động hóa toàn bộ 6 tầng bằng 1 lệnh duy nhất qua `Makefile` (`make all`) và `run_pipeline.py`.

---

## CHƯƠNG 4: KẾT QUẢ THỰC NGHIỆM & THẢO LUẬN

### 4.1. Bảng số liệu so sánh hiệu năng
| Metric | Ridge Regression (Baseline) | LightGBM Regressor (Đề Xuất) | Đánh Giá Cải Thiện |
| :--- | :---: | :---: | :--- |
| **$R^2$ Score** | 0.6208 | **0.8227** | Cải thiện **+32.5%** độ giải thích dữ liệu |
| **RMSE (thang $\log$)** | 0.6657 | **0.4552** | Giảm sai số thang log **-31.6%** |
| **MAE (Tỷ VNĐ)** | 10.66 Tỷ | **5.05 Tỷ** | Giảm hơn **52.6%** sai số tuyệt đối |
| **MAPE (%)** | 62.77% | **39.84%** | Giảm sai số phần trăm tương đối |

### 4.2. Phân tích Tầm quan trọng Đặc trưng (Feature Importance)
- Top 1: `area` (Diện tích nhà đất).
- Top 2: `district_clean` (Vị trí quận/huyện).
- Top 3: `road_width` & `car_access` (Đường trước nhà, ngõ ô tô).
- Top 4: `has_so_do` (Pháp lý rõ ràng).

### 4.3. Phân tích Sai số theo Vùng Địa Lý (Geographic Error Breakdown)
- **Hà Nội (16,266 tin):** Giá trung vị 9.0 Tỷ, MAE 4.31 Tỷ, MAPE trung vị **18.2%**.
- **TP. Hồ Chí Minh (16,171 tin):** Giá trung vị 8.5 Tỷ, MAE 6.63 Tỷ, MAPE trung vị **23.0%**.
- **Bình Dương (2,060 tin):** Giá trung vị 2.9 Tỷ, MAE 1.29 Tỷ, MAPE trung vị **17.9%**.
- **Hưng Yên (871 tin):** Giá trung vị 8.7 Tỷ, MAE 2.04 Tỷ, MAPE trung vị **11.8%**.

---

## CHƯƠNG 5: HƯỚNG DẪN CÀI ĐẶT & DEMO ỨNG DỤNG
- Hướng dẫn chạy 1 lệnh với `run_pipeline.py all`.
- Hình ảnh chụp giao diện Streamlit: Form dự đoán giá và Dashboard trực quan.
- Kết quả kiểm thử tự động đạt 7/7 test cases (100% Passed).

---

## CHƯƠNG 6: KẾT LUẬN & HƯỚNG PHÁT TRIỂN
- **Ưu điểm đạt được:**
  - Hoàn thành trọn vẹn 6 tầng theo kiến trúc Big Data chuẩn mực.
  - Tối ưu hóa thời gian phát triển trong 2 tuần (Minimal Stack) mà không bỏ sót bước kỹ thuật nào.
  - Mô hình có độ chính xác cao và khả năng giải thích tốt.
- **Hạn chế:**
  - Chưa tích hợp bản đồ không gian GIS (kinh độ, vĩ độ).
  - Chưa triển khai cụm phân tán đa node (hiện chạy Spark local).
- **Hướng phát triển:**
  - Kết nối Kafka streaming khi tin đăng phát sinh thời gian thực.
  - Đưa bản đồ nhiệt (Heatmap) không gian vào giao diện Streamlit.

---

# PHẦN 2: DÀN BÀI 10 SLIDE THUYẾT TRÌNH BẢO VỆ

| Slide | Tiêu Đề Slide | Nội Dung Cốt Lõi Cần Trình Bày | Hình Ảnh / Biểu Đồ Minh Họa |
| :---: | :--- | :--- | :--- |
| **1** | **Bìa & Giới Thiệu** | Tên đề tài, người thực hiện, giảng viên, mục tiêu đề tài. | Logo trường, ảnh phối cảnh BĐS |
| **2** | **Bối Cảnh & Dữ Liệu Lớn** | Thực trạng thị trường BĐS Việt Nam và đặc thù 3.5M tin đăng (6 chữ V của Big Data). | Sơ đồ 6 chữ V (Volume, Veracity, ...) |
| **3** | **Kiến Trúc Tổng Thể 6 Tầng** | Giới thiệu luồng đi: Raw $\rightarrow$ Bronze $\rightarrow$ Silver $\rightarrow$ Gold $\rightarrow$ Postgres $\rightarrow$ ML $\rightarrow$ Streamlit. | Sơ đồ luồng kiến trúc hệ thống |
| **4** | **Tầng Ingestion & Lưu Trữ Medallion** | Tải nạp theo lô, gắn audit trail, định dạng Parquet nén Snappy. | Cấu trúc thư mục Bronze/Silver/Gold |
| **5** | **Tầng Xử Lý PySpark ETL** | Xử lý song song out-of-core: Khử trùng lặp, lọc outlier miền giá trị, bóc tách NLP sổ đỏ/ngõ ô tô. | Code snippet PySpark Transformations |
| **6** | **Tầng CSDL PostgreSQL** | Bảng `real_estate_gold`, cơ chế đánh chỉ mục B-Tree, cơ chế tự động fallback SQLite. | Schema bảng & câu lệnh Index |
| **7** | **Chiến Lược Máy Học (No Leakage)** | Chia tập 80/10/10, biến đổi $\log(\text{giá})$, đối chứng Ridge Baseline vs. LightGBM Regressor. | Đồ thị phân phối giá trước & sau log |
| **8** | **Kết Quả & Phân Tích Thực Nghiệm** | Bảng so sánh $R^2 = 0.8227$, MAE giảm 52.6%, biểu đồ Feature Importance, sai số theo tỉnh thành. | Bảng chỉ số + Ảnh `feature_importance.png` |
| **9** | **Demo Trực Tiếp Ứng Dụng** | Trình diễn Form định giá trực tuyến và Dashboard thống kê thị trường trên Streamlit. | Ảnh chụp màn hình Web App Streamlit |
| **10** | **Kết Luận & Q&A** | Tóm lược kết quả đạt được, bài học kỹ thuật Big Data, cảm ơn và trả lời câu hỏi. | Thông tin liên hệ & Q&A |

---

# PHẦN 3: BỘ CÂU HỎI PHẢN BIỆN THƯỜNG GẶP & GỢI Ý TRẢ LỜI

### Câu 1: Tại sao lại áp dụng biến đổi $\log(1 + \text{price})$ cho biến mục tiêu?
- **Trả lời:** Phân phối giá bất động sản có độ lệch phải (Right-skewed) cực kỳ lớn với đuôi rất dài (từ vài trăm triệu đến hàng trăm tỷ). Nếu huấn luyện trực tiếp, mô hình sẽ bị chi phối bởi các căn nhà nghìn tỷ làm sai số bình phương nổ tung. Phép biến đổi $\log(1 + x)$ giúp co dải giá trị, ổn định phương sai (Variance Stabilization), đưa phân phối về gần phân phối chuẩn, giúp thuật toán học máy hội tụ ổn định hơn. Khi suy luận, ta dùng $\exp(y) - 1$ để chuyển về giá trị VNĐ ban đầu.

### Câu 2: Tại sao LightGBM lại cho kết quả vượt trội hơn hẳn Ridge Regression?
- **Trả lời:** Định giá bất động sản là bài toán có tính phi tuyến tính và tương tác đa chiều rất cao (ví dụ: cùng diện tích $60m^2$ nhưng ở Cầu Giấy sẽ có đơn giá khác hoàn toàn so với Ba Vì; cùng ở Cầu Giấy nhưng ngõ ô tô sẽ có giá vượt trội so với ngõ xe máy). Ridge là mô hình tuyến tính nên không thể tự động học được các mối tương tác phi tuyến này nếu không tạo biến thủ công. Trong khi đó, LightGBM dựa trên cây quyết định (GBDT) với thuật toán phân nhánh theo lá (leaf-wise) tự động nắm bắt các phân vùng không gian và mối quan hệ phi tuyến, giúp $R^2$ tăng từ 0.62 lên 0.82.

### Câu 3: Việc sử dụng PySpark có cần thiết không khi dataset có thể nén gọn khoảng 1.5 GB?
- **Trả lời:** Mặc dù 1.5 GB nén có thể ép đọc vào RAM máy tính cấu hình cao, nhưng khi giải nén ra dạng bảng và thực hiện các phép toán phức tạp (bóc tách chuỗi regex, join dữ liệu, tính toán ma trận tương quan), dung lượng RAM yêu cầu sẽ tăng gấp 5–8 lần (dễ gây lỗi tràn bộ nhớ Out-Of-Memory). Sử dụng PySpark với cơ chế tính toán lười (Lazy Evaluation) và quản lý bộ nhớ thông minh chứng minh được khả năng mở rộng (Scalability) của kiến trúc khi quy mô tin đăng tăng lên 10 triệu hay 50 triệu bản ghi trong tương lai.

### Câu 4: Làm thế nào bạn đảm bảo mô hình không bị rò rỉ dữ liệu (Data Leakage)?
- **Trả lời:** Dữ liệu được chia thành tập Train (80%) và Test (20%) ngay từ đầu với cố định random seed. Mọi bước học thông số (tính trung vị điền khuyết thiếu, Fit bộ mã hóa OrdinalEncoder) đều chỉ được thực hiện trên tập Train, sau đó mới dùng để Transform tập Test. Tuyệt đối không dùng toàn bộ dữ liệu để tính toán thống kê trước khi chia tập.

### Câu 5: Tại sao chọn Streamlit thay vì FastAPI + React/Vue trong sprint 2 tuần?
- **Trả lời:** Theo nguyên tắc của bản rút gọn 2 tuần, mục tiêu tối thượng là có sản phẩm chạy được trọn vẹn từ đầu đến cuối (End-to-End). Tách riêng FastAPI và Frontend yêu cầu viết thêm CORS, quản lý state, API client và giao tiếp 2 tiến trình độc lập, dễ phát sinh lỗi tích hợp và tốn nhiều ngày làm UI. Streamlit cho phép viết ứng dụng fullstack bằng 100% Python, tích hợp trực tiếp cả Dashboard phân tích và Form gọi model trong cùng một file, tiết kiệm thời gian phát triển mà vẫn đáp ứng trọn vẹn yêu cầu demo trực quan.
