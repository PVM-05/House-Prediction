# Vietnam Real Estate Big Data Pipeline (2-Week Sprint)
PYTHON = python

.PHONY: help ingest etl load train app evaluate all clean

help:
	@echo "Available commands:"
	@echo "  make ingest    - Ingest raw dataset from Hugging Face to Bronze Parquet"
	@echo "  make etl       - Run PySpark ETL: Clean (Silver) & Features (Gold)"
	@echo "  make load      - Load Gold data into PostgreSQL (with SQLite fallback)"
	@echo "  make train     - Train Ridge baseline and LightGBM model"
	@echo "  make evaluate  - Generate feature importance & regional error diagnostics"
	@echo "  make app       - Launch Streamlit serving application"
	@echo "  make all       - Run the entire end-to-end pipeline"

ingest:
	$(PYTHON) -m src.ingestion.ingest_raw

etl:
	$(PYTHON) -m src.etl.clean
	$(PYTHON) -m src.etl.features

load:
	$(PYTHON) -m src.storage.load_postgres

train:
	$(PYTHON) -m src.ml.train_baseline
	$(PYTHON) -m src.ml.train_lgbm

evaluate:
	$(PYTHON) -m src.analytics.generate_eda_charts
	$(PYTHON) -m src.ml.evaluate

app:
	streamlit run src/serving/app.py

all: ingest etl load train evaluate
	@echo "[✓] All pipelines executed successfully!"
