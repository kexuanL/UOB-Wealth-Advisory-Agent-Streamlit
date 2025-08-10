
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import json, re
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="Wealth Advisor Dashboard", layout="wide")
DATA_PATH    = Path("streamlit-cloud-starter/data/asset_recommendations.json")
SUMMARY_PATH = Path("streamlit-cloud-starter/data/all_articles.jsonl")

# ────────────────────────── Helpers ──────────────────────────
@st.cache_data
def load_json(p: Path):
    if not p.exists():
        st.error(f'❌ File not found: {p}'); st.stop()
    with p.open(encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def summary_stats(p: Path):
    "Return (#lines, earliest date, latest date) in JSONL"
    cnt, earliest, latest, date_rx = 0, None, None, re.compile(r'\d{4}-\d{2}-\d{2}')
    if not p.exists(): return cnt, None, None
    for raw in p.read_text(encoding='utf-8').splitlines():
        raw = raw.strip()
        if not raw: continue
        cnt += 1
        try:
            obj = json.loads(raw)
            dstr = next((obj[k] for k in obj if k.lower().startswith('publish') and 'date' in k.lower()), None)
        except json.JSONDecodeError:
            m = date_rx.search(raw); dstr = m.group(0) if m else None
        if not dstr: continue
        try: d = datetime.fromisoformat(str(dstr)[:10])
        except ValueError: continue
        earliest = d if not earliest or d < earliest else earliest
        latest   = d if not latest   or d > latest   else latest
    return cnt, earliest, latest

def boxed_names(lst):
    if not lst:
        return '<i>None</i>'
    return ' '.join(
        "<span style='display:inline-block;padding:6px 12px;margin:4px;"
        "border:1px solid #e0e0e0;border-radius:6px;background:#fafafa;'>{}</span>".format(x)
        for x in lst
    )

def render_panel(title: str, text: str):
    """A vertical panel with a centered, boxed title and body text below."""
    st.markdown(
        f"""
        <div style="border:1px solid #E6E8EB;border-radius:1rem;padding:1rem 1.2rem;margin-bottom:1rem;background:#ffffff">
            <div style="border:2px solid #D0D7DE;border-radius:.8rem;padding:.5rem 1rem;margin-bottom:.9rem;
                        text-align:center;font-weight:800;font-size:1.05rem;">
                {title}
            </div>
            <div style="white-space:pre-wrap;line-height:1.65;font-size:1rem;color:#222">
                {text if text.strip() else "<span style='color:#999'>（待填）</span>"}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ────────────────────────── Load data ─────────────────────────
DATA = load_json(DATA_PATH)

# ────────────────────────── Sidebar nav ───────────────────────
st.sidebar.title('☰ Navigation')
PAGE = st.sidebar.radio(
    'Select page',
    ('Article Inventory', 'Sentiment Ranking', 'Asset Dashboard', 'Original & Summary')
)

# ════════════════════ Page 1 · Article Inventory ════════════════════
if PAGE == 'Article Inventory':
    total, earliest, latest = summary_stats(SUMMARY_PATH)
    span = f"<p><b>Time span:</b> {earliest:%Y-%m-%d} → {latest:%Y-%m-%d}</p>" if earliest and latest else ''
    st.markdown(
        '''<div style="background:linear-gradient(135deg,#f3f7ff 0%,#d7e7ff 100%);
                      border-radius:1.4rem;padding:2rem;margin-bottom:1.5rem;
                      text-align:center;box-shadow:0 8px 18px rgba(0,0,0,.06)">
                 <h1 style="margin:.2rem 0">🗂️ Article Inventory</h1>
                 <p><b>Total summaries:</b>
                    <span style="font-size:1.6rem;font-weight:800;color:#1f77b4">{total:,}</span></p>
                 {span}
           </div>'''.format(total=total, span=span),
        unsafe_allow_html=True
    )

    st.subheader('🌍 Products covered')
    for cls, assets in DATA.items():
        with st.expander(f"🔸 {cls} ({len(assets)})"):
            cols = st.columns(3)
            for i, name in enumerate(assets):
                cols[i % 3].markdown(
                    "<div style='padding:6px 12px;margin:4px 0;border:1px solid #e0e0e0;"
                    "border-radius:6px;background:#fafafa;text-align:center'>{}</div>".format(name),
                    unsafe_allow_html=True
                )

# ════════════════════ Page 2 · Sentiment Ranking ═══════════════════
elif PAGE == 'Sentiment Ranking':
    st.title('📊 Sentiment score ranking (-1 = bearish, +1 = bullish)')

    # ---- DataFrame of scores ----
    rows = [
        {'asset': a,
         'score': pd.to_numeric(info.get('overall sentiment score'), errors='coerce')}
        for d in DATA.values() for a, info in d.items()
    ]
    df = pd.DataFrame(rows).dropna()
    df['score'] = df['score'].clip(-1, 1)
    df = df.sort_values('score', ascending=False)

    # ---- Buy / Sell lists ----
    buy_list  = df.loc[df.score >  0.8, 'asset'].tolist()
    sell_list = df.loc[df.score < -0.8, 'asset'].tolist()

    # ---- Hero panel ----
    _, _, latest = summary_stats(SUMMARY_PATH)
    latest_str = latest.strftime("%Y-%m-%d") if latest else "N/A"

    hero_html = '''
    <div style="background:linear-gradient(135deg,#f3f7ff 0%,#d7e7ff 100%);
                border-radius:1.4rem;padding:1.8rem 2.2rem;margin-bottom:1.5rem;
                box-shadow:0 8px 18px rgba(0,0,0,.06)">
        <p style="margin:0 0 1.2rem 0;
                  font-weight:800;font-size:1.6rem;text-align:center;">
            Asset recommendation from the day of
            <span style="color:#1f77b4">{latest}</span>
        </p>
        <div style="display:flex;gap:3rem;justify-content:center">
            <div style="flex:1">
                <p style="margin:0 0 .4rem 0;font-weight:700;font-size:1.05rem">📈 Buy (&gt; 0.8)</p>
                {buy}
            </div>
            <div style="flex:1">
                <p style="margin:0 0 .4rem 0;font-weight:700;font-size:1.05rem">📉 Sell (&lt; -0.8)</p>
                {sell}
            </div>
        </div>
    </div>
    '''.format(latest=latest_str,
               buy=boxed_names(buy_list),
               sell=boxed_names(sell_list))
    st.markdown(hero_html, unsafe_allow_html=True)

    # ---- Color mapping ----
    pos, neg = df[df.score > 0].score, df[df.score < 0].score
    pos_norm = plt.Normalize(0, pos.max() if not pos.empty else 1)
    neg_norm = plt.Normalize(0, abs(neg.min()) if not neg.empty else 1)
    df['color'] = df.score.apply(
        lambda v: cm.Reds(pos_norm(v)) if v > 0 else
                  cm.Greens(neg_norm(abs(v))) if v < 0 else
                  (0.5,0.5,0.5,1)
    )

    # ---- Plot ----
    fig, ax = plt.subplots(figsize=(9, 0.45*len(df)+1))
    ax.barh(df.asset, df.score, color=df.color)
    ax.set_xlim(-1, 1); ax.axvline(0, color='#444', lw=1)
    ax.set_xlabel('Sentiment score'); ax.invert_yaxis()
    st.pyplot(fig, clear_figure=True)

    # ---- Download ----
    with st.expander('📥 Download data'):
        st.dataframe(df[['asset','score']], use_container_width=True)
        st.download_button('Download CSV',
            df[['asset','score']].to_csv(index=False).encode(),
            'sentiment_ranking.csv')

# ════════════════════ Page 3 · Asset Dashboard ═══════════════════
elif PAGE == 'Asset Dashboard':
    cls   = st.sidebar.selectbox('Select asset class', list(DATA))
    asset = st.sidebar.radio('Select asset', list(DATA[cls]))
    info  = DATA[cls][asset]

    sent      = str(info.get('overall sentiment','')).upper()
    sent_col  = {'BUY':'green', 'SELL':'red'}.get(sent, 'gray')
    sent_score = info.get('overall sentiment score', 'N/A')

    st.title(f'💰 {asset}')
    st.markdown(
        "<div style='font-size:1.15rem'><b>Overall sentiment:</b> "
        "<span style='color:{c};font-weight:700'>{s}</span>&nbsp;&nbsp;"
        "<b>Sentiment score:</b> {sc}</div>".format(c=sent_col, s=sent or 'N/A', sc=sent_score),
        unsafe_allow_html=True
    )

    st.subheader('💭 Reasoning')
    st.write(info.get('summary','—'))

    st.subheader('🔍 Evidence & metadata')
    ev = info.get('evidence', [])
    if ev:
        df_e = pd.DataFrame(ev)
        # protect Markdown table from $
        df_e['content'] = df_e['content'].astype(str).str.replace('$','\\$', regex=False)
        if 'url' in df_e: df_e['url'] = df_e['url'].apply(lambda u:f'[link]({u})' if u else '')
        if 'date' in df_e:
            df_e['_t'] = pd.to_datetime(df_e['date'], errors='coerce')
            df_e = df_e.sort_values('_t', ascending=False).drop(columns='_t')
        order = ['content','reason','sentiment','sentiment score','source','title','url','date']
        df_e = df_e[[c for c in order if c in df_e]]
        st.markdown(df_e.to_markdown(index=False), unsafe_allow_html=True)
    else:
        st.info('No evidence available.')

# ════════════════════ Page 4 · Original & Summary ═══════════════════
elif PAGE == 'Original & Summary':
    st.title("📝 Original & Summary")

    # 可选：在页面里直接粘贴/修改文本（不影响下面的“展示区”的样式）
    with st.expander("✏️ Add / edit text (optional)"):
        st.session_state['original_text'] = st.text_area(
            "Original Text",
            value=st.session_state.get('original_text', ''),
            height=180,
            placeholder="Paste the original text here…"
        )
        st.session_state['summary_text'] = st.text_area(
            "Summary",
            value=st.session_state.get('summary_text', ''),
            height=180,
            placeholder="Paste the summary here…"
        )

    # 展示区：上下两个 panel；标题框住且居中，标题下接正文
    original = st.session_state.get('original_text', '')
    summary  = st.session_state.get('summary_text', '')

    render_panel("Original Text", original)
    render_panel("Summary", summary)