# Khảo Sát & Phân Tích Dữ Liệu Ban Đầu (Data Profile)
**Tập dữ liệu:** `tinixai/vietnam-real-estates` (Hugging Face Hub)  
**Thời gian thực hiện:** Ngày 1 (Sprint 2 Tuần)  
**Quy mô toàn bộ kho nguồn:** 3,500,744 bản ghi (10 phân mảnh Parquet)  
**Phân mảnh đưa vào Pipeline thực tế:** `shard_0000.parquet` (**350,075 bản ghi thô**)  
**Mẫu khảo sát thăm dò Ngày 1:** 50,000 bản ghi cắt lát ban đầu (Initial Exploration Sample)  

---

> [!NOTE]
> **Lưu ý phương pháp luận:** 
> - Mẫu 50,000 bản ghi dưới đây là lát cắt thăm dò ban đầu trong Ngày 1 để đội ngũ nắm bắt nhanh cấu trúc schema, kiểu dữ liệu và tỷ lệ khuyết thiếu sơ bộ.
> - Khi đưa vào vận hành pipeline Big Data thực tế từ Ngày 2, toàn bộ **350,075 bản ghi thô** của phân mảnh `shard_0000.parquet` đã được nạp đầy đủ vào Tầng Đồng (Bronze), làm sạch thành 307,457 dòng (Silver) và 300,295 dòng (Gold). Số liệu kiểm toán chính thức của toàn pipeline được trình bày chi tiết tại `docs/report.md`.

---

## 1. Cấu Trúc Các Trường Dữ Liệu (Schema & Dtypes)

Dataset gốc bao gồm 19 trường dữ liệu thô và được bổ sung thêm 3 trường siêu dữ liệu khi thu nạp vào Bronze Layer:

| Tên Cột | Kiểu Dữ Liệu Gốc | % Khuyết Thiếu (Mẫu 50k) | % Khuyết Thiếu (Bronze 350k) | Mô Tả & Ý Nghĩa Nghiệp Vụ |
| :--- | :--- | :---: | :---: | :--- |
| `name` | string | 0.00% | 0.00% | Tiêu đề tin đăng (chứa từ khóa quan trọng: sổ đỏ, ô tô, mặt tiền) |
| `description` | string | 0.00% | 0.00% | Nội dung mô tả chi tiết bất động sản |
| `property_type_name` | string | 0.00% | 0.00% | Loại hình BĐS (Nhà, Đất, Căn hộ chung cư, Biệt thự...) |
| `province_name` | string | 0.00% | 0.00% | Tỉnh / Thành phố trực thuộc trung ương (63 tỉnh thành) |
| `district_name` | string | 1.40% | 1.75% | Quận / Huyện / Thị xã |
| `ward_name` | string | 14.55% | 14.41% | Phường / Xã / Thị trấn |
| `street_name` | string | 40.92% | 40.85% | Tên đường phố |
| `project_name` | string | 75.18% | 75.10% | Tên dự án / khu đô thị |
| `price` | string/object | 2.83% | 3.73% | Giá niêm yết (dạng text, cần ép kiểu sang Double VNĐ) |
| `area` | float64 | 0.00% | 0.00% | Diện tích bất động sản ($m^2$) |
| `floor_count` | float64 | 85.07% | 82.50% | Số tầng (tỉ lệ null cao, điền giá trị miền mặc định = 1.0) |
| `frontage_width` | float64 | 45.83% | 45.81% | Chiều rộng mặt tiền ($m$) |
| `house_depth` | float64 | 96.32% | 96.20% | Chiều sâu thửa đất ($m$) |
| `road_width` | float64 | 91.52% | 88.40% | Độ rộng đường trước nhà ($m$) |
| `bedroom_count` | float64 | 50.73% | 49.46% | Số phòng ngủ (điền giá trị mặc định = 1.0) |
| `bathroom_count` | float64 | 53.79% | 45.20% | Số phòng vệ sinh (điền giá trị mặc định = 1.0) |
| `house_direction` | string | 67.58% | 67.64% | Hướng nhà (Đông, Tây, Nam, Bắc, Đông Nam...) |
| `balcony_direction` | string | 84.43% | 65.20% | Hướng ban công |
| `published_at` | string | 0.00% | 0.00% | Thời điểm đăng tin (tháng 6 – 7/2025) |
| `ingested_at` | string (ISO) | - | 0.00% | Siêu dữ liệu thời điểm nạp vào Bronze Layer |
| `batch_id` | string | - | 0.00% | Mã định danh lô thu nạp dữ liệu |
| `source_shard` | string | - | 0.00% | Tên shard nguồn trên Hugging Face |

