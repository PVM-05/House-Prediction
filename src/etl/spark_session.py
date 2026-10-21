"""
PySpark Session Helper
Configures an optimized SparkSession for local execution with Arrow enabled.
Includes cross-platform Parquet writer resilient to Windows winutils requirements.
"""
import os
import sys
import shutil
from pathlib import Path
from pyspark.sql import SparkSession
import pyarrow as pa
import pyarrow.parquet as pq


def get_spark_session(app_name: str = "VietnamRealEstateETL") -> SparkSession:
    """
    Initializes and returns a configured SparkSession.
    Automatically detects JDK 17 on Windows if default JAVA_HOME is older.
    """
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    if sys.platform == "win32":
        jdk17_path = Path("C:/Program Files/Java/jdk-17")
        if jdk17_path.exists():
            os.environ["JAVA_HOME"] = str(jdk17_path)
            jdk17_bin = str(jdk17_path / "bin")
            if jdk17_bin not in os.environ.get("PATH", ""):
                os.environ["PATH"] = jdk17_bin + os.pathsep + os.environ.get("PATH", "")


    builder = (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.driver.memory", "4g")
        .config("spark.driver.maxResultSize", "2g")
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.parquet.compression.codec", "snappy")
    )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def save_spark_to_parquet(df, output_path: Path):
    """
    Saves a Spark DataFrame to Parquet cleanly on Windows using PyArrow streaming.
    Bypasses Hadoop winutils requirement while keeping Spark transformations.
    Safely cleans up any legacy directories before writing file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.exists():
        if output_path.is_dir():
            shutil.rmtree(output_path)
        else:
            output_path.unlink()

    print(f"[*] Exporting Spark DataFrame to Parquet via PyArrow: {output_path.name}...")
    pdf = df.toPandas()
    table = pa.Table.from_pandas(pdf)
    pq.write_table(table, str(output_path), compression="snappy")
    print(f"[+] Saved {len(pdf):,} rows ({output_path.stat().st_size / (1024*1024):.2f} MB) to {output_path}")
