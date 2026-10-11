# Quy Tắc Phát Triển Dự Án (Sprint 2 Tuần)

## Phạm vi (deadline 2 tuần)
- Ưu tiên một pipeline chạy end-to-end đơn giản hơn là nhiều công nghệ.
- KHÔNG thêm Kafka, Airflow, MinIO, MLflow, FastAPI trừ khi được yêu cầu rõ.
- Stack cố định: Python, PySpark, Parquet, PostgreSQL, LightGBM/XGBoost, Streamlit.
- Mỗi tầng phải chạy được bằng một lệnh (Makefile / run_pipeline.py: make ingest / etl / load / train / app / all).
- Nếu một việc dự kiến quá 1 ngày, dừng lại và đề xuất phương án đơn giản hơn.

## Ưu tiên khi thiếu thời gian
1. Pipeline chạy được đủ 6 tầng
2. Kết quả model đo lường đúng (không leakage)
3. Demo Streamlit
4. Tài liệu và báo cáo
5. Tối ưu model, tính năng phụ

## Lịch trình 2 tuần
- **Tuần 1: Data + Pipeline**
  - Ngày 1: Load dataset, xem schema, null, phân phối giá; dựng repo + AGENTS.md -> `docs/data_profile.md`
  - Ngày 2: Ingestion: lưu raw, ghi Bronze Parquet (kèm `ingested_at`, `batch_id`) -> `src/ingestion/`
  - Ngày 3: ETL 1: làm sạch, chuẩn hoá đơn vị giá/diện tích, xử lý null, bỏ trùng -> `src/etl/clean.py` -> Silver
  - Ngày 4: ETL 2: outlier, chuẩn hoá địa chỉ, feature engineering -> `src/etl/features.py` -> Gold
  - Ngày 5: Nạp Gold vào PostgreSQL, viết schema doc -> `src/storage/load_postgres.py`, `docs/schema.md`
  - Ngày 6–7: Đệm / sửa lỗi / EDA nhanh cho báo cáo
- **Tuần 2: ML + Demo + Báo cáo**
  - Ngày 8: Split train/valid/test, baseline Ridge, dự đoán log(giá) -> `src/ml/train_baseline.py`
  - Ngày 9: LightGBM/XGBoost, so sánh metric (RMSE, MAE, R², MAPE) -> `models/metrics.json`
  - Ngày 10: Feature importance, phân tích lỗi theo khu vực -> `src/ml/evaluate.py`
  - Ngày 11: Streamlit: dashboard + form dự đoán -> `src/serving/app.py`
  - Ngày 12: Script chạy end-to-end (`make all`), README, sơ đồ kiến trúc
  - Ngày 13: Viết báo cáo + slide -> `docs/report.md`
  - Ngày 14: Tập demo, dự phòng
