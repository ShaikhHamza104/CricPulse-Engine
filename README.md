# 🏏 CricPulse-Engine — High-Performance IPL Analytics API

> **A production-ready analytical engine and REST API for historical Indian Premier League (IPL) data, powered by DuckDB, Apache Parquet, and FastAPI with defense-in-depth security middlewares and 92 automated tests.**
> 
> 🌐 **Live Production API:** [https://cricpulse-engine.onrender.com](https://cricpulse-engine.onrender.com) | 📚 **Interactive Swagger Docs:** [https://cricpulse-engine.onrender.com/docs](https://cricpulse-engine.onrender.com/docs)

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![DuckDB](https://img.shields.io/badge/DuckDB-OLAP_Engine-FFF000.svg?logo=duckdb&logoColor=black)](https://duckdb.org)
[![Tests](https://img.shields.io/badge/Tests-92%20Passed-brightgreen.svg?logo=pytest&logoColor=white)](tests/)
[![Flake8](https://img.shields.io/badge/Flake8-0%20Issues-brightgreen.svg)](https://flake8.pycqa.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌟 Architecture & Data Flow

CricPulse-Engine implements a modern **Medallion Data Architecture** (Bronze/Silver/Gold) designed for high-throughput OLAP analytics while remaining strictly defensive under memory-constrained environments (such as Render's 512MB RAM tier).

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
* **Real-World Cricket Domain Engineering:**
  * **Overs Decimal Notation:** Strictly formats overs as `(balls // 6) + ((balls % 6) / 10.0)` so the decimal part is always `0` to `5` (e.g. `605.1` overs for Bumrah).
  * **Orange Cap Accuracy:** Wides are excluded from balls faced; Super Overs excluded from player run totals.
  * **Purple Cap Rules:** Super Overs excluded; wickets counted only for bowler-credited dismissals.
  * **Franchise Acronym Resolution:** Queries accept both full names and common abbreviations (`CSK`, `RCB`, `MI`, `KKR`, `SRH`, `DC`, etc.).
  * **Venue Par Scores:** Averages computed strictly on completed/bowled-out innings ($\ge 19$ overs or 10 wickets) to prevent rain-shortened matches from corrupting stadium par.
* **Columnar OLAP Acceleration:** Leverages **DuckDB and Parquet** for analytical aggregations (`SUM`, `FILTER`, `GROUP BY`), executing complex queries in under 30ms.
* **Production Middleware Stack:**
  * **Sliding-Window Rate Limiter:** Enforces 60 requests/minute per IP with automatic memory cleanup to protect RAM limits.
  * **Reverse Proxy Support:** Detects real client IP via `X-Forwarded-For` with automatic fallback.
  * **OWASP Hardening:** Injects `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and `X-XSS-Protection`.
  * **Latency Profiling:** High-resolution `X-Process-Time` timer stamped on every response.
  * **Correlation Tracing:** `X-Request-ID` UUID propagation across logs and responses.
  * **Leak-Free Connections:** Generator-based DuckDB dependencies guarantee connection closure.

---

## 🧭 API Endpoints Catalog

Interactive Swagger UI documentation is available live at:
👉 **[https://cricpulse-engine.onrender.com/docs](https://cricpulse-engine.onrender.com/docs)** *(or locally at `http://localhost:8000/docs`)*.

### 1. Matches (`/api/v1/matches`)
* `GET /api/v1/matches` — Paginated match summaries with filtering by season, team alias, venue, and city.
* `GET /api/v1/matches/{match_id}` — Full scorecard metadata, toss decision, and player of the match.
* `GET /api/v1/matches/seasons` — Distinct sorted list of all IPL seasons (2008–2024).

### 2. Players (`/api/v1/players`)
* `GET /api/v1/players` — Searchable player directory with pagination (`?search=Kohli`).
* `GET /api/v1/players/{player_id}` — Complete career profile computing batting aggregates (runs, balls, strike rate, 4s, 6s, average) and bowling aggregates (wickets, overs, economy rate) live.

### 3. Analytics (`/api/v1/analytics`)
* `GET /api/v1/analytics/head-to-head?team1=CSK&team2=RCB` — Historical rivalry statistics and win percentages.
* `GET /api/v1/analytics/toss-impact` — Toss decision trends and winning probabilities across 1,243 matches.
* `GET /api/v1/analytics/venue?venue=Wankhede` — Stadium scoring records, average 1st-innings totals, and match counts.
* `GET /api/v1/analytics/orange-cap?season=2024` — Top run-scorers leaderboard.
* `GET /api/v1/analytics/purple-cap?season=2024` — Top wicket-takers leaderboard adhering to official bowler wicket rules.

### 4. Health & Monitoring
* `GET /health` — Liveness probe returning server status, environment, and latency headers.
* `GET /db-health` — Real-time DuckDB active connectivity check.

---

## 🧪 Testing & Code Quality

The repository is protected by a 3-layer automated test suite and strict linting:

```bash
# Run all 92 automated tests
uv run pytest tests/ -v

# Run Flake8 linter (0 issues)
uv run --with flake8 flake8 --count

# Run Mypy static type checker (0 errors across 45 files)
uv run mypy src tests

# Verify Ruff code formatting
uv run ruff format --check .
```

---

## 🛠️ Quickstart

### 1. Clone the repository
```bash
git clone https://github.com/ShaikhHamza104/CricPulse-Engine.git
cd CricPulse-Engine
```

### 2. Set up environment & install dependencies
```bash
# Using uv (fastest)
uv sync

# Or using standard python venv
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

## 🐳 Docker Deployment

A production-grade multi-stage Dockerfile is included:

```bash
# Build the minimal production container
docker build -t ipl-analytics-api .

# Run the container
docker run -d -p 8000:8000 --name ipl-api ipl-analytics-api

# Check container health
curl http://localhost:8000/health
```

---

## 🔄 CI/CD & Git Conventions

Every pull request and push to `main` is validated by [GitHub Actions](.github/workflows/ci.yml) against:
- **Conventional Commits**: Enforces standardized commit messages (`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`).
- **Issue Linking**: Automatically associates PRs using `Fixes #12`, `Resolves #34`, etc.
- **Flake8 & Mypy**: Zero-tolerance code quality gates.
- **Cricket Domain Invariants**: Live regression tests against DuckDB.

---

## 👨‍💻 Author

**Mohd Hamza Shaikh**
* GitHub: [@ShaikhHamza104](https://github.com/ShaikhHamza104)

---

## 📄 License
This project is licensed under the MIT License. Cricket data sourced from [Cricsheet](https://cricsheet.org/) under the Open Database License (ODbL).
