from collections.abc import Generator
from typing import Any

import numpy as np
import pandas as pd

VENUE_CITY_MAP = {
    "dubai international cricket stadium": "dubai",
    "sharjah cricket stadium": "sharjah",
}

TEAM_MAPPING = {
    # Historical Franchise Renamings
    "delhi daredevils": "delhi capitals",
    "kings xi punjab": "punjab kings",
    "royal challengers bangalore": "royal challengers bengaluru",
    "rising pune supergiants": "rising pune supergiant",
    # Franchise Acronyms and Aliases
    "csk": "chennai super kings",
    "mi": "mumbai indians",
    "rcb": "royal challengers bengaluru",
    "kkr": "kolkata knight riders",
    "srh": "sunrisers hyderabad",
    "dc": "delhi capitals",
    "dd": "delhi capitals",
    "rr": "rajasthan royals",
    "pbks": "punjab kings",
    "kxip": "punjab kings",
    "lsg": "lucknow super giants",
    "gt": "gujarat titans",
    "rps": "rising pune supergiant",
    "gl": "gujarat lions",
    "pw": "pune warriors",
    "pwi": "pune warriors",
    "ktk": "kochi tuskers kerala",
    "dch": "deccan chargers",
}

VENUE_MAPPING = {
    # Wankhede
    "wankhede stadium, mumbai": "wankhede stadium",
    # Eden Gardens
    "eden gardens, kolkata": "eden gardens",
    # M. Chinnaswamy
    "m chinnaswamy stadium, bengaluru": "m chinnaswamy stadium",
    "m.chinnaswamy stadium": "m chinnaswamy stadium",
    # MA Chidambaram (Chepauk)
    "ma chidambaram stadium, chepauk, chennai": "ma chidambaram stadium, chepauk",
    "ma chidambaram stadium": "ma chidambaram stadium, chepauk",
    # Feroz Shah Kotla / Arun Jaitley
    "feroz shah kotla": "arun jaitley stadium",
    "arun jaitley stadium, delhi": "arun jaitley stadium",
    # Sawai Mansingh
    "sawai mansingh stadium, jaipur": "sawai mansingh stadium",
    # Rajiv Gandhi
    "rajiv gandhi international stadium, uppal, hyderabad": (
        "rajiv gandhi international stadium, uppal"
    ),
    "rajiv gandhi international stadium": "rajiv gandhi international stadium, uppal",
    # DY Patil
    "dr dy patil sports academy, mumbai": "dr dy patil sports academy",
    # Brabourne
    "brabourne stadium, mumbai": "brabourne stadium",
    # MCA Pune
    "maharashtra cricket association stadium, pune": "maharashtra cricket association stadium",
    "subrata roy sahara stadium": "maharashtra cricket association stadium",
    # PCA Mohali
    "punjab cricket association is bindra stadium, mohali": (
        "punjab cricket association stadium, mohali"
    ),
    "punjab cricket association is bindra stadium": "punjab cricket association stadium, mohali",
    "punjab cricket association is bindra stadium, mohali, chandigarh": (
        "punjab cricket association stadium, mohali"
    ),
    # HPCA Dharamsala
    "himachal pradesh cricket association stadium, dharamsala": (
        "himachal pradesh cricket association stadium"
    ),
    # Motera / Narendra Modi
    "sardar patel stadium, motera": "narendra modi stadium, ahmedabad",
    "narendra modi stadium": "narendra modi stadium, ahmedabad",
    # Sheikh Zayed
    "zayed cricket stadium, abu dhabi": "sheikh zayed stadium",
    # ACA-VDCA Visakhapatnam
    "dr. y.s. rajasekhara reddy aca-vdca cricket stadium, visakhapatnam": (
        "dr. y.s. rajasekhara reddy aca-vdca cricket stadium"
    ),
    # Shaheed Veer Narayan Singh
    "shaheed veer narayan singh international stadium, raipur": (
        "shaheed veer narayan singh international stadium"
    ),
    # Mullanpur
    "maharaja yadavindra singh international cricket stadium, new chandigarh": (
        "maharaja yadavindra singh international cricket stadium, mullanpur"
    ),
}


