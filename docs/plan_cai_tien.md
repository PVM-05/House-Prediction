# Kế Hoạch Cải Tiến Dự Án Dựa Trên Skills & Workflows (.agents)
**Dự án:** Hệ Thống Tích Hợp & Phân Tích Dữ Liệu Lớn Dự Đoán Giá Nhà Việt Nam  
**Cơ sở áp dụng:** Bộ quy chế và kỹ năng chuẩn hóa trong `.agents/AGENTS.md` và `.agents/skills/`  

---

## 1. Tổng Quan Mục Tiêu Cải Tiến

Dựa trên bộ quy chuẩn chuyên nghiệp trong `.agents`, dự án sẽ được nâng cấp từ một **Pipeline 2 tuần hoàn thành mục tiêu cơ sở** lên một **Sản phẩm Đồ án Kỹ thuật Hoàn Chỉnh cấp độ Doanh nghiệp (Enterprise-ready & Academic Grade)** thông qua 5 nhóm năng lực cốt lõi:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. PLANNING WORKFLOW     : Brainstorming 3 phương án & Lập WBS         │
├────────────────────────────────────────────────────────────────────────┤
│ 2. TESTING WORKFLOW (TDD): Bổ sung Test Matrix, Edge Cases & Coverage  │
├────────────────────────────────────────────────────────────────────────┤
│ 3. CODE REVIEW WORKFLOW  : Rà soát Clean Code, Docstrings, Type Hints  │
├────────────────────────────────────────────────────────────────────────┤
│ 4. STANDARDS ENFORCEMENT : Tuân thủ design-rules & database-rules      │
├────────────────────────────────────────────────────────────────────────┤
│ 5. DOCUMENTATION PLAN    : Hoàn thiện trọn bộ 8 tài liệu đồ án chuẩn   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Chi Tiết Kế Hoạch Cải Tiến Theo Từng Nhóm Kỹ Năng

### 2.1. Nhóm Kế Hoạch & Thiết Kế (Planning - Skills: `brainstorming`, `writing-plans`)
*Mục tiêu: Đánh giá các phương án tối ưu hóa sâu hơn cho hệ thống trước khi triển khai.*

1. **Phương án Nâng cấp Mô hình Học máy (Machine Learning Brainstorming):**
   - **Phương án 1 (Hiện tại):** LightGBM Regressor đơn lẻ với Ordinal Encoding ($R^2 = 0.8227$).
   - **Phương án 2 (Đề xuất cải tiến):** Mô hình **Ensemble Stacking / Blending** kết hợp **LightGBM + CatBoost + XGBoost**, áp dụng Target Encoding theo vùng địa lý (`province`, `district`) kèm K-Fold Out-of-Fold (OOF) để triệt tiêu data leakage. Dự kiến nâng $R^2 \ge 0.85$.
   - **Phương án 3 (Không gian địa lý GIS):** K-Means Spatial Clustering trên tọa độ địa lý kết hợp Trọng số khoảng cách nghịch đảo (Inverse Distance Weighting - IDW) để phản ánh chính xác hiệu ứng láng giềng (Spatial Spillover Effect).

2. **Kế hoạch Phân rã Công việc (WBS Planning):**
   - Viết kế hoạch thực thi chi tiết theo chuẩn `writing-plans` với các checklist rõ ràng và tiêu chí nghiệm thu (acceptance criteria) trước khi chạm vào mã nguồn.

---

### 2.2. Nhóm Kiểm Thử & Gỡ Lỗi Hệ Thống (Testing - Skills: `test-driven-development`, `systematic-debugging`, `verification-before-completion`)
*Mục tiêu: Đưa chất lượng kiểm thử từ mức cơ bản (Smoke test) lên mức toàn diện (Full Regression & Defense-in-depth).*

1. **Mở rộng Ma trận Kiểm thử (Test Matrix Expansion):**
   - **Unit Tests cho NLP Regex Extractor:** Viết kịch bản kiểm thử độc lập cho các trường hợp biên của văn bản tiếng Việt:
     - Nhận diện từ khóa pháp lý: "sổ đỏ chính chủ", "sổ hồng riêng", "giấy tờ tay", "chưa sổ".
     - Nhận diện ngõ giao thông: "ngõ ô tô 7 chỗ đỗ cửa", "đường xe hơi tránh", "ngõ xe ba gác", "ngõ cụt xe máy".
     - Nhận diện mặt tiền: "mặt phố kinh doanh sầm uất", "nhà góc 2 mặt tiền".
   - **Test Outlier Filtering Boundaries:** Kiểm tra chính xác các ngưỡng lọc biên ($10m^2$, $5000m^2$, $0.1$ tỷ, $500$ tỷ VNĐ).
   - **Test Robustness / Exception Handling:** Kiểm tra phản ứng của mô hình khi gặp dữ liệu suy luận bất thường (diện tích cực lớn, địa chỉ không tồn tại, giá trị âm hoặc null).

