
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
    ('Article Inventory', 'Information Summarization Agent', 'Investment Direction Agent:Evidence', 'Investment Direction Agent:Score')
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
elif PAGE == 'Investment Direction Agent:Score':
    st.title('📊 Investment Direction Agent: Sentiment Score')

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
    ax.set_xlabel('Sentiment score (-1 = bearish, +1 = bullish)'); ax.invert_yaxis()
    ax.set_title('Sentiment Score Ranking of Assets')
    st.pyplot(fig, clear_figure=True)

    # ---- Download ----
    with st.expander('📥 Download data'):
        st.dataframe(df[['asset','score']], use_container_width=True)
        st.download_button('Download CSV',
            df[['asset','score']].to_csv(index=False).encode(),
            'sentiment_ranking.csv')

# ════════════════════ Page 3 · Asset Dashboard ═══════════════════
elif PAGE == 'Investment Direction Agent:Evidence':
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
elif PAGE == 'Information Summarization Agent':
    st.title("📝 Original & Summary Example")

    # 固定两段文本
    ORIGINAL_TEXT = '''Higher-for-longer policy rates have made this the best backdrop for earning income in bonds in two decades – without taking more interest rate or credit risk. We favor a mix of income sources. We like short-term government bonds: the U.S. budget bill passed last month highlighted a lack of fiscal discipline, while sticky inflation limits rate cuts, keeping us tactically cautious on long-term bonds. In credit, resilient growth has kept corporate balance sheets solid even with tariffs.

Income is back — Fixed income assets with yields of 4% or larger, 2000-2025.
After the global financial crisis (GFC), bond yields slid as central banks slashed policy rates to near zero or below and bought bonds. That left investors starved of income unless they took risk in long-term bonds. In a stark switch-up, some 80% of global fixed income assets now offer yields above 4% as interest rates have settled above pre-pandemic levels. See the chart. That’s made assets like credit, mortgage-backed securities and emerging market debt more attractive. We have seen notable bond market developments this year. Credit spreads have been relatively steady even with sharp equity volatility. And investors are demanding more compensation for the risk of holding long-term bonds, leading to a steepening of global yield curves. The curve between five- and 30-year U.S. Treasury yields has more than doubled this year to its steepest levels since 2021, according to LSEG data.

We see abundant opportunities to earn income. We prefer short- and medium-term government bonds given yields near 4%. Markets are pricing in multiple Federal Reserve rate cuts over the next year. Yet we see sticky inflation limiting rate cuts – even as renewed rate hikes are unlikely. Our preference is partly driven by our caution on long-term bonds due to the lack of U.S. fiscal discipline and sticky inflation – though we could see occasional sharp rallies. The U.S. is issuing nearly $500 billion of debt weekly to fund its persistent budget deficits, per Haver Analytics. And the Congressional Budget Office expects the One Big Beautiful Bill to only add to deficits in the near term. Trade tensions could cool foreign demand at a time when sustaining U.S. debt relies on their ongoing buying – as we noted in our 2025 Midyear Outlook. We’re watching the market’s ability to absorb heavy Treasury issuance. Fiscal sustainability is not just a U.S. story: In Japan, 30-year yields hit a record high last week as policymakers floated tax cuts before Sunday’s upper house election.

Where we find income.
Higher U.S. policy rates mean interest rate differentials between the U.S. and other countries stay wide, revealing an array of global fixed income opportunities. That’s because hedging foreign bonds back into U.S. dollars boosts the income they offer. Some euro area bonds, like Spain, offer yields above 5% with such hedging – higher than U.S. equivalents. Credit has become a clear choice for quality. Spreads are historically tight, yet credit income remains attractive as balance sheets have held up alongside growth, even with tariff uncertainty. Default rates for U.S. high yield credit remain about half the 25-year average, according to J.P. Morgan data. We prefer European fixed income over the U.S. given a more stable fiscal outlook, especially European bank debt given strong financial earnings and insulation from tariff impacts.

We get selective across and within regions. We went overweight U.S. agency mortgage-backed securities (MBS): spreads are wider than historical averages and we could see some investors switch from long-term Treasuries. We upped local currency emerging market (EM) debt to neutral this month: it has weathered U.S. trade policy shifts, and debt levels have improved.

Our bottom line.
We like a mix of income opportunities but stay selective due to fiscal sustainability risks. We favor short- and medium-term government bonds, U.S. agency MBS, currency-hedged international bonds and local currency EM debt.

Market backdrop.
The S&P 500 hit new record highs last week, helped by signs of U.S. economic resilience in strong U.S. retail sales data. U.S. corporate earnings season kicked off with some big tech companies, putting renewed focus on artificial intelligence and capital spending. The index quickly recovered from reports that U.S. President Donald Trump discussed removing Fed Chair Jerome Powell, which Trump denied. Thirty-year Treasury yields ended the week steady at 4.99%, near May’s two-year high.

This week, we’re watching the European Central Bank’s (ECB) policy decision. We expect it to hold rates steady until September. The central bank now sees policy rates within a neutral range that neither stimulates nor restricts economic activity, inflation remains around its 2% target, and euro area growth shows little change. We watch for signals on whether the ECB will stay cautious or begin laying the groundwork for easing later this year.

Read our past weekly market commentaries.

Big calls.
Our highest conviction views on tactical (6-12 month) and strategic (long-term) horizons, July 2025.

Tactical granular views.
Six- to 12-month tactical views on selected assets vs. broad global asset classes by level of conviction, July 2025.

Legend Granular.
The table below reflects our views on a tactical horizon and, importantly, leaves aside the opportunity for alpha, or the potential to generate above-benchmark returns – especially at times of heightened volatility.

Euro-denominated tactical granular views.
Six- to 12-month tactical views on selected assets vs. broad global asset classes by level of conviction, July 2025.

Legend Granular.'''

    SUMMARY_TEXT  = '''"Content": "U.S. Treasury (Haver Analytics): Issuing nearly $500 billion of debt weekly to fund budget deficits, raising concerns about fiscal sustainability.",
"Content": "European Central Bank (ECB): Expected to hold rates steady until September, with a focus on whether to remain cautious or prepare for easing later in the year.",
"Content": "LSEG Data: Indicates U.S. Treasury yields have risen to their steepest levels since 2021, with the curve between five- and 30-year yields more than doubling this year.",
"Content": "J.P. Morgan (Analyst team, J.P. Morgan): Reports that default rates for U.S. high yield credit remain about half the 25-year average, indicating credit remains attractive despite tariff uncertainty.",
"Content": "Investment Analysts: Favor short- and medium-term government bonds due to yields near 4% and sticky inflation limiting Federal Reserve rate cuts; caution advised on long-term bonds.",
"Content": "Investment Analysts: Recommend overweighting U.S. agency mortgage-backed securities (MBS) due to wider spreads than historical averages.",
"Content": "Investment Analysts: Highlight that approximately 80% of global fixed income assets now offer yields above 4%, making credit, mortgage-backed securities, and emerging market debt more attractive.",
"Content": "Investment Analysts: Upped local currency emerging market (EM) debt to neutral, citing improved debt levels and resilience to U.S. trade policy shifts.",
"Content": "S&P 500: Hit new record highs last week, driven by strong U.S. retail sales data indicating U.S. economic resilience.",
"Content": "Market Participants: Looking for signals from the ECB regarding potential easing measures later this year, as inflation remains around the 2% target and euro area growth shows little change.",
"Content": "Markets: Pricing in multiple Federal Reserve rate cuts over the next year, yet sticky inflation limits rate cuts.",
"Content": "Higher U.S. policy rates: Mean interest rate differentials between the U.S. and other countries stay wide, revealing an array of global fixed income opportunities.",
"Content": "Trade Tensions: Could cool foreign demand for U.S. debt, which is crucial for sustaining its issuance, as noted in 2025 Midyear Outlook.",
"Content": "Japan: 30-year yields recently hit a record high amid discussions of tax cuts before elections, indicating global fiscal sustainability concerns.",
"Content": "Preference for European Fixed Income: Based on a more stable fiscal outlook, particularly favoring European bank debt due to strong financial earnings and insulation from tariff impacts."'''

    def render_panel_with_word_count(title: str, text: str):
        # 按空白符切分，过滤空字符串
        word_count = len([w for w in text.split() if w.strip()])
        st.markdown(
            f"""
            <div style="border:1px solid #E6E8EB;border-radius:1rem;padding:1rem 1.2rem;margin-bottom:1rem;background:#ffffff">
                <div style="border:2px solid #D0D7DE;border-radius:.8rem;padding:.5rem 1rem;margin-bottom:.9rem;
                            text-align:center;font-weight:800;font-size:1.05rem;">
                    {title}
                </div>
                <div style="white-space:pre-wrap;line-height:1.65;font-size:1rem;color:#222">
                    {text if text.strip() else "<span style='color:#999'>（空）</span>"}
                </div>
                <div style="margin-top:.6rem;color:#555;font-size:0.9rem;">
                    Word Count：<b>{word_count}</b> words
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    render_panel_with_word_count("Original Text", ORIGINAL_TEXT)
    render_panel_with_word_count("Summary", SUMMARY_TEXT)