# 🏏 IPL Analytics Engine — Database Schema & Data Dictionary

> **Dataset Source:** [Cricsheet](https://cricsheet.org/) (Match JSON v1.3.0)  
> **Licensing:** [Open Data Commons Open Database License (ODbL 1.0)](https://opendatacommons.org/licenses/odbl/1-0/)  
> **Official Competition Portal:** [IPL Official Match Stats](https://www.iplt20.com/stats/)  
> **Architecture Pattern:** Medallion Architecture (Bronze `raw_*` & Silver `clean_*`)  
> **Storage Layer:** Columnar Parquet (`data/processed/*.parquet`) & Embedded DuckDB (`data/processed/ipl.duckdb`)  

---

## 🏛️ Database Architecture Overview

The database implements a **Medallion Architecture**:

1. **Bronze Layer (`raw_*`)**: Permanent historical audit trail of the original raw Cricsheet data as parsed.
   * `raw_matches` (1,243 rows)
   * `raw_deliveries` (295,732 rows)
   * `raw_players` (809 rows)
2. **Silver Layer (`clean_*` / standard aliases `matches`, `deliveries`, `players`)**: Production-ready, validated, downcast, and standardized tables powering the **FastAPI endpoints**.
   * `clean_matches` (1,243 rows)
   * `clean_deliveries` (295,732 rows)
   * `clean_players` (809 rows)

---

## 1. Clean Matches Table (`clean_matches` / `matches`)
* **Total Records:** 1,243 fixtures (IPL 2008 – present)
* **Granularity:** One record per match

| Column Name | Data Type | Nullable | Description | Example / Allowed Values |
| :--- | :--- | :--- | :--- | :--- |
| `match_id` | `INTEGER` (`int32`) | No | Unique match identifier assigned by Cricsheet | `1082591`, `335982` |
| `season` | `INTEGER` (`int32`) | No | Normalized 4-digit IPL season year | `2008`, `2017`, `2024` |
| `date` | `TIMESTAMP` (`datetime64[us]`) | No | Official calendar date of the match | `2017-04-05` |
| `team1` | `VARCHAR` | No | First listed competing team (lowercased, harmonized) | `sunrisers hyderabad` |
| `team2` | `VARCHAR` | No | Second listed competing team (lowercased, harmonized) | `royal challengers bengaluru` |
| `venue` | `VARCHAR` | No | Official stadium name where the match was played | `rajiv gandhi international stadium` |
| `city` | `VARCHAR` | No (0 nulls) | Host city (imputed via stadium venue mapping) | `hyderabad`, `sharjah`, `dubai` |
| `winner` | `VARCHAR` | Yes (9 true nulls) | Winning team (`null` indicates rain washouts/abandoned) | `sunrisers hyderabad` |
| `toss_winner` | `VARCHAR` | No | Team that won the pre-match coin toss | `royal challengers bengaluru` |
| `toss_decision` | `VARCHAR` | No | Toss winner's decision (`bat` or `field`) | `field` |
| `year` | `INTEGER` (`int32`) | No | Extracted calendar year from date | `2017` |
| `month` | `INTEGER` (`int32`) | No | Extracted calendar month from date | `4` |
| `outcome_status` | `VARCHAR` | No | Classification (`completed` vs `no_result`) | `completed`, `no_result` |

---

## 2. Clean Deliveries Table (`clean_deliveries` / `deliveries`)
* **Total Records:** 295,732 ball-by-ball deliveries
* **Granularity:** One record per ball delivered

| Column Name | Data Type | Nullable | Description | Example / Allowed Values |
| :--- | :--- | :--- | :--- | :--- |
| `match_id` | `INTEGER` (`int32`) | No | Foreign key referencing `matches.match_id` | `1082591` |
| `innings` | `TINYINT` (`int8`) | No | Innings number (1 = 1st, 2 = 2nd, 3/4 = Super Overs) | `1`, `2` |
| `batting_team` | `VARCHAR` | No | Team batting during this delivery (harmonized) | `sunrisers hyderabad` |
| `over_number` | `TINYINT` (`int8`) | No | Over number (0-indexed: 0 = 1st over, 19 = 20th over) | `0` to `19` |
| `ball_number` | `TINYINT` (`int8`) | No | Ball sequence within the over | `1` to `11` |
| `batter` | `VARCHAR` | No | Striker facing the ball (lowercased) | `da warner`, `v kohli` |
| `bowler` | `VARCHAR` | No | Bowler delivering the ball (lowercased) | `b kumar`, `jj bumrah` |
| `non_striker` | `VARCHAR` | No | Non-striking runner at bowler's end | `s dhawan` |
| `batter_runs` | `TINYINT` (`int8`) | No | Runs scored off the bat | `0`, `1`, `2`, `3`, `4`, `6` |
| `extra_runs` | `TINYINT` (`int8`) | No | Total penalty/extra runs on the ball | `0`, `1`, `5` |
| `total_runs` | `INTEGER` (`int32`) | No | Total delivery runs (`batter_runs + extra_runs`) | `0` to `7` |
| `wides` | `TINYINT` (`int8`) | No | Wide penalty runs | `0`, `1`, `2` |
| `noballs` | `TINYINT` (`int8`) | No | No-ball penalty runs | `0`, `1` |
| `byes` | `TINYINT` (`int8`) | No | Bye runs scored by batters | `0` to `4` |
| `legbyes` | `TINYINT` (`int8`) | No | Leg-bye runs scored off body/pads | `0` to `4` |
| `is_super_over` | `TINYINT` (`int8`) | No | 1 if ball was in Super Over, 0 otherwise | `0`, `1` |
| `is_boundary` | `BOOLEAN` | No | True boundary flag (4 or 6 off the bat) | `true`, `false` |

---

## 3. Clean Players Table (`clean_players` / `players`)
* **Total Records:** 809 registered players
* **Granularity:** One record per unique player identity

| Column Name | Data Type | Nullable | Description | Example / Allowed Values |
| :--- | :--- | :--- | :--- | :--- |
| `player_id` | `VARCHAR` | No | Cricsheet unique hash ID | `b0512837`, `63c0a466` |
| `player_name` | `VARCHAR` | No | Normalized player name (lowercased) | `v kohli`, `ms dhoni` |