2. **Quy trình Xác minh Trước khi Hoàn tất (`verification-before-completion`):**
   - Đo lường độ bao phủ mã nguồn (Code Coverage $\ge 85\%$).
   - Bắt buộc lưu vết log thực thi, kết quả kiểm tra cú pháp và kết quả benchmark trước khi đóng task.

3. **Cơ chế Gỡ lỗi Hệ thống (`systematic-debugging`):**
   - Áp dụng quy trình 4 bước khi phát sinh lỗi dữ liệu phân tán:
     1. Tái hiện lỗi trên tập dữ liệu tối thiểu (Minimal Reproduction).
     2. Truy vết nguyên nhân gốc rễ (Root Cause Tracing) qua DAG và Spark Execution Plan.
     3. Áp dụng giải pháp phòng thủ theo chiều sâu (Defense-in-depth).
     4. Xác minh không gây lỗi hồi quy (Regression Check).

---

### 2.3. Nhóm Rà Soát Mã Nguồn & Kiến Trúc (Code Review - Skills: `requesting-code-review`, `receiving-code-review`)
*Mục tiêu: Mã nguồn đạt chuẩn sản xuất (Production-grade), dễ đọc, dễ bảo trì.*

1. **Chuẩn hóa Mã nguồn (Clean Code & Refactoring):**
   - Bổ sung đầy đủ **Type Hints (`typing.Optional`, `typing.Tuple`, `typing.List`)** trên 100% các hàm.
   - Viết Docstrings chuẩn Google-style cho toàn bộ các module trong `src/`.
   - Phân tách các hàm xử lý dữ liệu dài thành các hàm đơn nhiệm (Single Responsibility Principle).

2. **Tối ưu Hiệu năng PySpark (Performance Tuning):**
   - Cấu hình quản lý bộ nhớ đệm: Áp dụng `.persist(StorageLevel.MEMORY_AND_DISK)` tại các điểm tái sử dụng DataFrame.
   - Tối ưu hóa phân vùng (Partition Pruning & Coalesce) trước khi ghi đĩa để tránh sinh ra quá nhiều tập tin nhỏ (Small Files Problem).

---

### 2.4. Nhóm Quy Tắc Thiết Kế & Cơ Sở Dữ Liệu (`design-rules.md`, `database-rules.md`)
*Mục tiêu: Đảm bảo giao diện người dùng và cơ sở dữ liệu tuân thủ tuyệt đối quy chuẩn.*

1. **Quy tắc Thiết kế Giao diện (`design-rules.md`):**
   - Duy trì **100% tiếng Việt chuẩn mực**, câu từ ngắn gọn, ngữ pháp chính xác.
   - Tuyệt đối **không sử dụng icon / emoji** trang trí trên toàn bộ giao diện và báo cáo (đã thực hiện và duy trì nghiêm ngặt).
   - Thiết kế Responsive Layout: Sử dụng `use_container_width=True` (hoặc `width='stretch'`), tự động xuống dòng trên các bảng dữ liệu khi chuỗi văn bản dài.
   - Thêm thông báo hướng dẫn người dùng thân thiện khi dữ liệu nhập vào vượt ngoài miền huấn luyện.

2. **Quy tắc Thiết kế Cơ sở Dữ liệu (`database-rules.md`):**
   - Tên bảng và tên cột bằng tiếng Anh, kiểu `snake_case`.
   - Chuẩn hóa Schema từ dạng bảng phẳng (Denormalized Flat Table) sang **Star Schema**:
     - Bảng chiều `dim_locations` (id, province_clean, district_clean, region).
     - Bảng chiều `dim_property_types` (id, type_name, description).
     - Bảng sự kiện `fct_real_estate_listings` (id, location_id, type_id, price, area, ...).
   - Đảm bảo trên các bảng cơ sở dữ liệu luôn có trường thời gian `created_at` và `updated_at`.

