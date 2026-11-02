# 🏏 CricPulse-Engine — High-Performance IPL Analytics API

> **A production-ready analytical engine and REST API for historical Indian Premier League (IPL) data, powered by DuckDB, Apache Parquet, and FastAPI with defense-in-depth security middlewares.**

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![DuckDB](https://img.shields.io/badge/DuckDB-OLAP_Engine-FFF000.svg?logo=duckdb&logoColor=black)](https://duckdb.org)
[![Apache Parquet](https://img.shields.io/badge/Apache_Parquet-Columnar_Storage-50B748.svg)](https://parquet.apache.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌟 Architecture & Data Flow

CricPulse-Engine implements a modern **Medallion Data Architecture** (Bronze/Silver) designed for high-throughput OLAP analytics while remaining strictly defensive under memory-constrained environments (such as Render's 512MB RAM free tier).

```
 [ Cricsheet JSON Raw Data (1,243 Matches) ]
                     │
                     ▼
       ┌───────────────────────────┐
       │     ETL Data Pipeline     │
       │  (extract.py, transform)  │
       └─────────────┬─────────────┘
                     ▼
       ┌───────────────────────────┐
       │  Medallion DuckDB Storage │
       │  ├── Bronze: raw_*        │
       │  └── Silver: clean_*      │
       └─────────────┬─────────────┘
                     ▼
       ┌───────────────────────────┐
       │ Pydantic Validation Layer │
       │  (Schemas & Type Safety)  │
       └─────────────┬─────────────┘
                     ▼
       ┌───────────────────────────┐
       │   FastAPI Middleware Stack│
       │  ├── Sliding Rate Limiter │
       │  ├── OWASP Sec Headers    │
       │  ├── Latency (X-Process)  │
       │  └── Trace (X-Request-ID) │
       └─────────────┬─────────────┘
                     ▼
          [ REST API Clients / UI ]
```

---

## 🚀 Key Features

* **Complete Historical Dataset:** Ingests and cleans **1,243 IPL matches (2008–2024)** and **295,732 ball-by-ball deliveries**.
* **Real-World Data Engineering:**
  * Imputed 51 missing match cities from venue data with 100% geographic coverage (Dubai & Sharjah).
  * Harmonized historical franchise rebrandings (e.g., Delhi Daredevils $\rightarrow$ Delhi Capitals).
  * Resolved Super Over ties and boundary count outcomes.
  * Extracted 14,705 total dismissals, separating true bowler wickets from run-outs and retired hurts.
* **Columnar OLAP Acceleration:** Leverages **DuckDB and Parquet** for analytical aggregations (`SUM`, `FILTER`, `GROUP BY`), executing complex queries in under 30ms.
* **Production Middleware Stack:**
  * **Sliding-Window Rate Limiter:** Enforces 60 requests/minute per IP with automatic memory cleanup to protect RAM limits.
  * **OWASP Hardening:** Injects `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and `X-XSS-Protection`.
  * **Latency Profiling:** High-resolution `X-Process-Time` timer stamped on every response.
  * **Correlation Tracing:** `X-Request-ID` UUID propagation across logs and responses.
  * **CORS Support:** Configured for cross-origin access by external frontend applications.

---

## 🧭 API Endpoints

Interactive Swagger UI documentation is available at `http://localhost:8000/docs`.

### 1. Matches (`/api/v1/matches`)
* `GET /api/v1/matches` — Paginated match summaries with filtering by season, team, venue, and city.
* `GET /api/v1/matches/{match_id}` — Full scorecard metadata, toss decision, and player of the match.
* `GET /api/v1/matches/seasons` — Distinct sorted list of all IPL seasons.

### 2. Players (`/api/v1/players`)
* `GET /api/v1/players` — Searchable player directory with pagination.
* `GET /api/v1/players/{player_id}` — Complete career profile computing batting aggregates (runs, strike rate, 4s, 6s) and bowling aggregates (wickets, overs, economy rate) live.

### 3. Analytics (`/api/v1/analytics`)
* `GET /api/v1/analytics/head-to-head?team1=...&team2=...` — Historical rivalry statistics and win percentages.
* `GET /api/v1/analytics/toss-impact` — Toss decision trends and winning probabilities across 1,243 matches.
* `GET /api/v1/analytics/venue?venue=...` — Stadium scoring records, average 1st-innings totals, and match counts.
* `GET /api/v1/analytics/orange-cap?season=...` — Top run-scorers leaderboard.
* `GET /api/v1/analytics/purple-cap?season=...` — Top wicket-takers leaderboard (adhering to official bowler wicket rules).

### 4. Health & System
* `GET /health` — Liveness probe returning server status and timestamp.
* `GET /db-health` — Real-time DuckDB connectivity check.

---

## 🛠️ Quickstart

### 1. Clone the repository
```bash
git clone https://github.com/ShaikhHamza104/CricPulse-Engine.git
cd CricPulse-Engine
```

### 2. Set up the environment
```bash
# Using uv (recommended)
uv sync

# Or using standard venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 3. Run the development server
```bash
uv run uvicorn src.ipl_analytics.main:app --reload --host 0.0.0.0 --port 8000
```

Visit **`http://localhost:8000/docs`** for interactive testing.

---

## 👨‍💻 Author

**Mohd Hamza Shaikh**
* GitHub: [@ShaikhHamza104](https://github.com/ShaikhHamza104)

---

## 📄 License
This project is licensed under the MIT License. Cricket data sourced from [Cricsheet](https://cricsheet.org/) under the Open Database License (ODbL).
