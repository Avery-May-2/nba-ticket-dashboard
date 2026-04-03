# nba-ticket-dashboard

A GitHub Pages-friendly NBA dashboard.

## Live app structure

This repository now includes a static web app that runs directly on GitHub Pages:

- `index.html`
- `styles.css`
- `app.js`
- `data/kaggle_nba_datasets_fallback.csv`

Because GitHub Pages serves static files, this app does not require a Python runtime in production.

## Deploy on GitHub Pages

1. Push these files to your default branch (for example, `main`).
2. In GitHub, open **Settings → Pages**.
3. Under **Build and deployment**, choose:
   - **Source**: `Deploy from a branch`
   - **Branch**: `main` (or your default branch)
   - **Folder**: `/ (root)`
4. Save and wait for the deployment to complete.

GitHub Pages should load `index.html` automatically.

## Local development (static app)

You can open `index.html` directly, or serve files locally:

```bash
python -m http.server 8000
# then visit http://localhost:8000
```

## Legacy Streamlit app

The original Streamlit prototype is still available in `app.py` for local experimentation:


```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