---

### 2.5. Nhóm Hoàn Thiện Bộ Tài Liệu Đồ Án (`document-plan.md`)
*Mục tiêu: Chuẩn bị trọn bộ 8 tài liệu theo quy định đồ án liên ngành.*

| STT | Tên Tài Liệu Quy Định | Tình Trạng Hiện Tại | Kế Hoạch Cải Tiến Hoàn Thiện |
| :---: | :--- | :---: | :--- |
| **1** | **Đặc tả yêu cầu (SRS)** | Đã có phác thảo trong data_profile | Viết file `docs/srs.md`: Chi tiết yêu cầu chức năng (FR1-FR6), phi chức năng (NFR), Actor, Use Cases. |
| **2** | **Thiết kế hệ thống** | Đã có kiến trúc trong README | Viết file `docs/system_design.md`: Sơ đồ kiến trúc tổng thể, sơ đồ tuần tự dữ liệu, sơ đồ ERD Star Schema. |
| **3** | **Tài liệu CSDL & Schema** | Đã có `docs/schema.md` | Bổ sung chi tiết giải thích kiểu dữ liệu, các ràng buộc toàn vẹn và tối ưu hóa index. |
| **4** | **Kế hoạch dự án (WBS)** | Đã có trong `AGENTS.md` | Bổ sung biểu đồ tiến độ Gantt Chart (bằng cú pháp Mermaid) và ma trận phân tích rủi ro. |
| **5** | **Tài liệu kiểm thử** | Đã có 7 unit test cases | Viết file `docs/test_plan.md`: Danh sách Test Cases, Test Matrix, kịch bản kiểm thử dữ liệu biên. |
| **6** | **Hướng dẫn sử dụng** | Đã có trong README | Viết file `docs/user_guide.md`: Hướng dẫn vận hành CLI và ảnh chụp thao tác từng bước trên Streamlit. |
| **7** | **Báo cáo đồ án cuối kỳ** | Đã có `docs/report.md` | Hoàn thiện bản báo cáo đầy đủ theo khung sườn chuẩn học thuật từ `docs/plan_bao_cao.md`. |
| **8** | **Slide bảo vệ đồ án** | Đã có `docs/slides.md` | Kiểm tra định dạng Marp, chèn biểu đồ EDA sắc nét phục vụ thuyết trình trực tiếp. |

---

## 3. Lộ Trình Thực Hiện Cải Tiến (Actionable Roadmap)

### Giai đoạn 1: Chuẩn hóa Kiểm thử & Chất lượng Mã nguồn (Testing & Code Quality)
- [ ] Mở rộng `tests/test_pipelines.py` bổ sung 10 test cases cho NLP regex và outlier edge cases.
- [ ] Thêm Type Annotations và chuẩn hóa Docstrings trong `src/etl/` và `src/ml/`.
- [ ] Đo lường độ bao phủ mã nguồn (code coverage).

### Giai đoạn 2: Tối ưu Hóa Mô Hình & Xử lý Dữ liệu Lớn (Model & Data Tuning)
- [ ] Triển khai script `src/ml/train_catboost.py` hoặc `train_stacking.py` đối chứng hiệu năng đa mô hình.
- [ ] Bổ sung bảng chiều `dim_locations` và `dim_property_types` chuẩn Star Schema trong PostgreSQL.

### Giai đoạn 3: Đóng Gói Bộ Tài Liệu Chuẩn 8 Hạng Mục (Full Document Suite)
- [ ] Hoàn thiện `docs/srs.md` (Đặc tả yêu cầu phần mềm).
- [ ] Hoàn thiện `docs/system_design.md` (Thiết kế kiến trúc và ERD chi tiết).
- [ ] Hoàn thiện `docs/test_plan.md` (Kế hoạch và ma trận kiểm thử chi tiết).

---

## 4. Cam Kết Tuân Thủ

Toàn bộ quá trình cải tiến cam kết:
1. Giữ vững tính ổn định: Không làm gián đoạn pipeline đang chạy thành công của dự án.
2. Tuyệt đối không dùng icon, emoji trong UI và tài liệu theo đúng `design-rules.md`.
3. Mọi thay đổi đều được kiểm thử và xác nhận bằng chứng (`verification-before-completion`) trước khi nghiệm thu.
