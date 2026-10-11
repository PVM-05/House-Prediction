"""
Pipeline Orchestrator (Cross-Platform CLI for Windows/Linux/macOS)
Supports running each tier individually or end-to-end:
  python run_pipeline.py ingest
  python run_pipeline.py etl
  python run_pipeline.py load
  python run_pipeline.py train
  python run_pipeline.py evaluate
  python run_pipeline.py app
  python run_pipeline.py all
"""
import sys
import subprocess
import argparse
from pathlib import Path

# UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PYTHON = sys.executable


def run_command(cmd, step_name):
    print(f"\n{'='*70}")
    print(f">> Executing: {step_name}")
    print(f">> Command: {' '.join(cmd)}")
    print(f"{'='*70}")
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"[!] Error: Step '{step_name}' failed with exit code {res.returncode}")
        sys.exit(res.returncode)
    print(f"[✓] Step '{step_name}' completed successfully.")


def main():
    parser = argparse.ArgumentParser(description="Vietnam Real Estate Big Data Pipeline Orchestrator")
    parser.add_argument(
        "action",
        choices=["ingest", "etl", "load", "train", "evaluate", "app", "all"],
        default="all",
        nargs="?",
        help="Pipeline phase to execute"
    )
    parser.add_argument("--sample-size", type=int, default=None, help="Sample size limit for ingestion")
    args = parser.parse_args()

    action = args.action

    if action == "ingest" or action == "all":
        ingest_cmd = [PYTHON, "-m", "src.ingestion.ingest_raw"]
        if args.sample_size:
            ingest_cmd.extend(["--sample-size", str(args.sample_size)])
        run_command(ingest_cmd, "Phase 2: Raw Ingestion -> Bronze Parquet")

    if action == "etl" or action == "all":
        run_command([PYTHON, "-m", "src.etl.clean"], "Phase 3 (ETL 1): Cleaning -> Silver Parquet")
        run_command([PYTHON, "-m", "src.etl.features"], "Phase 3 (ETL 2): Feature Engineering -> Gold Parquet")

    if action == "load" or action == "all":
        run_command([PYTHON, "-m", "src.storage.load_postgres"], "Phase 4: Lakehouse Storage -> Database")

    if action == "train" or action == "all":
        run_command([PYTHON, "-m", "src.ml.train_baseline"], "Phase 5 (ML Baseline): Ridge Regressor")
        run_command([PYTHON, "-m", "src.ml.train_lgbm"], "Phase 5 (ML Model): LightGBM Regressor")

    if action == "evaluate" or action == "all":
        run_command([PYTHON, "-m", "src.ml.evaluate"], "Phase 5 (ML Diagnostics): Feature Importance & Regional Errors")

    if action == "app":
        print("\n>> Launching Streamlit Web Application on http://localhost:8501 ...")
        subprocess.run(["streamlit", "run", "src/serving/app.py"])

    if action == "all":
        print("\n" + "#" * 70)
        print("  [✓] ALL 6 PIPELINES EXECUTED AND VERIFIED END-TO-END!")
        print("  To launch the interactive demo web application:")
        print("      streamlit run src/serving/app.py")
        print("      (or run: python run_pipeline.py app)")
        print("#" * 70 + "\n")


if __name__ == "__main__":
    main()
