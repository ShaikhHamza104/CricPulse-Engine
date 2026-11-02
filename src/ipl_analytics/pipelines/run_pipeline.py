from ipl_analytics.pipelines.extract import extract_matches
from ipl_analytics.pipelines.load import load_data
from ipl_analytics.pipelines.transform import transform_matches


def main():
    print("[Pipeline] Starting IPL ETL Pipeline...")

    # 1. Extract
    print("[Extract] Extracting matches from data/raw/...")
    raw_matches = extract_matches()

    # 2. Transform
    print("[Transform] Processing Bronze (raw) and Silver (clean) transformations...")
    raw_data, clean_data = transform_matches(raw_matches)

    raw_matches_df, raw_deliveries_df, raw_players_df = raw_data
    clean_matches_df, clean_deliveries_df, clean_players_df = clean_data

    print(f"  - Matches: {len(clean_matches_df):,} records")
    print(f"  - Deliveries: {len(clean_deliveries_df):,} records")
    print(f"  - Players: {len(clean_players_df):,} records")

    # 3. Load
    print("[Load] Ingesting tables into DuckDB and exporting Parquet files...")
    load_data(raw_data, clean_data, export_parquet=True)

    print("[Pipeline] Pipeline executed successfully! Both raw_* and clean_* datasets are ready.")


if __name__ == "__main__":
    main()
