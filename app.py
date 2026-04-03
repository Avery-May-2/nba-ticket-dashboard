from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from urllib.error import URLError
from urllib.request import urlopen

import pandas as pd
import streamlit as st

FIVETHIRTYEIGHT_ELO_URL = "https://projects.fivethirtyeight.com/nba-model/nba_elo.csv"
KAGGLE_DATASETS_URL = "https://www.kaggle.com/datasets?search=nba"
LOCAL_KAGGLE_FALLBACK = "data/kaggle_nba_datasets_fallback.csv"


@dataclass
class LoadResult:
    frame: pd.DataFrame
    source: str


def _download_text(url: str, timeout: int = 20) -> str:
    with urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


@st.cache_data(ttl=60 * 60)
def load_fivethirtyeight_data() -> LoadResult:
    """Load FiveThirtyEight NBA ELO data."""
    try:
        frame = pd.read_csv(FIVETHIRTYEIGHT_ELO_URL)
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        return LoadResult(frame=frame, source=FIVETHIRTYEIGHT_ELO_URL)
    except Exception:
        sample = pd.DataFrame(
            [
                {"date": "2024-10-22", "team1": "BOS", "team2": "NYK", "score1": 132, "score2": 109, "elo1_pre": 1672, "elo2_pre": 1501},
                {"date": "2024-10-22", "team1": "LAL", "team2": "MIN", "score1": 110, "score2": 103, "elo1_pre": 1598, "elo2_pre": 1562},
                {"date": "2024-10-23", "team1": "DEN", "team2": "PHX", "score1": 118, "score2": 114, "elo1_pre": 1640, "elo2_pre": 1621},
            ]
        )
        sample["date"] = pd.to_datetime(sample["date"])
        return LoadResult(frame=sample, source="embedded fallback sample")


@st.cache_data(ttl=60 * 60 * 24)
def load_kaggle_dataset_catalog() -> LoadResult:
    """Try to scrape Kaggle's NBA dataset links, fallback to local curated sample."""
    try:
        html = _download_text(KAGGLE_DATASETS_URL)
        matches = re.findall(r'href="(/datasets/[^"]+)"', html)
        records: list[dict[str, str]] = []
        seen: set[str] = set()
        for path in matches:
            if "?" in path:
                path = path.split("?", 1)[0]
            if path in seen:
                continue
            seen.add(path)
            slug = path.split("/datasets/")[-1]
            owner, name = slug.split("/", 1) if "/" in slug else ("unknown", slug)
            records.append(
                {
                    "dataset_name": name.replace("-", " ").title(),
                    "owner": owner,
                    "dataset_url": f"https://www.kaggle.com{path}",
                    "source": "live scrape",
                }
            )
        if records:
            return LoadResult(frame=pd.DataFrame(records), source=KAGGLE_DATASETS_URL)
    except URLError:
        pass
    except Exception:
        pass

    fallback = pd.read_csv(LOCAL_KAGGLE_FALLBACK)
    return LoadResult(frame=fallback, source=LOCAL_KAGGLE_FALLBACK)


def _team_elo_snapshot(frame: pd.DataFrame) -> pd.DataFrame:
    candidates: list[pd.DataFrame] = []

    if {"team1", "elo1_pre", "date"}.issubset(frame.columns):
        candidates.append(frame[["date", "team1", "elo1_pre"]].rename(columns={"team1": "team", "elo1_pre": "elo"}))
    if {"team2", "elo2_pre", "date"}.issubset(frame.columns):
        candidates.append(frame[["date", "team2", "elo2_pre"]].rename(columns={"team2": "team", "elo2_pre": "elo"}))

    if not candidates:
        return pd.DataFrame(columns=["team", "elo"])

    long = pd.concat(candidates, ignore_index=True).dropna(subset=["team", "elo"])
    latest = long.sort_values("date").groupby("team", as_index=False).tail(1)
    return latest[["team", "elo"]].sort_values("elo", ascending=False)


def _recent_games(frame: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    needed = ["date", "team1", "team2", "score1", "score2"]
    available = [c for c in needed if c in frame.columns]
    if not available:
        return pd.DataFrame()
    games = frame[available].copy()
    if "date" in games.columns:
        games = games.sort_values("date", ascending=False)
    return games.head(limit)


def main() -> None:
    st.set_page_config(page_title="NBA Data Hub", layout="wide")
    st.title("🏀 NBA Data Hub (Kaggle + FiveThirtyEight)")
    st.caption(
        f"Built with data discovered from Kaggle datasets and FiveThirtyEight. Updated on {date.today().isoformat()}."
    )

    with st.sidebar:
        st.header("Sources")
        st.markdown(f"- [Kaggle Datasets]({KAGGLE_DATASETS_URL})")
        st.markdown("- [FiveThirtyEight Data Hub](https://data.fivethirtyeight.com/)")

    fte = load_fivethirtyeight_data()
    kaggle = load_kaggle_dataset_catalog()

    left, right = st.columns([2, 1])
    with left:
        st.subheader("FiveThirtyEight NBA ELO")
        st.caption(f"Loaded from: `{fte.source}`")
        team_elo = _team_elo_snapshot(fte.frame)
        if team_elo.empty:
            st.warning("Could not infer team ELO values from the current dataset schema.")
        else:
            st.dataframe(team_elo.head(15), use_container_width=True)
            st.bar_chart(team_elo.head(12).set_index("team")["elo"])

        st.markdown("#### Recent games")
        st.dataframe(_recent_games(fte.frame, limit=25), use_container_width=True)

    with right:
        st.subheader("Kaggle NBA Dataset Catalog")
        st.caption(f"Loaded from: `{kaggle.source}`")
        st.metric("Datasets indexed", int(len(kaggle.frame.index)))

        q = st.text_input("Filter datasets")
        view = kaggle.frame.copy()
        if q:
            mask = view.apply(lambda row: row.astype(str).str.contains(q, case=False).any(), axis=1)
            view = view[mask]
        st.dataframe(view, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
