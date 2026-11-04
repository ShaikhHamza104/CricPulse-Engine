import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import importlib
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import pandas as pd

    import ipl_analytics.core.exploration

    importlib.reload(ipl_analytics.core.exploration)
    from ipl_analytics.core.exploration import explore_data

    return Path, explore_data, mo, np, pd


@app.cell
def _(Path):
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

    IPL_MATCHES = PROCESSED_DIR / "matches.parquet"
    IPL_PLAYERS = PROCESSED_DIR / "players.parquet"
    IPL_DELIVERIES = PROCESSED_DIR / "deliveries.parquet"
    return IPL_DELIVERIES, IPL_MATCHES, IPL_PLAYERS, PROCESSED_DIR


@app.cell
def _(IPL_MATCHES, explore_data, mo):
    matches_report = explore_data(IPL_MATCHES)

    display_matches = mo.vstack(
        [
            mo.md(f"""
        # 🏏 1. IPL Matches Data Exploration Report
        - **Total Matches:** {matches_report["rows"]:,}
        - **Total Columns:** {matches_report["columns"]}
        - **Duplicate Rows:** {matches_report["duplicate_rows"]}
        - **Memory Footprint:** {matches_report["memory_usage_mb"]} MB
        """),
            mo.md("#### Column Details & Missing Values"),
            matches_report["column_details"],
            mo.md("#### Sample Data (First 5 Rows)"),
            matches_report["sample"],
        ]
    )


@app.cell
def _(IPL_PLAYERS, explore_data, mo):
    players_report = explore_data(IPL_PLAYERS)

    display_players = mo.vstack(
        [
            mo.md(f"""
        # 👤 2. IPL Players Data Exploration Report
        - **Total Registered Players:** {players_report["rows"]:,}
        - **Columns:** {players_report["columns"]}
        - **Duplicate Rows:** {players_report["duplicate_rows"]}
        - **Memory Footprint:** {players_report["memory_usage_mb"]} MB
        """),
            mo.md("#### Column Details"),
            players_report["column_details"],
            mo.md("#### Sample Data (First 5 Rows)"),
            players_report["sample"],
        ]
    )


@app.cell
def _(IPL_DELIVERIES, explore_data, mo):
    deliveries_report = explore_data(IPL_DELIVERIES)

    display_deliveries = mo.vstack(
        [
            mo.md(f"""
        # ⚡ 3. IPL Deliveries (Ball-by-Ball) Exploration Report
        - **Total Deliveries:** {deliveries_report["rows"]:,}
        - **Columns:** {deliveries_report["columns"]}
        - **Duplicate Rows:** {deliveries_report["duplicate_rows"]}
        - **Memory Footprint:** {deliveries_report["memory_usage_mb"]} MB
        """),
            mo.md("#### Column Details & Dtypes"),
            deliveries_report["column_details"],
            mo.md("#### Numeric Summary"),
            deliveries_report["numeric_summary"],
            mo.md("#### Sample Data (First 5 Rows)"),
            deliveries_report["sample"],
        ]
    )


