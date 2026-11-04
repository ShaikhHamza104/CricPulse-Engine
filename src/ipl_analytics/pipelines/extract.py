import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def extract_matches():
    """Yield (match_id, match_json) for every JSON match."""

    for file_path in sorted(RAW_DIR.glob("*.json")):
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        yield file_path.stem, data
