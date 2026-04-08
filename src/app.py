"""
app.py  —  Traffic Accident Analysis Dashboard
Run with: streamlit run src/app.py
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import streamlit as st
import plotly.express as px

# ── Path setup so we can import sibling modules ──────────────────────────────
SRC_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(SRC_DIR, ".."))
sys.path.insert(0, SRC_DIR)

DATA_PATH = os.path.join(ROOT_DIR, "data", "accidents.csv")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Traffic Accident Analysis",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        text-align: center;
        border-left: 4px solid #e74c3c;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #e74c3c; }
    .metric-label { font-size: 0.85rem; color: #aaa; margin-top: 4px; }
    .insight-card {
        background: #f8f9fa;
        border-left: 4px solid #3498db;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 8px;
        font-size: 0.95rem;
    }
    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #2c3e50;
        border-bottom: 2px solid #e74c3c;
        padding-bottom: 6px;
        margin: 1.5rem 0 1rem 0;
    }
    .stPlotlyChart { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)


# ── Data loading (cached) ─────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading dataset...")
def load_data() -> pd.DataFrame:
    """
    Load data via PySpark if available, otherwise fall back to Pandas.
    This ensures the app works on Streamlit Cloud without a full Spark install.
    """
    try:
        from data_loader import create_spark_session, load_csv
        from data_cleaning import clean_data

        spark = create_spark_session()
        sdf = load_csv(spark, DATA_PATH)
        sdf = clean_data(sdf)
        df = sdf.toPandas()

        # Coerce dtypes after conversion
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["num_vehicles"] = pd.to_numeric(df["num_vehicles"], errors="coerce").fillna(1).astype(int)
        df["hour"] = pd.to_numeric(df["hour"], errors="coerce").fillna(0).astype(int)
        return df

    except Exception:
        # Fallback: plain Pandas pipeline (for Streamlit Cloud)
        df = pd.read_csv(DATA_PATH)
        df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["city", "date", "severity"])
        for col in ["city", "severity", "weather_condition", "road_condition"]:
            if col in df.columns:
                df[col] = df[col].str.strip().str.title()
        if "time" in df.columns:
            df["hour"] = df["time"].astype(str).str.split(":").str[0].str.extract(r"(\d+)")[0].fillna(0).astype(int)
        else:
            df["hour"] = 0
        df["month"] = df["date"].dt.month
        df["year"] = df["date"].dt.year
        df["month_year"] = df["date"].dt.to_period("M").astype(str)
        df["num_vehicles"] = pd.to_numeric(df.get("num_vehicles", 1), errors="coerce").fillna(1).astype(int)
        return df


# ── Filtering helper ──────────────────────────────────────────────────────────
def apply_filters(df: pd.DataFrame, cities, severities, date_range) -> pd.DataFrame:
    mask = pd.Series([True] * len(df))
    if cities:
        mask &= df["city"].isin(cities)
    if severities:
        mask &= df["severity"].isin(severities)
    if date_range and len(date_range) == 2:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        mask &= (df["date"] >= start) & (df["date"] <= end)
    return df[mask].copy()


# ── Main app ──────────────────────────────────────────────────────────────────
def main():
    # Header
    st.markdown("""
    <div style='text-align:center; padding: 10px 0 20px 0;'>
        <h1 style='font-size:2.5rem; color:#e74c3c;'>🚦 Traffic Accident Analysis Dashboard</h1>
        <p style='color:#666; font-size:1rem;'></p>
    </div>
    """, unsafe_allow_html=True)

    df_raw = load_data()

    # ── Sidebar filters ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("##  Filters")
        st.markdown("---")

        all_cities = sorted(df_raw["city"].dropna().unique())
        selected_cities = st.multiselect(
            " City", all_cities,
            default=all_cities[:5],
            help="Select one or more cities"
        )

        all_severities = sorted(df_raw["severity"].dropna().unique())
        selected_severities = st.multiselect(
            " Severity", all_severities,
            default=all_severities,
        )

        min_date = df_raw["date"].min().date()
        max_date = df_raw["date"].max().date()
        date_range = st.date_input(
            " Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        st.markdown("---")
        st.markdown("###  Dataset Info")
        st.info(f"**Total records:** {len(df_raw):,}")
        st.info(f"**Cities:** {df_raw['city'].nunique()}")
        st.info(f"**Date range:** {min_date} → {max_date}")

        st.markdown("---")
        st.markdown(
            "<small style='color:#aaa;'>Built with PySpark + Streamlit</small>",
            unsafe_allow_html=True
        )

    # Apply filters
    df = apply_filters(df_raw, selected_cities, selected_severities, date_range)

    if df.empty:
        st.warning("No data matches the selected filters. Please adjust your selections.")
        return

    # ── Section 1: Overview Metrics ───────────────────────────────────────────
    st.markdown('<div class="section-title"> Overview Metrics</div>', unsafe_allow_html=True)

    total = len(df)
    dangerous_city = df["city"].value_counts().idxmax() if total > 0 else "N/A"
    dangerous_city_count = df["city"].value_counts().max() if total > 0 else 0
    common_weather = df["weather_condition"].value_counts().idxmax() if "weather_condition" in df.columns else "N/A"
    high_severity = len(df[df["severity"] == "High"])
    high_pct = round(high_severity / total * 100, 1) if total > 0 else 0
    peak_hour_val = int(df["hour"].value_counts().idxmax()) if "hour" in df.columns and total > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    metrics = [
        (col1, "", f"{total:,}", "Total Accidents"),
        (col2, "", dangerous_city, f"Most Dangerous City ({dangerous_city_count:,} accidents)"),
        (col3, "", common_weather, "Most Common Weather"),
        (col4, "", f"{high_pct}%", "High Severity Rate"),
        (col5, "", f"{peak_hour_val:02d}:00", "Peak Accident Hour"),
    ]
    for col, icon, value, label in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:1.8rem;">{icon}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section 2: Charts ─────────────────────────────────────────────────────
    st.markdown('<div class="section-title"> Visual Analytics</div>', unsafe_allow_html=True)

    # Row 1: City bar + Severity pie
    col_a, col_b = st.columns([3, 2])

    with col_a:
        city_counts = df["city"].value_counts().reset_index()
        city_counts.columns = ["city", "accident_count"]
        fig_city = px.bar(
            city_counts.head(12), x="city", y="accident_count",
            title="Accidents by City",
            color="accident_count", color_continuous_scale="Reds",
            text="accident_count",
            labels={"accident_count": "Accidents", "city": "City"},
        )
        fig_city.update_traces(textposition="outside")
        fig_city.update_layout(
            coloraxis_showscale=False, xaxis_tickangle=-40,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=50, b=60),
        )
        st.plotly_chart(fig_city, use_container_width=True)

    with col_b:
        severity_counts = df["severity"].value_counts().reset_index()
        severity_counts.columns = ["severity", "count"]
        color_map = {"Low": "#2ECC71", "Medium": "#F39C12", "High": "#E74C3C", "Unknown": "#95A5A6"}
        fig_sev = px.pie(
            severity_counts, values="count", names="severity",
            title="Severity Distribution",
            color="severity", color_discrete_map=color_map,
            hole=0.42,
        )
        fig_sev.update_traces(textinfo="percent+label", pull=[0.03] * len(severity_counts))
        fig_sev.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=50))
        st.plotly_chart(fig_sev, use_container_width=True)

    # Row 2: Monthly trend
    monthly = df.groupby("month_year").size().reset_index(name="accident_count")
    monthly["month_year"] = pd.to_datetime(monthly["month_year"])
    monthly = monthly.sort_values("month_year")

    fig_trend = px.line(
        monthly, x="month_year", y="accident_count",
        title="Monthly Accident Trend",
        markers=True,
        labels={"accident_count": "Accidents", "month_year": "Month"},
        color_discrete_sequence=["#E74C3C"],
    )
    fig_trend.update_traces(line_width=2.5, fill="tozeroy", fillcolor="rgba(231,76,60,0.1)")
    fig_trend.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis_tickangle=-30, margin=dict(t=50),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # Row 3: Hourly distribution + Weather
    col_c, col_d = st.columns(2)

    with col_c:
        hourly = df.groupby("hour").size().reset_index(name="accident_count")
        peak_hours = [7, 8, 17, 18, 19]
        hourly["color"] = hourly["hour"].apply(lambda h: "#E74C3C" if h in peak_hours else "#3498DB")
        fig_hour = px.bar(
            hourly, x="hour", y="accident_count",
            title="Accidents by Hour of Day",
            labels={"accident_count": "Accidents", "hour": "Hour"},
            color="color", color_discrete_map="identity",
            text="accident_count",
        )
        fig_hour.update_traces(textposition="outside", textfont_size=9)
        fig_hour.update_layout(
            showlegend=False, xaxis=dict(tickmode="linear", dtick=1),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=50),
        )
        st.plotly_chart(fig_hour, use_container_width=True)

    with col_d:
        weather = df["weather_condition"].value_counts().reset_index()
        weather.columns = ["weather_condition", "count"]
        fig_weather = px.bar(
            weather.sort_values("count"), x="count", y="weather_condition",
            orientation="h",
            title="Accidents by Weather Condition",
            color="count", color_continuous_scale="Blues",
            labels={"count": "Accidents", "weather_condition": "Weather"},
            text="count",
        )
        fig_weather.update_traces(textposition="outside")
        fig_weather.update_layout(
            coloraxis_showscale=False,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=50),
        )
        st.plotly_chart(fig_weather, use_container_width=True)

    # Row 4: Road condition + Day/Night
    col_e, col_f = st.columns(2)

    with col_e:
        road = df["road_condition"].value_counts().reset_index()
        road.columns = ["road_condition", "count"]
        fig_road = px.bar(
            road, x="road_condition", y="count",
            title="Accidents by Road Condition",
            color="count", color_continuous_scale="Oranges",
            labels={"count": "Accidents", "road_condition": "Road Condition"},
            text="count",
        )
        fig_road.update_traces(textposition="outside")
        fig_road.update_layout(
            coloraxis_showscale=False, xaxis_tickangle=-20,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=50),
        )
        st.plotly_chart(fig_road, use_container_width=True)

    with col_f:
        df["period"] = df["hour"].apply(lambda h: "Day (6AM–6PM)" if 6 <= h < 18 else "Night (6PM–6AM)")
        dn = df["period"].value_counts().reset_index()
        dn.columns = ["period", "count"]
        fig_dn = px.pie(
            dn, values="count", names="period",
            title="Day vs Night Accidents",
            color="period",
            color_discrete_map={"Day (6AM–6PM)": "#F39C12", "Night (6PM–6AM)": "#2C3E50"},
            hole=0.4,
        )
        fig_dn.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=50))
        st.plotly_chart(fig_dn, use_container_width=True)

    # ── Section 3: Hotspot Map ────────────────────────────────────────────────
    if "latitude" in df.columns and "longitude" in df.columns:
        st.markdown('<div class="section-title"> Accident Hotspot Map</div>', unsafe_allow_html=True)
        map_df = df.dropna(subset=["latitude", "longitude"]).sample(min(2000, len(df)), random_state=42)
        sev_color = {"Low": "green", "Medium": "orange", "High": "red"}
        fig_map = px.scatter_mapbox(
            map_df, lat="latitude", lon="longitude",
            color="severity", color_discrete_map=sev_color,
            hover_data=["city", "date", "weather_condition"],
            zoom=3, opacity=0.55,
            title="Accident Hotspots",
            mapbox_style="carto-positron",
        )
        fig_map.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", height=480,
            margin=dict(t=40, b=10),
        )
        st.plotly_chart(fig_map, use_container_width=True)

    # ── Section 4: Insights ───────────────────────────────────────────────────
    st.markdown('<div class="section-title"> Key Insights</div>', unsafe_allow_html=True)

    top5_cities = df["city"].value_counts().head(5).index.tolist()
    most_dangerous = top5_cities[0] if top5_cities else "N/A"
    high_weather = df["weather_condition"].value_counts().idxmax() if "weather_condition" in df else "N/A"
    peak_h = int(df["hour"].value_counts().idxmax()) if total > 0 else 0
    night_pct = round(len(df[df["period"] == "Night (6PM–6AM)"]) / total * 100, 1) if total > 0 else 0
    high_road = df["road_condition"].value_counts().idxmax() if "road_condition" in df else "N/A"
    year_counts = df.groupby("year").size()
    trend = "increasing" if (len(year_counts) >= 2 and year_counts.iloc[-1] > year_counts.iloc[0]) else "stable or decreasing"

    insights = [
        f" <b>{most_dangerous}</b> is the most accident-prone city in the filtered dataset.",
        f" <b>{high_pct}%</b> of all accidents are classified as <b>High Severity</b> — requiring urgent intervention.",
        f" Most accidents ({df['weather_condition'].value_counts().iloc[0]:,}) occur under <b>{high_weather}</b> weather conditions.",
        f" The peak accident hour is <b>{peak_h:02d}:00</b>, likely corresponding to rush-hour traffic.",
        f" <b>{night_pct}%</b> of accidents happen at night, highlighting visibility and fatigue risks.",
        f" <b>{high_road}</b> road conditions are associated with the most accidents.",
        f" Accident frequency is <b>{trend}</b> over the analyzed period.",
        f" Average vehicles involved per accident: <b>{df['num_vehicles'].mean():.1f}</b>.",
    ]

    col_ins1, col_ins2 = st.columns(2)
    for i, insight in enumerate(insights):
        col = col_ins1 if i % 2 == 0 else col_ins2
        with col:
            st.markdown(
                f'<div class="insight-card">{insight}</div>',
                unsafe_allow_html=True
            )

    # ── Section 5: Raw Data Explorer ─────────────────────────────────────────
    with st.expander(" Explore Raw Data"):
        st.markdown(f"Showing **{len(df):,}** records matching your filters.")
        cols_to_show = [c for c in ["city", "date", "time", "severity", "weather_condition",
                                     "road_condition", "num_vehicles", "hour"] if c in df.columns]
        st.dataframe(df[cols_to_show].reset_index(drop=True), use_container_width=True, height=350)
        csv = df[cols_to_show].to_csv(index=False)
        st.download_button("⬇ Download Filtered Data", data=csv,
                           file_name="filtered_accidents.csv", mime="text/csv")

    # Footer
    st.markdown("""
    <hr style='margin-top:2rem;'>
    <div style='text-align:center; color:#aaa; font-size:0.85rem; padding-bottom:1rem;'>
        
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