@app.cell
def _(IPL_DELIVERIES, IPL_MATCHES, IPL_PLAYERS, np, pd):
    # --- Format & Downcast Matches ---
    clean_matches_df = pd.read_parquet(IPL_MATCHES)
    clean_matches_df["match_id"] = clean_matches_df["match_id"].astype(np.int32)
    clean_matches_df["season"] = (
        clean_matches_df["season"]
        .astype(str)
        .str.extract(r"(^\d{4})", expand=False)
        .astype(np.int32)
    )
    clean_matches_df["date"] = pd.to_datetime(clean_matches_df["date"])
    clean_matches_df["year"] = clean_matches_df["date"].dt.year.astype(np.int32)
    clean_matches_df["month"] = clean_matches_df["date"].dt.month.astype(np.int32)

    for col in [
        "team1",
        "team2",
        "venue",
        "city",
        "winner",
        "toss_winner",
        "toss_decision",
    ]:
        clean_matches_df[col] = clean_matches_df[col].astype(str).str.lower()
    clean_matches_df.loc[clean_matches_df["city"] == "nan", "city"] = None
    clean_matches_df.loc[clean_matches_df["winner"] == "nan", "winner"] = None

    # --- Format & Downcast Deliveries ---
    clean_deliveries_df = pd.read_parquet(IPL_DELIVERIES)
    clean_deliveries_df["match_id"] = clean_deliveries_df["match_id"].astype(np.int32)
    clean_deliveries_df["innings"] = clean_deliveries_df["innings"].astype(np.int8)
    clean_deliveries_df["over_number"] = clean_deliveries_df["over_number"].astype(
        np.int8
    )
    clean_deliveries_df["ball_number"] = clean_deliveries_df["ball_number"].astype(
        np.int8
    )
    clean_deliveries_df["batter_runs"] = clean_deliveries_df["batter_runs"].astype(
        np.int8
    )
    clean_deliveries_df["extra_runs"] = clean_deliveries_df["extra_runs"].astype(
        np.int8
    )
    clean_deliveries_df["total_runs"] = clean_deliveries_df["total_runs"].astype(
        np.int32
    )
    clean_deliveries_df["wides"] = clean_deliveries_df["wides"].astype(np.int8)
    clean_deliveries_df["noballs"] = clean_deliveries_df["noballs"].astype(np.int8)
    clean_deliveries_df["byes"] = clean_deliveries_df["byes"].astype(np.int8)
    clean_deliveries_df["legbyes"] = clean_deliveries_df["legbyes"].astype(np.int8)
    clean_deliveries_df["is_super_over"] = clean_deliveries_df["is_super_over"].astype(
        np.int8
    )
    clean_deliveries_df["is_boundary"] = clean_deliveries_df["is_boundary"].astype(bool)

    if "is_wicket" in clean_deliveries_df.columns:
        clean_deliveries_df["is_wicket"] = clean_deliveries_df["is_wicket"].astype(bool)
    if "dismissal_kind" in clean_deliveries_df.columns:
        clean_deliveries_df["dismissal_kind"] = (
            clean_deliveries_df["dismissal_kind"].astype(str).str.lower()
        )
        clean_deliveries_df.loc[
            clean_deliveries_df["dismissal_kind"].isin(["nan", "none", ""]),
            "dismissal_kind",
        ] = None
    if "player_dismissed" in clean_deliveries_df.columns:
        clean_deliveries_df["player_dismissed"] = (
            clean_deliveries_df["player_dismissed"].astype(str).str.lower()
        )
        clean_deliveries_df.loc[
            clean_deliveries_df["player_dismissed"].isin(["nan", "none", ""]),
            "player_dismissed",
        ] = None

    for col in ["batting_team", "batter", "bowler", "non_striker"]:
        clean_deliveries_df[col] = clean_deliveries_df[col].astype(str).str.lower()

    # --- Format & Lowercase Players ---
    clean_players_df = pd.read_parquet(IPL_PLAYERS)
    clean_players_df["player_id"] = (
        clean_players_df["player_id"].astype(str).str.lower()
    )
    clean_players_df["player_name"] = (
        clean_players_df["player_name"].astype(str).str.lower()
    )
    return clean_deliveries_df, clean_matches_df, clean_players_df


@app.cell
def _(
    PROCESSED_DIR,
    clean_deliveries_df,
    clean_matches_df,
    clean_players_df,
    mo,
):
    # Export clean Parquet datasets
    matches_out = PROCESSED_DIR / "clean_matches.parquet"
    deliveries_out = PROCESSED_DIR / "clean_deliveries.parquet"
    players_out = PROCESSED_DIR / "clean_players.parquet"

    clean_matches_df.to_parquet(matches_out, index=False)
    clean_deliveries_df.to_parquet(deliveries_out, index=False)
    clean_players_df.to_parquet(players_out, index=False)

    export_status = mo.md(f"""
    ---
    ### ✅ Clean Parquet Files Successfully Exported!
    - **`{matches_out.name}`**: {len(clean_matches_df):,} rows, {clean_matches_df.shape[1]} columns
    - **`{deliveries_out.name}`**: {len(clean_deliveries_df):,} rows, {clean_deliveries_df.shape[1]} columns
    - **`{players_out.name}`**: {len(clean_players_df):,} rows, {clean_players_df.shape[1]} columns

    *These files are saved in `{PROCESSED_DIR}` and ready for direct import in subsequent steps.*
    """)


@app.cell
def _(mo):
    summary_notes = mo.md("""
    ---
    ### 📝 Summary of Key Insights for Data Cleaning (`02_data_cleaning.py`):
    1. **Missing Data**:
       - `city`: ~51 missing rows in `matches` (can be imputed from `venue`).
       - `winner`: 9 matches abandoned due to rain / no result.
    2. **Wicket Tracking**:
       - `is_wicket`, `dismissal_kind`, and `player_dismissed` are properly captured.
    3. **Team Name Harmonization**:
       - Rebranded franchises (e.g., *Delhi Daredevils* ➔ *Delhi Capitals*, *Kings XI Punjab* ➔ *Punjab Kings*).
    """)


if __name__ == "__main__":
    app.run()
