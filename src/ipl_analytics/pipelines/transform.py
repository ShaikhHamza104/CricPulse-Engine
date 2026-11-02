from typing import Any, Generator, Tuple
import numpy as np
import pandas as pd

VENUE_CITY_MAP = {
    "dubai international cricket stadium": "dubai",
    "sharjah cricket stadium": "sharjah",
}

TEAM_MAPPING = {
    "delhi daredevils": "delhi capitals",
    "kings xi punjab": "punjab kings",
    "royal challengers bangalore": "royal challengers bengaluru",
    "rising pune supergiants": "rising pune supergiant",
}


def transform_raw_matches(
    raw_matches: Generator[Tuple[str, dict[str, Any]], None, None] | list[Tuple[str, dict[str, Any]]]
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Parse raw match JSON into uncleaned Bronze DataFrames."""
    matches = []
    deliveries = []
    players = {}

    for match_id, data in raw_matches:
        info = data["info"]
        teams = info["teams"]
        outcome = info.get("outcome", {})
        toss = info.get("toss", {})

        # Handle match winner (fall back to eliminator winner for Super Over ties)
        winner = outcome.get("winner")
        if not winner and outcome.get("eliminator"):
            winner = outcome.get("eliminator")

        # RAW MATCH RECORD
        matches.append({
            "match_id": str(match_id),
            "season": str(info.get("season")),
            "date": str(info["dates"][0]),
            "team1": str(teams[0]),
            "team2": str(teams[1]),
            "venue": str(info.get("venue")),
            "city": info.get("city"),
            "winner": winner,
            "toss_winner": str(toss.get("winner")),
            "toss_decision": str(toss.get("decision")),
        })

        # RAW PLAYER RECORD
        registry = info.get("registry", {}).get("people", {})
        for team, names in info.get("players", {}).items():
            for name in names:
                player_id = registry.get(name)
                if player_id:
                    players[player_id] = {
                        "player_id": str(player_id),
                        "player_name": str(name),
                    }

        # RAW DELIVERY RECORD
        for innings_no, innings in enumerate(data.get("innings", []), start=1):
            batting_team = innings["team"]
            for over in innings.get("overs", []):
                over_number = over["over"]
                for ball_number, ball in enumerate(over["deliveries"], start=1):
                    runs = ball["runs"]
                    extras = ball.get("extras", {})

                    wickets_info = ball.get("wickets", [])
                    is_wicket = len(wickets_info) > 0
                    dismissal_kind = wickets_info[0]["kind"] if is_wicket else None
                    player_dismissed = wickets_info[0]["player_out"] if is_wicket else None

                    deliveries.append({
                        "match_id": str(match_id),
                        "innings": innings_no,
                        "batting_team": batting_team,
                        "over_number": over_number,
                        "ball_number": ball_number,
                        "batter": ball["batter"],
                        "bowler": ball["bowler"],
                        "non_striker": ball["non_striker"],
                        "batter_runs": runs["batter"],
                        "extra_runs": runs["extras"],
                        "total_runs": runs["total"],
                        "wides": extras.get("wides", 0),
                        "noballs": extras.get("noballs", 0),
                        "byes": extras.get("byes", 0),
                        "legbyes": extras.get("legbyes", 0),
                        "is_super_over": innings.get("super_over", False),
                        "is_boundary": (
                            runs["batter"] in (4, 6)
                            and not runs.get("non_boundary", False)
                        ),
                        "is_wicket": is_wicket,
                        "dismissal_kind": dismissal_kind,
                        "player_dismissed": player_dismissed,
                    })

    raw_matches_df = pd.DataFrame(matches)
    raw_deliveries_df = pd.DataFrame(deliveries)
    raw_players_df = pd.DataFrame(players.values())

    return raw_matches_df, raw_deliveries_df, raw_players_df


def clean_data(
    raw_matches_df: pd.DataFrame,
    raw_deliveries_df: pd.DataFrame,
    raw_players_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Clean, type-cast, downcast, and standardize raw DataFrames into Silver tables."""
    # 1. Clean Matches
    clean_matches = raw_matches_df.copy()
    clean_matches["match_id"] = clean_matches["match_id"].astype(np.int32)
    clean_matches["season"] = (
        clean_matches["season"].str.extract(r"(^\d{4})", expand=False).astype(np.int32)
    )
    clean_matches["date"] = pd.to_datetime(clean_matches["date"])
    clean_matches["year"] = clean_matches["date"].dt.year.astype(np.int32)
    clean_matches["month"] = clean_matches["date"].dt.month.astype(np.int32)

    # Lowercase text columns
    for col in ["team1", "team2", "venue", "city", "winner", "toss_winner", "toss_decision"]:
        clean_matches[col] = clean_matches[col].astype(str).str.lower()

    # Restore true nulls
    clean_matches.loc[clean_matches["city"].isin(["nan", "none", ""]), "city"] = None
    clean_matches.loc[clean_matches["winner"].isin(["nan", "none", ""]), "winner"] = None

    # Impute missing cities from venue
    clean_matches["city"] = clean_matches["city"].fillna(
        clean_matches["venue"].map(VENUE_CITY_MAP)
    )

    # Harmonize franchise names
    clean_matches["team1"] = clean_matches["team1"].replace(TEAM_MAPPING)
    clean_matches["team2"] = clean_matches["team2"].replace(TEAM_MAPPING)
    clean_matches["winner"] = clean_matches["winner"].replace(TEAM_MAPPING)
    clean_matches["toss_winner"] = clean_matches["toss_winner"].replace(TEAM_MAPPING)

    # Outcome classification
    clean_matches["outcome_status"] = clean_matches["winner"].apply(
        lambda w: "no_result" if pd.isna(w) else "completed"
    )

    # 2. Clean Deliveries
    clean_deliveries = raw_deliveries_df.copy()
    clean_deliveries["match_id"] = clean_deliveries["match_id"].astype(np.int32)
    clean_deliveries["innings"] = clean_deliveries["innings"].astype(np.int8)
    clean_deliveries["over_number"] = clean_deliveries["over_number"].astype(np.int8)
    clean_deliveries["ball_number"] = clean_deliveries["ball_number"].astype(np.int8)
    clean_deliveries["batter_runs"] = clean_deliveries["batter_runs"].astype(np.int8)
    clean_deliveries["extra_runs"] = clean_deliveries["extra_runs"].astype(np.int8)
    clean_deliveries["total_runs"] = clean_deliveries["total_runs"].astype(np.int32)
    clean_deliveries["wides"] = clean_deliveries["wides"].astype(np.int8)
    clean_deliveries["noballs"] = clean_deliveries["noballs"].astype(np.int8)
    clean_deliveries["byes"] = clean_deliveries["byes"].astype(np.int8)
    clean_deliveries["legbyes"] = clean_deliveries["legbyes"].astype(np.int8)
    clean_deliveries["is_super_over"] = clean_deliveries["is_super_over"].astype(np.int8)
    clean_deliveries["is_boundary"] = clean_deliveries["is_boundary"].astype(bool)
    clean_deliveries["is_wicket"] = clean_deliveries["is_wicket"].astype(bool)

    # Lowercase text & harmonize teams
    for col in ["batting_team", "batter", "bowler", "non_striker"]:
        clean_deliveries[col] = clean_deliveries[col].astype(str).str.lower()
    clean_deliveries["batting_team"] = clean_deliveries["batting_team"].replace(TEAM_MAPPING)

    # Clean dismissal text
    clean_deliveries["dismissal_kind"] = clean_deliveries["dismissal_kind"].astype(str).str.lower()
    clean_deliveries.loc[clean_deliveries["dismissal_kind"].isin(["nan", "none", ""]), "dismissal_kind"] = None

    clean_deliveries["player_dismissed"] = clean_deliveries["player_dismissed"].astype(str).str.lower()
    clean_deliveries.loc[clean_deliveries["player_dismissed"].isin(["nan", "none", ""]), "player_dismissed"] = None

    # 3. Clean Players
    clean_players = raw_players_df.copy()
    clean_players["player_id"] = clean_players["player_id"].astype(str).str.lower()
    clean_players["player_name"] = clean_players["player_name"].astype(str).str.lower()

    return clean_matches, clean_deliveries, clean_players


def transform_matches(raw_matches):
    """Backwards-compatible wrapper returning clean datasets."""
    raw_matches_df, raw_deliveries_df, raw_players_df = transform_raw_matches(raw_matches)
    clean_matches_df, clean_deliveries_df, clean_players_df = clean_data(
        raw_matches_df, raw_deliveries_df, raw_players_df
    )
    return (raw_matches_df, raw_deliveries_df, raw_players_df), (
        clean_matches_df,
        clean_deliveries_df,
        clean_players_df,
    )
