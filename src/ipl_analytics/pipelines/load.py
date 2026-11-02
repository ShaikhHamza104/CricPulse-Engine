from pathlib import Path
import pandas as pd
from ipl_analytics.db.session import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def load_data(
    raw_data: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
    clean_data: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame],
    export_parquet: bool = True,
) -> None:
    """Ingest both Bronze (raw_*) and Silver (clean_*) tables into DuckDB and export to Parquet."""
    raw_matches_df, raw_deliveries_df, raw_players_df = raw_data
    clean_matches_df, clean_deliveries_df, clean_players_df = clean_data

    if clean_matches_df.empty or clean_deliveries_df.empty or clean_players_df.empty:
        print("Warning: One or more DataFrames are empty. Skipping database load.")
        return

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load into DuckDB
    with get_connection(read_only=False) as con:
        # Register raw DataFrames
        con.register("raw_matches_view", raw_matches_df)
        con.register("raw_deliveries_view", raw_deliveries_df)
        con.register("raw_players_view", raw_players_df)

        # Register clean DataFrames
        con.register("clean_matches_view", clean_matches_df)
        con.register("clean_deliveries_view", clean_deliveries_df)
        con.register("clean_players_view", clean_players_df)

        # Create Bronze (Raw) Tables
        con.execute("CREATE OR REPLACE TABLE raw_matches AS SELECT * FROM raw_matches_view")
        con.execute("CREATE OR REPLACE TABLE raw_deliveries AS SELECT * FROM raw_deliveries_view")
        con.execute("CREATE OR REPLACE TABLE raw_players AS SELECT * FROM raw_players_view")

        # Create Silver (Clean) Tables
        con.execute("CREATE OR REPLACE TABLE clean_matches AS SELECT * FROM clean_matches_view")
        con.execute("CREATE OR REPLACE TABLE clean_deliveries AS SELECT * FROM clean_deliveries_view")
        con.execute("CREATE OR REPLACE TABLE clean_players AS SELECT * FROM clean_players_view")

        # Create/Replace standard aliases pointing to clean data
        con.execute("CREATE OR REPLACE TABLE matches AS SELECT * FROM clean_matches_view")
        con.execute("CREATE OR REPLACE TABLE deliveries AS SELECT * FROM clean_deliveries_view")
        con.execute("CREATE OR REPLACE TABLE players AS SELECT * FROM clean_players_view")

        print("Successfully loaded Bronze (raw_*) and Silver (clean_*) tables into DuckDB!")

    # 2. Export Parquet files for fast disk access
    if export_parquet:
        # Clean Parquet files
        clean_matches_df.to_parquet(PROCESSED_DIR / "clean_matches.parquet", index=False)
        clean_deliveries_df.to_parquet(PROCESSED_DIR / "clean_deliveries.parquet", index=False)
        clean_players_df.to_parquet(PROCESSED_DIR / "clean_players.parquet", index=False)

        # Canonical aliases (matches.parquet, deliveries.parquet, players.parquet)
        clean_matches_df.to_parquet(PROCESSED_DIR / "matches.parquet", index=False)
        clean_deliveries_df.to_parquet(PROCESSED_DIR / "deliveries.parquet", index=False)
        clean_players_df.to_parquet(PROCESSED_DIR / "players.parquet", index=False)

        # Raw Parquet files
        raw_matches_df.to_parquet(PROCESSED_DIR / "raw_matches.parquet", index=False)
        raw_deliveries_df.to_parquet(PROCESSED_DIR / "raw_deliveries.parquet", index=False)
        raw_players_df.to_parquet(PROCESSED_DIR / "raw_players.parquet", index=False)

        print(f"Successfully exported clean and raw Parquet files to {PROCESSED_DIR}!")
