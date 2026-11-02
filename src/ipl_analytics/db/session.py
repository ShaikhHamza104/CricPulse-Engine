from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DB_PATH = PROJECT_ROOT / "data" / "processed" / "ipl.duckdb"


def get_connection(read_only: bool = True):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    return duckdb.connect(
        database=str(DB_PATH),
        read_only=read_only,
    )