def transform_raw_matches(
    raw_matches: Generator[tuple[str, dict[str, Any]]]
    | list[tuple[str, dict[str, Any]]],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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

        # Win outcome & victory margin
        by_outcome = outcome.get("by", {})
        win_outcome = None
        win_margin = None
        if "runs" in by_outcome:
            win_outcome = "runs"
            win_margin = int(by_outcome["runs"])
        elif "wickets" in by_outcome:
            win_outcome = "wickets"
            win_margin = int(by_outcome["wickets"])
        elif outcome.get("result") == "tie" or outcome.get("eliminator"):
            win_outcome = "super_over"
            win_margin = 0

        pom_list = info.get("player_of_match", [])
        player_of_match = str(pom_list[0]) if pom_list else None

        # RAW MATCH RECORD
        matches.append(
            {
                "match_id": str(match_id),
                "season": str(info.get("season")),
                "date": str(info["dates"][0]),
                "team1": str(teams[0]),
                "team2": str(teams[1]),
                "venue": str(info.get("venue")),
                "city": info.get("city"),
                "winner": winner,
                "win_outcome": win_outcome,
                "win_margin": win_margin,
                "player_of_match": player_of_match,
                "toss_winner": str(toss.get("winner")),
                "toss_decision": str(toss.get("decision")),
            }
        )

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
                    player_dismissed = (
                        wickets_info[0]["player_out"] if is_wicket else None
                    )

                    deliveries.append(
                        {
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
                        }
                    )

    raw_matches_df = pd.DataFrame(matches)
    raw_deliveries_df = pd.DataFrame(deliveries)
    raw_players_df = pd.DataFrame(players.values())

    return raw_matches_df, raw_deliveries_df, raw_players_df


def clean_data(
    raw_matches_df: pd.DataFrame,
    raw_deliveries_df: pd.DataFrame,
    raw_players_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Clean, type-cast, downcast, and standardize raw DataFrames into Silver tables."""
    # 1. Clean Matches
    clean_matches = raw_matches_df.copy()
    clean_matches["match_id"] = clean_matches["match_id"].astype(np.int32)

    # 🌟 CRICKET DOMAIN FIX: In IPL, the season is the calendar year the tournament was held.
    # Parsing dates ensures 2008 (from '2007/08') and 2010 (from '2009/10') are correctly restored.
    clean_matches["date"] = pd.to_datetime(clean_matches["date"])
    clean_matches["season"] = clean_matches["date"].dt.year.astype(np.int32)
    clean_matches["year"] = clean_matches["date"].dt.year.astype(np.int32)
    clean_matches["month"] = clean_matches["date"].dt.month.astype(np.int32)

    # Lowercase text columns
    for col in [
        "team1",
        "team2",
        "venue",
        "city",
        "winner",
        "toss_winner",
        "toss_decision",
    ]:
        clean_matches[col] = clean_matches[col].astype(str).str.lower().str.strip()

    # Restore true nulls
    clean_matches.loc[clean_matches["city"].isin(["nan", "none", ""]), "city"] = None
    clean_matches.loc[clean_matches["winner"].isin(["nan", "none", ""]), "winner"] = (
        None
    )

    # Impute missing cities from venue
    clean_matches["city"] = clean_matches["city"].fillna(
        clean_matches["venue"].map(VENUE_CITY_MAP)
    )

    # Harmonize franchise names and venue variations
    clean_matches["team1"] = clean_matches["team1"].replace(TEAM_MAPPING)
    clean_matches["team2"] = clean_matches["team2"].replace(TEAM_MAPPING)
    clean_matches["winner"] = clean_matches["winner"].replace(TEAM_MAPPING)
    clean_matches["toss_winner"] = clean_matches["toss_winner"].replace(TEAM_MAPPING)
    clean_matches["venue"] = clean_matches["venue"].replace(VENUE_MAPPING)

    # Match scorecard metrics
    clean_matches["win_outcome"] = clean_matches["win_outcome"].astype(object)
    clean_matches["win_margin"] = pd.to_numeric(
        clean_matches["win_margin"], errors="coerce"
    )
    clean_matches["player_of_match"] = clean_matches["player_of_match"].astype(object)
    clean_matches.loc[
        clean_matches["player_of_match"].isin(["nan", "none", ""]), "player_of_match"
    ] = None

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
    clean_deliveries["is_super_over"] = clean_deliveries["is_super_over"].astype(
        np.int8
    )
    clean_deliveries["is_boundary"] = clean_deliveries["is_boundary"].astype(bool)
    clean_deliveries["is_wicket"] = clean_deliveries["is_wicket"].astype(bool)

    # Lowercase text & harmonize teams
    for col in ["batting_team", "batter", "bowler", "non_striker"]:
        clean_deliveries[col] = (
            clean_deliveries[col].astype(str).str.lower().str.strip()
        )
    clean_deliveries["batting_team"] = clean_deliveries["batting_team"].replace(
        TEAM_MAPPING
    )

    # Clean dismissal text
    clean_deliveries["dismissal_kind"] = (
        clean_deliveries["dismissal_kind"].astype(str).str.lower().str.strip()
    )
    clean_deliveries.loc[
        clean_deliveries["dismissal_kind"].isin(["nan", "none", ""]), "dismissal_kind"
    ] = None

    clean_deliveries["player_dismissed"] = (
        clean_deliveries["player_dismissed"].astype(str).str.lower().str.strip()
    )
    clean_deliveries.loc[
        clean_deliveries["player_dismissed"].isin(["nan", "none", ""]),
        "player_dismissed",
    ] = None

    # 3. Clean Players
    clean_players = raw_players_df.copy()
    clean_players["player_id"] = (
        clean_players["player_id"].astype(str).str.lower().str.strip()
    )
    clean_players["player_name"] = (
        clean_players["player_name"].astype(str).str.lower().str.strip()
    )

    return clean_matches, clean_deliveries, clean_players


def transform_matches(raw_matches):
    """Backwards-compatible wrapper returning clean datasets."""
    raw_matches_df, raw_deliveries_df, raw_players_df = transform_raw_matches(
        raw_matches
    )
    clean_matches_df, clean_deliveries_df, clean_players_df = clean_data(
        raw_matches_df, raw_deliveries_df, raw_players_df
    )
    return (raw_matches_df, raw_deliveries_df, raw_players_df), (
        clean_matches_df,
        clean_deliveries_df,
        clean_players_df,
    )
