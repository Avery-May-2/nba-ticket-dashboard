# nba-ticket-dashboard
Real-time NBA ticket pricing dashboard with a demand-scoring engine powered by SportRadar data, deployable to GitHub Pages in minutes.

A lightweight Streamlit app that combines:

- **FiveThirtyEight NBA ELO data** (`https://projects.fivethirtyeight.com/nba-model/nba_elo.csv`)
- **Kaggle NBA dataset discovery** (`https://www.kaggle.com/datasets?search=nba`)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- The app attempts to load live data from both source sites.
- If Kaggle or FiveThirtyEight cannot be reached from your network, the app falls back to embedded sample data.

