"""
visualization.py
Generates static charts (Matplotlib/Seaborn) and interactive Plotly figures.
Saves PNG outputs to outputs/charts/.
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

CHARTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

PALETTE = ["#E74C3C", "#E67E22", "#F1C40F", "#2ECC71", "#3498DB",
           "#9B59B6", "#1ABC9C", "#E91E63", "#FF5722", "#607D8B"]

sns.set_theme(style="whitegrid", font_scale=1.1)


def _save(fig, filename: str) -> str:
    path = os.path.join(CHARTS_DIR, filename)
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return path


# ──────────────────────────────────────────────
# Static charts (Matplotlib / Seaborn)
# ──────────────────────────────────────────────

def plot_accidents_by_city(df: pd.DataFrame) -> str:
    """Bar chart: accident count per city."""
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(df["city"], df["accident_count"], color=PALETTE[:len(df)])
    ax.set_title("Accidents by City", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("City")
    ax.set_ylabel("Number of Accidents")
    ax.tick_params(axis="x", rotation=45)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 5,
                str(int(bar.get_height())),
                ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    return _save(fig, "accidents_by_city.png")


def plot_severity_pie(df: pd.DataFrame) -> str:
    """Pie chart: severity distribution."""
    colors = {"Low": "#2ECC71", "Medium": "#F39C12", "High": "#E74C3C"}
    fig, ax = plt.subplots(figsize=(7, 7))
    wedge_colors = [colors.get(s, "#95A5A6") for s in df["severity"]]
    wedges, texts, autotexts = ax.pie(
        df["count"],
        labels=df["severity"],
        autopct="%1.1f%%",
        colors=wedge_colors,
        startangle=140,
        pctdistance=0.8,
        wedgeprops={"edgecolor": "white", "linewidth": 2}
    )
    for at in autotexts:
        at.set_fontsize(12)
        at.set_fontweight("bold")
    ax.set_title("Severity Distribution", fontsize=16, fontweight="bold", pad=20)
    fig.tight_layout()
    return _save(fig, "severity_pie.png")


def plot_monthly_trend(df: pd.DataFrame) -> str:
    """Line chart: monthly accident trend."""
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(df["month_year"], df["accident_count"],
            marker="o", color="#E74C3C", linewidth=2, markersize=5)
    ax.fill_between(df["month_year"], df["accident_count"], alpha=0.15, color="#E74C3C")
    ax.set_title("Monthly Accident Trend", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Month")
    ax.set_ylabel("Accidents")
    ax.tick_params(axis="x", rotation=45)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.tight_layout()
    return _save(fig, "monthly_trend.png")


def plot_hourly_distribution(df: pd.DataFrame) -> str:
    """Bar chart: accidents by hour of day."""
    fig, ax = plt.subplots(figsize=(13, 5))
    colors = ["#E74C3C" if h in [7, 8, 17, 18, 19] else "#3498DB" for h in df["hour"]]
    ax.bar(df["hour"], df["accident_count"], color=colors)
    ax.set_title("Accidents by Hour of Day", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Hour (24h)")
    ax.set_ylabel("Accidents")
    ax.set_xticks(range(0, 24))
    ax.text(0.98, 0.95, "Red = peak hours", transform=ax.transAxes,
            ha="right", va="top", color="#E74C3C", fontsize=10)
    fig.tight_layout()
    return _save(fig, "hourly_distribution.png")


def plot_weather_bar(df: pd.DataFrame) -> str:
    """Horizontal bar chart: accidents by weather condition."""
    fig, ax = plt.subplots(figsize=(10, 6))
    df_sorted = df.sort_values("count")
    bars = ax.barh(df_sorted["weather_condition"], df_sorted["count"],
                   color=sns.color_palette("Blues_d", len(df_sorted)))
    ax.set_title("Accidents by Weather Condition", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Number of Accidents")
    for bar in bars:
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
                str(int(bar.get_width())), va="center", fontsize=10)
    fig.tight_layout()
    return _save(fig, "weather_conditions.png")


def plot_road_condition(df: pd.DataFrame) -> str:
    """Bar chart: accidents by road condition."""
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(df["road_condition"], df["count"],
           color=sns.color_palette("Oranges_d", len(df)))
    ax.set_title("Accidents by Road Condition", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Road Condition")
    ax.set_ylabel("Accidents")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    return _save(fig, "road_conditions.png")


# ──────────────────────────────────────────────
# Plotly interactive figures (for Streamlit)
# ──────────────────────────────────────────────

def plotly_city_bar(df: pd.DataFrame) -> go.Figure:
    """Interactive bar chart — accidents by city."""
    fig = px.bar(
        df, x="city", y="accident_count",
        title="Accidents by City",
        color="accident_count",
        color_continuous_scale="Reds",
        labels={"accident_count": "Accidents", "city": "City"},
        text="accident_count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        xaxis_tickangle=-40,
    )
    return fig


def plotly_severity_pie(df: pd.DataFrame) -> go.Figure:
    """Interactive pie chart — severity distribution."""
    color_map = {"Low": "#2ECC71", "Medium": "#F39C12", "High": "#E74C3C"}
    fig = px.pie(
        df, values="count", names="severity",
        title="Severity Distribution",
        color="severity",
        color_discrete_map=color_map,
        hole=0.4,
    )
    fig.update_traces(textinfo="percent+label", pull=[0.03] * len(df))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
    return fig


def plotly_monthly_trend(df: pd.DataFrame) -> go.Figure:
    """Interactive line chart — monthly trend."""
    fig = px.line(
        df, x="month_year", y="accident_count",
        title="Monthly Accident Trend",
        markers=True,
        labels={"accident_count": "Accidents", "month_year": "Month"},
        color_discrete_sequence=["#E74C3C"],
    )
    fig.update_traces(line_width=2.5)
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_tickangle=-40,
    )
    return fig


def plotly_hourly_bar(df: pd.DataFrame) -> go.Figure:
    """Interactive bar chart — accidents by hour."""
    peak = [7, 8, 17, 18, 19]
    colors = ["#E74C3C" if h in peak else "#3498DB" for h in df["hour"]]
    fig = go.Figure(go.Bar(
        x=df["hour"], y=df["accident_count"],
        marker_color=colors,
        text=df["accident_count"],
        textposition="outside",
    ))
    fig.update_layout(
        title="Accidents by Hour of Day",
        xaxis_title="Hour (24h)",
        yaxis_title="Accidents",
        xaxis=dict(tickmode="linear", dtick=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def plotly_weather_bar(df: pd.DataFrame) -> go.Figure:
    """Interactive horizontal bar — accidents by weather."""
    df_sorted = df.sort_values("count", ascending=True)
    fig = px.bar(
        df_sorted, x="count", y="weather_condition",
        orientation="h",
        title="Accidents by Weather Condition",
        color="count",
        color_continuous_scale="Blues",
        labels={"count": "Accidents", "weather_condition": "Weather"},
        text="count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
    )
    return fig


def plotly_scatter_map(df: pd.DataFrame) -> go.Figure:
    """Scatter map showing accident hotspots (requires lat/lon)."""
    if "latitude" not in df.columns or "longitude" not in df.columns:
        return None
    color_map = {"Low": "green", "Medium": "orange", "High": "red"}
    fig = px.scatter_mapbox(
        df.dropna(subset=["latitude", "longitude"]),
        lat="latitude", lon="longitude",
        color="severity",
        color_discrete_map=color_map,
        hover_data=["city", "date", "weather_condition"],
        zoom=3,
        title="Accident Hotspots Map",
        mapbox_style="carto-positron",
        opacity=0.6,
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=500)
    return fig


def generate_all_static_charts(analysis_results: dict) -> dict:
    """Generate and save all static charts. Returns dict of saved paths."""
    paths = {}
    paths["city_bar"] = plot_accidents_by_city(analysis_results["by_city"])
    paths["severity_pie"] = plot_severity_pie(analysis_results["severity"])
    paths["monthly_trend"] = plot_monthly_trend(analysis_results["monthly_trend"])
    paths["hourly"] = plot_hourly_distribution(analysis_results["by_hour"])
    paths["weather"] = plot_weather_bar(analysis_results["by_weather"])
    paths["road"] = plot_road_condition(analysis_results["by_road"])
    print(f"[Visualization] Charts saved to: {CHARTS_DIR}")
    return paths
