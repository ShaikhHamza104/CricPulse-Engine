from pathlib import Path

import duckdb
import pandas as pd


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_db_path() -> Path:
    return get_project_root() / "data" / "processed" / "ipl.duckdb"


DB_PATH = get_db_path()


def read_tables_from_duckdb() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    with duckdb.connect(database=str(DB_PATH), read_only=True) as connection:
        matches_df = connection.execute("SELECT * FROM matches").df()
        deliveries_df = connection.execute("SELECT * FROM deliveries").df()
        players_df = connection.execute("SELECT * FROM players").df()

    return matches_df, deliveries_df, players_df


def export_tables_as_parquet(
    matches_df: pd.DataFrame,
    deliveries_df: pd.DataFrame,
    players_df: pd.DataFrame,
) -> None:
    project_root = get_project_root()
    processed_data_dir = project_root / "data" / "processed"
    processed_data_dir.mkdir(parents=True, exist_ok=True)

    matches_df.to_parquet(processed_data_dir / "matches.parquet", index=False)
    deliveries_df.to_parquet(processed_data_dir / "deliveries.parquet", index=False)
    players_df.to_parquet(processed_data_dir / "players.parquet", index=False)


def read_parquet_file(parquet_file: Path) -> pd.DataFrame:
    return pd.read_parquet(parquet_file)


if __name__ == "__main__":
    matches_df, deliveries_df, players_df = read_tables_from_duckdb()
    export_tables_as_parquet(matches_df, deliveries_df, players_df)
    read_parquet_file(get_project_root() / "data" / "processed" / "matches.parquet")
