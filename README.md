# 🚦 Traffic Accident Data Analysis using Apache Spark

An end-to-end Big Data analytics system that processes traffic accident data with **Apache Spark**, uncovers patterns and hotspots, and presents results through an interactive **Streamlit** dashboard.

---


## ✨ Features

- **PySpark-powered** data ingestion, cleaning, and analysis at scale
- **Interactive dashboard** with real-time sidebar filters (city, severity, date range)
- **7 chart types**: bar, pie, donut, line trend, hourly heatmap, weather breakdown, road condition
- **Accident hotspot map** using Plotly Mapbox
- **Spark SQL** queries for advanced cross-dimensional analysis
- **Downloadable filtered dataset** from the dashboard
- **Pandas fallback** so the app runs on Streamlit Cloud without a full Spark install
- **Docker support** for containerized deployment

---

## 🏗️ Project Structure

```
traffic-accident-analysis-spark/
│
├── data/
│   └── accidents.csv            # 7,500-row synthetic dataset
│
├── notebooks/
│   └── eda.ipynb                # Exploratory Data Analysis notebook
│
├── src/
│   ├── data_loader.py           # SparkSession init + CSV loading
│   ├── data_cleaning.py         # Null handling, normalization, datetime parsing
│   ├── analysis.py              # Spark transformations & aggregations
│   ├── visualization.py         # Matplotlib/Seaborn static + Plotly interactive charts
│   └── app.py                   # Streamlit dashboard (main entry point)
│
├── outputs/
│   ├── charts/                  # Saved PNG chart images
│   └── processed_data/          # Exported cleaned CSVs
│
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Data Processing | Apache Spark (PySpark) |
| Data Wrangling | Pandas |
| Visualization | Plotly, Matplotlib, Seaborn |
| Frontend | Streamlit |
| Deployment | Streamlit Cloud |
| Version Control | GitHub |
| Containerization | Docker |

---

## 📊 Dataset

The included `data/accidents.csv` is a synthetic dataset with **7,500 rows** across 2021–2023.

| Column | Description |
|---|---|
| `id` | Unique accident ID |
| `city` | City where accident occurred |
| `date` | Date (YYYY-MM-DD) |
| `time` | Time (HH:MM) |
| `severity` | Low / Medium / High |
| `weather_condition` | Clear / Rain / Fog / Snow / Cloudy / Hail / Windy |
| `road_condition` | Dry / Wet / Icy / Slippery / Under Construction |
| `num_vehicles` | Number of vehicles involved |
| `latitude` / `longitude` | Approximate coordinates |

---

## 🚀 Run Locally

### Prerequisites
- Python 3.10+
- Java 17 (recommended for Spark)

### Install & Run

```bash
# 1. Clone the repo
git clone https://github.com/MaitreyeeDahane/traffic-accident-analysis-spark.git
cd traffic-accident-analysis-spark

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the dashboard
streamlit run src/app.py
```

The app opens at **http://localhost:8501**

---

## 🐳 Docker

```bash
# Build image
docker build -t traffic-accident-dashboard .

# Run container
docker run -p 8501:8501 traffic-accident-dashboard
```

---


## 📐 Architecture

```
CSV Dataset
    │
    ▼
PySpark (data_loader.py)
    │  Load + infer schema
    ▼
Cleaning Pipeline (data_cleaning.py)
    │  Nulls · Duplicates · Normalization · DateTime parsing
    ▼
Analysis Engine (analysis.py)
    │  groupBy · filter · aggregation · Spark SQL
    ▼
Visualization (visualization.py)
    │  Static PNG charts + Plotly interactive figures
    ▼
Streamlit Dashboard (app.py)
    │  Filters → Dynamic charts → Insights → Map
    ▼
Streamlit Cloud (live URL)
```

---



## 📄 License

MIT License — free to use, modify, and distribute.
