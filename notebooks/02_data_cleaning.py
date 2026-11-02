import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    import marimo as mo
    import numpy as np
    import pandas as pd

    return Path, mo, np, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 🧹 IPL Analytics Platform — Data Cleaning & Standardization

    > **Author:** Mohd Hamza Shaikh
    > **Project:** IPL REST API & Advanced Cricket Analytics Engine
    > **Stage:** Data Cleaning, Standardization, and Missing-Value Imputation

    ---

    ### 🌐 Data Provenance & Verified External Resources

    All underlying ball-by-ball match data was ingested and normalized from the open-source **Cricsheet** initiative.

    * **Data Source Provider:** [Cricsheet](https://cricsheet.org/) *(The de facto standard open database for international & franchise cricket)*
    * **Data Specification:** [Cricsheet Match JSON Format v1.3.0](https://cricsheet.org/format/json/)
    * **Raw Archive Download:** [Cricsheet IPL Matches Package](https://cricsheet.org/downloads/ipl_json.zip)
    * **Data Licensing:** [Open Data Commons Open Database License (ODbL 1.0)](https://opendatacommons.org/licenses/odbl/1-0/)
    * **Official League Source:** [IPL Official Website & Match Stats (iplt20.com)](https://www.iplt20.com/stats/)
    * **Secondary Validation Portal:** [ESPN Cricinfo IPL Series Archive](https://www.espncricinfo.com/series/indian-premier-league)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    ## 📚 Data Dictionary & Schema Specification

    ### 1. `clean_matches.parquet` (1,243 Matches)
    *Granularity: One record per IPL fixture from 2008 to present.*

    | Column | Type | Nullable | Description | Example / Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `match_id` | `int32` | No | Unique identifier for each match assigned by Cricsheet. | `1082591` |
    | `season` | `int32` | No | 4-digit normalized IPL season year. | `2017`, `2023` |
    | `date` | `datetime64[us]` | No | Primary calendar date on which the match was played. | `2017-04-05` |
    | `team1` | `string` | No | First listed competing team (lowercased). | `sunrisers hyderabad` |
    | `team2` | `string` | No | Second listed competing team (lowercased). | `royal challengers bangalore` |
    | `venue` | `string` | No | Official stadium name where the match was hosted. | `rajiv gandhi international stadium` |
    | `city` | `string` | Yes (~51 nulls) | Host city. Imputable using stadium venue mapping. | `hyderabad`, `sharjah`, `dubai` |
    | `winner` | `string` | Yes (25 nulls) | Winning team. `null` represents abandoned / no-result games. | `sunrisers hyderabad` |
    | `toss_winner` | `string` | No | Team that won the pre-match coin toss. | `royal challengers bangalore` |
    | `toss_decision` | `string` | No | Strategic decision by toss winner (`bat` or `field`). | `field` |
    | `year` | `int32` | No | Extracted match calendar year. | `2017` |
    | `month` | `int32` | No | Extracted match calendar month (typically April/May). | `4`, `5` |

    ---

    ### 2. `clean_deliveries.parquet` (295,732 Balls)
    *Granularity: One record per individual ball delivered.*

    | Column | Type | Nullable | Description | Example / Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `match_id` | `int32` | No | Foreign key referencing `clean_matches.match_id`. | `1082591` |
    | `innings` | `int8` | No | Innings number (1 = 1st, 2 = 2nd, 3/4 = Super Overs). | `1`, `2` |
    | `batting_team` | `string` | No | Name of team batting during this delivery. | `sunrisers hyderabad` |
    | `over_number` | `int8` | No | Over number (0-indexed: 0 = 1st over, 19 = 20th over). | `0` to `19` |
    | `ball_number` | `int8` | No | Sequence of ball delivered within the over. | `1` to `11` (with extras) |
    | `batter` | `string` | No | Striker facing the delivery (lowercased). | `da warner`, `v kohli` |
    | `bowler` | `string` | No | Bowler delivering the ball (lowercased). | `b kumar`, `jj bumrah` |
    | `non_striker` | `string` | No | Batter positioned at the bowler's non-striker end. | `s dhavan` |
    | `batter_runs` | `int8` | No | Runs credited off the bat (0, 1, 2, 3, 4, 6). | `4` |
    | `extra_runs` | `int8` | No | Total penalty/extra runs conceded on the ball. | `1` |
    | `total_runs` | `int32` | No | Total runs scored (`batter_runs + extra_runs`). | `5` |
    | `wides` | `int8` | No | Runs from wide delivery (0 if not wide). | `1` |
    | `noballs` | `int8` | No | Runs conceded from front-foot/height no-ball. | `1` |
    | `byes` | `int8` | No | Bye runs scored by batters. | `0` |
    | `legbyes` | `int8` | No | Leg-bye runs scored off batter pads. | `0` |
    | `is_super_over` | `int8` | No | Indicator whether ball was bowled in a Super Over (1 = yes, 0 = no). | `0` or `1` |
    | `is_boundary` | `bool` | No | Boolean flag indicating a true boundary 4 or 6. | `True` / `False` |
    | `is_wicket` | `bool` | No | Flag indicating if a dismissal occurred on this delivery. | `True` / `False` |
    | `dismissal_kind` | `string` | Yes | Method of dismissal (caught, bowled, lbw, run out, etc.). | `caught`, `bowled`, `lbw` |
    | `player_dismissed` | `string` | Yes | Name of the batter dismissed on this delivery. | `da warner`, `v kohli` |

    ---

    ### 3. `clean_players.parquet` (809 Players)
    *Granularity: One record per registered IPL player.*

    | Column | Type | Nullable | Description | Example / Notes |
    | :--- | :--- | :--- | :--- | :--- |
    | `player_id` | `string` | No | Cricsheet / People Registry unique hash ID. | `b0512837` |
    | `player_name` | `string` | No | Normalized player full name (lowercased). | `v kohli`, `ms dhoni` |
    """)
    return


@app.cell
def _(Path):
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

    MATCHES_FILE = PROCESSED_DIR / "clean_matches.parquet"
    DELIVERIES_FILE = PROCESSED_DIR / "clean_deliveries.parquet"
    PLAYERS_FILE = PROCESSED_DIR / "clean_players.parquet"
    return DELIVERIES_FILE, MATCHES_FILE, PLAYERS_FILE, PROCESSED_DIR


@app.cell
def _(DELIVERIES_FILE, MATCHES_FILE, PLAYERS_FILE, pd):
    matches_df = pd.read_parquet(MATCHES_FILE)
    deliveries_df = pd.read_parquet(DELIVERIES_FILE)
    players_df = pd.read_parquet(PLAYERS_FILE)
    return deliveries_df, matches_df, players_df


@app.cell(hide_code=True)
def _(deliveries_df, matches_df, mo, players_df):
    mo.md(
        rf"""
        ---
        ### 📊 Ingested Clean Dataset Statistics
        * **`matches_df`**: `{len(matches_df):,}` rows | `{matches_df.shape[1]}` columns | Memory: `{round(matches_df.memory_usage(deep=True).sum()/1024**2, 2)}` MB
        * **`deliveries_df`**: `{len(deliveries_df):,}` rows | `{deliveries_df.shape[1]}` columns | Memory: `{round(deliveries_df.memory_usage(deep=True).sum()/1024**2, 2)}` MB
        * **`players_df`**: `{len(players_df):,}` rows | `{players_df.shape[1]}` columns | Memory: `{round(players_df.memory_usage(deep=True).sum()/1024**2, 2)}` MB
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## 🎯 Cleaning Tasks Checklist for this Notebook:

    1. **City Imputation**: Fill ~51 missing city records using stadium `venue` mapping.
    2. **Franchise Harmonization**: Map historical re-branded team names to canonical names:
       * `delhi daredevils` ➔ `delhi capitals`
       * `kings xi punjab` ➔ `punjab kings`
       * `rising pune supergiant` / `rising pune supergiants` ➔ `rising pune supergiant`
       * `royal challengers bangalore` ➔ `royal challengers bengaluru`
    3. **Outcome Normalization**: Explicitly flag abandoned matches (`outcome = 'no result'`).
    """)
    return


@app.cell
def _(matches_df):
    # Impute missing cities from venue
    venue_city_map = {
        "dubai international cricket stadium": "dubai",
        "sharjah cricket stadium": "sharjah",
    }

    matches_df["city"] = matches_df["city"].fillna(
        matches_df["venue"].map(venue_city_map)
    )
    return


@app.cell
def _(deliveries_df, matches_df):
    team_mapping = {
        "delhi daredevils": "delhi capitals",
        "kings xi punjab": "punjab kings",
        "royal challengers bangalore": "royal challengers bengaluru",
        "rising pune supergiants": "rising pune supergiant",
    }

    # Apply to matches
    matches_df["team1"] = matches_df["team1"].replace(team_mapping)
    matches_df["team2"] = matches_df["team2"].replace(team_mapping)
    matches_df["winner"] = matches_df["winner"].replace(team_mapping)
    matches_df["toss_winner"] = matches_df["toss_winner"].replace(team_mapping)

    # Apply to deliveries
    deliveries_df["batting_team"] = deliveries_df["batting_team"].replace(team_mapping)
    return


@app.cell
def _(matches_df, pd):
    matches_df["outcome_status"] = matches_df["winner"].apply(
        lambda w: "no_result" if pd.isna(w) else "completed"
    )
    return


@app.cell
def _(PROCESSED_DIR, deliveries_df, matches_df, mo, players_df):
    # Save the cleaned datasets back to disk for validation and API use
    matches_df.to_parquet(PROCESSED_DIR / "clean_matches.parquet", index=False)
    deliveries_df.to_parquet(PROCESSED_DIR / "clean_deliveries.parquet", index=False)
    players_df.to_parquet(PROCESSED_DIR / "clean_players.parquet", index=False)

    save_status = mo.md(f"""
    ---
    ### ✅ All Cleaned Datasets Successfully Saved!
    * **`clean_matches.parquet`**: `{len(matches_df):,}` rows | `{matches_df.shape[1]}` columns (Missing cities: `{matches_df['city'].isna().sum()}`)
    * **`clean_deliveries.parquet`**: `{len(deliveries_df):,}` rows | `{deliveries_df.shape[1]}` columns (Harmonized team names & wicket metrics)
    * **`clean_players.parquet`**: `{len(players_df):,}` rows | `{players_df.shape[1]}` columns
    
    *Ready for validation in `03_data_validation.py`!*
    """)
    return (save_status,)


if __name__ == "__main__":
    app.run()
