# Khảo Sát & Phân Tích Dữ Liệu Ban Đầu (Data Profile)
**Tập dữ liệu:** `tinixai/vietnam-real-estates` (Hugging Face)  
**Thời gian thực hiện:** Ngày 1 (Sprint 2 Tuần)  
**Quy mô tổng thể:** 3,500,744 bản ghi (10 shards Parquet)  
**Mẫu khảo sát kiểm chứng:** 50,000 bản ghi từ `shard_0000.parquet`  

---

## 1. Cấu Trúc Các Trường Dữ Liệu (Schema & Dtypes)

Dataset gốc bao gồm 19 trường dữ liệu thô và được bổ sung thêm 3 trường siêu dữ liệu khi Ingestion vào Bronze Layer:

| Tên Cột | Kiểu Dữ Liệu Gốc | % Khuyết Thiếu (Null) | Mô Tả & Ý Nghĩa Nghiệp Vụ |
| :--- | :--- | :--- | :--- |
| `name` | string | 0.00% | Tiêu đề tin đăng (chứa từ khóa quan trọng: sổ đỏ, ô tô, mặt tiền) |
| `description` | string | 0.00% | Nội dung mô tả chi tiết bất động sản |
| `property_type_name` | string | 0.00% | Loại hình BĐS (Nhà, Đất, Căn hộ chung cư, Biệt thự...) |
| `province_name` | string | 0.00% | Tỉnh / Thành phố trực thuộc trung ương |
| `district_name` | string | 1.40% | Quận / Huyện / Thị xã |
| `ward_name` | string | 14.55% | Phường / Xã / Thị trấn |
| `street_name` | string | 40.92% | Tên đường phố |
| `project_name` | string | 75.18% | Tên dự án / khu đô thị |
| `price` | string/object | 2.83% | Giá niêm yết (cần ép kiểu sang float/double VND) |
| `area` | float64 | 0.00% | Diện tích bất động sản ($m^2$) |
| `floor_count` | float64 | 85.07% | Số tầng (tỉ lệ null cao, cần điền giá trị mặc định = 1.0) |
| `frontage_width` | float64 | 45.83% | Chiều rộng mặt tiền ($m$) |
| `house_depth` | float64 | 96.32% | Chiều sâu nhà ($m$) |
| `road_width` | float64 | 91.52% | Độ rộng đường trước nhà ($m$) |
| `bedroom_count` | float64 | 50.73% | Số phòng ngủ (impute bằng median theo loại hình) |
| `bathroom_count` | float64 | 53.79% | Số phòng vệ sinh |
| `house_direction` | string | 67.58% | Hướng nhà (Đông, Tây, Nam, Bắc, Đông Nam...) |
| `balcony_direction` | string | 84.43% | Hướng ban công |
| `published_at` | string | 0.00% | Thời điểm đăng tin (2025-06 đến 2026-03) |
| `ingested_at` | string (ISO) | 0.00% | Thời điểm nạp vào Bronze Layer |
| `batch_id` | string | 0.00% | Mã định danh lô thu nạp dữ liệu |
| `source_shard` | string | 0.00% | Tên shard nguồn trên Hugging Face |

---

## 2. Thống Kê Phân Phối Giá & Diện Tích

### Phân Phối Giá Bất Động Sản (Đơn vị: Tỷ VNĐ)
- **Số lượng có giá:** 48,583 / 50,000 dòng (1,417 dòng giá null hoặc thỏa thuận).
- **Giá trị nhỏ nhất (Min):** 0.0003 tỷ (300,000 VNĐ) $\rightarrow$ *Ngoại lai (outlier) do giá thuê hoặc tin rác.*
- **Phân vị 5% (P5):** 1.25 tỷ VNĐ.
- **Phân vị 25% (Q1):** 3.80 tỷ VNĐ.
- **Trung vị (Median / P50):** **7.25 tỷ VNĐ**.
- **Phân vị 75% (Q3):** 15.00 tỷ VNĐ.
- **Phân vị 95% (P95):** 55.00 tỷ VNĐ.
- **Giá trị lớn nhất (Max):** 881,020 tỷ VNĐ $\rightarrow$ *Ngoại lai cực trị, cần lọc bỏ trong tầng ETL.*
- **Nhận xét phân phối:** Phân phối giá bị lệch phải cực mạnh (Extreme Right-skewed). Bắt buộc phải áp dụng biến đổi $\log(1 + \text{price})$ để huấn luyện mô hình học máy hội tụ ổn định và tránh sai số cục bộ.

### Phân Phối Diện Tích (Đơn vị: $m^2$)
- **Giá trị nhỏ nhất (Min):** 3.63 $m^2$
- **Phân vị 25% (Q1):** 57.0 $m^2$
- **Trung vị (Median / P50):** **80.1 $m^2$**
- **Phân vị 75% (Q3):** 124.0 $m^2$
- **Phân vị 95% (P95):** 411.0 $m^2$
- **Giá trị lớn nhất (Max):** 470,000 $m^2$ (đất trang trại/nghỉ dưỡng quy mô lớn).

---

## 3. Phân Bổ Không Gian & Loại Hình Bất Động Sản

### Top 5 Tỉnh/Thành Có Lượng Tin Đăng Lớn Nhất:
1. **Hà Nội:** 17,328 tin (chiếm ~34.7%)
2. **TP. Hồ Chí Minh:** 16,955 tin (chiếm ~33.9%)
3. **Đà Nẵng:** 2,688 tin (chiếm ~5.4%)
4. **Bình Dương:** 2,231 tin (chiếm ~4.5%)
5. **Khánh Hòa:** 1,594 tin (chiếm ~3.2%)
*(Hai đại đô thị Hà Nội và TP.HCM chiếm tới gần 70% tổng lượng tin đăng thị trường).*

### Phân Loại Hình Bất Động Sản:
1. **Nhà riêng / Nhà phố:** 23,895 tin (47.8%)
2. **Đất nền / Đất ở:** 12,816 tin (25.6%)
3. **Căn hộ chung cư:** 8,867 tin (17.7%)
4. **Biệt thự / Nhà liền kề:** 3,563 tin (7.1%)
5. **Shophouse / Nhà phố thương mại:** 859 tin (1.7%)

---

## 4. Đề Xuất Chiến Lược Xử Lý Cho Tầng ETL (PySpark)

1. **Chuẩn hóa kiểu dữ liệu:** Ép kiểu trường `price` từ string sang Double, nhân hệ số hoặc lọc các tin `price <= 0` hoặc thỏa thuận.
2. **Xử lý giá trị ngoại lai (Outlier Thresholds):**
   - Lọc bỏ diện tích < $10m^2$ hoặc > $5,000m^2$.
   - Lọc bỏ tổng giá < 100 triệu VNĐ hoặc > 500 tỷ VNĐ.
   - Lọc đơn giá: $2 \text{ triệu/m}^2 \le \text{price\_per\_m2} \le 1 \text{ tỷ/m}^2$.
3. **Trích xuất đặc trưng văn bản (NLP/Regex):**
   - Khai thác tiêu đề và mô tả để tạo biến cờ nhị phân: `has_so_do` (có sổ đỏ/hồng), `car_access` (ngõ ô tô), `is_frontage` (nhà mặt tiền kinh doanh).
4. **Điền khuyết thiếu thông minh (Imputation):**
   - `floor_count`: điền 1.0.
   - `bedroom_count`: điền trung vị 1.0 hoặc 2.0.
   - `road_width`: điền 0.0 kèm theo cờ `car_access` từ văn bản mô tả.
