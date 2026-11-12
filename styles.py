"""Vizuelni stil FinNews-a: urednički 'večernje izdanje' - topla crna, krem tekst,
narandžasti i zlatni akcenti, serif naslovi kao u finansijskim dnevnim novinama."""
import hashlib

PALETTE = ["#C2435F", "#D6B072", "#C99A7A", "#9CC79A", "#E07C8A", "#B9A0C9", "#8FB8B0", "#D99A80"]
CAT_ICON = {"Vesti": "◆", "Centralne banke i makro": "🏛", "Analize i blogovi": "✎",
            "Srbija i region": "🇷🇸", "Istraživanja": "🔬",
            "Srbija": "🇷🇸", "Svet": "🌍", "Kompanije": "🏢"}


def src_color(name):
    return PALETTE[int(hashlib.md5((name or "").encode()).hexdigest(), 16) % len(PALETTE)]


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');
:root { --bg:#0B0909; --panel:#141011; --panel2:#1B1517; --line:#2C2124; --line2:#3E2E33; --text:#F5ECE4;
        --muted:#A8979A; --accent:#C2435F; --gold:#D6B072; --sky:#C99A7A; }
html, body, .stMarkdown, p, label, input, textarea, button { font-family: 'Inter', system-ui, sans-serif; }
.stApp { background: radial-gradient(1100px 420px at 100% -5%, rgba(150,30,58,.10), transparent 60%),
                     radial-gradient(800px 380px at -5% 0%, rgba(214,176,114,.06), transparent 60%), var(--bg); }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.4rem; max-width: 1120px; }
h1, h2, h3 { font-family: 'Fraunces', Georgia, serif !important; letter-spacing: -.01em; }

