# Wealth Advisor Dashboard (Streamlit Cloud)

This repo is ready to deploy on **Streamlit Community Cloud** with a **stable public URL**.

## Quick start
1. **Download** this zip and push it to a new GitHub repo.
2. Go to https://share.streamlit.io → *New app* → select your repo → `streamlit_app.py` → **Deploy**.
3. Replace the sample data in `data/` with your real files:
   - `data/asset_recommendations.json`
   - `data/all_articles.jsonl`

> If your data updates regularly, you can automate it via CI or fetch from object storage at runtime.

## Local run
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Notes
- No Colab or ngrok is used here.
- Paths are **relative** so Streamlit Cloud can find files.
- Secrets (API keys, etc.) should go to **Streamlit Cloud → App → Settings → Secrets**.