---

## 2. Thống Kê Phân Phối Giá & Diện Tích Thăm Dò

### Phân Phối Giá Bất Động Sản (Mẫu thăm dò ban đầu)
- **Số lượng có giá:** 48,583 / 50,000 dòng (1,417 dòng giá null hoặc thỏa thuận).
- **Giá trị nhỏ nhất (Min):** 0.0003 tỷ (300,000 VNĐ) $\rightarrow$ *Ngoại lai (outlier) do giá thuê hoặc tin rác.*
- **Phân vị 25% (Q1):** 3.80 tỷ VNĐ.
- **Trung vị (Median):** **7.25 tỷ VNĐ** (rất sát với trung vị 7.30 tỷ của toàn bộ 300k dòng Tầng Vàng).
- **Phân vị 75% (Q3):** 15.00 tỷ VNĐ.
- **Giá trị lớn nhất (Max):** 881,020 tỷ VNĐ $\rightarrow$ *Ngoại lai cực trị, cần lọc bỏ trong tầng PySpark ETL.*
- **Nhận xét phân phối:** Phân phối giá bị lệch phải cực mạnh (Extreme Right-skewed). Bắt buộc phải áp dụng biến đổi $\log(1 + \text{price})$ trong Tầng Vàng.

### Phân Phối Diện Tích (Đơn vị: $m^2$)
- **Giá trị nhỏ nhất (Min):** 3.63 $m^2$
- **Phân vị 25% (Q1):** 57.0 $m^2$
- **Trung vị (Median):** **80.1 $m^2$** (khớp với trung vị 80.0 m² của toàn bộ Tầng Vàng).
- **Phân vị 75% (Q3):** 124.0 $m^2$
- **Giá trị lớn nhất (Max):** 470,000 $m^2$ (đất nông trường hoặc lỗi nhập liệu).

---

## 3. Phân Bổ Không Gian & Loại Hình Bất Động Sản

### Top 5 Tỉnh/Thành Có Lượng Tin Đăng Lớn Nhất (Khảo sát sơ bộ):
1. **Hà Nội:** ~34.7% tổng số tin
2. **TP. Hồ Chí Minh:** ~33.9% tổng số tin
3. **Đà Nẵng:** ~5.4% tổng số tin
4. **Bình Dương:** ~4.5% tổng số tin
5. **Khánh Hòa:** ~3.2% tổng số tin
*(Hà Nội và TP.HCM chiếm gần 70% thị trường, định hướng chiến lược phân tích theo khu vực).*

---

## 4. Đề Xuất Quy Tắc Cho Tầng ETL PySpark

1. **Chuẩn hóa kiểu dữ liệu:** Ép kiểu trường `price` sang Double, lọc bỏ tin `price <= 0`.
2. **Xử lý ngoại lệ nghiệp vụ:**
   - Diện tích: $10 \le \text{area} \le 5,000\text{ m}^2$.
   - Tổng giá: $100\text{ triệu} \le \text{price} \le 500\text{ tỷ VNĐ}$.
   - Đơn giá: $2\text{ triệu} \le \text{price/m}^2 \le 1\text{ tỷ VNĐ/m}^2$.
   - Cấu trúc: $\text{floor\_count} \le 25$, $\text{bedroom\_count} \le 20$.
3. **Trích xuất đặc trưng văn bản NLP (Regex):** Tạo cờ `has_so_do`, `car_access`, `is_frontage`.
4. **Điền khuyết thiếu miền nghiệp vụ:** Số tầng = 1.0, số phòng ngủ = 1.0, đường trước nhà = 0.0.
