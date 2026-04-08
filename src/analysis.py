"""
analysis.py
Core analytics using Spark transformations: groupBy, filter, aggregation.
Returns Pandas DataFrames for downstream visualization.
"""

import pandas as pd
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def accidents_by_city(df: DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Return accident counts per city, sorted descending."""
    result = (
        df.groupBy("city")
        .agg(F.count("*").alias("accident_count"))
        .orderBy(F.desc("accident_count"))
        .limit(top_n)
    )
    return result.toPandas()


def top_accident_prone_areas(df: DataFrame, n: int = 5) -> pd.DataFrame:
    """Top N most dangerous cities with severity breakdown."""
    result = (
        df.groupBy("city", "severity")
        .agg(F.count("*").alias("count"))
        .orderBy(F.desc("count"))
    )
    pdf = result.toPandas()
    # Pivot to wide format
    pivot = pdf.pivot_table(index="city", columns="severity", values="count", fill_value=0)
    pivot["total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("total", ascending=False).head(n).reset_index()
    return pivot


def accidents_by_hour(df: DataFrame) -> pd.DataFrame:
    """Accident count grouped by hour of day."""
    result = (
        df.groupBy("hour")
        .agg(F.count("*").alias("accident_count"))
        .orderBy("hour")
    )
    return result.toPandas()


def accidents_day_night(df: DataFrame) -> pd.DataFrame:
    """Split accidents into Day (6–18) vs Night (18–6)."""
    df_dn = df.withColumn(
        "period",
        F.when((F.col("hour") >= 6) & (F.col("hour") < 18), "Day").otherwise("Night")
    )
    result = (
        df_dn.groupBy("period")
        .agg(F.count("*").alias("count"))
        .orderBy("period")
    )
    return result.toPandas()


def accidents_by_weather(df: DataFrame) -> pd.DataFrame:
    """Accident count and percentage grouped by weather condition."""
    total = df.count()
    result = (
        df.groupBy("weather_condition")
        .agg(F.count("*").alias("count"))
        .withColumn("percentage", F.round(F.col("count") / total * 100, 2))
        .orderBy(F.desc("count"))
    )
    return result.toPandas()


def severity_distribution(df: DataFrame) -> pd.DataFrame:
    """Count and percentage per severity level."""
    total = df.count()
    result = (
        df.groupBy("severity")
        .agg(F.count("*").alias("count"))
        .withColumn("percentage", F.round(F.col("count") / total * 100, 2))
        .orderBy(F.desc("count"))
    )
    return result.toPandas()


def monthly_trend(df: DataFrame) -> pd.DataFrame:
    """Accidents aggregated by month-year for trend analysis."""
    result = (
        df.groupBy("month_year")
        .agg(F.count("*").alias("accident_count"))
        .orderBy("month_year")
    )
    pdf = result.toPandas()
    pdf["month_year"] = pd.to_datetime(pdf["month_year"])
    pdf = pdf.sort_values("month_year")
    return pdf


def peak_accident_hours(df: DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Return the N peak accident hours with counts."""
    result = (
        df.groupBy("hour")
        .agg(F.count("*").alias("count"))
        .orderBy(F.desc("count"))
        .limit(top_n)
    )
    return result.toPandas()


def accidents_by_road_condition(df: DataFrame) -> pd.DataFrame:
    """Accident breakdown by road condition."""
    result = (
        df.groupBy("road_condition")
        .agg(F.count("*").alias("count"))
        .orderBy(F.desc("count"))
    )
    return result.toPandas()


def yearly_summary(df: DataFrame) -> pd.DataFrame:
    """Year-over-year accident count."""
    result = (
        df.groupBy("year")
        .agg(
            F.count("*").alias("total_accidents"),
            F.avg("num_vehicles").alias("avg_vehicles"),
        )
        .orderBy("year")
    )
    return result.toPandas()


def spark_sql_analysis(df: DataFrame) -> dict:
    """
    Bonus: Run key queries using Spark SQL.
    Returns a dict of result DataFrames.
    """
    df.createOrReplaceTempView("accidents")
    spark = df.sparkSession

    results = {}

    results["high_severity_by_city"] = spark.sql("""
        SELECT city, COUNT(*) AS high_severity_count
        FROM accidents
        WHERE severity = 'High'
        GROUP BY city
        ORDER BY high_severity_count DESC
        LIMIT 10
    """).toPandas()

    results["weather_severity_cross"] = spark.sql("""
        SELECT weather_condition, severity, COUNT(*) AS count
        FROM accidents
        GROUP BY weather_condition, severity
        ORDER BY weather_condition, severity
    """).toPandas()

    results["monthly_high_accidents"] = spark.sql("""
        SELECT month_year, COUNT(*) AS accidents,
               SUM(CASE WHEN severity='High' THEN 1 ELSE 0 END) AS high_count
        FROM accidents
        GROUP BY month_year
        ORDER BY month_year
    """).toPandas()

    return results


def run_all_analysis(df: DataFrame) -> dict:
    """Run entire analysis suite and return all results as a dict."""
    print("\n[Analysis] Running full analysis suite...")
    results = {
        "by_city": accidents_by_city(df),
        "top_areas": top_accident_prone_areas(df),
        "by_hour": accidents_by_hour(df),
        "day_night": accidents_day_night(df),
        "by_weather": accidents_by_weather(df),
        "severity": severity_distribution(df),
        "monthly_trend": monthly_trend(df),
        "peak_hours": peak_accident_hours(df),
        "by_road": accidents_by_road_condition(df),
        "yearly": yearly_summary(df),
        "sql_results": spark_sql_analysis(df),
    }
    print("[Analysis] All analyses complete.")
    return results
