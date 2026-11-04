import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import duckdb
    import marimo as mo
    import pandas as pd

    return Path, duckdb, mo, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 🧪 IPL Analytics Platform — Data Quality & Validation Gate

    > **Stage:** Quality Assurance & Production Database Ingestion
    > **Purpose:** Verify data integrity, constraints, and business rules before saving into DuckDB.

    ---
    """)


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
    mo.md(rf"""
    ### 📋 Validation Suite Overview
    Loaded Clean Datasets:
    * **Matches:** `{len(matches_df):,}` rows
    * **Deliveries:** `{len(deliveries_df):,}` rows
    * **Players:** `{len(players_df):,}` rows
    ---
    """)


@app.cell
def _(deliveries_df, matches_df, mo):
    # Test 1: Referential Integrity (Every delivery must belong to an existing match)
    match_ids_in_matches = set(matches_df["match_id"])
    orphan_deliveries = deliveries_df[
        ~deliveries_df["match_id"].isin(match_ids_in_matches)
    ]
    ref_integrity_passed = len(orphan_deliveries) == 0

    print(
        "Referential Integrity Check:", "PASSED" if ref_integrity_passed else "FAILED"
    )
    print(f"Orphan Deliveries Found: {len(orphan_deliveries)}")

    t1 = mo.md(f"""
    #### Test 1: Referential Integrity Check
    * **Status:** {"✅ PASSED" if ref_integrity_passed else "❌ FAILED"}
    * **Orphan Deliveries Found:** `{len(orphan_deliveries)}`
    """)
    return (ref_integrity_passed,)


@app.cell
def _(matches_df, mo):
    # Test 2: Null Checks on Essential Columns
    essential_cols = ["match_id", "season", "date", "team1", "team2", "venue", "city"]
    null_counts = matches_df[essential_cols].isna().sum()
    null_checks_passed = null_counts.sum() == 0

    print(
        "Null Checks on Essential Columns:",
        "PASSED" if null_checks_passed else "FAILED",
    )
    print("Null Counts:\n", null_counts)

    t2 = mo.md(f"""
    #### Test 2: Critical Null Checks (Matches)
    * **Status:** {"✅ PASSED" if null_checks_passed else "❌ FAILED"}
    * **Missing Cities:** `{matches_df["city"].isna().sum()}`
    * **Missing Dates:** `{matches_df["date"].isna().sum()}`
    * **Missing Teams:** `{matches_df[["team1", "team2"]].isna().sum().sum()}`
    """)
    return (null_checks_passed,)


@app.cell
def _(deliveries_df, mo):
    # Test 3: Delivery Run Consistency (total_runs == batter_runs + extra_runs)
    mismatched_runs = deliveries_df[
        deliveries_df["total_runs"]
        != (deliveries_df["batter_runs"] + deliveries_df["extra_runs"])
    ]
    runs_consistency_passed = len(mismatched_runs) == 0

    print(
        "Delivery Run Consistency Check:",
        "PASSED" if runs_consistency_passed else "FAILED",
    )
    print(f"Mismatched Deliveries Found: {len(mismatched_runs)}")

    t3 = mo.md(f"""
    #### Test 3: Run Mathematics Consistency Check
    * **Status:** {"✅ PASSED" if runs_consistency_passed else "❌ FAILED"}
    * **Mismatched Deliveries:** `{len(mismatched_runs)}`
    """)
    return (runs_consistency_passed,)


@app.cell
def _(deliveries_df, mo):
    # Test 4: Overs Range Check (0 <= over_number <= 19)
    invalid_overs = deliveries_df[
        (deliveries_df["over_number"] < 0) | (deliveries_df["over_number"] > 19)
    ]
    overs_range_passed = len(invalid_overs) == 0

    print("Overs Range Check:", "PASSED" if overs_range_passed else "FAILED")
    print(f"Invalid Overs Found: {len(invalid_overs)}")

    t4 = mo.md(f"""
    #### Test 4: Over Number Range Check (0 to 19)
    * **Status:** {"✅ PASSED" if overs_range_passed else "❌ FAILED"}
    * **Deliveries with Out-of-Range Overs:** `{len(invalid_overs)}`
    """)
    return (overs_range_passed,)


@app.cell
def _(deliveries_df, mo):
    # Test 5: Wickets Integrity Check
    has_wickets = "is_wicket" in deliveries_df.columns
    if has_wickets:
        wickets_count = deliveries_df["is_wicket"].sum()
        invalid_wickets = deliveries_df[
            deliveries_df["is_wicket"]
            & (deliveries_df["dismissal_kind"].isna())
        ]
        wickets_integrity_passed = len(invalid_wickets) == 0
    else:
        wickets_count = 0
        invalid_wickets = []
        wickets_integrity_passed = False

    print(
        "Wickets Integrity Check:", "PASSED" if wickets_integrity_passed else "FAILED"
    )
    print(f"Total Wickets Verified: {wickets_count:,}")

    t5 = mo.md(f"""
    #### Test 5: Wickets Consistency Check
    * **Status:** {"✅ PASSED" if wickets_integrity_passed else "❌ FAILED"}
    * **Total Dismissals Verified:** `{wickets_count:,}`
    * **Invalid Wicket Records:** `{len(invalid_wickets)}`
    """)
    return (wickets_integrity_passed,)


@app.cell
def _(
    mo,
    null_checks_passed,
    overs_range_passed,
    ref_integrity_passed,
    runs_consistency_passed,
    wickets_integrity_passed,
):
    all_passed = all(
        [
            ref_integrity_passed,
            null_checks_passed,
            runs_consistency_passed,
            overs_range_passed,
            wickets_integrity_passed,
        ]
    )
    print("Overall Data Quality Status:", "PASSED" if all_passed else "FAILED")

    final_card = mo.md(f"""
    ---
    ### 🏆 Overall Validation Result: {"✅ ALL 5 TESTS PASSED — READY FOR DUCKDB & PARQUET EXPORT" if all_passed else "❌ VALIDATION FAILED"}
    """)
    return (all_passed,)


@app.cell
def _(
    PROCESSED_DIR,
    all_passed,
    deliveries_df,
    duckdb,
    matches_df,
    mo,
    players_df,
):
    save_msg = None
    if all_passed:
        db_path = PROCESSED_DIR / "ipl.duckdb"
        # 1. Update DuckDB database tables atomically
        with duckdb.connect(database=str(db_path), read_only=False) as con:
            con.register("validated_matches", matches_df)
            con.register("validated_deliveries", deliveries_df)
            con.register("validated_players", players_df)

            # Update clean tables
            con.execute(
                "CREATE OR REPLACE TABLE clean_matches AS SELECT * FROM validated_matches"
            )
            con.execute(
                "CREATE OR REPLACE TABLE clean_deliveries AS SELECT * FROM validated_deliveries"
            )
            con.execute(
                "CREATE OR REPLACE TABLE clean_players AS SELECT * FROM validated_players"
            )

            # Update canonical aliases
            con.execute(
                "CREATE OR REPLACE TABLE matches AS SELECT * FROM validated_matches"
            )
            con.execute(
                "CREATE OR REPLACE TABLE deliveries AS SELECT * FROM validated_deliveries"
            )
            con.execute(
                "CREATE OR REPLACE TABLE players AS SELECT * FROM validated_players"
            )

        # 2. Export validated clean Parquet files to disk
        matches_df.to_parquet(PROCESSED_DIR / "clean_matches.parquet", index=False)
        deliveries_df.to_parquet(
            PROCESSED_DIR / "clean_deliveries.parquet", index=False
        )
        players_df.to_parquet(PROCESSED_DIR / "clean_players.parquet", index=False)

        # 3. Keep canonical alias Parquet files in sync
        matches_df.to_parquet(PROCESSED_DIR / "matches.parquet", index=False)
        deliveries_df.to_parquet(PROCESSED_DIR / "deliveries.parquet", index=False)
        players_df.to_parquet(PROCESSED_DIR / "players.parquet", index=False)

        print(
            f"Successfully saved validated tables to DuckDB ({db_path}) and exported all clean Parquet files!"
        )

        save_msg = mo.md(f"""
        ---
        ### 💾 Production Database & Parquet Export: SUCCESS!
        All 5 automated quality tests passed. Data has been safely written:
        * **DuckDB Database (`{db_path.name}`)**:
          * `clean_matches` & `matches`: `{len(matches_df):,}` rows | `{matches_df.shape[1]}` columns
          * `clean_deliveries` & `deliveries`: `{len(deliveries_df):,}` rows | `{deliveries_df.shape[1]}` columns (with `{deliveries_df["is_wicket"].sum():,}` dismissals)
          * `clean_players` & `players`: `{len(players_df):,}` rows
        * **Parquet Files Exported**:
          * `clean_matches.parquet` & `matches.parquet`
          * `clean_deliveries.parquet` & `deliveries.parquet`
          * `clean_players.parquet` & `players.parquet`

        *Everything is in sync, verified, and completely unbreakable!*
        """)
    else:
        save_msg = mo.md(
            "### ❌ Validation Failed: Aborted database & parquet update to preserve data integrity."
        )


if __name__ == "__main__":
    app.run()
