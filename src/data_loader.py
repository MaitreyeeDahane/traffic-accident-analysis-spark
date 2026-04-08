"""
data_loader.py
Handles SparkSession initialization and CSV data loading.
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql import DataFrame


def create_spark_session(app_name: str = "TrafficAccidentAnalysis") -> SparkSession:
    """Initialize and return a SparkSession."""
    spark = (
        SparkSession.builder
        .appName(app_name)
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.driver.memory", "2g")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def load_csv(spark: SparkSession, filepath: str) -> DataFrame:
    """
    Load a CSV file into a Spark DataFrame.
    Enables inferSchema and header detection automatically.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found at: {filepath}")

    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .option("multiLine", "true")
        .option("escape", '"')
        .csv(filepath)
    )
    return df


def show_sample(df: DataFrame, n: int = 5) -> None:
    """Print sample rows and schema for quick inspection."""
    print(f"\n{'='*60}")
    print(f"Dataset loaded: {df.count()} rows, {len(df.columns)} columns")
    print(f"{'='*60}")
    print("\nSchema:")
    df.printSchema()
    print(f"\nSample ({n} rows):")
    df.show(n, truncate=False)