/* bočni meni */
section[data-testid="stSidebar"] { background: #121110; border-right: 1px solid var(--line); }
.fn-logo { font-family:'Fraunces'; font-size: 1.75rem; font-weight: 700; letter-spacing:-.02em; margin-bottom:.3rem }
.fn-logo span { color: var(--accent); font-style: italic; }

/* zaglavlje */
.fn-head { display:flex; justify-content:space-between; align-items:flex-end; gap:20px; flex-wrap:wrap;
           padding: 4px 2px 18px; border-bottom: 1px solid var(--line); margin-bottom: 14px; }
.fn-kicker { color: var(--gold); font-size:.74rem; font-weight:600; text-transform:uppercase; letter-spacing:.16em; }
.fn-h1 { font-family:'Fraunces'; font-size: 2.6rem; font-weight:700; margin: 2px 0 0; letter-spacing:-.02em; line-height:1.05 }
.fn-h1 span { color: var(--accent); font-style: italic; }
.fn-sub { color: var(--muted); font-size: .92rem; margin-top: 4px; }
.fn-kpis { display:flex; gap:10px; flex-wrap:wrap; }
.fn-kpi { background: var(--panel); border:1px solid var(--line); border-radius: 12px; padding: 9px 14px; min-width: 104px; }
.fn-kpi b { display:block; font-family:'JetBrains Mono'; font-size: 1.25rem; color: var(--text); }
.fn-kpi span { color: var(--muted); font-size: .7rem; text-transform: uppercase; letter-spacing:.08em; }

/* navigacija (segmented control) */
[class*="st-key-nav"] button { border-radius: 999px !important; }
[data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[kind="segmented_controlActive"] {
     background: rgba(150,30,58,.15) !important; border-color: rgba(150,30,58,.6) !important; color: var(--text) !important; }

/* kartice */
[class*="st-key-card_"], [class*="st-key-hero_"] { background: var(--panel); border: 1px solid var(--line) !important;
     border-radius: 14px !important; padding: 16px 20px 12px !important; transition: border-color .15s ease; }
[class*="st-key-card_"]:hover { border-color: var(--line2) !important; }
[class*="st-key-hero_"] { background: linear-gradient(135deg, rgba(150,30,58,.12), rgba(214,176,114,.05) 55%, var(--panel)) !important;
     border: 1px solid rgba(150,30,58,.45) !important; padding: 22px 24px 14px !important; }
.fn-meta { display:flex; flex-wrap:wrap; gap:8px; align-items:center; font-size:.75rem; color: var(--muted); }
.fn-src { color: var(--c); background: color-mix(in srgb, var(--c) 12%, transparent);
     border: 1px solid color-mix(in srgb, var(--c) 32%, transparent); padding: 2px 9px; border-radius: 999px; font-weight:600; }
.fn-pill { border:1px solid var(--line2); padding: 2px 9px; border-radius: 999px; }
.fn-imp { font-family:'JetBrains Mono'; color: var(--gold); }
.fn-dots { letter-spacing: 2px; color: var(--gold); }
.fn-dots i { font-style: normal; color: var(--line2); }
.fn-more { color: var(--sky); font-weight:600; }
.fn-cite { font-family:'JetBrains Mono'; color: var(--sky); font-weight:600; }
.fn-badge { color:#0B0909; background: var(--accent); padding: 2px 9px; border-radius: 999px; font-weight:700;
     letter-spacing:.08em; text-transform:uppercase; font-size:.66rem }
a.fn-title { display:block; color: var(--text) !important; text-decoration:none !important; font-family:'Fraunces', Georgia, serif;
     font-weight:600; font-size: 1.2rem; line-height: 1.3; margin-top: 8px; }
[class*="st-key-hero_"] a.fn-title { font-size: 1.7rem; }
a.fn-title:hover { color: var(--accent) !important; }
.fn-sum { color: #D2C3BB; font-size: .92rem; line-height: 1.6; margin: 6px 0 0; }
.fn-why { color: #E7DBD2; font-size: .92rem; line-height:1.6; border-left: 3px solid var(--gold); padding: 2px 0 2px 12px; margin-top: 6px; }

/* red sa akcijama u kartici - odvojen, bez preklapanja */
[class*="st-key-act_"] { border-top: 1px solid var(--line); padding-top: 10px; margin-top: 4px; gap: 8px; }
[class*="st-key-act_"] button { border-radius: 999px !important; border: 1px solid var(--line2) !important;
     background: transparent !important; color: var(--muted) !important; padding: 2px 14px !important;
     min-height: 30px !important; font-size: .82rem !important; }
[class*="st-key-act_"] button:hover { border-color: var(--accent) !important; color: var(--text) !important; }

/* dugmići */
.stButton > button, .stDownloadButton > button, .stLinkButton > a { border-radius: 999px; }
.stButton > button[kind="primary"] { background: var(--accent); color:#0B0909; border:none; font-weight:600; }
.stButton > button[kind="primary"]:hover { background: #D0627A; color:#0B0909; }
[data-testid="stExpander"] { border: 1px solid var(--line); border-radius: 12px; background: var(--panel); }
.fn-section { font-family:'Fraunces'; font-size:1.3rem; font-weight:600; margin: 22px 0 10px; }
.fn-section:after { content:''; display:block; width:44px; height:3px; background: var(--accent); border-radius: 2px; margin-top:6px }

/* čitač */
div[role="dialog"] { background: #141210 !important; border: 1px solid var(--line2); border-radius: 18px !important; }
.fn-read-title { font-family:'Fraunces'; font-size: 1.85rem; font-weight: 700; line-height: 1.2; margin: 10px 0 16px; }
.fn-read-box { background: var(--panel2); border: 1px solid var(--line); border-left: 4px solid var(--accent);
     border-radius: 12px; padding: 14px 18px 4px; margin-bottom: 10px; }
.fn-alt { color: var(--sky); font-size: .82rem; margin: 4px 0 10px; }
.fn-article { max-width: 70ch; font-family: 'Fraunces', Georgia, serif; font-size: 1.08rem; line-height: 1.8; color: #E9E2D7; }
.fn-article p { margin: 0 0 1.05em; }
</style>
"""

CSS += """
<style>
.fn-trends { display:grid; gap:8px; margin-bottom: 8px; }
.fn-trend { display:grid; grid-template-columns: minmax(180px, 2.2fr) 3fr 70px 70px; gap: 12px; align-items:center; font-size:.88rem; }
.fn-trend-bar { height: 8px; background: #2C2124; border-radius: 6px; overflow:hidden }
.fn-trend-bar i { display:block; height:100%; background: linear-gradient(90deg, #C2435F, #D6B072); border-radius: 6px }
.fn-trend b { font-family:'JetBrains Mono'; text-align:right; }
.fn-trend em { font-style:normal; font-family:'JetBrains Mono'; font-size:.8rem; text-align:right }
.fn-trend em.up { color:#9CC79A } .fn-trend em.down { color:#E07C8A }
a.fn-gap-src { color:#A8979A !important; font-size:.76rem; text-decoration:none }
.fn-why { margin-bottom: 8px; }
@media (max-width: 700px) { .fn-trend { grid-template-columns: 1fr 60px 60px; } .fn-trend-bar { display:none } }
</style>
"""

CSS += """
<style>
.fn-finding { font-family:'Fraunces', Georgia, serif; font-size: 1.12rem; line-height: 1.55; color: #F5ECE4; margin: 10px 0 6px; }
.fn-finding span { display:inline-block; font-family:'Inter'; font-size:.66rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase;
     color:#0B0909; background:#D6B072; border-radius: 999px; padding: 2px 8px; margin-right: 10px; vertical-align: 3px; }
a.fn-title.fn-small { font-family:'Inter'; font-size: .86rem; font-weight: 500; color: #A8979A !important; margin-top: 2px; }
</style>
"""

CSS += """
<style>
.fn-chips { display:flex; flex-wrap:wrap; gap:8px; margin-bottom: 6px; }
.fn-chip { background:#1B1517; border:1px solid #3E2E33; border-radius:999px; padding:5px 12px; font-size:.84rem; color:#F5ECE4; }
.fn-chip b { font-family:'JetBrains Mono'; color:#D6B072; margin-left:4px; }
.fn-chip-muted { color:#A8979A; background: transparent; }
.fn-rows { background:#141011; border:1px solid #2C2124; border-radius:14px; overflow:hidden; }
.fn-row { display:grid; grid-template-columns: 56px 150px 1fr 70px; gap: 12px; align-items:center; padding: 10px 16px;
          border-bottom: 1px solid #2C2124; font-size:.9rem; }
.fn-row:last-child { border-bottom: none; }
.fn-row:hover { background:#1B1517; }
.fn-row-time { font-family:'JetBrains Mono'; color:#A8979A; font-size:.78rem; }
.fn-row .fn-src { font-size:.72rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; text-align:center; }
a.fn-row-title { color:#F5ECE4 !important; text-decoration:none !important; line-height:1.35; }
a.fn-row-title:hover { color:#C2435F !important; }
.fn-row .fn-dots { text-align:right; font-size:.7rem; }
@media (max-width: 760px) { .fn-row { grid-template-columns: 48px 1fr; } .fn-row .fn-src, .fn-row .fn-dots { display:none } }
/* AI tekstovi (brief, pregledi) */
[class*="st-key-briefmd"] h2, [class*="st-key-briefmd"] h3 { font-family:'Fraunces' !important; font-size:1.2rem !important;
     border-top:1px solid #2C2124; padding-top:14px !important; margin-top:10px !important; }
[class*="st-key-briefmd"] h2:first-of-type { border-top:none; }
[class*="st-key-briefmd"] li { margin-bottom:6px; line-height:1.6; color:#E7DBD2; }
[class*="st-key-briefmd"] a { color:#D6B072 !important; text-decoration:none; font-size:.85em; }
</style>
"""

CSS += """
<style>
/* bez bočnog menija */
section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] { display:none !important; }
.block-container { padding-top: 1.2rem !important; }
.fn-h1 { font-size: 2.4rem; margin-top: 0; }

/* kontrole u zaglavlju */
[class*="st-key-hdr_ctrl"] { gap: 10px; }
[class*="st-key-hdr_ctrl"] [data-testid="stButtonGroup"] button { min-height: 32px; padding: 0 14px; border-radius: 999px !important;
     font-weight: 600; font-size: .8rem; letter-spacing: .08em; }
[class*="st-key-refresh_btn"] button { width: 36px; height: 36px; min-height: 36px; padding: 0; border-radius: 50% !important;
     font-size: 1.05rem; border: 1px solid #3E2E33; }
[class*="st-key-refresh_btn"] button:hover { border-color: #C2435F; color: #C2435F; }
[class*="st-key-orig"] label p { font-size: .82rem; color: #A8979A; }

/* brojači - tanka traka ispod logoa */
.fn-kpis { display:flex; gap: 0; margin: 14px 0 0; border-top: 1px solid #2C2124; border-bottom: 1px solid #2C2124; }
.fn-kpi { background: transparent; border: none; border-right: 1px solid #2C2124; border-radius: 0; padding: 10px 18px; min-width: 0; flex: 1; }
.fn-kpi:last-child { border-right: none; }
.fn-kpi b { font-size: 1.1rem; }
.fn-kpi span { font-size: .66rem; }

/* glavni meni - kao rubrike u novinama */
[class*="st-key-nav"] { margin: 4px 0 18px; border-bottom: 1px solid #2C2124; }
[class*="st-key-nav"] [role="radiogroup"] { gap: 2px 22px; flex-wrap: wrap; }
[class*="st-key-nav"] [data-testid="stRadioOption"] > div > div:first-child:not([data-testid]) { display: none !important; }
[class*="st-key-nav"] [role="radiogroup"] label { padding: 12px 0 10px; margin: 0; border-bottom: 2px solid transparent; cursor: pointer; }
[class*="st-key-nav"] [role="radiogroup"] label > div:first-child { display: none; }
[class*="st-key-nav"] [role="radiogroup"] label p { font-family: 'Inter'; font-size: .76rem; font-weight: 600; letter-spacing: .09em; white-space: nowrap;
     text-transform: uppercase; color: #A8979A; }
[class*="st-key-nav"] [role="radiogroup"] label:hover p { color: #F5ECE4; }
[class*="st-key-nav"] [role="radiogroup"] label[data-selected="true"], [class*="st-key-nav"] [role="radiogroup"] label:has(input:checked) { border-bottom-color: #C2435F; }
[class*="st-key-nav"] [role="radiogroup"] label[data-selected="true"] p, [class*="st-key-nav"] [role="radiogroup"] label:has(input:checked) p { color: #F5ECE4; }

/* analiza rada bez AI */
.fn-an { display:grid; grid-template-columns: 140px 1fr; gap: 12px; padding: 8px 0; border-top: 1px solid #2C2124; font-size: .92rem; }
.fn-an:first-of-type { border-top: none; }
.fn-an b { color: #D6B072; font-weight: 600; }
.fn-an span { color: #E7DBD2; line-height: 1.55; }
/* mapa praznina */
.fn-heat { overflow-x: auto; }
.fn-heat table { border-collapse: separate; border-spacing: 4px; font-size: .82rem; width: 100%; }
.fn-heat th { color: #A8979A; font-weight: 600; text-align: left; padding: 4px 6px; }
.fn-heat tr:first-child th { text-align: center; font-size: .74rem; }
.fn-heat td { text-align: center; padding: 10px 6px; border-radius: 8px; font-family: 'JetBrains Mono';
     background: rgba(150,30,58,var(--a)); color: #F5ECE4; }
.fn-heat td.gap { outline: 2px solid #D6B072; outline-offset: -2px; }
div.fn-title { font-family:'Fraunces'; font-weight:600; font-size:1.2rem; margin-top:8px; }
</style>
"""

CSS += """
<style>
.fn-disclaimer { background:#1B1517; border:1px solid #3E2E33; border-left:4px solid #D6B072; border-radius:12px;
     padding:12px 16px; font-size:.86rem; color:#D2C3BB; line-height:1.55; margin: 6px 0 12px; }
.fn-pick { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; }
.fn-tk { font-family:'JetBrains Mono'; font-size:.8rem; color:#A8979A; font-weight:500; margin-left:6px; }
.fn-score { text-align:center; min-width:72px; padding:8px 10px; border-radius:12px; background:rgba(150,30,58,.12);
     border:1px solid rgba(150,30,58,.45); }
.fn-score b { display:block; font-family:'JetBrains Mono'; font-size:1.6rem; color:#C2435F; line-height:1.1; }
.fn-score span { font-size:.66rem; text-transform:uppercase; letter-spacing:.1em; color:#A8979A; }
.fn-fbars { display:grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap:6px 18px; margin-top:12px; }
.fn-fbar { display:grid; grid-template-columns: 1fr 90px; gap:10px; align-items:center; font-size:.76rem; color:#A8979A; }
.fn-fbar > div { height:6px; background:#2C2124; border-radius:4px; overflow:hidden; }
.fn-fbar i { display:block; height:100%; background: linear-gradient(90deg, #C2435F, #D6B072); }
[data-testid="stPills"] button { border-radius:999px !important; }
</style>
"""

CSS += """
<style>
.fn-ind { display:grid; grid-template-columns: 1fr 210px; gap:18px; align-items:center; }
.fn-ind-name { font-family:'Fraunces'; font-weight:600; font-size:1.08rem; }
.fn-ind-val { text-align:right; }
.fn-ind-val b { display:block; font-family:'JetBrains Mono'; font-size:1.35rem; color:#F5ECE4; }
.fn-ind-val span { display:block; font-size:.72rem; color:#A8979A; margin-top:3px; }
.fn-g { display:inline-block !important; font-size:.66rem !important; font-weight:700; text-transform:uppercase; letter-spacing:.08em;
     padding:2px 9px; border-radius:999px; margin-top:4px; }
.fn-g-good { background:rgba(156,199,154,.15); color:#9CC79A !important; border:1px solid rgba(156,199,154,.4); }
.fn-g-mid { background:rgba(214,176,114,.13); color:#D6B072 !important; border:1px solid rgba(214,176,114,.4); }
.fn-g-bad { background:rgba(224,124,138,.13); color:#E07C8A !important; border:1px solid rgba(224,124,138,.4); }
.fn-chip.fn-g-good b { color:#9CC79A } .fn-chip.fn-g-mid b { color:#D6B072 } .fn-chip.fn-g-bad b { color:#E07C8A }
[class*="st-key-card_ind_"] [data-testid="stExpander"] { border:none; background:transparent; }
[class*="st-key-card_ind_"] [data-testid="stExpander"] summary p { font-size:.82rem; color:#A8979A; }
@media (max-width: 700px) { .fn-ind { grid-template-columns: 1fr; } .fn-ind-val { text-align:left; } }
</style>
"""

CSS += """
<style>
.fn-rows .fn-an { grid-template-columns: minmax(220px, 300px) 1fr; padding: 10px 16px; border-top: 1px solid #2C2124; }
.fn-rows .fn-an:first-child { border-top: none; }
.fn-rows .fn-an span { font-family: 'JetBrains Mono', monospace; }
@media (max-width: 700px) { .fn-rows .fn-an { grid-template-columns: 1fr; gap: 2px; } }
</style>
"""

CSS += """
<style>
.fn-kpis-big .fn-kpi b { font-size: 1.3rem; }
.fn-kpis-big .fn-kpi b.fn-up { color: #9CC79A; }
.fn-kpis-big .fn-kpi b.fn-down { color: #E07C8A; }
[data-testid="stForm"] { border: 1px solid #2C2124 !important; border-radius: 14px !important; background: #141011; }
</style>
"""

CSS += """
<style>
.fn-alloc { display:flex; height:14px; border-radius:8px; overflow:hidden; gap:2px; margin-top:6px; }
.fn-alloc i { display:block; height:100%; }
</style>
"""

# ---------- v3: napredniji izgled + telefon ----------
CSS += """
<style>
.block-container { max-width: 1180px; }
.stApp { background: radial-gradient(1200px 520px at 105% -10%, rgba(150,30,58,.13), transparent 62%),
                     radial-gradient(900px 460px at -10% -5%, rgba(214,176,114,.07), transparent 60%),
                     radial-gradient(700px 500px at 50% 115%, rgba(201,154,122,.05), transparent 60%), #0B0909; background-attachment: fixed; }
.fn-h1 { background: linear-gradient(92deg, #F5ECE4 30%, #D6B072 130%); -webkit-background-clip: text; background-clip: text; color: transparent; }
.fn-h1 span { -webkit-text-fill-color: #C2435F; }

/* traka tržišta */
.fn-ticker { display:flex; gap:0; margin: 14px 0 0; border:1px solid #2C2124; border-radius: 14px; overflow-x:auto; scrollbar-width:none;
     background: linear-gradient(180deg, rgba(27,21,23,.9), rgba(20,16,17,.9)); backdrop-filter: blur(8px); }
.fn-ticker::-webkit-scrollbar { display:none }
.fn-tk-i { flex: 1 0 auto; padding: 10px 16px 9px; border-right: 1px solid #2C2124; min-width: 104px; }
.fn-tk-i:last-child { border-right: none; }
.fn-tk-i span { display:block; color:#A8979A; font-size:.64rem; text-transform:uppercase; letter-spacing:.1em; white-space:nowrap; }
.fn-tk-i b { display:block; font-family:'JetBrains Mono'; font-size:.98rem; color:#F5ECE4; margin-top:2px; white-space:nowrap; }
.fn-tk-i i { font-style:normal; font-family:'JetBrains Mono'; font-size:.7rem; white-space:nowrap; }
.fn-tk-i i.fn-up, .fn-up { color:#9CC79A; } .fn-tk-i i.fn-down, .fn-down { color:#E07C8A; }
.fn-tk-meta b { color:#D6B072; }

/* kartice: dubina i pokret */
[class*="st-key-card_"], [class*="st-key-hero_"] { box-shadow: 0 1px 0 rgba(255,255,255,.03) inset, 0 8px 24px -18px rgba(0,0,0,.9);
     transition: border-color .18s ease, transform .18s ease, box-shadow .18s ease; height: 100%; }
[class*="st-key-card_"]:hover { transform: translateY(-2px); border-color: rgba(150,30,58,.38) !important;
     box-shadow: 0 1px 0 rgba(255,255,255,.04) inset, 0 16px 34px -20px rgba(150,30,58,.35); }
[class*="st-key-hero_"] .fn-title, [class*="st-key-hero_"] .fn-title a { font-size: 1.7rem; line-height: 1.18; }
[class*="st-key-hero_"] .fn-sum { font-size: 1rem; }
.fn-full { color:#9CC79A; border:1px solid rgba(156,199,154,.35); background: rgba(156,199,154,.08); padding: 2px 9px; border-radius:999px; font-weight:600; }
.fn-alt { color:#A8979A; font-size:.82rem; margin: 6px 0 10px; }
[class*="st-key-readbox_"] { background: linear-gradient(135deg, rgba(214,176,114,.09), rgba(150,30,58,.04)); border:1px solid rgba(214,176,114,.28);
     border-radius: 14px; padding: 16px 20px 8px; margin: 12px 0 6px; }
[class*="st-key-readbox_"] .fn-read-box { all: unset; display:block; }
[class*="st-key-readbox_"] li { font-size: .96rem; line-height: 1.55; margin-bottom: 6px; }
.fn-article { font-size: 1.04rem; line-height: 1.75; max-width: 74ch; margin: 6px auto 0; }
.fn-article p { margin: 0 0 1.05em; }

/* filteri */
[data-testid="stExpander"] details { border: 1px solid #2C2124 !important; border-radius: 12px !important; background: rgba(20,16,17,.6); }
[data-testid="stExpander"] summary p { font-size: .84rem; font-weight: 600; letter-spacing: .02em; }
[data-testid="stPills"] button, [data-testid="stButtonGroup"] button { border-radius: 999px !important; }
div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input, .stDateInput input { background: #141011 !important; border-color: #2C2124 !important; border-radius: 10px !important; }
.stTextInput input:focus { border-color: rgba(150,30,58,.6) !important; }
button[kind="primary"] { background: linear-gradient(135deg, #C2435F, #9E2A45) !important; border: none !important; color: #F5ECE4 !important; font-weight: 600 !important; }

/* zaključani deo, o aplikaciji */
.fn-lock { text-align:center; padding: 46px 20px 8px; max-width: 520px; margin: 0 auto; }
.fn-lock-ic { font-size: 2.2rem; margin-bottom: 8px; }
.fn-about-hero { padding: 26px 28px 18px; margin: 4px 0 16px; border:1px solid rgba(150,30,58,.35); border-radius: 18px;
     background: linear-gradient(135deg, rgba(150,30,58,.13), rgba(214,176,114,.05) 55%, #141011); }
.fn-about-hero .fn-sum { max-width: 78ch; font-size: 1rem; }
.fn-flow { display:grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.fn-flow-s { display:flex; gap: 12px; background:#141011; border:1px solid #2C2124; border-radius: 14px; padding: 14px 16px 6px; }
.fn-flow-s > b { font-family:'Fraunces'; font-size: 1.7rem; color:#C2435F; line-height: 1; font-style: italic; }
.fn-flow-s .fn-sum { font-size: .86rem; margin-top: 4px; }
.fn-srcgrid { display:grid; grid-template-columns: repeat(2, 1fr); gap: 6px 28px; }
.fn-srcgrid .fn-sum { font-size: .86rem; margin-top: 4px; }
.katex { color: #F5ECE4; font-size: 1.02em; }
[data-testid="stDataFrame"] { border: 1px solid #2C2124; border-radius: 12px; overflow: hidden; }

/* ---------- telefon i tablet ---------- */
@media (max-width: 900px) { .fn-flow { grid-template-columns: 1fr 1fr; } }
@media (max-width: 640px) {
  .block-container { padding: .7rem .8rem 4rem !important; }
  .fn-h1 { font-size: 1.9rem; } .fn-kicker { font-size: .66rem; letter-spacing: .12em; }
  [class*="st-key-hdr_ctrl"] { justify-content: flex-start !important; margin-top: 2px; }
  [class*="st-key-fbar_"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 6px 10px !important; }
  [class*="st-key-fbar_"] [data-testid="stColumn"] { min-width: 0 !important; flex: 1 1 40% !important; width: auto !important; }
  [class*="st-key-fbar_"] [data-testid="stColumn"]:first-child { flex: 1 1 100% !important; }
  [class*="st-key-fbar_"] label { display: none !important; }
  .fn-ticker { margin: 8px -0.8rem 0; border-radius: 0; border-left: none; border-right: none; }
  .fn-tk-i { padding: 8px 13px 7px; min-width: 92px; }
  /* meni: jedan red koji se prevlači prstom, zalepljen za vrh */
  [class*="st-key-nav"] { position: sticky; top: 0; z-index: 50; margin: 0 -0.8rem 12px; padding: 0 .8rem;
       background: rgba(11,9,9,.92); backdrop-filter: blur(10px); }
  [class*="st-key-nav"] [role="radiogroup"] { flex-wrap: nowrap !important; overflow-x: auto; gap: 0 18px; scrollbar-width: none; -webkit-overflow-scrolling: touch; }
  [class*="st-key-nav"] [role="radiogroup"]::-webkit-scrollbar { display: none; }
  [class*="st-key-nav"] [role="radiogroup"] label { flex: 0 0 auto; padding: 13px 0 11px; }
  [class*="st-key-nav"] [role="radiogroup"] label p { font-size: .74rem; }
  [data-testid="stButtonGroup"] { flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; }
  [data-testid="stPills"] > div, [data-testid="stPills"] [data-testid="stButtonGroup"] { flex-wrap: nowrap !important; overflow-x: auto; scrollbar-width: none; }
  [class*="st-key-card_"], [class*="st-key-hero_"] { padding: 14px 15px 10px !important; border-radius: 13px !important; }
  [class*="st-key-card_"]:hover { transform: none; }
  [class*="st-key-hero_"] .fn-title, [class*="st-key-hero_"] .fn-title a { font-size: 1.3rem; }
  .fn-title, .fn-title a { font-size: 1.05rem; }
  .fn-sum { font-size: .9rem; }
  .fn-read-title { font-size: 1.45rem !important; line-height: 1.2; }
  .fn-article { font-size: 1.02rem; line-height: 1.7; }
  .fn-kpis, .fn-kpis-big { display: grid !important; grid-template-columns: 1fr 1fr; }
  .fn-kpis .fn-kpi { border-right: none !important; padding: 10px 6px; }
  .fn-flow, .fn-srcgrid, .fn-fbars { grid-template-columns: 1fr !important; }
  .fn-pick { grid-template-columns: 1fr !important; } .fn-score { text-align: left !important; }
  .fn-about-hero { padding: 18px 16px 10px; }
  div[role="dialog"] { width: 100vw !important; max-width: 100vw !important; margin: 0 !important; border-radius: 16px 16px 0 0 !important; max-height: 96vh; }
  div[role="dialog"] > div { padding-left: .9rem !important; padding-right: .9rem !important; }
  button, [data-testid="stBaseButton-secondary"] { min-height: 40px; }
  .stTextInput input, .stNumberInput input, div[data-baseweb="select"] input { font-size: 16px !important; } /* iOS ne zumira polje */
}
</style>
"""

# ---------- v4: crna + burgundy, animacije ----------
CSS += """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,600;1,700&display=swap');
:root { --bg:#0B0909; --panel:#141011; --panel2:#1B1517; --line:#2C2124; --line2:#3E2E33; --text:#F5ECE4; --muted:#A8979A;
        --accent:#C2435F; --wine:#7A1A33; --wine2:#4A0E1F; --gold:#D6B072; --copper:#C99A7A; --up:#9CC79A; --down:#E07C8A;
        --ease: cubic-bezier(.2,.7,.2,1); }
.stApp { background:
   radial-gradient(1100px 560px at 108% -12%, rgba(150,30,58,.32), transparent 62%),
   radial-gradient(900px 520px at -12% -8%, rgba(122,26,51,.20), transparent 60%),
   radial-gradient(800px 600px at 50% 120%, rgba(214,176,114,.06), transparent 60%), #0B0909 !important; background-attachment: fixed !important; }
h1, h2, h3, .fn-h1, .fn-title, .fn-read-title, .fn-section { font-family: 'Playfair Display', 'Fraunces', Georgia, serif !important; }
.fn-h1 { font-weight: 700; letter-spacing: -.015em; background: linear-gradient(100deg, #F5ECE4 0%, #F5ECE4 40%, #E9D3B0 50%, #F5ECE4 60%, #F5ECE4 100%);
         background-size: 250% 100%; -webkit-background-clip: text; background-clip: text; color: transparent; animation: fnSheen 9s ease-in-out infinite; }
.fn-h1 span { -webkit-text-fill-color: var(--accent); font-style: italic; }
.fn-kicker { color: var(--gold); }
.fn-section { position: relative; }
.fn-section::after { background: linear-gradient(90deg, var(--accent), var(--gold)) !important; }

/* kartice */
[class*="st-key-card_"], [class*="st-key-hero_"] { background: linear-gradient(180deg, rgba(27,21,23,.92), rgba(20,16,17,.92)) !important;
     border: 1px solid #2C2124 !important; animation: fnUp .55s var(--ease) both; }
[class*="st-key-card_"]:hover { border-color: rgba(194,67,95,.55) !important; box-shadow: 0 18px 40px -24px rgba(194,67,95,.55) !important; }
[class*="st-key-hero_"] { background: linear-gradient(120deg, rgba(122,26,51,.55), rgba(74,14,31,.35) 45%, rgba(20,16,17,.95) 80%) !important;
     background-size: 180% 180% !important; animation: fnUp .55s var(--ease) both, fnShift 14s ease-in-out infinite !important;
     border: 1px solid rgba(194,67,95,.55) !important; }
[data-testid="stColumn"]:nth-child(2) [class*="st-key-card_"] { animation-delay: .08s; }
.fn-badge { background: linear-gradient(135deg, var(--accent), var(--wine)) !important; color: #F5ECE4 !important; }
.fn-rows .fn-row { animation: fnUp .45s var(--ease) both; }
.fn-rows .fn-row:nth-child(2) { animation-delay: .04s } .fn-rows .fn-row:nth-child(3) { animation-delay: .08s }
.fn-rows .fn-row:nth-child(4) { animation-delay: .12s } .fn-rows .fn-row:nth-child(5) { animation-delay: .16s }
.fn-rows .fn-row:nth-child(n+6) { animation-delay: .2s }
.fn-fbar i, .fn-alloc i { transform-origin: left center; animation: fnGrow .9s var(--ease) both; }
.fn-kpi, .fn-tk-i { animation: fnFade .6s var(--ease) both; }
.fn-tk-i:nth-child(2){animation-delay:.03s} .fn-tk-i:nth-child(3){animation-delay:.06s} .fn-tk-i:nth-child(4){animation-delay:.09s}
.fn-tk-i:nth-child(5){animation-delay:.12s} .fn-tk-i:nth-child(6){animation-delay:.15s} .fn-tk-i:nth-child(n+7){animation-delay:.18s}
.fn-ticker { background: linear-gradient(180deg, rgba(27,21,23,.85), rgba(20,16,17,.85)) !important; border-color: #2C2124 !important; position: relative; }
.fn-ticker::before { content:""; position:absolute; inset:0; pointer-events:none; border-radius: inherit;
     background: linear-gradient(100deg, transparent 30%, rgba(214,176,114,.07) 50%, transparent 70%); background-size: 250% 100%; animation: fnSheen 7s linear infinite; }
.fn-live { display:inline-block; width:7px; height:7px; border-radius:50%; background: var(--up); margin-right:6px; vertical-align: middle;
     box-shadow: 0 0 0 0 rgba(156,199,154,.6); animation: fnPulse 2.2s infinite; }

/* meni */
[class*="st-key-nav"] [role="radiogroup"] label { transition: border-color .25s var(--ease); }
[class*="st-key-nav"] [role="radiogroup"] label p { transition: color .2s ease; }
[class*="st-key-nav"] [role="radiogroup"] label:has(input:checked) { border-bottom-color: var(--accent) !important; }

/* dugmad i kontrole */
.stButton button, [data-testid="stBaseButton-secondary"] { transition: transform .12s ease, border-color .2s ease, background .2s ease, box-shadow .2s ease; }
.stButton button:hover { border-color: rgba(194,67,95,.7) !important; color: #F5ECE4 !important; box-shadow: 0 6px 18px -10px rgba(194,67,95,.8); }
.stButton button:active { transform: scale(.97); }
button[kind="primary"] { background: linear-gradient(135deg, #A8304B, #6E1630) !important; box-shadow: 0 10px 24px -14px rgba(194,67,95,.9); }
[data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[kind="segmented_controlActive"],
[data-testid="stButtonGroup"] button[kind="pillsActive"] {
     background: linear-gradient(135deg, rgba(194,67,95,.35), rgba(122,26,51,.35)) !important; border-color: rgba(194,67,95,.75) !important; color: #F5ECE4 !important; }
[class*="st-key-refresh_btn"] button:hover { border-color: var(--accent) !important; color: var(--accent) !important; }
[class*="st-key-refresh_btn"] button:hover p { display:inline-block; animation: fnSpin .8s var(--ease); }
div[role="dialog"] { animation: fnDialog .35s var(--ease) both; border: 1px solid #3E2E33; background: #110D0E !important; }
[data-testid="stSpinner"] i, [data-testid="stSpinner"] svg { color: var(--accent) !important; border-top-color: var(--accent) !important; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--accent) !important; }
.stTabs [aria-selected="true"] p { color: #F5ECE4 !important; }
a { color: inherit; }
::selection { background: rgba(194,67,95,.45); }

/* početna */
.fn-home-grid { display:grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 4px 0 6px; }
.fn-stat { background: linear-gradient(180deg, rgba(27,21,23,.92), rgba(20,16,17,.92)); border: 1px solid #2C2124; border-radius: 16px; padding: 16px 18px;
     animation: fnUp .5s var(--ease) both; position: relative; overflow: hidden; }
.fn-stat::after { content:""; position:absolute; right:-40px; top:-40px; width:120px; height:120px; border-radius:50%;
     background: radial-gradient(circle, rgba(194,67,95,.22), transparent 70%); }
.fn-stat span { color: var(--muted); font-size:.68rem; text-transform: uppercase; letter-spacing: .12em; }
.fn-stat b { display:block; font-family:'JetBrains Mono'; font-size: 1.45rem; margin-top: 6px; color: #F5ECE4; }
.fn-stat i { font-style: normal; font-family:'JetBrains Mono'; font-size: .8rem; }
.fn-stat:nth-child(2){animation-delay:.05s} .fn-stat:nth-child(3){animation-delay:.1s} .fn-stat:nth-child(4){animation-delay:.15s}
.fn-bullets { list-style: none; padding: 0; margin: 4px 0 0; }
.fn-bullets li { position: relative; padding: 9px 0 9px 22px; border-bottom: 1px solid #2C2124; line-height: 1.5; animation: fnUp .45s var(--ease) both; }
.fn-bullets li:last-child { border-bottom: none; }
.fn-bullets li::before { content:""; position:absolute; left:2px; top: 17px; width:8px; height:8px; border-radius: 2px; transform: rotate(45deg);
     background: linear-gradient(135deg, var(--accent), var(--gold)); }
.fn-bullets li small { color: var(--muted); font-size: .76rem; margin-left: 6px; }
.fn-bullets li a { color: #F5ECE4 !important; text-decoration: none; border-bottom: 1px solid transparent; transition: border-color .2s; }
.fn-bullets li a:hover { border-bottom-color: var(--accent); color: #fff !important; }
.fn-bullets li small a { color: var(--muted) !important; }
.fn-trendchip { display:inline-flex; gap:6px; align-items:center; border:1px solid #3E2E33; border-radius:999px; padding: 4px 11px; font-size:.8rem; margin: 0 6px 6px 0; animation: fnFade .5s both; }
.fn-trendchip b { font-family: 'JetBrains Mono'; font-size: .74rem; }
.fn-opp { display:grid; grid-template-columns: 1fr auto; gap: 14px; align-items: start; }
.fn-gauge { width: 74px; height: 74px; border-radius: 50%; display:grid; place-items:center; position: relative;
     background: conic-gradient(var(--accent) calc(var(--v) * 1%), #2C2124 0); animation: fnFade .8s both; }
.fn-gauge::before { content:""; position:absolute; inset: 7px; border-radius:50%; background:#141011; }
.fn-gauge b { position: relative; font-family:'JetBrains Mono'; font-size: 1.15rem; }
.fn-gauge small { position:absolute; bottom: -18px; font-size: .62rem; color: var(--muted); text-transform: uppercase; letter-spacing: .1em; white-space: nowrap; }
.fn-note { border-left: 3px solid var(--accent); background: rgba(122,26,51,.18); padding: 10px 14px; border-radius: 0 10px 10px 0; font-size: .9rem; margin: 8px 0; }
.fn-risk { border-left-color: var(--gold); background: rgba(214,176,114,.07); }

[class*="st-key-fn_head"] { display: none !important; }
@keyframes fnUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }
@keyframes fnFade { from { opacity: 0; } to { opacity: 1; } }
@keyframes fnGrow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
@keyframes fnShift { 0%,100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
@keyframes fnSheen { 0% { background-position: 120% 0; } 100% { background-position: -120% 0; } }
@keyframes fnPulse { 0% { box-shadow: 0 0 0 0 rgba(156,199,154,.55); } 70% { box-shadow: 0 0 0 8px rgba(156,199,154,0); } 100% { box-shadow: 0 0 0 0 rgba(156,199,154,0); } }
@keyframes fnSpin { to { transform: rotate(360deg); } }
@keyframes fnDialog { from { opacity: 0; transform: translateY(24px) scale(.985); } to { opacity: 1; transform: none; } }
@media (max-width: 900px) { .fn-home-grid { grid-template-columns: 1fr 1fr; } }
@media (max-width: 640px) {
  [data-testid="stButtonGroup"] { max-width: 100%; }
  [data-testid="stButtonGroup"] > div:last-child { flex-wrap: nowrap !important; overflow-x: auto !important; scrollbar-width: none;
       -webkit-overflow-scrolling: touch; padding-bottom: 2px; mask-image: linear-gradient(90deg, #000 88%, transparent); }
  [data-testid="stButtonGroup"] > div:last-child::-webkit-scrollbar { display: none; }
  [class*="st-key-hdr_ctrl"] [data-testid="stButtonGroup"] > div:last-child { mask-image: none; }
  [data-testid="stButtonGroup"] > div:last-child button { flex: 0 0 auto; }
  .fn-stat { padding: 12px 13px; } .fn-stat b { font-size: 1.15rem; }
  .fn-opp { grid-template-columns: 1fr; } .fn-gauge { width: 60px; height: 60px; margin-bottom: 14px; }
  div[role="dialog"] { animation: fnSheet .35s var(--ease) both; }
}
@keyframes fnSheet { from { transform: translateY(40px); opacity: 0; } to { transform: none; opacity: 1; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
</style>
"""


# ---------- v5: ikonice u meniju, donja traka na telefonu, hover svuda ----------
def _icon(paths):
    import urllib.parse
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.9' "
           "stroke-linecap='round' stroke-linejoin='round'>" + paths + "</svg>")
    return "url(\"data:image/svg+xml;utf8," + urllib.parse.quote(svg) + "\")"


NAV_ICONS = [
    "<path d='M3 10.5 12 3l9 7.5'/><path d='M5 9.5V21h5v-6h4v6h5V9.5'/>",                                   # početna
    "<rect x='3' y='4' width='14' height='16' rx='2'/><path d='M17 8h3v10a2 2 0 0 1-2 2'/><path d='M7 8h6M7 12h6M7 16h4'/>",  # vesti
    "<path d='M3 17l6-6 4 4 8-8'/><path d='M14 7h7v7'/>",                                                   # akcije
    "<rect x='3' y='7' width='18' height='13' rx='2'/><path d='M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18'/>",  # portfolio
    "<rect x='3' y='5' width='18' height='16' rx='2'/><path d='M16 3v4M8 3v4M3 10h18M8 14h3M8 17h6'/>",    # pregled
    "<path d='M9 3h6M10 3v6L4.5 19a1.5 1.5 0 0 0 1.3 2h12.4a1.5 1.5 0 0 0 1.3-2L14 9V3M7 15h10'/>",       # istraživanja
    "<rect x='3' y='4' width='18' height='5' rx='1'/><path d='M5 9v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9M10 13h4'/>",  # arhiva
    "<path d='M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1'/><circle cx='15' cy='6' r='2'/><circle cx='9' cy='12' r='2'/><circle cx='17' cy='18' r='2'/>",  # podešavanja
]
_icons_css = "\n".join(
    f'[class*="st-key-nav"] [role="radiogroup"] > div:nth-child({i + 1}) label::before {{ -webkit-mask-image: {_icon(p)}; mask-image: {_icon(p)}; }}'
    for i, p in enumerate(NAV_ICONS))

CSS += """
<style>
/* meni sa ikonicama */
[class*="st-key-nav"] [role="radiogroup"] label { display: flex !important; align-items: center; gap: 7px; position: relative; }
[class*="st-key-nav"] [role="radiogroup"] label::before { content: ""; width: 17px; height: 17px; flex: 0 0 auto; background: #A8979A;
     -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat; -webkit-mask-position: center; mask-position: center;
     -webkit-mask-size: contain; mask-size: contain; transition: background .2s ease, transform .25s var(--ease); }
[class*="st-key-nav"] [role="radiogroup"] label:hover::before { background: #F5ECE4; transform: translateY(-1px) scale(1.08); }
[class*="st-key-nav"] [role="radiogroup"] label:has(input:checked)::before { background: var(--accent); }
[class*="st-key-nav"] [role="radiogroup"] label::after { content: ""; position: absolute; left: 0; right: 0; bottom: -1px; height: 2px;
     background: linear-gradient(90deg, var(--accent), var(--gold)); transform: scaleX(0); transform-origin: left; transition: transform .3s var(--ease); }
[class*="st-key-nav"] [role="radiogroup"] label:hover::after { transform: scaleX(.6); }
[class*="st-key-nav"] [role="radiogroup"] label:has(input:checked)::after { transform: scaleX(1); }
[class*="st-key-nav"] [role="radiogroup"] label:has(input:checked) { border-bottom-color: transparent !important; }
""" + _icons_css + """

/* naslov stranice */
.fn-phead { margin: 6px 0 14px; animation: fnUp .5s var(--ease) both; }
.fn-phead h2 { font-family: 'Playfair Display', Georgia, serif !important; font-size: 2rem; margin: 0; padding: 0; line-height: 1.15; color: #F5ECE4; }
.fn-phead p { color: var(--muted); margin: 4px 0 0; font-size: .95rem; max-width: 70ch; }

/* hover efekti za sve */
.fn-stat { transition: transform .25s var(--ease), border-color .25s ease, box-shadow .25s ease; }
.fn-stat:hover { transform: translateY(-3px); border-color: rgba(194,67,95,.55); box-shadow: 0 16px 34px -22px rgba(194,67,95,.7); }
.fn-chip, .fn-trendchip, .fn-src, .fn-pill { transition: transform .18s ease, border-color .2s ease, background .2s ease; }
.fn-chip:hover, .fn-trendchip:hover, .fn-pill:hover { transform: translateY(-1px); border-color: rgba(194,67,95,.6); background: rgba(122,26,51,.18); }
.fn-src:hover { transform: translateY(-1px); }
.fn-bullets li { transition: background .2s ease, padding-left .25s var(--ease); border-radius: 8px; }
.fn-bullets li:hover { background: rgba(122,26,51,.12); padding-left: 28px; }
.fn-bullets li::before { transition: transform .25s var(--ease); }
.fn-bullets li:hover::before { transform: rotate(135deg) scale(1.15); }
.fn-rows .fn-row { transition: background .2s ease, transform .2s ease; border-radius: 8px; }
.fn-rows .fn-row:hover { background: rgba(122,26,51,.12); transform: translateX(3px); }
.fn-tk-i { transition: background .2s ease; } .fn-tk-i:hover { background: rgba(122,26,51,.16); }
.fn-ind { transition: border-color .2s ease, background .2s ease; border-radius: 12px; }
.fn-ind:hover { background: rgba(122,26,51,.08); }
[data-testid="stExpander"] summary { transition: background .2s ease, color .2s ease; border-radius: 12px; }
[data-testid="stExpander"] summary:hover { background: rgba(122,26,51,.15); }
[data-testid="stExpander"] details { transition: border-color .2s ease; }
[data-testid="stExpander"] details:hover { border-color: rgba(194,67,95,.45) !important; }
div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input, .stDateInput input { transition: border-color .2s ease, box-shadow .2s ease !important; }
div[data-baseweb="select"] > div:hover, .stTextInput input:hover { border-color: rgba(194,67,95,.55) !important; }
div[data-baseweb="select"] > div:focus-within, .stTextInput input:focus { box-shadow: 0 0 0 3px rgba(194,67,95,.22) !important; border-color: rgba(194,67,95,.8) !important; }
[data-testid="stButtonGroup"] button { transition: transform .15s ease, border-color .2s ease, background .2s ease !important; }
[data-testid="stButtonGroup"] button:hover { transform: translateY(-1px); border-color: rgba(194,67,95,.65) !important; }
.stTabs [data-baseweb="tab"] { transition: color .2s ease, background .2s ease; border-radius: 10px 10px 0 0; }
.stTabs [data-baseweb="tab"]:hover { background: rgba(122,26,51,.15); }
a.fn-title, .fn-title a { background-image: linear-gradient(var(--accent), var(--accent)); background-size: 0 1px; background-repeat: no-repeat;
     background-position: 0 100%; transition: background-size .35s var(--ease), color .2s ease; }
a.fn-title:hover, .fn-title a:hover { background-size: 100% 1px; }
[data-testid="stDataFrame"] { transition: border-color .2s ease; } [data-testid="stDataFrame"]:hover { border-color: rgba(194,67,95,.4); }
[data-testid="stVegaLiteChart"] { animation: fnFade .7s ease both; }

/* kartice akcija */
.fn-spark { width: 100%; height: 64px; display: block; margin: 8px 0 4px; overflow: visible; }
.fn-spark-line { stroke-dasharray: 1; stroke-dashoffset: 1; animation: fnDraw 1.2s var(--ease) .1s forwards; }
.fn-spark-area { opacity: 0; animation: fnFade .8s ease .5s forwards; }
[class*="st-key-card_"]:hover .fn-spark-line { stroke-width: 2.6; }
.fn-sc-head { display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; }
.fn-sc-name { font-family: 'Playfair Display', Georgia, serif; font-size: 1.12rem; font-weight: 600; line-height: 1.25; }
.fn-sc-px { text-align: right; font-family: 'JetBrains Mono'; white-space: nowrap; }
.fn-sc-px b { display: block; font-size: 1.02rem; } .fn-sc-px i { font-style: normal; font-size: .76rem; }
.fn-sc-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-top: 4px; }
.fn-sc-stats div { background: rgba(255,255,255,.025); border: 1px solid #2C2124; border-radius: 9px; padding: 6px 8px; transition: border-color .2s ease, background .2s ease; }
.fn-sc-stats div:hover { border-color: rgba(194,67,95,.5); background: rgba(122,26,51,.14); }
.fn-sc-stats span { display: block; color: var(--muted); font-size: .6rem; text-transform: uppercase; letter-spacing: .08em; }
.fn-sc-stats b { font-family: 'JetBrains Mono'; font-size: .82rem; font-weight: 500; }
.fn-tag { display: inline-block; font-size: .66rem; letter-spacing: .06em; text-transform: uppercase; padding: 2px 8px; border-radius: 999px;
     border: 1px solid rgba(214,176,114,.45); color: var(--gold); margin-left: 6px; vertical-align: middle; }
[class*="st-key-stk_search"] div[data-baseweb="select"] > div { min-height: 48px; border-radius: 14px !important; font-size: 1rem;
     background: linear-gradient(180deg, rgba(27,21,23,.95), rgba(20,16,17,.95)) !important; }
@keyframes fnDraw { to { stroke-dashoffset: 0; } }
[data-testid="stAlertContainer"], [data-testid="stAlert"] > div { background: linear-gradient(135deg, rgba(122,26,51,.22), rgba(20,16,17,.9)) !important;
     border: 1px solid rgba(194,67,95,.35) !important; border-radius: 14px !important; color: #F5ECE4 !important; }
[data-testid="stAlertContainer"] p, [data-testid="stAlertContainer"] div { color: #E7DBD2 !important; }
[data-testid="stAlertContentSuccess"] p { color: #9CC79A !important; }
[data-testid="stAlertContentError"] p { color: #E07C8A !important; }
[data-testid="stAlertContentWarning"] p { color: #D6B072 !important; }

/* telefon: meni kao donja traka sa ikonicama */
@media (max-width: 640px) {
  .block-container { padding-bottom: 96px !important; }
  [class*="st-key-nav"] { position: fixed !important; top: auto !important; bottom: 0 !important; left: 0 !important; right: 0 !important;
       z-index: 1000 !important; margin: 0 !important; padding: 4px 2px calc(6px + env(safe-area-inset-bottom)) !important;
       background: rgba(14,10,11,.94) !important; backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
       border-top: 1px solid #2C2124; border-bottom: none !important; width: 100% !important; }
  [class*="st-key-nav"] [role="radiogroup"] { gap: 0 !important; flex-wrap: nowrap !important; overflow-x: auto; justify-content: flex-start; }
  [class*="st-key-nav"] [role="radiogroup"] > div { flex: 0 0 20% !important; min-width: 0; }
  [class*="st-key-nav"] [role="radiogroup"] label { width: 100%; justify-content: center; flex-direction: column; gap: 3px; padding: 7px 0 5px !important; }
  [class*="st-key-nav"] [role="radiogroup"] label p { font-size: .56rem !important; letter-spacing: .03em !important; }
  [class*="st-key-nav"] [role="radiogroup"] label::before { width: 22px; height: 22px; }
  [class*="st-key-nav"] [role="radiogroup"] label::after { left: 30%; right: 30%; bottom: auto; top: -4px; }
  .fn-phead h2 { font-size: 1.55rem; }
  .fn-ticker { margin-bottom: 16px !important; }
  .fn-sc-stats { grid-template-columns: repeat(2, 1fr); }
}
</style>
"""
