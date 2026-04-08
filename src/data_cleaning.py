"""
data_cleaning.py
Handles null values, duplicates, type conversion, and normalization.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, FloatType


# Mapping of possible raw column names → standardized names
COLUMN_ALIASES = {
    "location": "city",
    "accident_location": "city",
    "place": "city",
    "accident_date": "date",
    "accident_time": "time",
    "accident_severity": "severity",
    "weather": "weather_condition",
    "road_type": "road_condition",
    "vehicles_involved": "num_vehicles",
    "vehicle_count": "num_vehicles",
    "lat": "latitude",
    "lon": "longitude",
    "lng": "longitude",
}

REQUIRED_COLUMNS = ["city", "date", "time", "severity", "weather_condition",
                    "road_condition", "num_vehicles"]


def standardize_column_names(df: DataFrame) -> DataFrame:
    """Rename columns to a consistent standard, handling variations."""
    renamed = {c: c.lower().strip().replace(" ", "_") for c in df.columns}
    for old, new in renamed.items():
        if old != new:
            df = df.withColumnRenamed(old, new)

    # Apply known aliases
    for alias, standard in COLUMN_ALIASES.items():
        if alias in df.columns and standard not in df.columns:
            df = df.withColumnRenamed(alias, standard)

    return df


def drop_duplicates(df: DataFrame) -> DataFrame:
    """Remove exact duplicate rows."""
    before = df.count()
    df = df.dropDuplicates()
    after = df.count()
    print(f"Duplicates removed: {before - after}")
    return df


def handle_nulls(df: DataFrame) -> DataFrame:
    """
    Drop rows missing critical fields.
    Fill minor nulls with sensible defaults.
    """
    # Drop rows without core identifying fields
    critical = ["city", "date", "severity"]
    df = df.dropna(subset=critical)

    # Fill categorical nulls with 'Unknown'
    cat_cols = ["weather_condition", "road_condition"]
    for col in cat_cols:
        if col in df.columns:
            df = df.fillna({col: "Unknown"})

    # Fill numeric nulls with median-friendly defaults
    if "num_vehicles" in df.columns:
        df = df.fillna({"num_vehicles": 1})

    return df


def normalize_categoricals(df: DataFrame) -> DataFrame:
    """Title-case all categorical string columns for consistency."""
    cat_cols = ["city", "severity", "weather_condition", "road_condition"]
    for col in cat_cols:
        if col in df.columns:
            df = df.withColumn(col, F.initcap(F.trim(F.col(col))))
    return df


def parse_datetime(df: DataFrame) -> DataFrame:
    """
    Parse date and time columns; extract hour, day_of_week, month, year.
    Supports common date formats.
    """
    date_formats = ["yyyy-MM-dd", "MM/dd/yyyy", "dd-MM-yyyy", "yyyy/MM/dd"]

    # Try parsing date with multiple formats
    date_col = F.col("date").cast("string")
    parsed_date = None
    for fmt in date_formats:
        parsed_date = F.to_date(date_col, fmt)
        # Use coalesce to keep first non-null parse
        df = df.withColumn("_parsed_date", parsed_date)
        df = df.withColumn("date", F.coalesce(F.col("_parsed_date"), F.col("date").cast("date")))

    df = df.drop("_parsed_date")

    # Extract time parts if time column exists
    if "time" in df.columns:
        df = df.withColumn(
            "hour",
            F.hour(F.to_timestamp(F.col("time"), "HH:mm"))
        )
        # Fallback: parse hour from string directly
        df = df.withColumn(
            "hour",
            F.coalesce(
                F.col("hour"),
                F.split(F.col("time").cast("string"), ":").getItem(0).cast(IntegerType())
            )
        )

    # Extract calendar fields from date
    df = (df
          .withColumn("day_of_week", F.dayofweek(F.col("date")))
          .withColumn("month", F.month(F.col("date")))
          .withColumn("year", F.year(F.col("date")))
          .withColumn("month_year", F.date_format(F.col("date"), "yyyy-MM"))
          )

    return df


def cast_numerics(df: DataFrame) -> DataFrame:
    """Ensure numeric columns have correct types."""
    if "num_vehicles" in df.columns:
        df = df.withColumn("num_vehicles", F.col("num_vehicles").cast(IntegerType()))
    for col in ["latitude", "longitude"]:
        if col in df.columns:
            df = df.withColumn(col, F.col(col).cast(FloatType()))
    return df


def clean_data(df: DataFrame) -> DataFrame:
    """Full cleaning pipeline — call this as the single entry point."""
    print("\n[Cleaning] Starting data cleaning pipeline...")
    df = standardize_column_names(df)
    df = drop_duplicates(df)
    df = handle_nulls(df)
    df = normalize_categoricals(df)
    df = parse_datetime(df)
    df = cast_numerics(df)
    print(f"[Cleaning] Cleaned dataset: {df.count()} rows remaining.")
    return df
