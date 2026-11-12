"""FinNews - lični terminal za finansijske vesti i istraživanja (SR / EN)."""
import os
import json
import urllib.parse
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

import html as _html

import ai
import db
import eu
import fetcher
import indicators
import insights
import portfolio
import reader
import research
import stocks
import styles

try:  # Streamlit Cloud: tajne (Secrets) postaju promenljive okruženja
    for _k, _v in st.secrets.items():
        if isinstance(_v, (str, int, float)):
            os.environ.setdefault(_k, str(_v))
except Exception:  # noqa: BLE001
    pass
_ASSETS = Path(__file__).parent / "assets"
try:
    from PIL import Image as _Img
    _ICON = _Img.open(_ASSETS / "favicon.png")
except Exception:  # noqa: BLE001
    _ICON = "📈"
st.set_page_config(page_title="FinNews", page_icon=_ICON, layout="wide", initial_sidebar_state="collapsed")
st.markdown(styles.CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _touch_icon():
    import base64
    try:
        return base64.b64encode((_ASSETS / "touch-icon.png").read_bytes()).decode()
    except OSError:
        return ""


_HEAD_JS = """<script>
const d = window.parent.document;
if (!d.getElementById('fn-touch')) {
  const add = (tag, attrs) => { const e = d.createElement(tag); Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v)); d.head.appendChild(e); return e; };
  add('link', {id: 'fn-touch', rel: 'apple-touch-icon', href: 'data:image/png;base64,""" + _touch_icon() + """'});
  add('meta', {name: 'theme-color', content: '#0B0909'});
  add('meta', {name: 'apple-mobile-web-app-capable', content: 'yes'});
  add('meta', {name: 'mobile-web-app-capable', content: 'yes'});
  add('meta', {name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent'});
  add('meta', {name: 'apple-mobile-web-app-title', content: 'FinNews'});
}
</script>"""
with st.container(key="fn_head"):  # ikonica za početni ekran telefona i boja trake (skriveno)
    if hasattr(st, "iframe"):
        st.iframe(_HEAD_JS, height=1)
    else:
        import streamlit.components.v1 as _components
        _components.html(_HEAD_JS, height=0)
RESEARCH = "Istraživanja"
NEWS_CATS = ["Vesti", "Centralne banke i makro", "Analize i blogovi", "Srbija i region"]
GENERAL_CATS = ["Srbija", "Svet"]
CLASSICS = json.loads((Path(__file__).parent / "classics.json").read_text(encoding="utf-8"))

# ---------- prevod interfejsa ----------
T = {
    "lang": ("Jezik", "Language"),
    "orig": ("Prikaži original (bez prevoda)", "Show original (no translation)"),
    "refresh": ("🔄 Osveži vesti", "🔄 Refresh news"),
    "fetching": ("Preuzimam vesti...", "Fetching news..."),
    "new_items": ("Novih stavki", "New items"),
    "src_err": ("izvora nije odgovorilo (vidi Podešavanja)", "sources did not respond (see Settings)"),
    "last": ("Poslednje osvežavanje", "Last refresh"),
    "ai_on": ("AI: Claude ✅", "AI: Claude ✅"),
    "ai_off": ("AI: osnovni režim (dodaj API ključ u Podešavanjima)", "AI: basic mode (add an API key in Settings)"),
    "in_arch": ("U arhivi", "In archive"),
    "items": ("stavki", "items"),
    "since": ("od", "since"),
    "t_top": ("📰 Najvažnije", "📰 Top stories"),
    "t_brief": ("🧠 Dnevni brief", "🧠 Daily brief"),
    "t_6m": ("📅 Pregled 6 meseci", "📅 6-month review"),
    "t_res": ("🔬 Istraživanja", "🔬 Research"),
    "t_arch": ("🗂 Arhiva", "🗂 Archive"),
    "t_saved": ("★ Sačuvano", "★ Saved"),
    "t_set": ("⚙️ Podešavanja", "⚙️ Settings"),
    "period": ("Period", "Period"),
    "cats": ("Kategorije", "Categories"),
    "sources": ("Izvori", "Sources"),
    "all_src": ("Svi izvori", "All sources"),
    "count": ("Broj", "Count"),
    "search": ("Pretraga", "Search"),
    "none": ("Nema stavki za izabrane filtere.", "Nothing matches these filters."),
    "importance": ("važnost", "importance"),
    "star_help": ("Sačuvaj / ukloni", "Save / remove"),
    "explain": ("🧠 Objasni", "🧠 Explain"),
    "analyzing": ("Claude analizira...", "Claude is analysing..."),
    "translating": ("Prevodim", "Translating"),
    "day": ("Dan", "Day"),
    "past_briefs": ("Sačuvani briefovi", "Saved briefs"),
    "make_brief": ("✨ Napravi brief", "✨ Create brief"),
    "remake": ("♻️ Napravi ponovo", "♻️ Regenerate"),
    "writing": ("Pišem...", "Writing..."),
    "no_day": ("Za ovaj period nema vesti u arhivi.", "No news in the archive for this period."),
    "made": ("Napravljeno", "Created"),
    "dl_md": ("⬇️ Preuzmi (Markdown)", "⬇️ Download (Markdown)"),
    "no_brief": ("Još nema briefa - klikni dugme iznad.", "No brief yet - click the button above."),
    "bf_info": ("Arhiva prethodnih 6 meseci još nije učitana. Preuzimanje traje nekoliko minuta (jednom).",
                "The 6-month archive is not loaded yet. It takes a few minutes (one time)."),
    "bf_btn": ("📥 Učitaj najvažnije vesti iz poslednjih 6 meseci", "📥 Load the most important news of the last 6 months"),
    "bf_redo": ("📥 Dopuni arhivu 6 meseci", "📥 Top up the 6-month archive"),
    "bf_done": ("Učitano novih vesti", "New items loaded"),
    "month": ("Mesec", "Month"),
    "top_month": ("Najvažnije vesti meseca", "Top stories of the month"),
    "by_week": ("Po nedeljama", "By week"),
    "week": ("Nedelja", "Week"),
    "more_src": ("izvora", "sources"),
    "month_ai": ("✨ AI pregled meseca", "✨ AI monthly review"),
    "six_ai": ("✨ AI pregled celih 6 meseci", "✨ AI review of all 6 months"),
    "view": ("Prikaz", "View"),
    "r_latest": ("🆕 Najnovije (arXiv, NBER, BIS)", "🆕 Latest (arXiv, NBER, BIS)"),
    "r_journals": ("📚 Novo u top časopisima", "📚 New in top journals"),
    "r_c6": ("🔥 Najcitiranije - 6 meseci", "🔥 Most cited - 6 months"),
    "r_c24": ("🏆 Najcitiranije - 2 godine", "🏆 Most cited - 2 years"),
    "r_classic": ("🏛 Klasici i temelji oblasti", "🏛 Classics & foundations"),
    "r_refresh": ("🔄 Osveži radove (OpenAlex)", "🔄 Refresh papers (OpenAlex)"),
    "r_empty": ("Radovi još nisu preuzeti - klikni „Osveži radove“.", "Papers not loaded yet - click 'Refresh papers'."),
    "cited": ("citata", "citations"),
    "curated": ("Odabrani temeljni radovi", "Curated landmark papers"),
    "most_cited_all": ("Najcitiraniji radovi po tvojim temama (svih vremena)", "Most cited papers on your topics (all time)"),
    "topic": ("Tema", "Topic"),
    "all": ("Sve", "All"),
    "why": ("Zašto je bitan", "Why it matters"),
    "range": ("Od - do", "From - to"),
    "sort": ("Sortiraj", "Sort"),
    "by_imp": ("Po važnosti", "By importance"),
    "by_date": ("Po datumu", "By date"),
    "found": ("Pronađeno", "Found"),
    "csv": ("⬇️ Izvezi CSV", "⬇️ Export CSV"),
    "api": ("Anthropic API ključ (console.anthropic.com)", "Anthropic API key (console.anthropic.com)"),
    "oa_key": ("OpenAlex API ključ (opciono, besplatan)", "OpenAlex API key (optional, free)"),
    "script": ("Pismo za srpski", "Serbian script"),
    "topics": ("Teme istraživanja (jedna po redu)", "Research topics (one per line)"),
    "save": ("💾 Sačuvaj", "💾 Save"),
    "saved": ("Sačuvano.", "Saved."),
    "feeds_help": ("Dodaj red za novi RSS izvor ili isključi postojeći.", "Add a row for a new RSS feed or disable one."),
    "save_feeds": ("💾 Sačuvaj izvore", "💾 Save sources"),
    "status": ("Status izvora", "Source status"),
    "read": ("📖 Čitaj", "📖 Read"),
    "r_summary": ("Sažetak", "Summary"),
    "r_full": ("Ceo tekst na srpskom", "Full text"),
    "r_orig": ("Original", "Original"),
    "r_loading": ("Preuzimam članak...", "Loading article..."),
    "r_summ": ("Pravim sažetak...", "Summarising..."),
    "r_tr": ("Prevodim ceo tekst (do pola minuta)...", "Translating the full text (up to 30s)..."),
    "r_paywall": ("Ovaj izvor je iza paywall-a, pa pun tekst nije dostupan u aplikaciji. Sažetak je napravljen iz opisa koji izvor objavljuje.",
                  "This source is paywalled, so the full text isn't available in the app. The summary is based on the publisher's description."),
    "r_short": ("Sajt nije dozvolio preuzimanje punog teksta. Sažetak je napravljen iz dostupnog dela.",
                "The site didn't allow fetching the full text. The summary uses what was available."),
    "r_abstract": ("Za naučne radove prikazuje se sažetak rada (abstract).", "For research papers the paper's abstract is shown."),
    "r_open": ("Otvori na sajtu ↗", "Open on site ↗"),
    "r_retry": ("↻ Pokušaj ponovo", "↻ Try again"),
    "t_rr": ("🧪 Pregled istraživanja", "🧪 Research review"),
    "rr_intro": ("Šta su studije pronašle - ključni rezultat svake u 1-2 rečenice, da ne moraš da ih čitaš cele.",
                 "What studies found - each one's key result in 1-2 sentences, so you don't have to read them."),
    "rr_period": ("Period", "Period"),
    "rr_making": ("Izdvajam ključne nalaze...", "Extracting key findings..."),
    "rr_review": ("✨ Zbirni pregled oblasti", "✨ Field review"),
    "rr_need": ("",
                "The field review is written by Claude - add an Anthropic API key in Settings. Findings below work without one."),
    "rr_found": ("Nalaz", "Finding"),
    "rr_none": ("Nema studija za ovaj period - osveži Doktorat radar ili radove u Istraživanjima.",
                "No studies for this period - refresh the PhD radar or the papers in Research."),
    "t_phd": ("🎓 Doktorat radar", "🎓 PhD radar"),
    "p_intro": ("Najvažnije studije iz poslednjih 6 meseci u oblastima koje su napredni nastavak tvog master rada, rangirane po relevantnosti, citatima, kvalitetu časopisa i svežini.",
                "The most important studies of the last 6 months in areas that extend your master's thesis, ranked by relevance, citations, venue quality and recency."),
    "p_refresh": ("🔄 Osveži radar (OpenAlex, ~1 min)", "🔄 Refresh radar (OpenAlex, ~1 min)"),
    "p_empty": ("Radar još nije učitan - klikni „Osveži radar“.", "Radar not loaded yet - click 'Refresh radar'."),
    "p_trends": ("Trendovi: radovi u poslednjih 6 meseci (naslov i abstract) i rast - pre 3-9 meseci naspram pre 9-15 meseci",
                 "Trends: papers in the last 6 months (title & abstract) and growth - 3-9 months ago vs 9-15 months ago"),
    "p_top": ("Top studije - 6 meseci", "Top studies - 6 months"),
    "p_map": ("Mapa praznina", "Gap map"),
    "p_saved": ("Moja lista za doktorat", "My PhD reading list"),
    "p_gaps": ("Šta autori kažu da fali (ograničenja i buduća istraživanja)", "What authors say is missing (limitations & future work)"),
    "p_gaps_help": ("Rečenice iz zaključaka pročitanih studija - najbrži put do praznine u literaturi. Otvori nekoliko studija (📖) da se lista popuni.",
                    "Sentences from the conclusions of papers you've opened - the fastest route to a research gap. Open a few papers (📖) to fill this list."),
    "p_ideas": ("✨ Predloži teme za doktorat", "✨ Suggest PhD topics"),
    "p_ideas_need": ("Tekstualni predlog tema piše AI - uključi besplatni lokalni AI u Podešavanjima. Do tada koristi „Mapa praznina“ i listu iznad.",
                     "Written topic suggestions need AI - enable the free local AI in Settings. Meanwhile use the 'Gap map' and the list above."),
    "p_save": ("🎓 Za doktorat", "🎓 Add to PhD list"),
    "p_saved_b": ("🎓 Na listi", "🎓 On list"),
    "p_abs": ("Abstract", "Abstract"),
    "p_concl": ("Zaključak", "Conclusion"),
    "p_future": ("Pravci za dalja istraživanja (iz rada)", "Future research directions (from the paper)"),
    "p_noconcl": ("Pun tekst nije slobodno dostupan (časopis naplaćuje pristup), pa je prikazan samo abstract.",
                  "The full text isn't openly available (paywalled journal), so only the abstract is shown."),
    "p_reading": ("Preuzimam rad i tražim zaključak...", "Fetching the paper and locating the conclusion..."),
    "p_analysis": ("Analiza za doktorat", "PhD-oriented analysis"),
    "p_pdf": ("PDF ↗", "PDF ↗"),
    "p_thesis": ("Opis mog master rada (koristi se za predloge tema)", "My master's thesis description (used for topic suggestions)"),
    "p_topics_set": ("Teme radara (jedna po redu: upit na engleskom | naziv)", "Radar topics (one per line: English query | label)"),
    "all_topics": ("Sve teme", "All topics"),
    "auto_read": ("Automatski pripremi sažetke za top vesti (u pozadini)", "Prepare summaries for top stories automatically (in the background)"),
}
MONTHS = {"sr": ["januar", "februar", "mart", "april", "maj", "jun", "jul", "avgust", "septembar",
                 "oktobar", "novembar", "decembar"],
          "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                 "October", "November", "December"]}


@st.cache_resource
def get_con():
    return db.connect()


con = get_con()
PUBLIC = os.environ.get("FINNEWS_PUBLIC") == "1"  # deljenje preko linka / hosting: lični delovi su iza PIN-a


@st.cache_resource
def _background():
    import run_fetch
    return run_fetch.start_background()


def _sync_portfolio(pull=False):
    """Mac <-> internet verzija: posle izmene šalje u pozadini; na Početnoj i Portfoliju preuzima noviju verziju."""
    import time as _time
    import cloud_sync
    if not cloud_sync.enabled():
        return
    try:
        if pull and _time.time() - st.session_state.get("pulled_at", 0) > 90:
            st.session_state["pulled_at"] = _time.time()
            cloud_sync.pull(con)
        elif (db.get_meta(con, "portfolio_changed") or "") > (db.get_meta(con, "sync_ok") or ""):
            db.set_meta(con, "sync_ok", db.get_meta(con, "portfolio_changed"))
            cloud_sync.push_async(db.connect)
    except Exception as ex:  # noqa: BLE001
        db.set_meta(con, "sync_error", str(ex)[:200])


_sync_portfolio()


_background()

# ---------- zaglavlje: logo, jezik, original, osvežavanje ----------
_cfg = ai.load_config()
if "ui" not in st.session_state:
    st.session_state["ui"] = "SR" if _cfg.get("ui_lang", "sr") == "sr" else "EN"
ui = "sr" if st.session_state.get("ui") in ("SR", "Srpski", None) else "en"
if _cfg.get("ui_lang") != ui and not PUBLIC:  # pamti izbor (koristi ga i widget u menu baru)
    _cfg["ui_lang"] = ui
    ai.save_config(_cfg)


def t(key):
    return T[key][0 if ui == "sr" else 1]


@st.cache_data(ttl=60, show_spinner=False)
def _llm_status(_k):
    return ai.llm_on(), ai.llm_name()


DAYS = {"sr": ["ponedeljak", "utorak", "sreda", "četvrtak", "petak", "subota", "nedelja"],
        "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
_td = date.today()
hc1, hc2 = st.columns([3, 2], vertical_alignment="bottom")
hc1.markdown(f'<div class="fn-kicker">{DAYS[ui][_td.weekday()]}, {_td.day}. {MONTHS[ui][_td.month - 1]} {_td.year}</div>'
             '<div class="fn-h1">Fin<span>News</span></div>', unsafe_allow_html=True)
with hc2:
    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center", key="hdr_ctrl"):
        st.segmented_control("lang", ["SR", "EN"], key="ui", label_visibility="collapsed")
        show_orig = bool(_cfg.get("show_original"))
        do_refresh = st.button("↻", key="refresh_btn", help=t("refresh"))
lang = None if show_orig else ui
last = db.get_meta(con, "last_fetch")
if do_refresh and PUBLIC and last and datetime.now(timezone.utc) - datetime.fromisoformat(last) < timedelta(minutes=10):
    do_refresh = False
    st.toast("Vesti su osvežene pre manje od 10 minuta." if ui == "sr" else "News was refreshed less than 10 minutes ago.")
if do_refresh or (not last and not st.session_state.get("auto_fetched")):
    st.session_state["auto_fetched"] = True
    with st.spinner(t("fetching")):
        res = fetcher.fetch_all(con)
    st.toast(f"{t('new_items')}: {res['new']}" + (f" · {len(res['errors'])} {t('src_err')}" if res["errors"] else ""))
    last = db.get_meta(con, "last_fetch")
ai_on, ai_name = _llm_status(_cfg.get("anthropic_api_key", "") + _cfg.get("ollama_model", ""))
s = db.stats(con)


# ---------- pomoćne funkcije ----------
def esc(s):
    return (s or "").replace("$", "\\$").replace("[", "\\[").replace("]", "\\]").replace("*", "\\*")


def utc_iso(dt):
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def day_bounds(d1, d2=None):
    d2 = d2 or d1
    return (utc_iso(datetime.combine(d1, time.min).astimezone()),
            utc_iso(datetime.combine(d2 + timedelta(days=1), time.min).astimezone()))


def fmt_time(iso):
    try:
        dt = datetime.fromisoformat(iso).astimezone()
    except (TypeError, ValueError):
        return "-"
    if dt.date() == date.today():
        return dt.strftime("%H:%M")
    return dt.strftime("%d.%m. %H:%M") if dt.year == date.today().year else dt.strftime("%d.%m.%Y.")


if not db.get_meta(con, "cleanup_v6"):
    con.execute("DELETE FROM briefs WHERE content LIKE '%Osnovni režim%' OR content LIKE '%Basic mode%'")
    con.commit()
    db.set_meta(con, "cleanup_v6", "1")
if not db.get_meta(con, "cleanup_v5"):  # stari neuspeli prevodi su keširani kao original - obriši ih
    con.execute("DELETE FROM translations WHERE item_id IN (SELECT t.item_id FROM translations t "
                "JOIN items i ON i.id = t.item_id WHERE t.title = i.title)")
    con.execute("DELETE FROM article_ai")
    con.commit()
    db.set_meta(con, "cleanup_v5", "1")


def ensure_translations(items, lang):
    """items: dict-ovi sa id, title, summary (ili abstract), lang."""
    if not lang or not items:
        return {}
    have = db.get_translations(con, [it["id"] for it in items], lang)
    missing = [it for it in items if it["id"] not in have and it.get("lang", "en") != lang]
    import time as _time
    if missing and _time.time() - st.session_state.get("tr_fail_at", 0) < 120:
        return have  # prevod je upravo pao - ne usporavaj stranicu ponovnim pokušajima, probaće ponovo za 2 minuta
    if missing:
        with st.spinner(f"{t('translating')} {len(missing)}..."):
            out = ai.translate_items(
                [(it["title"], (it.get("summary") or it.get("abstract") or "")[:700]) for it in missing], lang)
        failed = 0
        for it, (tt, ss) in zip(missing, out):
            if tt == it["title"]:
                failed += 1
                continue  # prevod nije uspeo - ne keširaj, probaj ponovo kasnije
            db.save_translation(con, it["id"], lang, tt, ss)
            have[it["id"]] = {"title": tt, "summary": ss}
        if failed == len(missing):
            st.session_state["tr_fail_at"] = _time.time()
        if failed == len(missing) and not st.session_state.get("tr_warned"):
            st.session_state["tr_warned"] = True
            st.toast(("⚠️ Prevod trenutno ne radi" if ui == "sr" else "⚠️ Translation is not working")
                     + (f": {ai.LAST_ERROR}" if getattr(ai, "LAST_ERROR", None) else ""), icon="🌐")
    return have


def explain_button(container, it, key):
    if not ai_on:
        return
    ek = f"exp_{it['id']}_{ui}"
    if ek in st.session_state:
        container.markdown(f'<div class="fn-why">{_html.escape(st.session_state[ek])}</div>', unsafe_allow_html=True)
    elif container.button(t("explain"), key=f"{key}_ex_{it['id']}", type="tertiary"):
        with st.spinner(t("analyzing")):
            try:
                st.session_state[ek] = ai.explain_item(
                    {"source": it.get("source") or it.get("venue", ""), "title": it["title"],
                     "summary": it.get("summary") or it.get("abstract")}, ui)
            except Exception as ex:  # noqa: BLE001
                st.session_state[ek] = f"Error: {ex}"
        st.rerun()


def h(s):
    return _html.escape(s or "").replace("$", "&#36;")


def dots(score):
    n = max(1, min(5, round(score / 4.5)))
    return f'<span class="fn-dots" title="{score:.1f}">{"●" * n}<i>{"●" * (5 - n)}</i></span>'


CAT_EN = {"Vesti": "News", "Centralne banke i makro": "Central banks & macro", "Analize i blogovi": "Analysis",
          "Srbija i region": "Serbia & region", "Istraživanja": "Research", "Srbija": "Serbia", "Svet": "World",
          "Kompanije": "Companies"}


def cat_label(c):
    return c if ui == "sr" else CAT_EN.get(c, c)


def card(title, link, meta_html, summary=""):
    st.markdown(
        f'<div class="fn-meta">{meta_html}</div>'
        f'<a class="fn-title" href="{h(link)}" target="_blank">{h(title)}</a>'
        + (f'<p class="fn-sum">{h(summary)}</p>' if summary else ""),
        unsafe_allow_html=True)


def paragraphs(text):
    return "".join(f"<p>{h(p.strip())}</p>" for p in (text or "").split("\n") if p.strip())


def translated_full(it, text, target):
    full = db.get_article_ai(con, it["id"], target, "full")
    if not full:
        with st.spinner(t("r_tr")):
            full = ai.translate_full(text, target)
        if full.strip() != text.strip():
            db.save_article_ai(con, it["id"], target, "full", full)
        else:
            st.warning(("Prevod nije uspeo" if ui == "sr" else "Translation failed")
                       + (f": {ai.LAST_ERROR}" if ai.LAST_ERROR else ""))
    return full


@st.dialog("FinNews", width="large")
def reader_dialog(it):
    tr = ensure_translations([it], lang).get(it["id"], {})
    title = tr.get("title") or it["title"]
    with st.spinner("Tražim ceo tekst vesti..." if ui == "sr" else "Looking for the full article..."):
        art = reader.get_article(con, it)
    status = art["status"]
    alt_src = status[4:] if status.startswith("alt:") else None
    st.markdown(f'<div class="fn-meta"><span class="fn-src" style="--c:{styles.src_color(it["source"])}">{h(it["source"])}</span>'
                f'<span>{fmt_time(it["published"])}</span>'
                + (f'<span class="fn-full">✓ {"ceo tekst" if ui == "sr" else "full text"}</span>' if reader.is_full(status) else "")
                + f'</div><div class="fn-read-title">{h(title)}</div>', unsafe_allow_html=True)
    if not reader.is_full(status):
        st.warning("Ceo tekst ove vesti trenutno nije dostupan ni na izvornom sajtu ni kod drugih besplatnih izvora, pa je ne prikazujem "
                   "delimično. Probaj ponovo kasnije (druge redakcije često prenesu vest u roku od par sati) ili je otvori na sajtu."
                   if ui == "sr" else
                   "The full text of this story is not available right now, either at the source or from other free outlets, so it is "
                   "not shown in part. Try again later (other newsrooms often carry the story within hours) or open it on the site.")
        with st.container(horizontal=True, key=f"act_reader_{it['id']}"):
            st.link_button(t("r_open"), art.get("url") or it["link"])
            if st.button(t("r_retry"), key=f"retry_{it['id']}"):
                reader.get_article(con, it, force=True)
                st.rerun()
        return
    text = art["text"]
    if alt_src:
        st.markdown('<div class="fn-alt">' + (f"↪ Ceo tekst iste vesti preuzet je od izvora: <b>{h(alt_src)}</b>" if ui == "sr"
                    else f"↪ Full text of the same story taken from: <b>{h(alt_src)}</b>") + "</div>", unsafe_allow_html=True)
    # trenutni sažetak (bez čekanja), AI sažetak na zahtev
    quick = db.get_article_ai(con, it["id"], ui, "quick")
    if not quick:
        quick = ai.quick_summary(text, ui, it.get("lang") or "en")
        if quick:
            db.save_article_ai(con, it["id"], ui, "quick", quick)
    ai_s = db.get_article_ai(con, it["id"], ui, "summary")
    with st.container(key=f"readbox_{it['id']}"):
        st.markdown(f'<div class="fn-read-box"><div class="fn-kicker">{"Najvažnije" if ui == "sr" else "Key points"}</div></div>',
                    unsafe_allow_html=True)
        st.markdown((ai_s or quick or "").replace("$", "\\$"))
        if ai_on and not ai_s and st.button("🧠 " + ("AI sažetak i zašto je bitno" if ui == "sr" else "AI summary and why it matters"),
                                            key=f"ais_{it['id']}"):
            with st.spinner(t("r_summ")):
                try:
                    ai.LAST_ERROR = None
                    ai_s = ai.summarize_article(it["title"], text, ui)
                    if not ai.LAST_ERROR:
                        db.save_article_ai(con, it["id"], ui, "summary", ai_s)
                    st.markdown(ai_s.replace("$", "\\$"))
                except Exception as ex:  # noqa: BLE001
                    st.error(str(ex))
    if status == "abstract":
        st.caption(t("r_abstract"))
    if ui == "sr":
        tab_a, tab_b = st.tabs([t("r_full"), t("r_orig")])
        with tab_a:
            body = text if it.get("lang") == "sr" else translated_full(it, text, "sr")
            st.markdown(f'<div class="fn-article">{paragraphs(body)}</div>', unsafe_allow_html=True)
        with tab_b:
            st.markdown(f'<div class="fn-article">{paragraphs(text)}</div>', unsafe_allow_html=True)
    else:
        tab_a, tab_b = st.tabs([t("r_full"), "Srpski"])
        with tab_a:
            body = translated_full(it, text, "en") if it.get("lang") == "sr" else text
            st.markdown(f'<div class="fn-article">{paragraphs(body)}</div>', unsafe_allow_html=True)
        with tab_b:
            if st.button("Prevedi na srpski", key=f"tr_sr_{it['id']}"):
                st.markdown(f'<div class="fn-article">{paragraphs(translated_full(it, text, "sr"))}</div>',
                            unsafe_allow_html=True)
    with st.container(horizontal=True, key=f"act_reader_{it['id']}"):
        st.link_button(t("r_open"), art.get("url") or it["link"])


def only_full(items):
    """Izbacuje vesti za koje je provereno da ceo tekst nije dostupan (ni kod drugih izvora)."""
    stt = reader.statuses(con, [i["id"] for i in items])
    return [i for i in items if i["id"] not in stt or reader.is_full(stt[i["id"]])]


def render_items(items, key, show_score=True, extra=None, hero_first=False, grid=False):
    if not items:
        st.info(t("none"))
        return
    tr = ensure_translations(items, lang)
    stt = reader.statuses(con, [i["id"] for i in items])

    def one(it, hero):
        tx = tr.get(it["id"], {})
        title, summ = tx.get("title") or it["title"], tx.get("summary") or it.get("summary") or ""
        with st.container(border=True, key=f"{'hero' if hero else 'card'}_{key}_{it['id']}"):
            meta = (('<span class="fn-badge">' + ("Vest dana" if ui == "sr" else "Top story") + '</span>') if hero else "")
            meta += (f'<span class="fn-src" style="--c:{styles.src_color(it["source"])}">{h(it["source"])}</span>'
                     f'<span class="fn-pill">{styles.CAT_ICON.get(it["category"], "•")} {h(cat_label(it["category"]))}</span>'
                     f'<span>{fmt_time(it["published"])}</span>')
            if show_score:
                meta += dots(it["score"])
            if extra and it["id"] in extra:
                meta += f'<span class="fn-more">+{extra[it["id"]]} {t("more_src")}</span>'
            if reader.is_full(stt.get(it["id"])) and it["category"] != RESEARCH:
                meta += f'<span class="fn-full">✓ {"ceo tekst" if ui == "sr" else "full text"}</span>'
            lim = 420 if hero or not grid else 220
            card(title, it["link"], meta, summ[:lim] + ("…" if len(summ) > lim else ""))
            ek = f"exp_{it['id']}_{ui}"
            if ek in st.session_state:
                st.markdown(f'<div class="fn-why">{h(st.session_state[ek])}</div>', unsafe_allow_html=True)
            with st.container(horizontal=True, key=f"act_{key}_{it['id']}"):
                if st.button(t("read"), key=f"{key}_rd_{it['id']}"):
                    if it["category"] == RESEARCH:
                        paper_dialog(it)
                    else:
                        reader_dialog(it)
                if st.button(("★ " if it["starred"] else "☆ ") + ("Sačuvano" if it["starred"] and ui == "sr" else
                             "Saved" if it["starred"] else "Sačuvaj" if ui == "sr" else "Save"),
                             key=f"{key}_st_{it['id']}", help=t("star_help")):
                    db.toggle_star(con, it["id"])
                    st.rerun()
                if ai_on and ek not in st.session_state and st.button(t("explain"), key=f"{key}_ex_{it['id']}"):
                    with st.spinner(t("analyzing")):
                        try:
                            st.session_state[ek] = ai.explain_item(it, ui)
                        except Exception as ex:  # noqa: BLE001
                            st.session_state[ek] = f"Error: {ex}"
                    st.rerun()

    rest = list(items)
    if hero_first:
        one(rest.pop(0), True)
    if not grid:
        for it in rest:
            one(it, False)
        return
    for k in range(0, len(rest), 2):
        cols = st.columns(2)
        for col, it in zip(cols, rest[k:k + 2]):
            with col:
                one(it, False)


@st.dialog("FinNews", width="large")
def paper_dialog(p):
    p = dict(p)
    p.setdefault("abstract", p.get("summary") or "")
    p.setdefault("venue", p.get("source", ""))
    tr = ensure_translations([{"id": p["id"], "title": p["title"], "summary": ""}], lang).get(p["id"], {})
    st.markdown(f'<div class="fn-meta"><span class="fn-src" style="--c:{styles.src_color(p["venue"])}">{h(p["venue"] or "-")}</span>'
                f'<span>{h(p.get("authors") or "")}</span><span>{h(p.get("pub_date") or fmt_time(p.get("published", "")))}</span>'
                + (f'<span class="fn-cite">❝ {p["cited_by"]}</span>' if p.get("cited_by") is not None else "")
                + f'</div><div class="fn-read-title">{h(tr.get("title") or p["title"])}</div>', unsafe_allow_html=True)
    if lang and tr.get("title"):
        st.caption(p["title"])
    with st.spinner(t("p_reading")):
        info = reader.get_paper(con, p)
    if not ai_on:
        an_r = insights.analyze(info["abstract"], info["conclusion"], ui)
        lines = []
        if an_r["methods"]:
            lines.append(("Metod" if ui == "sr" else "Method", ", ".join(an_r["methods"])))
        if an_r["data"]:
            lines.append(("Podaci" if ui == "sr" else "Data", ", ".join(an_r["data"])))
        res_txt = an_r["result"]
        lim_txt = " ".join(an_r["limits"])
        if lang == "sr":
            pair = ai._free_translate([(res_txt, lim_txt)], "sr")[0] if (res_txt or lim_txt) else ("", "")
            res_txt, lim_txt = pair[0] or res_txt, pair[1] or lim_txt
        if res_txt:
            lines.append(("Glavni rezultat" if ui == "sr" else "Key result", res_txt))
        if lim_txt:
            lines.append(("Ograničenja" if ui == "sr" else "Limitations", lim_txt))
        if lines:
            st.markdown('<div class="fn-read-box"><div class="fn-kicker">' + t("p_analysis") + '</div>'
                        + "".join(f'<div class="fn-an"><b>{h(k)}</b><span>{h(v)}</span></div>' for k, v in lines)
                        + "</div>", unsafe_allow_html=True)
    if ai_on:
        an = db.get_article_ai(con, p["id"], ui, "paper_ai")
        if not an:
            with st.spinner(t("analyzing")):
                try:
                    an = ai.analyze_paper(p["title"], info["abstract"], info["conclusion"], ui, research.thesis_text())
                    db.save_article_ai(con, p["id"], ui, "paper_ai", an)
                except Exception as ex:  # noqa: BLE001
                    an = f"Error: {ex}"
        with st.container(key=f"readbox_p_{p['id']}"):
            st.markdown(f'<div class="fn-read-box"><div class="fn-kicker">{t("p_analysis")}</div></div>', unsafe_allow_html=True)
            st.markdown(an.replace("$", "\\$"))

    def show(text, kind):
        if not text:
            return
        body = text if not lang or lang == "en" else translated_full({"id": p["id"] + "_" + kind}, text, lang)
        st.markdown(f'<div class="fn-article">{paragraphs(body)}</div>', unsafe_allow_html=True)

    names = [t("p_abs"), t("p_concl")] + ([t("r_orig")] if lang == "sr" else [])
    tabs_p = st.tabs(names)
    with tabs_p[0]:
        show(info["abstract"], "abs")
    with tabs_p[1]:
        if info["conclusion"]:
            show(info["conclusion"], "concl")
        else:
            st.info(t("p_noconcl"))
    if lang == "sr":
        with tabs_p[2]:
            st.markdown(f'<div class="fn-article">{paragraphs(info["abstract"])}</div>', unsafe_allow_html=True)
            if info["conclusion"]:
                st.markdown(f'<div class="fn-section">{t("p_concl")}</div><div class="fn-article">{paragraphs(info["conclusion"])}</div>',
                            unsafe_allow_html=True)
    if info["future"]:
        st.markdown(f'<div class="fn-section">{t("p_future")}</div>', unsafe_allow_html=True)
        fut = info["future"]
        if lang == "sr":
            fut = translated_full({"id": p["id"] + "_fut"}, "\n".join(fut), "sr").split("\n")
        st.markdown("".join(f'<div class="fn-why">{h(x)}</div>' for x in fut if x.strip()), unsafe_allow_html=True)
    saved = p["id"] in db.saved_paper_ids(con)
    with st.container(horizontal=True, key=f"act_pd_{p['id']}"):
        st.link_button(t("r_open"), p.get("link") or "#")
        if info.get("pdf"):
            st.link_button(t("p_pdf"), info["pdf"])
        if st.button(t("p_saved_b") if saved else t("p_save"), key=f"pd_sv_{p['id']}"):
            db.toggle_paper_saved(con, p["id"])
            st.rerun()


def render_papers(papers, key, show_topics=False):
    if not papers:
        st.info(t("r_empty"))
        return
    tr = ensure_translations(papers, lang)
    saved = db.saved_paper_ids(con)
    topic_label = {tp["q"]: tp[ui] for tp in research.phd_topics()}
    for p in papers:
        tx = tr.get(p["id"], {})
        title, abstract = tx.get("title") or p["title"], tx.get("summary") or reader.clean_abstract(p.get("abstract"))
        with st.container(border=True, key=f"card_{key}_{p['id']}"):
            meta = (f'<span class="fn-src" style="--c:{styles.src_color(p["venue"])}">{h(p["venue"] or "-")}</span>'
                    f'<span>{h(p["authors"])}</span><span>{h(p["pub_date"] or str(p["year"]))}</span>'
                    f'<span class="fn-cite">❝ {p["cited_by"]} {t("cited")}</span>'
                    + (f'<span class="fn-pill">📄 {"slobodan pristup" if ui == "sr" else "open access"}</span>' if p.get("oa") else ""))
            if show_topics and p.get("topics"):
                meta += "".join(f'<span class="fn-pill">{h(topic_label.get(q, q))}</span>'
                                for q in sorted(set(p["topics"].split("|")))[:2])
            card(title, p["link"], meta, abstract[:420] + ("…" if len(abstract) > 420 else ""))
            with st.container(horizontal=True, key=f"act_{key}_{p['id']}"):
                if st.button(t("read"), key=f"{key}_rd_{p['id']}"):
                    paper_dialog(p)
                if st.button(t("p_saved_b") if p["id"] in saved else t("p_save"), key=f"{key}_sv_{p['id']}"):
                    db.toggle_paper_saved(con, p["id"])
                    st.rerun()


def dedupe(items, limit):
    """Spaja vesti o istoj temi iz različitih izvora; vraća (lista, {id: broj ostalih izvora})."""
    kept, extra, toks = [], {}, []
    for it in items:
        tk = fetcher.tokens(it["title"])
        dup = None
        for i, k in enumerate(toks):
            inter = len(tk & k)
            if tk and inter >= 3 and inter / len(tk | k) >= 0.3:
                dup = i
                break
        if dup is None:
            kept.append(it); toks.append(tk)
        else:
            extra[kept[dup]["id"]] = extra.get(kept[dup]["id"], 0) + 1
        if len(kept) >= limit:
            break
    return kept, extra


def brief_block(key, label, build_items, period_label):
    blang = ui
    existing = db.get_brief(con, key, blang)
    if st.button(label if not existing else t("remake"), key=f"btn_{key}", type="primary" if not existing else "secondary"):
        news, res_items = build_items()
        if not news and not res_items:
            st.warning(t("no_day"))
        else:
            tr = {} if ai_on else ensure_translations(news[:40] + res_items[:10], blang)
            with st.spinner(t("writing")):
                try:
                    content = ai.daily_brief(period_label, news, res_items, blang, tr)
                    db.save_brief(con, key, blang, content, utc_iso(datetime.now(timezone.utc)))
                    existing = db.get_brief(con, key, blang)
                except Exception as ex:  # noqa: BLE001
                    st.error(str(ex))
    if existing:
        st.caption(f"{t('made')}: {fmt_time(existing['created_at'])}")
        st.markdown(existing["content"].replace("$", "\\$"))
        st.download_button(t("dl_md"), existing["content"], file_name=f"brief_{key}_{blang}.md", key=f"dl_{key}")
    return existing


_d_start, _d_end = day_bounds(_td)
_k_news = con.execute("SELECT COUNT(*) FROM items WHERE published >= ? AND category != ?", (_d_start, RESEARCH)).fetchone()[0]
_upd = datetime.fromisoformat(last).astimezone().strftime("%H:%M") if last else "-"
try:
    _mk = stocks.market_strip(con)
except Exception:  # noqa: BLE001
    _mk = []
_num = (lambda v, d: (f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".") if ui == "sr" else f"{v:,.{d}f}"))
_MK_EN = {"Zlato $": "Gold $", "US 10g %": "US 10y %"}
_tick = "".join(f'<div class="fn-tk-i"><span>{h(n_ if ui == "sr" else _MK_EN.get(n_, n_))}</span><b>{_num(v_, d_)}</b>'
                f'<i class="{"fn-up" if c_ >= 0 else "fn-down"}">{"▲" if c_ >= 0 else "▼"} {abs(c_) * 100:.2f}%</i></div>'
                for n_, v_, c_, d_ in _mk)
st.markdown('<div class="fn-ticker">' + _tick
            + f'<div class="fn-tk-i fn-tk-meta"><span>{"vesti danas" if ui == "sr" else "news today"}</span><b>{_k_news}</b></div>'
            + f'<div class="fn-tk-i fn-tk-meta"><span><i class="fn-live"></i>{"osveženo" if ui == "sr" else "updated"}</span><b>{_upd}</b></div></div>',
            unsafe_allow_html=True)

NAV = {"t_home": ("Početna", "Home"), "t_news": ("Vesti", "News"), "t_stocks": ("Akcije", "Stocks"),
       "t_port": ("Portfolio", "Portfolio"), "t_brief": ("Pregled", "Review"), "t_res": ("Istraživanja", "Research"),
       "t_arch": ("Arhiva", "Archive"), "t_set": ("Podešavanja", "Settings")}
HEADS = {
    "t_news": (("Vesti", "Najvažnije iz finansija, kompanija, Srbije i sveta. Izaberi period, pročitaj sažetak ili ceo tekst."),
               ("News", "The most important stories from finance, companies, Serbia and the world. Pick a period, read the summary or the full story.")),
    "t_stocks": (("Akcije", "Prilike na tržištu, pretraga svih akcija i grafikoni - pronađi akciju i odmah vidi kako se kreće."),
                 ("Stocks", "Market opportunities, search across all stocks and charts - find a stock and see how it moves.")),
    "t_port": (("Tvoj portfolio", "Vrednost, prinos i raspodela. Sve stavke možeš da menjaš, dodaješ i brišeš."),
               ("Your portfolio", "Value, return and allocation. You can edit, add and delete everything.")),
    "t_brief": (("Pregled perioda", "Šta je bilo bitno - vesti, naučni nalazi i tržišta za 1 do 180 dana."),
                ("Period review", "What mattered - news, research findings and markets for 1 to 180 days.")),
    "t_res": (("Istraživanja", "Najnoviji i najcitiraniji radovi, njihovi ključni nalazi i ideje za doktorat."),
              ("Research", "The newest and most cited papers, their key findings and PhD ideas.")),
    "t_arch": (("Arhiva", "Pretraga svih vesti, pregled po mesecima i sačuvane vesti."),
               ("Archive", "Search all stories, monthly review and saved stories.")),
    "t_set": (("Podešavanja", "Jezik, izvori vesti, lista akcija, telefon i menu bar."),
              ("Settings", "Language, news sources, watchlist, phone and menu bar.")),
}
PAGES = list(NAV)
# starije stranice su sada pod-pregledi: (glavna stranica, ključ pod-menija, vrednost)
_SUB = {"t_top": ("t_news", "news_sub", "fin"), "t_world": ("t_news", "news_sub", "srb"), "t_rr": ("t_res", "res_sub", "t_rr"),
        "t_phd": ("t_res", "res_sub", "t_phd"), "t_6m": ("t_arch", "arch_sub", "t_6m"), "t_saved": ("t_arch", "arch_sub", "t_saved")}
if st.session_state.get("nav") in _SUB:
    _m, _sk, _sv = _SUB[st.session_state["nav"]]
    st.session_state[_sk] = _sv
    st.session_state["nav"] = _m
if st.session_state.get("nav") not in PAGES:
    st.session_state["nav"] = "t_home"


def go(pg, **sub):
    """Prelazak na drugu stranicu iz dugmeta (koristi se kao on_click)."""
    st.session_state["nav"] = pg
    st.session_state.update(sub)


page = st.radio("nav", PAGES, format_func=lambda k: NAV[k][0 if ui == "sr" else 1], key="nav",
                horizontal=True, label_visibility="collapsed")
if page in HEADS:
    _ht, _hs = HEADS[page][0 if ui == "sr" else 1]
    st.markdown(f'<div class="fn-phead"><h2>{_ht}</h2><p>{_hs}</p></div>', unsafe_allow_html=True)
if page == "t_res":
    page = st.segmented_control("res_sub", ["t_res", "t_rr", "t_phd"], key="res_sub", default=None if "res_sub" in st.session_state else "t_rr",
                                label_visibility="collapsed",
                                format_func=lambda k: {"t_res": ("Radovi", "Papers"), "t_rr": ("Najvažniji nalazi", "Key findings"),
                                                       "t_phd": ("Doktorat radar", "PhD radar")}[k][0 if ui == "sr" else 1]) or "t_rr"
if page == "t_arch":
    page = st.segmented_control("arch_sub", ["t_arch", "t_6m", "t_saved"], key="arch_sub", default=None if "arch_sub" in st.session_state else "t_arch",
                                label_visibility="collapsed",
                                format_func=lambda k: {"t_arch": ("Pretraga arhive", "Search archive"), "t_6m": ("Po mesecima", "By month"),
                                                       "t_saved": ("★ Sačuvano", "★ Saved")}[k][0 if ui == "sr" else 1]) or "t_arch"


def _pin_hash(pin):
    import hashlib
    return hashlib.sha256(("finnews:" + pin.strip()).encode()).hexdigest()


if PUBLIC and page in ("t_port", "t_set") and not st.session_state.get("unlocked"):
    _ph = _cfg.get("pin_hash") or (_pin_hash(os.environ["FINNEWS_PIN"]) if os.environ.get("FINNEWS_PIN") else None)
    st.markdown(f'<div class="fn-lock"><div class="fn-lock-ic">🔒</div><div class="fn-title">'
                f'{"Lični deo aplikacije" if ui == "sr" else "Private section"}</div><p class="fn-sum">'
                + ("Portfolio i podešavanja vidi samo vlasnik. Vesti, akcije, istraživanja i pregledi su otvoreni za sve."
                   if ui == "sr" else "Portfolio and settings are visible to the owner only. News, stocks, research and briefings are open to everyone.")
                + "</p></div>", unsafe_allow_html=True)
    if _ph:
        _c1, _c2, _c3 = st.columns([1, 1.2, 1])
        with _c2.form("pin_form", border=False):
            _pin = st.text_input("PIN", type="password")
            if st.form_submit_button("Otključaj" if ui == "sr" else "Unlock", type="primary"):
                if _pin_hash(_pin) == _ph:
                    st.session_state["unlocked"] = True
                    st.rerun()
                else:
                    st.error("Pogrešan PIN." if ui == "sr" else "Wrong PIN.")
    st.stop()

# ---------- Dnevni brief ----------
THEMES = [("Fed", "Fed", r"\bfed\b|federal reserve|fomc|powell"), ("ECB", "ECB", r"\becb\b|lagarde|eurozone|euro zone"),
          ("Inflacija", "Inflation", r"inflation|\bcpi\b|\bpce\b|inflacij"),
          ("Kamate i obveznice", "Rates & bonds", r"rate cut|rate hike|interest rate|yield|treasur|bond|kamat"),
          ("Tržište rada", "Labour market", r"\bjobs\b|payroll|unemployment|labor market"),
          ("Rezultati kompanija", "Earnings", r"earnings|guidance|profit|revenue"),
          ("Tehnologija i AI", "Tech & AI", r"nvidia|\bai\b|artificial intelligence|chip|semiconductor|apple|microsoft|alphabet|meta\b"),
          ("Nafta i energija", "Oil & energy", r"\boil\b|opec|crude|natural gas|energy"), ("Zlato", "Gold", r"\bgold\b"),
          ("Kripto", "Crypto", r"bitcoin|crypto|stablecoin|ether"), ("Carine i trgovina", "Tariffs & trade", r"tariff|trade war|sanction|export"),
          ("Kina", "China", r"china|chinese|beijing|pboc"), ("Srbija", "Serbia", r"\bnbs\b|srbij|serbia|belex|dinar")]


def rows_html(items, tr):
    out = ""
    for it in items:
        tx = tr.get(it["id"], {})
        out += (f'<div class="fn-row"><span class="fn-row-time">{fmt_time(it["published"])}</span>'
                f'<span class="fn-src" style="--c:{styles.src_color(it["source"])}">{h(it["source"][:22])}</span>'
                f'<a class="fn-row-title" href="{h(it["link"])}" target="_blank">{h(tx.get("title") or it["title"])}</a>'
                f'{dots(it["score"])}</div>')
    return f'<div class="fn-rows">{out}</div>'


def brief_live(start, end, long=False):
    import re as _re
    news = db.query_items(con, start, end, exclude_categories=[RESEARCH], order="score", limit=1500 if long else 400)
    res_items = db.query_items(con, start, end, categories=[RESEARCH], order="score", limit=5)
    if not news and not res_items:
        st.info(t("no_day"))
        return
    top, extra = dedupe(news, 80)
    tr = ensure_translations(top[:45] + res_items, lang)
    # teme dana
    counts = []
    for sr_l, en_l, rx in THEMES:
        n_ = sum(1 for it in news if _re.search(rx, it["title"].lower()))
        if n_:
            counts.append((n_, sr_l if ui == "sr" else en_l))
    counts.sort(reverse=True)
    chips = "".join(f'<span class="fn-chip">{h(lbl)} <b>{n_}</b></span>' for n_, lbl in counts[:8])
    stats = (f'{len(news)} vesti · {len({x["source"] for x in news})} izvora' if ui == "sr"
             else f'{len(news)} stories · {len({x["source"] for x in news})} sources')
    st.markdown(f'<div class="fn-section">{("Teme perioda" if long else "Teme dana") if ui == "sr" else ("Themes of the period" if long else "Themes of the day")}</div>'
                f'<div class="fn-chips">{chips}<span class="fn-chip fn-chip-muted">{stats}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="fn-section">{("Najvažnije u periodu" if long else "Ukratko - 3 najvažnije vesti") if ui == "sr" else ("What mattered most" if long else "In short - top 3 stories")}</div>',
                unsafe_allow_html=True)
    fin_top = [x for x in top if x["category"] in NEWS_CATS][:5 if long else 3]
    if fin_top:
        render_items(fin_top, "brtop", extra=extra, hero_first=True, grid=True)
    by_cat = {}
    for it in top:
        if it not in fin_top:
            by_cat.setdefault(it["category"], []).append(it)
    for cat in NEWS_CATS + ["Kompanije"] + GENERAL_CATS:
        if by_cat.get(cat):
            label = {"Vesti": "Tržišta", "Centralne banke i makro": "Centralne banke i makro", "Analize i blogovi": "Analize",
                     "Srbija i region": "Finansije u Srbiji", "Kompanije": "Kompanije", "Srbija": "Srbija - opšte vesti",
                     "Svet": "Svet - opšte vesti"}[cat] if ui == "sr" else \
                    {"Vesti": "Markets", "Centralne banke i makro": "Central banks & macro", "Analize i blogovi": "Analysis",
                     "Srbija i region": "Finance in Serbia", "Kompanije": "Companies", "Srbija": "Serbia - general news",
                     "Svet": "World - general news"}[cat]
            st.markdown(f'<div class="fn-section">{styles.CAT_ICON.get(cat, "")} {label}</div>' + rows_html(by_cat[cat][:7], tr),
                        unsafe_allow_html=True)
    if res_items:
        st.markdown(f'<div class="fn-section">🔬 {"Nova istraživanja" if ui == "sr" else "New research"}</div>'
                    + rows_html(res_items, tr), unsafe_allow_html=True)


# ---------- Portfolio ----------
if page == "t_port":
    import altair as alt
    L = (lambda a, b: a if ui == "sr" else b)
    eur = (lambda x, d=2: "-" if x is None else (f"{x:,.{d}f} €".replace(",", "X").replace(".", ",").replace("X", ".") if ui == "sr" else f"€{x:,.{d}f}"))
    sgn = (lambda x: "-" if x is None else (f"{x * 100:+.2f}%".replace(".", ",") if ui == "sr" else f"{x * 100:+.2f}%"))
    stocks._init(con)
    portfolio._init(con)
    p_upd = db.get_meta(con, "prices_refreshed")
    missing_px = [t_ for t_ in portfolio.tickers(con) if not con.execute("SELECT 1 FROM prices WHERE ticker=? LIMIT 1", (t_,)).fetchone()]
    cA, cB = st.columns([4, 1], vertical_alignment="center")
    cA.caption(L("Cene: Yahoo Finance (Xetra, EUR), dnevne, sa zakašnjenjem. Osveženo: ", "Prices: Yahoo Finance (Xetra, EUR), daily, delayed. Updated: ")
               + (fmt_time(p_upd) if p_upd else "-"))
    if cB.button("↻ " + L("Osveži cene", "Refresh prices"), key="pf_refresh") or (missing_px and not st.session_state.get("pf_auto")):
        st.session_state["pf_auto"] = True
        with st.spinner(L("Preuzimam cene...", "Fetching prices...")):
            try:
                stocks.refresh_prices(con)
                stocks.refresh_info(con)
            except Exception as ex:  # noqa: BLE001
                st.error(f"Yahoo Finance: {ex}")
    infos_p = {t_: stocks.info(con, t_) for t_ in portfolio.tickers(con)}
    vals = portfolio.valuation(con, infos_p)
    avals = portfolio.asset_values(con)
    tot_a = sum(a["value"] or 0 for a in avals)
    tot_v = sum(r["value"] or 0 for r in vals)
    tot_c = sum(r["cost"] for r in vals)
    day_e = sum(r["day_eur"] or 0 for r in vals)
    cls = (lambda x: "" if not x else ("fn-up" if x > 0 else "fn-down"))
    _gs = portfolio.gold_series(con, 12)
    g_idx = _gs[-1][1] if _gs else portfolio.gold_eur(con)
    g_day = (_gs[-1][1] / _gs[-2][1] - 1) if len(_gs) > 1 else None
    day_e += sum((a["value"] or 0) * (g_day or 0) for a in avals if a["kind"] == "gold")
    tot_ca = tot_c + sum(a["base_eur"] for a in avals)
    pl_t = (tot_v + tot_a - tot_ca) if (tot_v or tot_a) else None
    kp = [(eur(tot_v + tot_a, 0), L("ukupna vrednost portfolija", "total portfolio value"), ""),
          (eur(tot_ca, 0), L("uloženo", "invested"), ""),
          (eur(pl_t), L("dobit / gubitak", "profit / loss"), cls(pl_t)),
          (sgn((tot_v + tot_a) / tot_ca - 1) if tot_ca and (tot_v + tot_a) else "-", L("prinos", "return"), cls(pl_t)),
          (eur(day_e), L("danas", "today"), cls(day_e)),
          (f"{len(vals) + len(avals)}", L("pozicija", "positions"), "")]
    st.markdown('<div class="fn-kpis fn-kpis-big">' + "".join(
        f'<div class="fn-kpi"><b class="{c_}">{h(v)}</b><span>{h(l)}</span></div>' for v, l, c_ in kp) + "</div>", unsafe_allow_html=True)

    # --- pozicije
    st.markdown(f'<div class="fn-section">{L("Pozicije", "Holdings")}</div>', unsafe_allow_html=True)
    kind_lbl = {"gold": L("Zlato (indeks)", "Gold (index)"), "bond": L("Obveznice", "Bonds"), "savings": L("Štednja", "Savings"),
                "cash": L("Gotovina", "Cash"), "other": L("Ostalo", "Other")}
    tot_all = tot_v + tot_a
    if vals or avals:
        prow = [{L("Klasa", "Class"): L("ETF / akcija", "ETF / stock"), L("Simbol", "Symbol"): r["ticker"].replace(".DE", ""), L("Naziv", "Name"): r["name"],
                 L("Količina", "Qty"): r["qty"], L("Nabavna cena", "Avg cost"): r["avg"],
                 L("Nabavna vrednost", "Cost"): r["cost"], L("Tržišna cena", "Price"): r["price"],
                 L("Tržišna vrednost", "Value"): r["value"], L("Razlika %", "P/L %"): (r["pl_pct"] or 0) * 100,
                 L("Razlika €", "P/L €"): r["pl"], L("Danas %", "Today %"): (r["day"] or 0) * 100,
                 L("Udeo", "Weight"): (r["value"] or 0) / tot_all * 100 if tot_all else 0} for r in vals]
        for a in avals:  # zlato se vodi kao ulaganje u indeks zlata, dinarski deo kao obveznica sa fiksnim prinosom
            a_pl = (a["value"] or 0) - a["base_eur"]
            prow.append({L("Klasa", "Class"): kind_lbl.get(a["kind"], a["kind"]),
                         L("Simbol", "Symbol"): {"gold": "XAU/EUR", "bond": "RSD " + f"{(a['rate'] or 0) * 100:.1f}%", "savings": "RSD"}.get(a["kind"], a["currency"]),
                         L("Naziv", "Name"): a["name"], L("Količina", "Qty"): None, L("Nabavna cena", "Avg cost"): None,
                         L("Nabavna vrednost", "Cost"): a["base_eur"], L("Tržišna cena", "Price"): g_idx if a["kind"] == "gold" else None,
                         L("Tržišna vrednost", "Value"): a["value"], L("Razlika %", "P/L %"): a_pl / a["base_eur"] * 100 if a["base_eur"] else 0,
                         L("Razlika €", "P/L €"): a_pl, L("Danas %", "Today %"): (g_day or 0) * 100 if a["kind"] == "gold" else 0,
                         L("Udeo", "Weight"): (a["value"] or 0) / tot_all * 100 if tot_all else 0})
        for r_ in prow:  # prazna polja umesto "None" za stavke bez količine i jedinične cene
            for c_ in (L("Nabavna cena", "Avg cost"), L("Tržišna cena", "Price")):
                r_[c_] = "" if r_[c_] is None else f"{r_[c_]:,.2f} €"
            r_[L("Količina", "Qty")] = "" if r_[L("Količina", "Qty")] is None else f"{r_[L('Količina', 'Qty')]:g}"
        df = pd.DataFrame(prow)
        pcs = [L("Razlika %", "P/L %"), L("Razlika €", "P/L €"), L("Danas %", "Today %")]
        sty = df.style.map(lambda v: f"color: {'#9CC79A' if (v or 0) > 0 else '#E07C8A' if (v or 0) < 0 else 'inherit'}", subset=pcs)
        money = {c_: st.column_config.NumberColumn(format="%.2f €") for c_ in [L("Nabavna vrednost", "Cost"), L("Tržišna vrednost", "Value"), L("Razlika €", "P/L €")]}
        st.dataframe(sty, hide_index=True, column_config={
            **money, L("Razlika %", "P/L %"): st.column_config.NumberColumn(format="%+.2f%%"),
            L("Danas %", "Today %"): st.column_config.NumberColumn(format="%+.2f%%"),
            L("Količina", "Qty"): st.column_config.TextColumn(width="small"),
            L("Simbol", "Symbol"): st.column_config.TextColumn(width="small"),
            L("Klasa", "Class"): st.column_config.TextColumn(width="small"),
            L("Naziv", "Name"): st.column_config.TextColumn(width="medium"),
            L("Udeo", "Weight"): st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%", width="small")})
    else:
        st.info(L("Još nema izvršenih pozicija.", "No filled positions yet."))

    if vals:
        with st.expander("➕➖ " + L("Dokupi ili prodaj deo pozicije", "Buy more or sell part of a position")):
            with st.form("pf_quick", clear_on_submit=True, border=False):
                q1, q2, q3, q4, q5, q6 = st.columns([2, 1.1, 1, 1, 1, 1.2])
                q_tk = q1.selectbox(L("Pozicija", "Position"), [r["ticker"] for r in vals],
                                    format_func=lambda t_: f'{t_.replace(".DE", "")} - {next(r["name"] for r in vals if r["ticker"] == t_)[:34]}')
                q_side = q2.selectbox(L("Radnja", "Action"), ["buy", "sell"], format_func=lambda x: L("Dokupi", "Buy more") if x == "buy" else L("Prodaj", "Sell"))
                q_qty = q3.number_input(L("Količina", "Qty"), 0.0, 1e7, 1.0, 1.0)
                q_px = q4.number_input(L("Cena €", "Price €"), 0.0, 1e7, 0.0, 0.01, help=L("Prazno (0) = poslednja tržišna cena", "Empty (0) = last market price"))
                q_fee = q5.number_input(L("Provizija €", "Fee €"), 0.0, 1e4, 0.0, 0.5)
                q_d = q6.date_input(L("Datum", "Date"), date.today(), format="DD.MM.YYYY")
                if st.form_submit_button(L("Sačuvaj", "Save"), type="primary"):
                    r_ = next(r for r in vals if r["ticker"] == q_tk)
                    px_ = q_px or r_["price"]
                    if q_side == "sell" and q_qty > r_["qty"] + 1e-9:
                        st.error(L(f"Imaš samo {r_['qty']:g} komada.", f"You only hold {r_['qty']:g}."))
                    elif q_qty <= 0 or not px_:
                        st.error(L("Unesi količinu i cenu.", "Enter quantity and price."))
                    else:
                        portfolio.add(con, q_tk, r_["name"], r_.get("isin") or "", q_side, q_qty, px_, q_fee, q_d.isoformat(), "filled")
                        st.success(L("Sačuvano.", "Saved."))
                        st.rerun()

    # --- nalozi na čekanju
    pend = [x for x in portfolio.txns(con) if x["status"] == "pending"]
    if pend:
        st.markdown(f'<div class="fn-section">{L("Nalozi na čekanju", "Pending orders")}</div>', unsafe_allow_html=True)
        for o in pend:
            cur_px = portfolio._closes(con, o["ticker"])
            last_px = cur_px[-1][1] if cur_px else None
            with st.container(border=True, key=f"card_pend_{o['id']}"):
                st.markdown(f'<div class="fn-meta"><span class="fn-badge">{L("nalog", "order")}</span>'
                            f'<span class="fn-src" style="--c:#C99A7A">{h(o["ticker"].replace(".DE", ".XETRA"))}</span>'
                            f'<span>{L("kupovina" if o["side"] == "buy" else "prodaja", "buy" if o["side"] == "buy" else "sell")} · '
                            f'{o["qty"]:g} × LIMIT {eur(o["limit_price"])} · {o["d"] or ""}</span></div>'
                            f'<div class="fn-title">{h(o["name"])}</div>'
                            + (f'<p class="fn-sum">{L("Poslednja cena", "Last price")}: {eur(last_px)} - '
                               + (L("ispod limita, nalog bi trebalo da se izvrši", "below the limit, the order should fill") if last_px <= o["limit_price"]
                                  else L(f"{(last_px / o['limit_price'] - 1) * 100:.1f}% iznad limita", f"{(last_px / o['limit_price'] - 1) * 100:.1f}% above the limit"))
                               + "</p>" if last_px and o["limit_price"] else "")
                            + f'<p class="fn-sum" style="font-size:.8rem">{L("Dnevni (DAY) nalog važi do kraja današnjeg trgovanja; ako se ne izvrši, otkaži ga ovde ili unesi novi.", "A DAY order is valid until today’s close; if it does not fill, cancel it here or enter a new one.")}</p>',
                            unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns([1.2, 1, 1.2, 1.4], vertical_alignment="bottom")
                fp = c1.number_input(L("Izvršna cena (€)", "Fill price (€)"), 0.0, 1e6, float(o["limit_price"] or 0), 0.01, key=f"fp_{o['id']}")
                ff = c2.number_input(L("Provizija (€)", "Fee (€)"), 0.0, 1000.0, 0.0, 0.5, key=f"ff_{o['id']}")
                fd = c3.date_input(L("Datum", "Date"), date.today(), key=f"fd_{o['id']}", format="DD.MM.YYYY")
                with c4.container(horizontal=True, key=f"act_pend_{o['id']}"):
                    if st.button("✅ " + L("Izvršen", "Filled"), key=f"fill_{o['id']}"):
                        portfolio.fill(con, o["id"], fp, ff, fd.isoformat())
                        st.rerun()
                    if st.button("🗑 " + L("Otkaži", "Cancel"), key=f"cancel_{o['id']}"):
                        portfolio.delete(con, o["id"])
                        st.rerun()

    # --- zlato, štednja, gotovina
    st.markdown(f'<div class="fn-section">{L("Zlato, obveznice i gotovina - detalji", "Gold, bonds and cash - details")}</div>', unsafe_allow_html=True)
    g_now = portfolio.gold_eur(con)
    for a in avals:
        with st.container(border=True, key=f"card_asset_{a['id']}"):
            if a["kind"] == "gold":
                sub = (L(f"vodi se kao ulaganje u indeks cene zlata u evrima · od unosa: {sgn(a['extra'])}", f"held as an investment in the gold price index in EUR · since entry: {sgn(a['extra'])}")
                       if a["extra"] is not None else L("vrednost će pratiti indeks cene zlata posle osvežavanja cena", "value will track the gold price index after a price refresh"))
            elif a["kind"] == "bond":
                sub = L(f"{a['amount']:,.0f} RSD · fiksni prinos {(a['rate'] or 0) * 100:.2f}% godišnje · obračunat prinos {a['extra'] or 0:,.0f} RSD · kurs {a['rsd']:.2f}",
                        f"{a['amount']:,.0f} RSD · fixed yield {(a['rate'] or 0) * 100:.2f}% a year · accrued {a['extra'] or 0:,.0f} RSD · EUR/RSD {a['rsd']:.2f}").replace(",", ".")
                if a["maturity"]:
                    sub += L(f" · dospeva {a['maturity']}", f" · matures {a['maturity']}")
            elif a["kind"] == "savings":
                sub = (L(f"{a['amount']:,.0f} RSD · kamata {(a['rate'] or 0) * 100:.2f}% (bez poreza na dinarsku štednju) · obračunata kamata {a['extra'] or 0:,.0f} RSD · kurs {a['rsd']:.2f}",
                         f"{a['amount']:,.0f} RSD · interest {(a['rate'] or 0) * 100:.2f}% (dinar savings interest is tax-free) · accrued {a['extra'] or 0:,.0f} RSD · rate {a['rsd']:.2f}").replace(",", "."))
                if a["maturity"]:
                    sub += L(f" · dospeva {a['maturity']}", f" · matures {a['maturity']}")
            else:
                sub = f"{a['amount']:,.2f} {a['currency']}"
            st.markdown(f'<div class="fn-ind"><div><div class="fn-meta"><span class="fn-src" style="--c:{"#D6B072" if a["kind"] == "gold" else "#C99A7A"}">{h(kind_lbl.get(a["kind"], a["kind"]))}</span></div>'
                        f'<div class="fn-ind-name" style="margin-top:6px">{h(a["name"])}</div><div class="fn-sum" style="margin:2px 0 0">{h(sub)}</div></div>'
                        f'<div class="fn-ind-val"><b>{eur(a["value"], 0)}</b><span>{(a["value"] or 0) / (tot_v + tot_a) * 100 if (tot_v + tot_a) else 0:.0f}% {L("imovine", "of wealth")}</span></div></div>',
                        unsafe_allow_html=True)
    with st.expander("✏️ " + L("Izmeni, dodaj ili obriši zlato, obveznice, štednju i gotovinu", "Edit, add or delete gold, bonds, savings and cash")):
        st.caption(L("Menjaj direktno u tabeli. Novi red dodaješ na dnu (+), a brišeš ga tako što ga označiš levo i klikneš 🗑. Na kraju klikni „Sačuvaj“.",
                     "Edit directly in the table. Add a row at the bottom (+), delete by selecting it on the left and clicking 🗑. Then click 'Save'."))
        _kinds = ["gold", "bond", "savings", "cash", "other"]
        adf = pd.DataFrame([{"id": a["id"], "kind": a["kind"], "name": a["name"], "amount": a["amount"], "currency": a["currency"],
                             "rate": (a["rate"] or 0) * 100, "start": a["start"] or "", "maturity": a["maturity"] or ""} for a in portfolio.assets(con)],
                           columns=["id", "kind", "name", "amount", "currency", "rate", "start", "maturity"])
        ed_a = st.data_editor(adf, num_rows="dynamic", hide_index=True, key="asset_editor", width="stretch", column_config={
            "id": None,
            "kind": st.column_config.SelectboxColumn(L("Vrsta", "Type"), options=_kinds, required=True, default="gold",
                                                     help=" / ".join(f"{k} = {kind_lbl[k]}" for k in _kinds)),
            "name": st.column_config.TextColumn(L("Naziv", "Name"), required=True),
            "amount": st.column_config.NumberColumn(L("Iznos", "Amount"), min_value=0.0, step=100.0, format="%.2f", required=True),
            "currency": st.column_config.SelectboxColumn(L("Valuta", "Currency"), options=["EUR", "RSD", "USD"], default="EUR", required=True),
            "rate": st.column_config.NumberColumn(L("Prinos %", "Yield %"), min_value=0.0, max_value=50.0, step=0.05, format="%.2f"),
            "start": st.column_config.TextColumn(L("Od (GGGG-MM-DD)", "From (YYYY-MM-DD)")),
            "maturity": st.column_config.TextColumn(L("Dospeće", "Maturity"))})
        if st.button("💾 " + L("Sačuvaj imovinu", "Save assets"), key="asset_save", type="primary"):
            old_ids = set(adf["id"].dropna().astype(int))
            new_ids = set()
            for r_ in ed_a.to_dict("records"):
                if not r_.get("name") or r_.get("amount") is None or pd.isna(r_.get("amount")):
                    continue
                rate_ = (float(r_["rate"]) / 100) if r_.get("rate") and not pd.isna(r_["rate"]) else None
                if r_.get("id") is not None and not pd.isna(r_["id"]):
                    aid = int(r_["id"]); new_ids.add(aid)
                    old = next(a for a in portfolio.assets(con) if a["id"] == aid)
                    kw = {"kind": r_["kind"], "name": r_["name"], "amount": float(r_["amount"]), "currency": r_["currency"], "rate": rate_,
                          "start": r_.get("start") or old["start"], "maturity": r_.get("maturity") or None}
                    if r_["kind"] == "gold" and float(r_["amount"]) != old["amount"]:
                        kw["gold_base"] = g_now  # nova procena vrednosti postaje polazna tačka za indeks zlata
                    portfolio.update_asset(con, aid, **kw)
                else:
                    portfolio.add_asset(con, r_["kind"] or "other", r_["name"], float(r_["amount"]), r_.get("currency") or "EUR",
                                        rate=rate_, start=r_.get("start") or None, maturity=r_.get("maturity") or None)
            for aid in old_ids - new_ids:
                portfolio.delete_asset(con, aid)
            st.success(L("Sačuvano.", "Saved."))
            st.rerun()
    if tot_v + tot_a:
        cls_alloc = [(L("Akcije i ETF-ovi", "Stocks & ETFs"), tot_v)] + [
            (kind_lbl[k], sum(a["value"] or 0 for a in avals if a["kind"] == k)) for k in ("gold", "bond", "savings", "cash", "other")]
        cls_alloc = [(k, v_) for k, v_ in cls_alloc if v_]
        st.markdown(f'<div class="fn-kicker" style="margin-top:12px">{L("Raspodela ukupne imovine", "Overall allocation")}</div>'
                    '<div class="fn-alloc">' + "".join(
                        f'<i style="flex:{v_:.0f}; background:{c_}" title="{h(k)}"></i>' for (k, v_), c_ in
                        zip(cls_alloc, ["#C2435F", "#D6B072", "#C99A7A", "#9CC79A", "#B9A0C9", "#E07C8A"])) + "</div>"
                    '<div class="fn-chips" style="margin-top:8px">' + "".join(
                        f'<span class="fn-chip"><span style="color:{c_}">●</span> {h(k)} <b>{v_ / (tot_v + tot_a) * 100:.0f}%</b></span>'
                        for (k, v_), c_ in zip(cls_alloc, ["#C2435F", "#D6B072", "#C99A7A", "#9CC79A", "#B9A0C9", "#E07C8A"])) + "</div>",
                    unsafe_allow_html=True)

    if vals:
        c1, c2 = st.columns([3, 2])
        # --- kretanje vrednosti
        with c1:
            st.markdown(f'<div class="fn-section">{L("Kretanje vrednosti portfolija", "Portfolio value over time")}</div>',
                        unsafe_allow_html=True)
            rng_p = st.segmented_control("prng", ["1M", "6M", "1Y", "2Y"], default="1Y", key="pf_rng", label_visibility="collapsed") or "1Y"
            hist = portfolio.total_history(con, {"1M": 31, "6M": 183, "1Y": 366, "2Y": 732}[rng_p])
            if hist:
                n_tot, n_sec, n_inv = L("Ukupno", "Total"), L("ETF-ovi i akcije", "ETFs & stocks"), L("Uloženo", "Invested")
                hdf = pd.DataFrame([{"d": pd.to_datetime(d_), n_tot: tv_, n_sec: sv_, n_inv: tot_ca} for d_, sv_, tv_ in hist])
                hl = hdf.melt("d", var_name="s", value_name="v")
                ch = alt.Chart(hl).mark_line(strokeWidth=2).encode(
                    x=alt.X("d:T", title=None, axis=alt.Axis(format="%d.%m.%y", grid=False, labelColor="#A8979A")),
                    y=alt.Y("v:Q", title=None, scale=alt.Scale(zero=False), axis=alt.Axis(gridColor="#2C2124", labelColor="#A8979A", format=",.0f")),
                    color=alt.Color("s:N", scale=alt.Scale(domain=[n_tot, n_sec, n_inv], range=["#C2435F", "#C99A7A", "#A8979A"]), legend=alt.Legend(orient="top", title=None, labelColor="#F5ECE4")),
                    strokeDash=alt.condition(alt.datum.s == n_inv, alt.value([4, 3]), alt.value([1, 0])),
                    tooltip=[alt.Tooltip("d:T", format="%d.%m.%Y"), "s:N", alt.Tooltip("v:Q", format=",.2f")],
                ).properties(height=280).configure_view(strokeWidth=0).configure(background="transparent")
                st.altair_chart(ch, width="stretch")
                st.caption(L("Pokazuje kako bi se kretala vrednost sadašnjeg portfolija da si ga držala ceo period: ETF-ovi po tržišnim cenama, "
                             "zlato po indeksu cene zlata u evrima, obveznice sa ravnomernim prirastom prinosa. Nije stvarna istorija kupovina.",
                             "Shows how today's portfolio would have moved over the whole period: ETFs at market prices, gold by the gold "
                             "price index in EUR, bonds with steady yield accrual. Not your actual purchase history."))
        # --- izloženost
        with c2:
            st.markdown(f'<div class="fn-section">{L("Izloženost po regionima", "Exposure by region")}</div>', unsafe_allow_html=True)
            ex = portfolio.exposure(vals, lambda t_: eu.country(t_, infos_p.get(t_)))
            st.markdown('<div class="fn-fbars" style="grid-template-columns:1fr">' + "".join(
                f'<div class="fn-fbar" style="grid-template-columns: 1fr 120px 46px"><span>{h(k if ui == "sr" else portfolio.REGION_EN.get(k, k))}</span>'
                f'<div><i style="width:{v_ * 100:.0f}%"></i></div><span style="text-align:right">{v_ * 100:.0f}%</span></div>' for k, v_ in ex)
                + "</div>", unsafe_allow_html=True)
            st.markdown(f'<div class="fn-section">{L("Udeo pozicija", "Position weights")}</div>', unsafe_allow_html=True)
            st.markdown('<div class="fn-fbars" style="grid-template-columns:1fr">' + "".join(
                f'<div class="fn-fbar" style="grid-template-columns: 1fr 120px 46px"><span>{h(r["ticker"].replace(".DE", ""))}</span>'
                f'<div><i style="width:{r["weight"] * 100:.0f}%"></i></div><span style="text-align:right">{r["weight"] * 100:.0f}%</span></div>' for r in vals)
                + "</div>", unsafe_allow_html=True)
            us_share = dict(ex).get("SAD", 0)
            if us_share > 0.75:
                st.markdown('<div class="fn-why">' + h(L(
                    f"Oko {us_share * 100:.0f}% portfolija je izloženo američkom tržištu (S&P 500 ETF + američki deo MSCI World + pojedinačne "
                    "američke akcije). To nije greška, ali znači da rezultat najviše zavisi od SAD i kursa dolara prema evru.",
                    f"About {us_share * 100:.0f}% of the portfolio is exposed to the US market (S&P 500 ETF + the US part of MSCI World + "
                    "individual US stocks). That is not a mistake, but results depend mostly on the US and the dollar-euro rate.")) + "</div>",
                            unsafe_allow_html=True)
        st.caption(L("Izloženost fondova je približna (prema strukturi indeksa) i služi za orijentaciju.",
                     "Fund exposure is approximate (based on index composition) and indicative only."))

    # --- nova transakcija
    st.markdown(f'<div class="fn-section">{L("Dodaj kupovinu, prodaju ili nalog", "Add a buy, sell or order")}</div>', unsafe_allow_html=True)
    with st.form("pf_add", clear_on_submit=True, border=True):
        c1, c2, c3 = st.columns([1.2, 2.2, 1.6])
        tk_in = c1.text_input(L("Simbol (Yahoo)", "Symbol (Yahoo)"), placeholder="SXR8.DE",
                              help=L("Xetra hartije imaju nastavak .DE (npr. EUNL.DE, SAP.DE, NVD.DE). Proveri simbol na finance.yahoo.com.",
                                     "Xetra securities end in .DE (e.g. EUNL.DE, SAP.DE, NVD.DE). Check the symbol on finance.yahoo.com."))
        nm_in = c2.text_input(L("Naziv", "Name"), placeholder="iShares Core S&P 500 UCITS ETF")
        isin_in = c3.text_input("ISIN", placeholder="IE00B5BMR087")
        c4, c5, c6, c7, c8, c9 = st.columns(6)
        side_in = c4.selectbox(L("Vrsta", "Type"), ["buy", "sell"], format_func=lambda x: L("Kupovina", "Buy") if x == "buy" else L("Prodaja", "Sell"))
        st_in = c5.selectbox("Status", ["filled", "pending"], format_func=lambda x: L("Izvršeno", "Filled") if x == "filled" else L("Nalog na čekanju", "Pending order"))
        q_in = c6.number_input(L("Količina", "Quantity"), 0.0, 1e7, 1.0, 1.0)
        px_in = c7.number_input(L("Cena (€)", "Price (€)"), 0.0, 1e7, 0.0, 0.01, help=L("Izvršna cena ili limit naloga", "Fill price or order limit"))
        fee_in = c8.number_input(L("Provizija (€)", "Fee (€)"), 0.0, 1e4, 0.0, 0.5)
        d_in = c9.date_input(L("Datum", "Date"), date.today(), format="DD.MM.YYYY")
        if st.form_submit_button("➕ " + L("Dodaj", "Add"), type="primary"):
            if not tk_in.strip() or q_in <= 0 or px_in <= 0:
                st.error(L("Unesi simbol, količinu i cenu.", "Enter a symbol, quantity and price."))
            else:
                portfolio.add(con, tk_in, nm_in or tk_in, isin_in, side_in, q_in,
                              px_in if st_in == "filled" else None, fee_in, d_in.isoformat(), st_in,
                              limit_price=px_in if st_in == "pending" else None)
                try:
                    stocks.refresh_prices(con)
                    stocks.refresh_info(con)
                except Exception:  # noqa: BLE001
                    pass
                st.success(L("Dodato.", "Added."))
                st.rerun()

    # --- sve transakcije: izmena, brisanje, dodavanje
    with st.expander("✏️ " + L("Sve transakcije - izmeni, obriši ili dodaj", "All transactions - edit, delete or add")):
        st.caption(L("Promeni bilo koje polje (količinu, cenu, datum, status...). Red brišeš tako što ga označiš levo i klikneš 🗑, "
                     "a novi dodaješ na dnu (+). Na kraju klikni „Sačuvaj transakcije“.",
                     "Change any field (quantity, price, date, status...). Delete a row by selecting it and clicking 🗑, add one at the "
                     "bottom (+). Then click 'Save transactions'."))
        _tx = portfolio.txns(con)
        tdf = pd.DataFrame([{"id": x["id"], "d": x["d"] or "", "ticker": x["ticker"], "name": x["name"], "side": x["side"], "status": x["status"],
                             "qty": x["qty"], "price": x["price"], "limit_price": x["limit_price"], "fee": x["fee"] or 0.0, "isin": x["isin"] or ""}
                            for x in _tx], columns=["id", "d", "ticker", "name", "side", "status", "qty", "price", "limit_price", "fee", "isin"])
        ed_t = st.data_editor(tdf, num_rows="dynamic", hide_index=True, key="tx_editor", width="stretch", column_config={
            "id": None,
            "d": st.column_config.TextColumn(L("Datum (GGGG-MM-DD)", "Date (YYYY-MM-DD)")),
            "ticker": st.column_config.TextColumn(L("Simbol", "Symbol"), required=True, help="npr. EUNL.DE, SXR8.DE, NVD.DE"),
            "name": st.column_config.TextColumn(L("Naziv", "Name")),
            "side": st.column_config.SelectboxColumn(L("Kupovina/prodaja", "Buy/sell"), options=["buy", "sell"], default="buy", required=True),
            "status": st.column_config.SelectboxColumn("Status", options=["filled", "pending"], default="filled", required=True,
                                                       help=L("filled = izvršeno, pending = nalog na čekanju", "filled or pending order")),
            "qty": st.column_config.NumberColumn(L("Količina", "Qty"), min_value=0.0, step=1.0, format="%g", required=True),
            "price": st.column_config.NumberColumn(L("Cena €", "Price €"), min_value=0.0, format="%.2f"),
            "limit_price": st.column_config.NumberColumn(L("Limit €", "Limit €"), min_value=0.0, format="%.2f"),
            "fee": st.column_config.NumberColumn(L("Provizija €", "Fee €"), min_value=0.0, format="%.2f"),
            "isin": st.column_config.TextColumn("ISIN")})
        if st.button("💾 " + L("Sačuvaj transakcije", "Save transactions"), key="tx_save", type="primary"):
            old_ids = set(tdf["id"].dropna().astype(int))
            new_ids = set()
            num = (lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) else float(v))
            for r_ in ed_t.to_dict("records"):
                if not r_.get("ticker") or not num(r_.get("qty")):
                    continue
                kw = {"d": r_.get("d") or date.today().isoformat(), "ticker": r_["ticker"], "name": r_.get("name") or r_["ticker"],
                      "side": r_.get("side") or "buy", "status": r_.get("status") or "filled", "qty": num(r_["qty"]),
                      "price": num(r_.get("price")), "limit_price": num(r_.get("limit_price")), "fee": num(r_.get("fee")) or 0.0,
                      "isin": r_.get("isin") or ""}
                if r_.get("id") is not None and not pd.isna(r_["id"]):
                    new_ids.add(int(r_["id"]))
                    portfolio.update(con, int(r_["id"]), **kw)
                else:
                    portfolio.add(con, kw["ticker"], kw["name"], kw["isin"], kw["side"], kw["qty"], kw["price"], kw["fee"], kw["d"],
                                  kw["status"], limit_price=kw["limit_price"])
            for tid in old_ids - new_ids:
                portfolio.delete(con, tid)
            try:
                stocks.refresh_prices(con)
            except Exception:  # noqa: BLE001
                pass
            st.success(L("Sačuvano.", "Saved."))
            st.rerun()
    if vals and all((eu.ETF_INFO.get(r["ticker"]) or {}).get("policy") == "acc" or eu.region(r["ticker"], infos_p.get(r["ticker"])) == "us" for r in vals):
        st.caption(L("Porezi: tvoji ETF-ovi akumuliraju dividende, pa nema poreza na dividende ni prijava PP OPO; 15% se plaća na kapitalni "
                     "dobitak pri prodaji (PPDG-3R). Detalji: Akcije → Troškovi, dividende i porez.",
                     "Tax: your ETFs accumulate dividends, so there is no dividend tax or PP OPO filing; 15% applies to capital gains "
                     "on sale (PPDG-3R). Details: Stocks → Costs, dividends & tax."))


# ---------- Svet i Srbija ----------
WTHEMES = [("Politika", "Politics", r"vlad|izbor|skupštin|predsednik|premijer|ministar|stranka|government|election|parliament|president|minister|party"),
           ("Ekonomija", "Economy", r"ekonom|inflac|plat|penzij|cen[ae]|budžet|investic|econom|inflation|wage|price|budget|gdp|tariff"),
           ("Rat i bezbednost", "War & security", r"\brat\b|rata|napad|vojsk|oružj|\bwar\b|attack|military|ceasefire|missile|troops|drone"),
           ("EU i diplomatija", "EU & diplomacy", r"\beu\b|evrop|diplomat|samit|nato|ambasad|europe|summit|diplomac|embassy"),
           ("Društvo", "Society", r"škol|zdrav|bolnic|protest|student|obrazov|health|school|hospital|protest|education"),
           ("Tehnologija", "Technology", r"\bai\b|veštačk|tehnolog|tech|artificial intelligence|chip|startup"),
           ("Nesreće i klima", "Disasters & climate", r"zemljotres|poplav|požar|klim|nesreć|earthquake|flood|wildfire|climate|storm")]

# ---------- periodi i sažeci ----------
PERIODS = {1: ("1 dan", "1 day"), 7: ("7 dana", "7 days"), 30: ("30 dana", "30 days"), 60: ("60 dana", "60 days"),
           90: ("90 dana", "90 days"), 180: ("180 dana", "180 days")}


def period_pick(key, default=1):
    return st.segmented_control("period", list(PERIODS), key=key, default=None if key in st.session_state else default,
                                label_visibility="collapsed", format_func=lambda d: PERIODS[d][0 if ui == "sr" else 1]) or default


def _stamp():
    return (db.get_meta(con, "last_fetch") or "")[:16]


@st.cache_data(ttl=900, show_spinner=False, max_entries=80)
def _pool(days, cats, offset_days, stamp):
    """Vesti u periodu, po važnosti (keširano do sledećeg osvežavanja vesti)."""
    end = datetime.now(timezone.utc) - timedelta(days=offset_days)
    return db.query_items(con, start_iso=utc_iso(end - timedelta(days=days)), end_iso=utc_iso(end), categories=list(cats),
                          order="score", limit=4000 if days > 30 else 1500)


def _starred_fix(items):
    stars = {r[0] for r in con.execute("SELECT id FROM items WHERE starred=1")}
    return [dict(x, starred=1 if x["id"] in stars else 0) for x in items]


def _theme_counts(items, themes):
    import re as _re
    out = {}
    for k, _, rx in themes:
        r_ = _re.compile(rx, _re.I)
        out[k] = sum(1 for x in items if r_.search(x["title"] + " " + (x.get("summary") or "")[:300]))
    return out


def _cats_key(cats):
    import hashlib
    return hashlib.md5("|".join(sorted(cats)).encode()).hexdigest()[:8]


def news_summary(days, cats, themes, key, n=6, show_ai=True):
    """Sažetak perioda: najvažnije vesti (spojene iz više izvora), teme i njihov trend u odnosu na prethodni period."""
    cats = tuple(cats)
    pool = _pool(days, cats, 0, _stamp())
    L = (lambda a, b: a if ui == "sr" else b)
    if not pool:
        st.markdown(f'<div class="fn-sub">{L("Nema vesti u ovom periodu.", "No news in this period.")}</div>', unsafe_allow_html=True)
        return
    prev = _pool(days, cats, days, _stamp())
    top, extra = dedupe(pool, n)
    tr = ensure_translations(top, lang)
    cnow, cprev = _theme_counts(pool, themes), _theme_counts(prev, themes)
    lbl = (lambda k: k if ui == "sr" else next(e for s_, e, _ in themes if s_ == k))

    def trend(k):
        a, b = cnow[k], cprev.get(k, 0)
        if not b:
            return f'<b class="fn-up">{L("novo", "new")}</b>'
        ch = a / b - 1
        return f'<b class="{"fn-up" if ch >= 0 else "fn-down"}">{"▲" if ch >= 0 else "▼"}{abs(ch) * 100:.0f}%</b>'
    chips = "".join(f'<span class="fn-trendchip">{h(lbl(k))} <span class="fn-sub">{cnow[k]}</span> {trend(k)}</span>'
                    for k in sorted([k for k in cnow if cnow[k]], key=lambda k: -cnow[k])[:8])
    bullets = "".join(
        f'<li><a href="{h(it["link"])}" target="_blank">{h(tr.get(it["id"], {}).get("title") or it["title"])}</a>'
        f'<small>{h(it["source"])}{" · +" + str(extra[it["id"]]) + " " + t("more_src") if extra.get(it["id"]) else ""} · {fmt_time(it["published"])}</small></li>'
        for it in top)
    chg = (len(pool) / len(prev) - 1) if prev else None
    stats = L(f"{len(pool)} vesti iz {len({x['source'] for x in pool})} izvora", f"{len(pool)} stories from {len({x['source'] for x in pool})} sources") + (
        L(f" · {chg * 100:+.0f}% u odnosu na prethodnih {PERIODS[days][0]}", f" · {chg * 100:+.0f}% vs the previous {PERIODS[days][1]}") if chg is not None else "")
    st.markdown(f'<div class="fn-kicker">{L("Sažetak", "Summary")} · {PERIODS[days][0 if ui == "sr" else 1]}</div>'
                f'<ul class="fn-bullets">{bullets}</ul>'
                + (f'<div class="fn-kicker" style="margin-top:12px">{L("Teme i trend", "Themes and trend")}</div><div style="margin-top:6px">{chips}</div>' if chips else "")
                + f'<div class="fn-sub" style="margin-top:4px">{h(stats)}</div>', unsafe_allow_html=True)
    if ai_on and show_ai:
        with st.expander("✨ " + L("AI tekstualni sažetak perioda", "AI written summary of the period")):
            with st.container(key=f"briefmd_{key}"):
                brief_block(f"S{days}-{_cats_key(cats)}-{date.today().isoformat()}", t("make_brief"),
                            lambda: (top + [x for x in pool[:60] if x not in top], []), PERIODS[days][0 if ui == "sr" else 1])


def findings_pool(days, topic=None, search=None, limit=40):
    """Radovi iz perioda sa ključnim nalazom (1-2 rečenice), keširano u bazi."""
    since_ = (date.today() - timedelta(days=days)).isoformat()
    pool = [p for p in db.phd_papers(con, topic=topic, search=search or None, limit=300) if (p["pub_date"] or "") >= since_]
    if topic is None:
        seen = {p["id"] for p in pool}
        for p in db.papers_by_tag(con, "cited_6m", search=search or None, limit=60):
            if p["id"] not in seen and (p["pub_date"] or "") >= since_:
                pool.append(p); seen.add(p["id"])
        for it in db.query_items(con, start_iso=utc_iso(datetime.now(timezone.utc) - timedelta(days=days)), categories=[RESEARCH],
                                 search=search or None, order="score", limit=40):
            if it["id"] not in seen:
                pool.append({"id": it["id"], "title": it["title"], "venue": it["source"], "authors": "", "cited_by": None,
                             "pub_date": it["published"][:10], "year": it["published"][:4], "link": it["link"],
                             "abstract": reader.clean_abstract(it.get("summary")), "oa": 1})
                seen.add(it["id"])
    pool = sorted(pool, key=lambda p: -(p.get("phd_score") or 0.0) - (p.get("cited_by") or 0) / 200)[:limit]
    have = {p["id"]: db.get_article_ai(con, p["id"], ui, "finding") for p in pool}
    tried = st.session_state.setdefault("fp_tried", set())
    missing = [p for p in pool if not have[p["id"]] and p["id"] not in tried]
    tried.update(p["id"] for p in missing)
    if missing:
        with st.spinner(f"{t('rr_making')} ({len(missing)})"):
            for p in missing:
                cached = db.get_article(con, p["id"])
                p["conclusion"] = cached["text"] if cached and cached["status"] == "concl" else ""
            got = ai.findings(missing, ui)
        for pid, f in got.items():
            if f:
                db.save_article_ai(con, pid, ui, "finding", f)
                have[pid] = f
    for p in pool:
        p["finding"] = have.get(p["id"]) or ""
    return pool


def research_summary(days, key, n=3):
    L = (lambda a, b: a if ui == "sr" else b)
    pool = [p for p in findings_pool(days, limit=n * 3) if p["finding"]][:n]
    if not pool:
        st.markdown(f'<div class="fn-sub">{L("Nema novih studija u ovom periodu - probaj duži period.", "No new studies in this period - try a longer one.")}</div>',
                    unsafe_allow_html=True)
        return
    st.markdown('<ul class="fn-bullets">' + "".join(
        f'<li>{h(p["finding"])}<small><a href="{h(p["link"])}" target="_blank">{h((p.get("venue") or "")[:40])}</a>'
        f'{" · ❝ " + str(p["cited_by"]) if p.get("cited_by") else ""}</small></li>' for p in pool) + "</ul>", unsafe_allow_html=True)


@st.fragment
def news_page(key, cats_all, themes, cats_default=None, placeholder="Fed, inflation, Nvidia, NBS...", research_side=True):
    """Vesti sa izborom perioda (1-180 dana), sažetkom perioda i naprednim filterima."""
    import re as _re
    L = (lambda a, b: a if ui == "sr" else b)
    days = period_pick(f"per_{key}", 1)
    base_cats = tuple(cats_default or cats_all)
    with st.container(key=f"sumbox_{key}"):
        if research_side:
            c1, c2 = st.columns([3, 2], gap="large")
            with c1:
                news_summary(days, base_cats, themes, key)
            with c2:
                st.markdown(f'<div class="fn-kicker">🔬 {L("Iz istraživanja - isti period", "From research - same period")}</div>', unsafe_allow_html=True)
                research_summary(days, key, 3)
        else:
            news_summary(days, base_cats, themes, key)
    st.markdown(f'<div class="fn-section">{L("Sve vesti u periodu", "All stories in the period")}</div>', unsafe_allow_html=True)
    sorts = {"rel": L("Relevantnost", "Relevance"), "new": L("Najnovije", "Newest"), "imp": L("Važnost", "Importance"),
             "src": L("Najviše izvora", "Most covered")}
    c1, c3 = st.container(key=f"fbar_{key}").columns([3, 1.6], vertical_alignment="bottom")
    q = c1.text_input(t("search"), key=f"q_{key}", placeholder=placeholder)
    sort = c3.selectbox(L("Sortiraj", "Sort by"), list(sorts), format_func=sorts.get, key=f"sort_{key}")
    with st.expander("⚙ " + L("Napredni filteri", "Advanced filters")):
        f1, f2 = st.columns(2)
        cats = f1.multiselect(t("cats"), cats_all, default=list(base_cats), format_func=cat_label, key=f"cats_{key}") if len(cats_all) > 1 else list(cats_all)
        src_opts = sorted({x["source"] for x in _pool(30, tuple(cats_all), 0, _stamp())})
        srcs = (f2 if len(cats_all) > 1 else f1).multiselect(t("sources"), src_opts, placeholder=t("all_src"), key=f"srcs_{key}")
        excl = (f2 if len(cats_all) == 1 else f1).multiselect(L("Isključi izvore", "Exclude sources"), src_opts, key=f"excl_{key}",
                                                              placeholder=L("nijedan", "none"))
        g1, g2, g3, g4 = st.columns([1.2, 1.4, 1, 1])
        lng = g1.selectbox(L("Jezik originala", "Original language"), ["all", "en", "sr"], key=f"lng_{key}",
                           format_func=lambda x: {"all": L("Svi", "All"), "en": "English", "sr": "Srpski"}[x])
        min_imp = g2.select_slider(L("Najmanja važnost", "Minimum importance"), [1, 2, 3, 4, 5], value=1, key=f"imp_{key}",
                                   format_func=lambda v: "●" * v)
        n = g3.selectbox(t("count"), [20, 40, 80, 150], key=f"n_{key}")
        layout = g4.selectbox(L("Prikaz", "Layout"), ["grid", "list"], key=f"lay_{key}",
                              format_func=lambda x: L("Mreža", "Grid") if x == "grid" else L("Lista", "List"))
        t1, t2, t3 = st.columns(3)
        full_only = t1.toggle(L("Samo vesti sa celim tekstom", "Only stories with full text"), value=True, key=f"full_{key}",
                              help=L("Sakriva vesti za koje ceo tekst nije pronađen ni kod drugih izvora", "Hides stories whose full text was not found at any source"))
        multi = t2.toggle(L("Samo vesti koje prenosi više izvora", "Only stories covered by several sources"), key=f"multi_{key}")
        starred = t3.toggle(L("Samo sačuvane", "Saved only"), key=f"star_{key}")
    cats = tuple(cats or cats_all)
    if q or srcs or starred:
        pool = db.query_items(con, start_iso=utc_iso(datetime.now(timezone.utc) - timedelta(days=days)), categories=list(cats),
                              sources=srcs or None, search=q or None, starred_only=starred, order="score", limit=1500)
    else:
        pool = _starred_fix(_pool(days, cats, 0, _stamp()))
    total = len(pool)
    if excl:
        pool = [x for x in pool if x["source"] not in excl]
    if lng != "all":
        pool = [x for x in pool if (x.get("lang") or "en") == lng]
    if min_imp > 1:
        pool = [x for x in pool if x["score"] >= (min_imp - 0.5) * 4.5]
    if full_only:
        pool = only_full(pool)
    txt = lambda x: (x["title"] + " " + (x.get("summary") or "")).lower()
    counts = {k: sum(1 for x in pool if _re.search(rx, txt(x))) for k, _, rx in themes}
    opts = sorted([k for k in counts if counts[k]], key=lambda k: -counts[k])
    picked = st.pills("teme", opts, key=f"th_{key}", selection_mode="multi", label_visibility="collapsed",
                      format_func=lambda k: f"{k if ui == 'sr' else next(e for s_, e, _ in themes if s_ == k)}  {counts[k]}") if opts else []
    if picked:
        rxs = [rx for k, _, rx in themes if k in picked]
        pool = [x for x in pool if any(_re.search(rx, txt(x)) for rx in rxs)]
    now_ = datetime.now(timezone.utc)
    if sort == "rel":
        pool.sort(key=lambda x: -fetcher.relevance(x, now_, 18.0 if days <= 1 else days * 8.0))
    elif sort == "new":
        pool.sort(key=lambda x: x["published"], reverse=True)
    items, extra = dedupe(pool, 400 if (multi or sort == "src") else n)
    if multi:
        items = [x for x in items if extra.get(x["id"])]
    if sort == "src":
        items.sort(key=lambda x: -extra.get(x["id"], 0))
    items = items[:n]
    st.caption(L(f"Prikazano {len(items)} od {total} vesti u periodu · vesti o istoj temi iz više izvora su spojene",
                 f"Showing {len(items)} of {total} stories in the period · same-topic stories from several sources are merged"))
    if not items:
        st.info(L("Nema vesti za ove filtere. Proširi period ili isključi filter „Samo vesti sa celim tekstom“.",
                  "No stories match. Widen the period or switch off 'Only stories with full text'.") if total else
                L("Još nema vesti - klikni ↻ gore desno da ih preuzmeš.", "No news yet - click ↻ at the top right to fetch."))
        return
    render_items(items, key, extra=extra, hero_first=sort in ("rel", "imp", "src"), grid=layout == "grid")


if page == "t_news":
    _ns = {"fin": ("Finansije i tržišta", "Finance & markets"), "comp": ("Kompanije", "Companies"),
           "srb": ("Srbija", "Serbia"), "svet": ("Svet", "World")}
    nsub = st.segmented_control("news_sub", list(_ns), key="news_sub", default=None if "news_sub" in st.session_state else "fin",
                                label_visibility="collapsed", format_func=lambda k: _ns[k][0 if ui == "sr" else 1]) or "fin"
    if nsub == "fin":
        news_page("fin", NEWS_CATS + ["Kompanije"], THEMES, cats_default=NEWS_CATS)
    elif nsub == "comp":
        news_page("comp", ["Kompanije"], THEMES, placeholder="Nvidia, SAP, ASML, LVMH...")
    elif nsub == "srb":
        news_page("srb", ["Srbija", "Srbija i region"], WTHEMES, placeholder="Vlada, NBS, EXPO, plate..." if ui == "sr" else "Government, NBS, wages...",
                  research_side=False)
    else:
        news_page("svet", ["Svet"], WTHEMES, placeholder="EU, Ukrajina, izbori..." if ui == "sr" else "EU, Ukraine, election...",
                  research_side=False)


# ---------- Akcije ----------
def pct(v, signed=True):
    return "-" if v is None else (f"{v * 100:+.1f}%" if signed else f"{v * 100:.1f}%")


def big(v):
    if not v:
        return "-"
    for d, u in ((1e12, " bil."), (1e9, " mlrd."), (1e6, " mil.")):
        if v >= d:
            return f"{v / d:.1f}{u if ui == 'sr' else {' bil.': 'T', ' mlrd.': 'B', ' mil.': 'M'}[u]}"
    return f"{v:,.0f}"


@st.cache_data(ttl=300, show_spinner=False)
def _stock_rows(_stamp):
    rows = stocks.metrics(con)
    return rows, stocks.apply_tax_preferences(stocks.score([dict(r) for r in rows]), con)


def spark_svg(vals, uid):
    """Mali grafikon cene (SVG) koji se iscrta animirano."""
    vals = [v for v in (vals or []) if v]
    if len(vals) < 2:
        return ""
    w, hh = 300, 64
    lo, hi = min(vals), max(vals)
    rg = (hi - lo) or 1
    pts = [(i * w / (len(vals) - 1), hh - 4 - (v - lo) / rg * (hh - 10)) for i, v in enumerate(vals)]
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    col = "#9CC79A" if vals[-1] >= vals[0] else "#E07C8A"
    gid = "g" + "".join(ch for ch in uid if ch.isalnum())
    return (f'<svg class="fn-spark" viewBox="0 0 {w} {hh}" preserveAspectRatio="none"><defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{col}" stop-opacity=".32"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>'
            f'<path class="fn-spark-area" d="{d} L{w},{hh} L0,{hh} Z" fill="url(#{gid})"/>'
            f'<path class="fn-spark-line" d="{d}" fill="none" stroke="{col}" stroke-width="2" vector-effect="non-scaling-stroke" pathLength="1"/></svg>')


def price_chart(tk, days=183, height=300, sma=False, mini=False):
    """Interaktivni grafikon cene: prelaskom mišem (ili prstom) vidiš datum i cenu."""
    import altair as alt
    full = stocks.series(con, tk)
    if len(full) < 5:
        st.caption("Nema dovoljno podataka o ceni." if ui == "sr" else "Not enough price data.")
        return
    cl = [c_ for _, c_ in full]
    rows_ = []
    for i, (d_, c_) in enumerate(full):
        r_ = {"d": d_, "v": c_}
        if sma:
            r_["s50"] = sum(cl[max(0, i - 49):i + 1]) / len(cl[max(0, i - 49):i + 1])
            r_["s200"] = sum(cl[max(0, i - 199):i + 1]) / len(cl[max(0, i - 199):i + 1])
        rows_.append(r_)
    df = pd.DataFrame(rows_)
    df = df[df["d"] >= (date.today() - timedelta(days=days)).isoformat()]
    if len(df) < 2:
        return
    df["d"] = pd.to_datetime(df["d"])
    _lo, _hi = df["v"].min(), df["v"].max()
    df["b"] = _lo - (_hi - _lo) * 0.08  # dno senke odmah ispod najniže cene (ne od nule)
    up = df["v"].iloc[-1] >= df["v"].iloc[0]
    col, rgb = ("#9CC79A", "156,199,154") if up else ("#E07C8A", "224,124,138")
    lc = "#A8979A"
    x = alt.X("d:T", title=None, axis=None if mini else alt.Axis(format="%d.%m.%y", grid=False, labelColor=lc, domain=False, tickColor="#2C2124"))
    y = alt.Y("v:Q", title=None, scale=alt.Scale(zero=False, padding=8),
              axis=None if mini else alt.Axis(gridColor="#221A1C", labelColor=lc, domain=False, ticks=False, format=",.2f"))
    base = alt.Chart(df).encode(x=x)
    area = base.mark_area(line={"color": col, "strokeWidth": 2}, interpolate="monotone",
                          color=alt.Gradient(gradient="linear", stops=[alt.GradientStop(color=f"rgba({rgb},0)", offset=0),
                                                                       alt.GradientStop(color=f"rgba({rgb},0.35)", offset=1)],
                                             x1=1, x2=1, y1=1, y2=0)).encode(y=y, y2="b:Q")
    hover = alt.selection_point(fields=["d"], nearest=True, on="pointerover", empty=False, clear="pointerout")
    lbl_d, lbl_v = ("Datum", "Cena") if ui == "sr" else ("Date", "Price")
    catch = base.mark_rule(opacity=0, strokeWidth=12).encode(
        tooltip=[alt.Tooltip("d:T", title=lbl_d, format="%d.%m.%Y"), alt.Tooltip("v:Q", title=lbl_v, format=",.2f")]).add_params(hover)
    rule = base.mark_rule(color="#D6B072", strokeDash=[3, 3]).encode(opacity=alt.condition(hover, alt.value(0.7), alt.value(0)))
    dot = base.mark_circle(size=70, color=col, stroke="#0B0909", strokeWidth=2).encode(y="v:Q", opacity=alt.condition(hover, alt.value(1), alt.value(0)))
    layers = [area]
    if sma:
        for k_, c_ in (("s50", "#D6B072"), ("s200", "#C99A7A")):
            layers.append(base.mark_line(strokeWidth=1.4, strokeDash=[4, 3], color=c_, interpolate="monotone").encode(y=alt.Y(f"{k_}:Q")))
    layers += [rule, dot, catch]
    ch = alt.layer(*layers).properties(height=height).configure_view(strokeWidth=0).configure(background="transparent")
    st.altair_chart(ch, width="stretch")
    if sma and not mini:
        st.markdown('<div class="fn-sub" style="font-size:.78rem">' + (
            '<span style="color:#D6B072">- - prosek 50 dana</span> &nbsp; <span style="color:#C99A7A">- - prosek 200 dana</span>' if ui == "sr" else
            '<span style="color:#D6B072">- - 50-day average</span> &nbsp; <span style="color:#C99A7A">- - 200-day average</span>') + "</div>",
                    unsafe_allow_html=True)


def stock_card(r, key, opp=None):
    """Kartica akcije u pretrazi: cena, promena, mali grafikon i ključni brojevi."""
    import signals
    L = (lambda a, b: a if ui == "sr" else b)
    sec = signals.SECTOR_SR.get(r["sector"], r["sector"]) if ui == "sr" else r["sector"]
    d1 = r.get("r1d") or 0
    tag = f'<span class="fn-tag">{L("prilika", "opportunity")}</span>' if opp and opp.get("qualifies") else ""
    stats = [(L("1 godina", "1 year"), pct(r.get("r1y"))), (L("od maksimuma", "from high"), pct(opp["dd"]) if opp else "-"),
             (L("cilj analit.", "analyst tgt"), pct(r.get("upside"))), (L("ocena", "score"), str(opp["opp"]) if opp else "-")]
    with st.container(border=True, key=f"card_{key}_{r['ticker']}"):
        st.markdown(
            f'<div class="fn-sc-head"><div><div class="fn-meta"><span class="fn-src" style="--c:{styles.src_color(r["sector"] or "ETF")}">{h(sec or "ETF")}</span>'
            f'<span class="fn-tk">{h(r["ticker"])}</span>{tag}</div><div class="fn-sc-name" style="margin-top:6px">{h(r["name"])}</div></div>'
            f'<div class="fn-sc-px"><b>{r["price"]:,.2f}</b><i class="{"fn-up" if d1 >= 0 else "fn-down"}">{"▲" if d1 >= 0 else "▼"} {abs(d1) * 100:.2f}%</i></div></div>'
            + spark_svg(r.get("spark"), f"{key}{r['ticker']}")
            + '<div class="fn-sc-stats">' + "".join(f"<div><span>{a_}</span><b>{b_}</b></div>" for a_, b_ in stats) + "</div>",
            unsafe_allow_html=True)
        st.button("📈 " + L("Grafikon i detalji", "Chart & details"), key=f"{key}_go_{r['ticker']}",
                  on_click=lambda tk_=r["ticker"]: st.session_state.update(ssub="s_detail", stock_sel=tk_))


@st.cache_data(ttl=900, show_spinner=False)
def _opps(_p_stamp, _n_stamp):
    import signals
    rows = stocks.metrics(con)
    th = signals.theme_momentum(con, 7)
    return signals.opportunities(con, rows, th), th


def opp_card(o, i, compact=False, chart=True):
    """Kartica jedne prilike: zašto, rizici, katalizatori iz vesti."""
    import signals
    L = (lambda a, b: a if ui == "sr" else b)
    sec = signals.SECTOR_SR.get(o["sector"], o["sector"]) if ui == "sr" else o["sector"]
    reasons = [signals.text(c_, v_, ui, signals.REASON_TXT) for c_, v_ in o["reasons"]]
    risks = [signals.text(c_, v_, ui, signals.RISK_TXT) for c_, v_ in o["risks"]]
    with st.container(border=True, key=f"{'hero' if i == 0 and not compact else 'card'}_opp{'c' if compact else ''}_{o['ticker']}"):
        st.markdown(
            f'<div class="fn-opp"><div><div class="fn-meta"><span class="fn-badge">#{i + 1}</span>'
            f'<span class="fn-src" style="--c:{styles.src_color(o["sector"])}">{h(sec or "-")}</span>'
            f'<span class="fn-cite">{o["price"]:.2f} {h(o["currency"])}</span>'
            f'<span class="fn-down">{o["dd"] * 100:.0f}% {L("od maksimuma", "from high")}</span>'
            + (f'<span class="fn-up">{L("cilj", "target")} {o["upside"] * 100:+.0f}%</span>' if o.get("upside") else "")
            + f'</div><div class="fn-title" style="margin-top:8px">{h(o["name"])} <span class="fn-tk">{h(o["ticker"])}</span></div></div>'
            f'<div class="fn-gauge" style="--v:{o["opp"]}"><b>{o["opp"]}</b><small>{L("prilika", "opportunity")}</small></div></div>',
            unsafe_allow_html=True)
        if compact:
            st.markdown(spark_svg(o.get("spark"), f"c{o['ticker']}") + f'<div class="fn-sub">{h(" · ".join(reasons[:2]))}</div>', unsafe_allow_html=True)
            return
        if chart:
            price_chart(o["ticker"], days=183, height=170)
        st.markdown(f'<div class="fn-note"><b>{L("Zašto sada", "Why now")}:</b> {h("; ".join(reasons))}.</div>'
                    + (f'<div class="fn-note fn-risk"><b>{L("Na šta paziti", "Watch out for")}:</b> {h("; ".join(risks))}.</div>' if risks else ""),
                    unsafe_allow_html=True)
        news_ = o["catalysts"] + o["negatives"]
        if news_:
            tr_ = ensure_translations(news_, lang)
            st.markdown(f'<div class="fn-kicker" style="margin-top:6px">{L("Vesti koje mogu da pokrenu cenu", "News that may move the price")}</div>'
                        '<ul class="fn-bullets">' + "".join(
                            f'<li>{"🟢" if n_ in o["catalysts"] else "🔴"} <a href="{h(n_["link"])}" target="_blank">{h(tr_.get(n_["id"], {}).get("title") or n_["title"])}</a>'
                            f'<small>{h(n_["source"])} · {fmt_time(n_["published"])}</small></li>' for n_ in news_) + "</ul>", unsafe_allow_html=True)
        if o["themes"]:
            st.markdown('<div style="margin-top:6px">' + "".join(
                f'<span class="fn-trendchip">{h(a_ if ui == "sr" else b_)} <b class="{"fn-up" if e_ > 0 else "fn-down"}">{"↑" if e_ > 0 else "↓"} {h(sec)}</b></span>'
                for a_, b_, e_ in o["themes"]) + "</div>", unsafe_allow_html=True)
        if chart:
            st.button("🔎 " + L("Grafikon i detalji", "Chart & details"), key=f"oppd_{o['ticker']}",
                      on_click=lambda tk_=o["ticker"]: st.session_state.update(ssub="s_detail", stock_sel=tk_))


def themes_block(th, n=5):
    import signals
    L = (lambda a, b: a if ui == "sr" else b)
    if not th:
        st.markdown(f'<div class="fn-sub">{L("Nema dovoljno vesti za procenu tema.", "Not enough news to assess themes.")}</div>', unsafe_allow_html=True)
        return
    for t_ in th[:n]:
        eff = "".join(f'<span class="fn-trendchip">{h(signals.SECTOR_SR.get(k, k) if ui == "sr" else k)} '
                      f'<b class="{"fn-up" if v > 0 else "fn-down"}">{"↑" if v > 0 else "↓"}</b></span>'
                      for k, v in sorted(t_["effects"].items(), key=lambda x: -x[1]))
        trend_ = (f'{t_["ratio"]:.1f}× {L("više nego ranije", "more than before")}' if t_["prev"] else L("nova tema", "new theme"))
        st.markdown(f'<div class="fn-ind" style="grid-template-columns:1fr"><div><div class="fn-ind-name">{h(t_["sr"] if ui == "sr" else t_["en"])}'
                    f' <span class="fn-sub">· {t_["n"]} {L("vesti", "stories")} · {trend_}</span></div>'
                    f'<div class="fn-sum" style="margin:4px 0 6px">{h(t_["why_sr"] if ui == "sr" else t_["why_en"])}</div>{eff}</div></div>',
                    unsafe_allow_html=True)



# ---------- Početna ----------
if page == "t_home":
    _sync_portfolio(pull=True)
    L = (lambda a, b: a if ui == "sr" else b)
    _hr = datetime.now().hour
    st.markdown(f'<div class="fn-read-title" style="margin:2px 0 12px">'
                f'{(L("Dobro jutro", "Good morning") if _hr < 11 else L("Dobar dan", "Good afternoon") if _hr < 18 else L("Dobro veče", "Good evening"))}.'
                f' <span class="fn-sub" style="font-family:Inter;font-size:1rem">{L("Evo šta je danas važno.", "Here is what matters today.")}</span></div>',
                unsafe_allow_html=True)
    eur0 = (lambda x: (f"{x:,.0f} €".replace(",", ".") if ui == "sr" else f"€{x:,.0f}"))
    tiles = []
    if not PUBLIC or st.session_state.get("unlocked"):
        try:
            _v = portfolio.valuation(con, {t_: stocks.info(con, t_) for t_ in portfolio.tickers(con)})
            _a = portfolio.asset_values(con)
            _gs = portfolio.gold_series(con, 12)
            _gd = _gs[-1][1] / _gs[-2][1] - 1 if len(_gs) > 1 else 0
            _tv = sum(r["value"] or 0 for r in _v) + sum(a["value"] or 0 for a in _a)
            _td = sum(r["day_eur"] or 0 for r in _v) + sum((a["value"] or 0) * _gd for a in _a if a["kind"] == "gold")
            _tc = sum(r["cost"] for r in _v) + sum(a["base_eur"] for a in _a)
            tiles.append((L("Portfolio", "Portfolio"), eur0(_tv),
                          f'<i class="{"fn-up" if _td >= 0 else "fn-down"}">{"▲" if _td >= 0 else "▼"} {eur0(abs(_td))} {L("danas", "today")}</i>'))
            tiles.append((L("Prinos ukupno", "Total return"), (f"{(_tv / _tc - 1) * 100:+.1f}%".replace(".", "," if ui == "sr" else ".") if _tc else "-"),
                          f'<i class="fn-sub">{L("uloženo", "invested")} {eur0(_tc)}</i>'))
        except Exception:  # noqa: BLE001
            pass
    else:
        tiles.append((L("Portfolio", "Portfolio"), "🔒", f'<i class="fn-sub">{L("samo za vlasnika", "owner only")}</i>'))
    try:
        _ops, _th = _opps(db.get_meta(con, "prices_refreshed") or "", _stamp())
    except Exception:  # noqa: BLE001
        _ops, _th = [], []
    _q = [o for o in _ops if o["qualifies"]]
    tiles.append((L("Vesti danas", "News today"), str(_k_news), f'<i class="fn-sub">{L("osveženo", "updated")} {_upd}</i>'))
    tiles.append((L("Tema u usponu", "Rising theme"), h((_th[0]["sr"] if ui == "sr" else _th[0]["en"]) if _th else "-"),
                  f'<i class="fn-sub">{_th[0]["n"]} {L("vesti za 7 dana", "stories in 7 days")}</i>' if _th else ""))
    if len(tiles) < 4:
        tiles.append((L("Prilike", "Opportunities"), str(len(_q)), f'<i class="fn-sub">{L("akcija u padu sa potencijalom", "fallen stocks with upside")}</i>'))
    st.markdown('<div class="fn-home-grid">' + "".join(
        f'<div class="fn-stat"><span>{a_}</span><b style="font-family:{"Playfair Display" if not any(ch.isdigit() for ch in b_) else "JetBrains Mono"}">{b_}</b>{c_}</div>'
        for a_, b_, c_ in tiles[:4]) + "</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1.3, 1], gap="large")
    with c1:
        st.markdown(f'<div class="fn-section">{L("Danas ukratko", "Today in brief")}</div>', unsafe_allow_html=True)
        news_summary(1, tuple(NEWS_CATS + ["Kompanije"]), THEMES, "home", n=7, show_ai=False)
        st.button(L("Sve vesti →", "All news →"), key="h_news", on_click=go, args=("t_news",), kwargs={"news_sub": "fin"})
        st.markdown(f'<div class="fn-section">{L("Srbija i svet", "Serbia & world")}</div>', unsafe_allow_html=True)
        _gen, _gx = dedupe(_pool(1, tuple(GENERAL_CATS), 0, _stamp()), 4)
        if _gen:
            _gt = ensure_translations(_gen, lang)
            st.markdown('<ul class="fn-bullets">' + "".join(
                f'<li><a href="{h(it["link"])}" target="_blank">{h(_gt.get(it["id"], {}).get("title") or it["title"])}</a>'
                f'<small>{h(it["source"])} · {fmt_time(it["published"])}</small></li>' for it in _gen) + "</ul>", unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="fn-section">{L("Prilike na tržištu", "Market opportunities")}</div>', unsafe_allow_html=True)
        if _q:
            for i, o in enumerate(_q[:3]):
                opp_card(o, i, compact=True)
        else:
            st.markdown(f'<div class="fn-sub">{L("Trenutno nema akcija koje ispunjavaju uslove.", "No stocks qualify right now.")}</div>', unsafe_allow_html=True)
        st.button(L("Sve prilike i teme →", "All opportunities & themes →"), key="h_opp", on_click=go, args=("t_stocks",), kwargs={"ssub": "s_opp"})
        st.markdown(f'<div class="fn-section">{L("Teme u usponu", "Rising themes")}</div>', unsafe_allow_html=True)
        themes_block(_th, 3)
    st.markdown(f'<div class="fn-section">🔬 {L("Novo iz istraživanja - poslednjih 30 dana", "New in research - last 30 days")}</div>', unsafe_allow_html=True)
    research_summary(30, "home", 3)
    st.button(L("Svi nalazi →", "All findings →"), key="h_res", on_click=go, args=("t_res",), kwargs={"res_sub": "t_rr"})

if page == "t_stocks":
    stocks._init(con)
    if st.session_state.get("ssub") == "s_pick":
        st.session_state["ssub"] = "s_find"
    _all_stk = {t_: (stocks.info(con, t_) or {}).get("shortName") or n_ for t_, n_ in stocks.watchlist()}

    def _pick_stock():
        if st.session_state.get("stk_search"):
            st.session_state.update(stock_sel=st.session_state["stk_search"], ssub="s_detail", stk_search=None)
    st.selectbox("search", list(_all_stk), index=None, key="stk_search", on_change=_pick_stock, label_visibility="collapsed",
                 placeholder=("🔎  Pretraži akciju po nazivu ili simbolu - npr. Nvidia, SAP, ASML..." if ui == "sr" else
                              "🔎  Search a stock by name or symbol - e.g. Nvidia, SAP, ASML..."),
                 format_func=lambda t_: f"{_all_stk[t_]}  ·  {t_}")
    sv = st.segmented_control("ssub", ["s_opp", "s_find", "s_detail", "s_over", "s_ind", "s_news", "s_tax"], key="ssub", default=None if "ssub" in st.session_state else "s_opp",
                              label_visibility="collapsed",
                              format_func=lambda k: {"s_opp": ("💡 Prilike sada", "💡 Opportunities now"), "s_find": ("🔍 Istraži sve akcije", "🔍 Explore all stocks"), "s_over": ("Tabela", "Table"),
                                                     "s_news": ("Vesti kompanija", "Company news"), "s_detail": ("📈 Grafikon i detalji", "📈 Chart & details"),
                                                     "s_ind": ("Pokazatelji", "Fundamentals"),
                                                     "s_tax": ("Troškovi i porez", "Costs & tax")}[k][0 if ui == "sr" else 1]) or "s_opp"
    p_upd = db.get_meta(con, "prices_refreshed")
    cA, cB = st.columns([4, 1], vertical_alignment="center")
    cA.caption(("Cene: Yahoo Finance, dnevne, sa zakašnjenjem. Poslednje osvežavanje: " if ui == "sr" else
                "Prices: Yahoo Finance, daily, delayed. Last refresh: ") + (fmt_time(p_upd) if p_upd else "-"))
    if cB.button("↻ " + ("Osveži akcije" if ui == "sr" else "Refresh stocks"), key="st_refresh") or not p_upd and not st.session_state.get("st_auto"):
        st.session_state["st_auto"] = True
        with st.spinner("Preuzimam cene, pokazatelje i vesti..." if ui == "sr" else "Fetching prices, fundamentals and news..."):
            try:
                stocks.refresh_prices(con)
                stocks.refresh_info(con)
                stocks.refresh_news(con)
            except Exception as ex:  # noqa: BLE001
                st.error(f"Yahoo Finance: {ex}")
        _stock_rows.clear()
        p_upd = db.get_meta(con, "prices_refreshed")
    rows_s, ranked = _stock_rows(p_upd or "")
    if sv in ("s_opp", "s_find", "s_over") and rows_s:
        flt = st.segmented_control("flt", ["all", "eu", "us", "eur"], key="st_flt2", label_visibility="collapsed",
                                   default=None if "st_flt2" in st.session_state else "all",
                                   format_func=lambda k: {"all": ("Sve akcije", "All stocks"), "eu": ("Evropa", "Europe"), "us": ("SAD", "US"),
                                                          "eur": ("Kotirane u evrima", "Quoted in EUR")}[k][0 if ui == "sr" else 1]) or "all"
        infos_ = {x["ticker"]: stocks.info(con, x["ticker"]) for x in rows_s}
        dmap = {x["ticker"]: x for x in ranked}

        def _keep(tk_):
            if flt == "all":
                return True
            if flt == "eur":
                return eu.is_eur(tk_, infos_[tk_])
            return eu.region(tk_, infos_[tk_]) == flt
        rows_s = [x for x in rows_s if _keep(x["ticker"])]
        ranked = [x for x in ranked if _keep(x["ticker"])]
    if not rows_s:
        st.info("Još nema podataka o cenama - klikni „Osveži akcije“." if ui == "sr" else "No price data yet - click 'Refresh stocks'.")
    elif sv == "s_over":
        df = pd.DataFrame([{"Ticker": r["ticker"], ("Naziv" if ui == "sr" else "Name"): r["name"],
                            ("Sektor" if ui == "sr" else "Sector"): r["sector"], ("Cena" if ui == "sr" else "Price"): r["price"],
                            "1d %": (r["r1d"] or 0) * 100, "1m %": (r["r1m"] or 0) * 100,
                            ("1g %" if ui == "sr" else "1y %"): (r["r1y"] or 0) * 100,
                            ("90 dana" if ui == "sr" else "90 days"): r["spark"], "P/E": r["pe"],
                            ("Region" if ui == "sr" else "Region"): {"eu": "EU", "us": ("SAD" if ui == "sr" else "US"), "other": "-"}.get(
                                next((x.get("region") for x in ranked if x["ticker"] == r["ticker"]), None), "ETF" if r["etf"] else "-"),
                            ("Poreski gubitak/god." if ui == "sr" else "Tax drag/yr"): (next((x.get("drag") for x in ranked if x["ticker"] == r["ticker"]), None) or 0) * 100,
                            ("Skor" if ui == "sr" else "Score"): next((x["score"] for x in ranked if x["ticker"] == r["ticker"]), None)}
                           for r in rows_s])
        pc = [c for c in df.columns if c.endswith("%")]
        sty = df.style.map(lambda v: f"color: {'#9CC79A' if v > 0 else '#E07C8A' if v < 0 else 'inherit'}", subset=pc)
        st.dataframe(sty, hide_index=True, height=min(38 * len(df) + 40, 900), column_config={
            **{c: st.column_config.NumberColumn(c, format="%+.1f%%") for c in pc},
            ("Cena" if ui == "sr" else "Price"): st.column_config.NumberColumn(format="%.2f"),
            "P/E": st.column_config.NumberColumn(format="%.1f"),
            ("Poreski gubitak/god." if ui == "sr" else "Tax drag/yr"): st.column_config.NumberColumn(
                format="%.2f%%", help=("Koliko godišnjeg prinosa gubiš na porezu na dividendu iznad srpskih 15% (bez povraćaja)"
                                       if ui == "sr" else "Annual return lost to dividend tax above Serbia's 15% (no reclaim)")),
            ("90 dana" if ui == "sr" else "90 days"): st.column_config.LineChartColumn(width="small", color="#C2435F"),
            ("Skor" if ui == "sr" else "Score"): st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d")})
        st.caption("Listu akcija menjaš u ⚙ Podešavanjima." if ui == "sr" else "Edit the watchlist in ⚙ Settings.")
    elif sv == "s_opp":
        import signals
        L = (lambda a, b: a if ui == "sr" else b)
        opps, th = _opps(p_upd or "", _stamp())
        keep_ = {x["ticker"] for x in rows_s}
        qual = [o for o in opps if o["qualifies"] and o["ticker"] in keep_]
        tw = signals.sector_tailwind(th)
        st.markdown('<div class="fn-disclaimer">' + L(
            "Ovde su akcije sa tvoje liste koje su <b>značajno pale</b>, a za koje <b>analitičari, kvalitet poslovanja, vesti i teme na tržištu</b> "
            "ukazuju da bi mogle da se oporave. To je alat za istraživanje, a ne investicioni savet - pad može i da se nastavi.",
            "These are stocks from your list that have <b>fallen significantly</b>, where <b>analysts, business quality, news and market themes</b> "
            "suggest a possible recovery. It is a research tool, not investment advice - the decline may continue.") + "</div>", unsafe_allow_html=True)
        good = sorted([(v, k) for k, v in tw.items() if v > 0.1], reverse=True)[:3]
        bad = sorted([(v, k) for k, v in tw.items() if v < -0.1])[:2]
        if qual or good:
            lines = []
            if good:
                lines.append(L("Sektori sa vetrom u leđa iz aktuelnih vesti: ", "Sectors with a tailwind from current news: ")
                             + ", ".join(f"<b>{h(signals.SECTOR_SR.get(k, k) if ui == 'sr' else k)}</b>" for _, k in good))
            if bad:
                lines.append(L("Oprez kod: ", "Be careful with: ") + ", ".join(h(signals.SECTOR_SR.get(k, k) if ui == "sr" else k) for _, k in bad))
            if qual:
                lines.append(L("Najzanimljivije za dalju analizu: ", "Most interesting for further research: ")
                             + ", ".join(f"<b>{h(o['name'])}</b> ({o['dd'] * 100:.0f}%)" for o in qual[:3]))
            st.markdown(f'<div class="fn-section">{L("Gde ima smisla gledati sada", "Where it makes sense to look now")}</div>'
                        '<ul class="fn-bullets">' + "".join(f"<li>{x}</li>" for x in lines) + "</ul>", unsafe_allow_html=True)
        c_l, c_r = st.columns([1.7, 1], gap="large")
        with c_l:
            st.markdown(f'<div class="fn-section">{L("Akcije u padu sa potencijalom rasta", "Fallen stocks with upside potential")} · {len(qual)}</div>',
                        unsafe_allow_html=True)
            if not qual:
                st.info(L("Trenutno nijedna akcija sa liste ne ispunjava uslove (pad ≥ 8% od maksimuma i cilj analitičara ≥ 5% iznad cene).",
                          "No stock on the list currently qualifies (≥ 8% below its high and analyst target ≥ 5% above the price)."))
            for i, o in enumerate(qual[:10]):
                opp_card(o, i)
        with c_r:
            st.markdown(f'<div class="fn-section">{L("Teme koje pokreću tržište", "Themes driving the market")}</div>', unsafe_allow_html=True)
            st.caption(L("Poslednjih 7 dana u odnosu na prethodne 4 nedelje", "Last 7 days vs the previous 4 weeks"))
            themes_block(th, 6)
        with st.expander(L("Kako se računa ocena prilike", "How the opportunity score works")):
            st.markdown(L(
                "- **Pad od maksimuma** (25%) - koliko je akcija ispod 52-nedeljnog maksimuma (do 40%)\n"
                "- **Cilj analitičara** (22%) - razlika do prosečne ciljne cene\n- **Kvalitet** (13%) - ROE, profitna marža i rast prihoda\n"
                "- **Preporuka analitičara** (12%)\n- **Vesti o kompaniji** (12%) - pozitivni i negativni izrazi u vestima poslednje 3 nedelje\n"
                "- **Tehnički znaci oporavka** (8%) - cena iznad 20-dnevnog proseka, RSI ispod 35\n"
                "- **Teme na tržištu** (8%) - da li aktuelne teme iz vesti idu u korist sektoru\n\n"
                "Prikazuju se samo akcije koje su bar 8% ispod maksimuma i imaju cilj analitičara bar 5% iznad trenutne cene.",
                "- **Drawdown** (25%) - how far below the 52-week high (up to 40%)\n- **Analyst target** (22%) - distance to the mean target price\n"
                "- **Quality** (13%) - ROE, profit margin and revenue growth\n- **Analyst rating** (12%)\n"
                "- **Company news** (12%) - positive and negative phrases in news over the last 3 weeks\n"
                "- **Technical recovery signs** (8%) - price above the 20-day average, RSI below 35\n"
                "- **Market themes** (8%) - whether current news themes favour the sector\n\n"
                "Only stocks at least 8% below their high with an analyst target at least 5% above the price are shown."))
    elif sv == "s_find":
        L = (lambda a, b: a if ui == "sr" else b)
        import signals
        opps_all, _th = _opps(p_upd or "", _stamp())
        omap = {o["ticker"]: o for o in opps_all}
        sectors_ = sorted({r["sector"] for r in rows_s if r["sector"]})
        f1, f2, f3 = st.columns([1.6, 1.4, 1.2], vertical_alignment="bottom")
        fq = f1.text_input(L("Filtriraj", "Filter"), key="find_q", placeholder=L("naziv, simbol ili sektor", "name, symbol or sector"))
        fsec = f2.multiselect(L("Sektor", "Sector"), sectors_, key="find_sec", placeholder=L("svi sektori", "all sectors"),
                              format_func=lambda x: signals.SECTOR_SR.get(x, x) if ui == "sr" else x)
        sorts_ = {"opp": L("Najbolja prilika", "Best opportunity"), "score": L("Faktorski skor", "Factor score"),
                  "dd": L("Najveći pad od maksimuma", "Biggest drop from high"), "up": L("Najveći cilj analitičara", "Biggest analyst upside"),
                  "r1y": L("Najveći rast za godinu", "Best 1-year return"), "r1d": L("Najveći rast danas", "Best today"),
                  "div": L("Najveća dividenda", "Highest dividend")}
        fsort = f3.selectbox(L("Poređaj po", "Sort by"), list(sorts_), format_func=sorts_.get, key="find_sort")
        g1, g2, _g3 = st.columns([1, 1, 2])
        only_down = g1.toggle(L("Samo akcije u padu", "Only fallen stocks"), key="find_down")
        no_etf = g2.toggle(L("Bez ETF-ova", "Hide ETFs"), value=True, key="find_noetf")
        smap = {x["ticker"]: x["score"] for x in ranked}
        items_ = []
        for r in rows_s:
            o = omap.get(r["ticker"])
            if no_etf and r.get("etf"):
                continue
            if fsec and r["sector"] not in fsec:
                continue
            if fq and fq.lower() not in f'{r["name"]} {r["ticker"]} {r["sector"]} {signals.SECTOR_SR.get(r["sector"], "")}'.lower():
                continue
            if only_down and not (o and o["dd"] <= -0.08):
                continue
            items_.append((r, o))
        keyf = {"opp": lambda x: -(x[1]["opp"] if x[1] else 0), "score": lambda x: -(smap.get(x[0]["ticker"]) or 0),
                "dd": lambda x: (x[1]["dd"] if x[1] else 0), "up": lambda x: -(x[0].get("upside") or -9),
                "r1y": lambda x: -(x[0].get("r1y") or -9), "r1d": lambda x: -(x[0].get("r1d") or -9),
                "div": lambda x: -(x[0].get("div") or 0)}[fsort]
        items_.sort(key=keyf)
        n_show = st.session_state.get("find_n", 12)
        st.caption(L(f"{len(items_)} akcija · prikazano {min(n_show, len(items_))}", f"{len(items_)} stocks · showing {min(n_show, len(items_))}"))
        for k in range(0, min(n_show, len(items_)), 3):
            cols_ = st.columns(3)
            for col_, (r, o) in zip(cols_, items_[k:k + 3]):
                with col_:
                    stock_card(r, "find", o)
        if len(items_) > n_show:
            st.button(L("Prikaži još", "Show more"), key="find_more", on_click=lambda: st.session_state.update(find_n=n_show + 12))
        with st.expander("➕ " + L("Dodaj akciju koje nema na listi", "Add a stock that is not on the list")):
            a1, a2, a3 = st.columns([1, 2, 1], vertical_alignment="bottom")
            new_t = a1.text_input(L("Simbol (Yahoo)", "Symbol (Yahoo)"), key="find_new_t", placeholder="AMD, RHM.DE, OR.PA")
            new_n = a2.text_input(L("Naziv", "Name"), key="find_new_n", placeholder="Advanced Micro Devices")
            if a3.button(L("Dodaj i prikaži", "Add & open"), key="find_add", type="primary") and new_t.strip():
                tk_new = new_t.strip().upper()
                wl_ = [(t_, n_) for t_, n_ in stocks.watchlist() if t_ != tk_new] + [(tk_new, new_n.strip() or tk_new)]
                stocks.save_watchlist("\n".join(f"{t_} | {n_}" for t_, n_ in wl_))
                with st.spinner(L("Preuzimam cene i podatke...", "Fetching prices and data...")):
                    try:
                        stocks.refresh_prices(con)
                        stocks.refresh_info(con)
                    except Exception as ex:  # noqa: BLE001
                        st.error(str(ex))
                _stock_rows.clear(); _opps.clear()
                st.session_state.update(ssub="s_detail", stock_sel=tk_new)
                st.rerun()
    elif sv == "s_pick":
        st.markdown('<div class="fn-disclaimer">' + (
            "Ovo je <b>faktorski filter</b> (momentum, vrednovanje, profitabilnost, rast, mišljenje analitičara, volatilnost) "
            "primenjen na listu praćenja, a ne investicioni savet. Rangira akcije prema tome koliko su atraktivne po ovim merilima "
            "u odnosu na ostale sa liste - pre ulaganja uvek proveri kompaniju i svoj profil rizika."
            if ui == "sr" else
            "This is a <b>factor screen</b> (momentum, valuation, profitability, growth, analyst view, volatility) applied to your "
            "watchlist, not investment advice. It ranks stocks by how attractive they look on these measures relative to the rest "
            "of the list - always check the company and your risk profile before investing.") + "</div>", unsafe_allow_html=True)
        with st.expander("Kako se računa skor" if ui == "sr" else "How the score works"):
            st.markdown("\n".join(f"- **{(sr_ if ui == 'sr' else en_)}** - {int(w * 100)}%" for _, w, _, sr_, en_ in stocks.FACTORS)
                        + ("\n- **trend** (cena iznad 200-dnevnog proseka) - 10% ukupnog skora\n\nSvaki faktor je rang (0-100) unutar liste praćenja."
                           "\n\nSve akcije se rangiraju po istim merilima, bez obzira na zemlju. Porez na dividendu je prikazan samo kao "
                           "informacija uz svaku akciju i ne utiče na skor."
                           if ui == "sr" else "\n- **trend** (price above the 200-day average) - 10% of the total\n\nEach factor is a rank (0-100) within the watchlist."
                           "\n\nAll stocks are ranked on the same measures regardless of country. Dividend tax is shown for information "
                           "only and does not affect the score."))
        labels_f = {k: (sr_ if ui == "sr" else en_) for k, _, _, sr_, en_ in stocks.FACTORS}
        for i, r in enumerate(ranked[:10]):
            with st.container(border=True, key=f"{'hero' if i == 0 else 'card'}_pick_{r['ticker']}"):
                bars = "".join(f'<div class="fn-fbar"><span>{h(labels_f[k])}</span><div><i style="width:{v * 100:.0f}%"></i></div></div>'
                               for k, v in r["parts"].items())
                why = "".join(f'<span class="fn-chip">{h(x)}</span>' for x in stocks.reasons(r, ui))
                dg = r.get("drag") or 0
                if r.get("region") in ("eu", "us") and (r.get("div_y") or 0) > 0:
                    why += (f'<span class="fn-chip fn-chip-muted">{"dividenda" if ui == "sr" else "dividend"} {(r.get("div_y") or 0) * 100:.2f}% · '
                            f'{"porez na nju" if ui == "sr" else "tax on it"} {dg * 100:.2f}%/{"god." if ui == "sr" else "yr"}</span>')
                st.markdown(f'<div class="fn-meta"><span class="fn-badge">#{i + 1}</span><span class="fn-src" style="--c:{styles.src_color(r["sector"])}">{h(r["sector"] or "-")}</span>'
                            f'<span class="fn-cite">{r["price"]:.2f} {h(r["currency"])}</span><span>{"1g" if ui == "sr" else "1y"} {pct(r["r1y"])}</span></div>'
                            f'<div class="fn-pick"><div><div class="fn-title">{h(r["name"])} <span class="fn-tk">{h(r["ticker"])}</span></div>'
                            f'<div class="fn-chips" style="margin-top:8px">{why}</div></div>'
                            f'<div class="fn-score"><b>{r["score"]}</b><span>{"skor" if ui == "sr" else "score"}</span></div></div>'
                            f'<div class="fn-fbars">{bars}</div>', unsafe_allow_html=True)
                with st.container(horizontal=True, key=f"act_pick_{r['ticker']}"):
                    st.button("📈 " + ("Detalj" if ui == "sr" else "Detail"), key=f"pk_d_{r['ticker']}",
                              on_click=lambda tk_=r["ticker"]: st.session_state.update(ssub="s_detail", stock_sel=tk_))
    elif sv == "s_ind":
        tick_names = {r["ticker"]: r["name"] for r in rows_s}
        if st.session_state.get("stock_sel") not in tick_names:
            st.session_state["stock_sel"] = next(iter(tick_names))
        c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
        tk = c1.selectbox("Kompanija" if ui == "sr" else "Company", list(tick_names), key="stock_sel",
                          format_func=lambda x: f"{tick_names[x]} ({x})")
        glossary = c2.toggle("Rečnik svih pokazatelja" if ui == "sr" else "Glossary of all indicators", key="ind_gloss")
        r = next(x for x in rows_s if x["ticker"] == tk)
        vals = indicators.values(stocks.info(con, tk), r)
        # medijana liste praćenja, za poređenje
        all_vals = [indicators.values(stocks.info(con, x["ticker"]), x) for x in rows_s if not x["etf"]]
        def med(k):
            xs = sorted(v[k] for v in all_vals if v[k] is not None)
            return xs[len(xs) // 2] if xs else None
        gl = {"good": ("dobro", "good"), "mid": ("prosečno", "average"), "bad": ("slabo", "weak")}
        counts_g = {g_: sum(1 for k in vals if indicators.grade(k, vals[k]) == g_) for g_ in gl}
        if r["etf"]:
            st.info("Ovo je ETF (fond) - većina pokazatelja za kompanije se ne odnosi na njega." if ui == "sr" else
                    "This is an ETF (fund) - most company indicators do not apply to it.")
        else:
            st.markdown('<div class="fn-chips">' + "".join(
                f'<span class="fn-chip fn-g-{g_}">{gl[g_][0 if ui == "sr" else 1]} <b>{n_}</b></span>' for g_, n_ in counts_g.items())
                + f'<span class="fn-chip fn-chip-muted">{"ocena je orijentaciona i zavisi od sektora" if ui == "sr" else "grades are indicative and depend on the sector"}</span></div>',
                unsafe_allow_html=True)
        for gk, gsr, gen, dsr, den in indicators.GROUPS:
            st.markdown(f'<div class="fn-section">{gsr if ui == "sr" else gen}</div><p class="fn-sub" style="margin-top:-4px">{h(dsr if ui == "sr" else den)}</p>',
                        unsafe_allow_html=True)
            for d in indicators.DEFS:
                if d[1] != gk:
                    continue
                k = d[0]
                v = vals.get(k)
                if v is None and not glossary:
                    continue
                g_ = indicators.grade(k, v)
                m_ = med(k)
                with st.container(border=True, key=f"card_ind_{k}"):
                    pill = f'<span class="fn-g fn-g-{g_}">{gl[g_][0 if ui == "sr" else 1]}</span>' if g_ else ""
                    cmp_ = (f'{"medijana liste" if ui == "sr" else "watchlist median"}: {indicators.fmt(k, m_, ui)}' if m_ is not None else "")
                    st.markdown(f'<div class="fn-ind"><div><div class="fn-ind-name">{h(d[2] if ui == "sr" else d[3])}</div>'
                                f'<div class="fn-sum" style="margin:2px 0 0">{h(d[7] if ui == "sr" else d[8])}</div></div>'
                                f'<div class="fn-ind-val"><b>{indicators.fmt(k, v, ui)}</b>{pill}<span>{h(cmp_)}</span></div></div>',
                                unsafe_allow_html=True)
                    with st.expander("Šta znači i kako se tumači" if ui == "sr" else "What it means and how to read it",
                                     expanded=False):
                        st.markdown(d[9] if ui == "sr" else d[10])
        st.caption(("Podaci: Yahoo Finance (poslednji objavljeni finansijski izveštaji i procene analitičara), osvežavaju se jednom dnevno. "
                    "Ocene dobro/prosečno/slabo su opšte granice - uvek poredi sa firmama iz istog sektora.") if ui == "sr" else
                   ("Data: Yahoo Finance (latest reported financials and analyst estimates), refreshed daily. "
                    "Good/average/weak grades use general thresholds - always compare with peers in the same sector."))
    elif sv == "s_tax":
        tick_names = {r["ticker"]: r["name"] for r in rows_s}
        if st.session_state.get("stock_sel") not in tick_names:
            st.session_state["stock_sel"] = next(iter(tick_names))
        tk = st.selectbox("Akcija ili ETF" if ui == "sr" else "Stock or ETF", list(tick_names), key="stock_sel",
                          format_func=lambda x: f"{tick_names[x]} ({x})")
        r = next(x for x in rows_s if x["ticker"] == tk)
        inf = stocks.info(con, tk)
        cc = eu.country(tk, inf)
        cname = eu.COUNTRY_NAME.get(cc, (cc, cc))[0 if ui == "sr" else 1]
        etf = eu.ETF_INFO.get(tk)
        dt = eu.dividend_tax(cc)
        L = (lambda a, b: a if ui == "sr" else b)
        vals_i = indicators.values(inf, r)
        # --- osnovno o instrumentu
        kp = [(cname, L("zemlja izdavaoca" if not etf else "domicil fonda", "issuer country" if not etf else "fund domicile")),
              (inf.get("currency") or ("EUR" if eu.is_eur(tk) else "-"), L("valuta trgovanja", "trading currency")),
              (inf.get("fullExchangeName") or inf.get("exchange") or "-", L("berza", "exchange"))]
        if etf:
            ter_txt = f'{etf["ter"] * 100:.2f}%'
            kp += [(ter_txt.replace(".", ",") if ui == "sr" else ter_txt, "TER"),
                   (L("akumulira", "accumulating") if etf["policy"] == "acc" else L("isplaćuje", "distributing"), L("dividende", "dividends"))]
        else:
            kp += [(indicators.fmt("div_y", vals_i["div_y"], ui), L("dividendni prinos", "dividend yield")),
                   (indicators.fmt("payout", vals_i["payout"], ui), L("racio isplate", "payout ratio"))]
        st.markdown('<div class="fn-kpis">' + "".join(f'<div class="fn-kpi"><b>{h(str(v))}</b><span>{h(l)}</span></div>' for v, l in kp)
                    + "</div>", unsafe_allow_html=True)
        if not eu.is_eur(tk, inf):
            st.warning(L("Ova hartija se ne trguje u evrima - računaj trošak konverzije valute.",
                         "This security does not trade in euros - account for currency conversion costs."))
        # --- ETF / indeks
        if etf:
            st.markdown(f'<div class="fn-section">{L("Fond i indeks", "Fund and index")}</div>', unsafe_allow_html=True)
            rows_e = [(L("Indeks", "Index"), etf["index"]), ("ISIN", etf["isin"]),
                      (L("Godišnji trošak (TER)", "Annual cost (TER)"), f'{etf["ter"] * 100:.2f}%'),
                      (L("Domicil", "Domicile"), eu.COUNTRY_NAME[etf["dom"]][0 if ui == "sr" else 1]),
                      (L("Dividende", "Dividends"), L("akumuliraju se u fondu (Acc)", "reinvested in the fund (Acc)") if etf["policy"] == "acc"
                       else L("isplaćuju se investitorima (Dist)", "paid out to investors (Dist)")),
                      (L("Replikacija", "Replication"), etf["repl"][0 if ui == "sr" else 1]),
                      (L("Broj kompanija", "Holdings"), etf["holdings"])]
            if inf.get("totalAssets"):
                rows_e.append((L("Veličina fonda", "Fund size"), indicators.fmt("mcap", inf["totalAssets"], ui)))
            st.markdown('<div class="fn-rows">' + "".join(f'<div class="fn-an"><b>{h(k)}</b><span>{h(v)}</span></div>' for k, v in rows_e)
                        + "</div>", unsafe_allow_html=True)
            idx_txt = eu.INDEX_INFO.get(etf["index"])
            if idx_txt:
                st.markdown(f'<div class="fn-why"><b>{h(etf["index"])}:</b> {h(idx_txt[0 if ui == "sr" else 1])}</div>', unsafe_allow_html=True)
            st.caption(L("Podaci o fondu su približni - proveri aktuelni TER i veličinu na justETF.com ili sajtu izdavaoca.",
                         "Fund data are approximate - check the current TER and size on justETF.com or the issuer's site."))
        # --- dividende
        divs = inf.get("_divs") or []
        if not (etf and etf["policy"] == "acc"):
            st.markdown(f'<div class="fn-section">{L("Dividende", "Dividends")}</div>', unsafe_allow_html=True)
            last12 = [d for d in divs if d[0] >= (date.today() - timedelta(days=365)).isoformat()]
            freq = len(last12)
            freq_txt = {0: L("nema isplata u poslednjih 12 meseci", "no payments in the last 12 months"), 1: L("godišnje", "annual"),
                        2: L("polugodišnje", "semi-annual"), 4: L("kvartalno", "quarterly")}.get(freq, L(f"{freq} puta godišnje", f"{freq} times a year"))
            ex_d = inf.get("exDividendDate")
            ex_txt = datetime.fromtimestamp(ex_d, timezone.utc).strftime("%d.%m.%Y.") if isinstance(ex_d, (int, float)) else "-"
            rows_d = [(L("Godišnja dividenda po akciji", "Annual dividend per share"),
                       f'{inf["dividendRate"]:.2f} {inf.get("currency", "")}' if inf.get("dividendRate") else "-"),
                      (L("Dividendni prinos", "Dividend yield"), indicators.fmt("div_y", vals_i["div_y"], ui)),
                      (L("Učestalost isplate", "Payment frequency"), freq_txt),
                      (L("Poslednji ex-dividend datum", "Latest ex-dividend date"), ex_txt),
                      (L("Racio isplate (deo dobiti)", "Payout ratio (share of profit)"), indicators.fmt("payout", vals_i["payout"], ui))]
            st.markdown('<div class="fn-rows">' + "".join(f'<div class="fn-an"><b>{h(k)}</b><span>{h(v)}</span></div>' for k, v in rows_d)
                        + "</div>", unsafe_allow_html=True)
            if divs:
                st.caption(L("Isplate (2 godine): ", "Payments (2 years): ") + ", ".join(
                    f'{datetime.fromisoformat(d).strftime("%d.%m.%Y.")} - {a:.2f}' for d, a in divs[-8:]))
        # --- porez
        st.markdown(f'<div class="fn-section">{L("Porez na dividendu za rezidenta Srbije", "Dividend tax for a Serbian resident")}</div>',
                    unsafe_allow_html=True)
        if etf and etf["policy"] == "acc":
            st.markdown('<div class="fn-why">' + h(L(
                "Fond akumulira dividende, pa ti ne isplaćuje ništa: nema poreza na dividende ni prijava PP OPO. "
                "Porez od 15% plaćaš samo na kapitalni dobitak kada prodaš udele (prijava PPDG-3R).",
                "The fund reinvests dividends and pays you nothing: no dividend tax and no PP OPO filings. "
                "You pay 15% capital gains tax only when you sell (form PPDG-3R).")) + "</div>", unsafe_allow_html=True)
        elif dt:
            stat, extra, tot_nr, tot_r, recl = dt
            treaty = eu.WHT[cc][1]
            pc_ = lambda x: (f"{x * 100:.2f}".rstrip("0").rstrip(".").replace(".", ",") if ui == "sr" else f"{x * 100:.2f}".rstrip("0").rstrip(".")) + "%"
            rows_t = [(L("Zadržava država izdavaoca (statutarno)", "Withheld by issuer country (statutory)"), pc_(stat)),
                      (L("Stopa iz ugovora sa Srbijom", "Rate under treaty with Serbia"), pc_(treaty) if treaty is not None else L("nema ugovora", "no treaty")),
                      (L("Može da se traži povraćaj", "Reclaimable from abroad"), pc_(recl)),
                      (L("Doplata u Srbiji (bez povraćaja / uz povraćaj)", "Top-up in Serbia (no reclaim / with reclaim)"),
                       f"{pc_(extra)} / {pc_(max(0, eu.SERBIA_RATE - (treaty if treaty is not None else stat)))}"),
                      (L("Ukupan porez - bez povraćaja", "Total tax - without reclaim"), pc_(tot_nr)),
                      (L("Ukupan porez - uz povraćaj", "Total tax - with reclaim"), pc_(tot_r)),
                      (L("Godišnji gubitak prinosa zbog poreza (bez / uz povraćaj)", "Annual return lost to tax (no / with reclaim)"),
                       f"{pc_(eu.drag(vals_i['div_y'], cc))} / {pc_(eu.drag(vals_i['div_y'], cc, reclaim=True))}")]
            st.markdown('<div class="fn-rows">' + "".join(f'<div class="fn-an"><b>{h(k)}</b><span>{h(v)}</span></div>' for k, v in rows_t)
                        + "</div>", unsafe_allow_html=True)
            if cc == "FR":
                st.caption(L("Francuska zadržava 12,8% fizičkim licima nerezidentima; ako ti broker zadrži 25%, razliku do 15% možeš da tražiš nazad. "
                             "Pri kupovini akcija velikih francuskih kompanija plaća se i porez na transakcije od 0,4%.",
                             "France withholds 12.8% for non-resident individuals; if your broker withholds 25%, you can reclaim the excess over 15%. "
                             "Buying shares of large French companies also incurs a 0.4% transaction tax."))
            if etf:
                st.caption(L("Za fondove sa domicilom u Nemačkoj poreski tretman isplata nerezidentima može da se razlikuje - proveri kod brokera.",
                             "For Germany-domiciled funds the tax on distributions to non-residents may differ - check with your broker."))
        # --- kalkulator troškova
        st.markdown(f'<div class="fn-section">{L("Kalkulator troškova i poreza", "Cost and tax calculator")}</div>', unsafe_allow_html=True)
        cfg_c = ai.load_config()
        c1, c2, c3 = st.columns(3)
        amt = c1.number_input(L("Ulog (EUR)", "Amount (EUR)"), 100.0, 1e7, 5000.0, 500.0, key="cc_amt")
        yrs = c2.number_input(L("Period (godina)", "Horizon (years)"), 1, 40, 5, key="cc_yrs")
        er = c3.number_input(L("Očekivani rast cene godišnje (%)", "Expected price growth per year (%)"), -20.0, 30.0, 6.0, 0.5, key="cc_er") / 100
        c4, c5, c6, c7 = st.columns(4)
        com = c4.number_input(L("Provizija brokera (%)", "Broker commission (%)"), 0.0, 3.0, float(cfg_c.get("com_pct", 0.10)), 0.01, key="cc_com") / 100
        cmin = c5.number_input(L("Minimalna provizija (EUR)", "Minimum commission (EUR)"), 0.0, 50.0, float(cfg_c.get("com_min", 3.0)), 0.5, key="cc_min")
        fxp = c6.number_input(L("Konverzija valute (%)", "Currency conversion (%)"), 0.0, 3.0, 0.0, 0.05, key="cc_fx",
                              help=L("0 ako ti je račun kod brokera u evrima", "0 if your broker account is in euros")) / 100
        recl_on = c7.toggle(L("Tražim povraćaj poreza", "I reclaim excess tax"), key="cc_recl")
        dy_ = 0.0 if (etf and etf["policy"] == "acc") else (vals_i["div_y"] or 0.0)
        res_c = eu.costs(amt, yrs, er, dy_, cc, com, cmin, fxp, ter=(etf["ter"] if etf else 0.0),
                         accumulating=bool(etf and etf["policy"] == "acc"), reclaim=recl_on)
        eur = (lambda x: f"{x:,.0f} €".replace(",", ".") if ui == "sr" else f"€{x:,.0f}")
        rows_k = [(L("Provizija pri kupovini", "Buy commission"), eur(res_c["buy_fee"])),
                  (L("Konverzija valute", "Currency conversion"), eur(res_c["fx"])),
                  (L("Porez na transakcije (Francuska 0,4%)", "Transaction tax (France 0.4%)"), eur(res_c["ftt"])),
                  (L("Trošak fonda (TER) ukupno", "Fund cost (TER) total"), eur(res_c["ter"])),
                  (L("Porez na dividende ukupno", "Dividend tax total"), eur(res_c["div_tax"])),
                  (L("Neto dividende primljene", "Net dividends received"), eur(res_c["divs_net"])),
                  (L("Provizija pri prodaji", "Sell commission"), eur(res_c["sell_fee"])),
                  (L("Porez na kapitalni dobitak (15%)", "Capital gains tax (15%)"),
                   eur(res_c["cg_tax"]) + (L(" - oslobođeno posle 10 godina", " - exempt after 10 years") if yrs > 10 else "")),
                  (L("Vrednost posle prodaje i poreza", "Value after sale and tax"), eur(res_c["end_value"]))]
        st.markdown('<div class="fn-rows">' + "".join(f'<div class="fn-an"><b>{h(k)}</b><span>{h(v)}</span></div>' for k, v in rows_k)
                    + "</div>", unsafe_allow_html=True)
        tot_cost = res_c["buy_fee"] + res_c["fx"] + res_c["ftt"] + res_c["ter"] + res_c["div_tax"] + res_c["sell_fee"] + res_c["cg_tax"]
        st.caption(L(f"Ukupno troškovi i porezi: {eur(tot_cost)}. Pojednostavljen model: konstantan rast i dividendni prinos, "
                     f"bez reinvestiranja dividendi. Provizije unesi prema svom brokeru.",
                     f"Total costs and taxes: {eur(tot_cost)}. Simplified model: constant growth and dividend yield, dividends "
                     f"not reinvested. Enter commissions from your own broker."))
        if st.button("💾 " + L("Zapamti proviziju kao podrazumevanu", "Save commission as default"), key="cc_save"):
            cfg_c.update({"com_pct": com * 100, "com_min": cmin})
            ai.save_config(cfg_c)
            st.toast(t("saved"))
        with st.expander(L("Kako funkcionišu porezi i troškovi - objašnjenje", "How taxes and costs work - explainer"), expanded=False):
            st.markdown(eu.EXPLAIN[ui])
            st.markdown(L("**Izvori:** ", "**Sources:** ") + " · ".join(f"[{n}]({u})" for n, u in eu.SOURCES))
        # --- poređenje zemalja
        with st.expander(L("Poređenje poreza po zemljama", "Tax comparison by country"), expanded=False):
            tbl = []
            for code_ in ["NL", "DE", "FR", "BE", "AT", "IT", "ES", "IE", "CH", "US"]:
                d_ = eu.dividend_tax(code_)
                tbl.append({L("Zemlja", "Country"): eu.COUNTRY_NAME[code_][0 if ui == "sr" else 1],
                            L("Statutarno", "Statutory"): d_[0] * 100,
                            L("Ugovor sa Srbijom", "Treaty with Serbia"): (eu.WHT[code_][1] * 100) if eu.WHT[code_][1] is not None else None,
                            L("Ukupno bez povraćaja", "Total, no reclaim"): d_[2] * 100,
                            L("Ukupno uz povraćaj", "Total, with reclaim"): d_[3] * 100})
            dft = pd.DataFrame(tbl)
            st.dataframe(dft, hide_index=True, column_config={c_: st.column_config.NumberColumn(format="%.2f%%") for c_ in dft.columns[1:]})
    elif sv == "s_news":
        tick_names = {r["ticker"]: r["name"] for r in rows_s}
        sel_t = st.multiselect("Kompanije" if ui == "sr" else "Companies", [t_ for t_ in tick_names if t_ not in stocks.ETFS],
                               format_func=lambda x: f"{tick_names[x]} ({x})", placeholder=t("all"), key="news_tk")
        nq = st.text_input(t("search"), key="q_cnews", placeholder="earnings, AI, guidance...")
        cn = db.query_items(con, start_iso=utc_iso(datetime.now(timezone.utc) - timedelta(days=7)), categories=["Kompanije"],
                            search=nq or None, order="date", limit=600)
        if sel_t:
            ids_t = {r_["id"] for r_ in con.execute(f"SELECT id FROM items WHERE ticker IN ({','.join('?' * len(sel_t))})", sel_t)}
            cn = [x for x in cn if x["id"] in ids_t]
        cn, cextra = dedupe(cn, 40)
        render_items(cn, "cnews", extra=cextra)
    else:
        tick_names = {r["ticker"]: r["name"] for r in rows_s}
        opts_t = list(tick_names)
        if st.session_state.get("stock_sel") not in opts_t:
            st.session_state["stock_sel"] = opts_t[0]
        c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
        tk = c1.selectbox("Akcija" if ui == "sr" else "Stock", opts_t, key="stock_sel", format_func=lambda x: f"{tick_names[x]} ({x})")
        rng = c2.segmented_control("rng", ["1M", "6M", "1Y", "2Y"], default="6M", key="stock_rng", label_visibility="collapsed") or "6M"
        r = next(x for x in rows_s if x["ticker"] == tk)
        rk = next((x for x in ranked if x["ticker"] == tk), None)
        kp = [(f'{r["price"]:.2f}', r["currency"] or ("cena" if ui == "sr" else "price")), (pct(r["r1d"]), "1d"),
              (pct(r["r1y"]), "1g" if ui == "sr" else "1y"), (f'{r["pe"]:.1f}' if r["pe"] else "-", "P/E"),
              (pct(r["roe"], False) if r["roe"] is not None else "-", "ROE"),
              (pct(r["upside"]), "do cilja analitičara" if ui == "sr" else "to analyst target"),
              (big(r["mcap"]), "tržišna vrednost" if ui == "sr" else "market cap"),
              (str(rk["score"]) if rk else "-", "skor" if ui == "sr" else "score")]
        st.markdown('<div class="fn-kpis">' + "".join(f'<div class="fn-kpi"><b>{h(v)}</b><span>{h(l)}</span></div>' for v, l in kp)
                    + "</div>", unsafe_allow_html=True)
        price_chart(tk, days={"1M": 31, "6M": 183, "1Y": 366, "2Y": 732}[rng], height=340, sma=True)
        _od = next((o for o in _opps(p_upd or "", _stamp())[0] if o["ticker"] == tk), None)
        if _od and _od["qualifies"]:
            opp_card(_od, 0, chart=False)
        if rk:
            st.markdown('<div class="fn-chips">' + "".join(f'<span class="fn-chip">{h(x)}</span>' for x in stocks.reasons(rk, ui)) + "</div>",
                        unsafe_allow_html=True)
        if r["summary"]:
            with st.expander("O kompaniji" if ui == "sr" else "About the company"):
                body = translated_full({"id": f"bs_{tk}"}, r["summary"], "sr") if lang == "sr" else r["summary"]
                st.markdown(f'<div class="fn-article">{paragraphs(body)}</div>', unsafe_allow_html=True)
        tk_news = [dict(x) for x in con.execute("SELECT * FROM items WHERE ticker=? ORDER BY published DESC LIMIT 12", (tk,))]
        if ai_on and tk not in stocks.ETFS:
            ak = f"aiv_{tk}_{ui}"
            if ak in st.session_state:
                with st.container(key="briefmd_stock"):
                    st.markdown(st.session_state[ak].replace("$", "\\$"))
            elif st.button("🧠 " + ("AI analiza akcije" if ui == "sr" else "AI stock analysis"), key="ai_stock", type="primary"):
                with st.spinner(t("analyzing")):
                    try:
                        st.session_state[ak] = stocks.ai_view(rk or r, tk_news, ui)
                    except Exception as ex:  # noqa: BLE001
                        st.session_state[ak] = f"Error: {ex}"
                st.rerun()
        st.markdown(f'<div class="fn-section">{"Najnovije vesti" if ui == "sr" else "Latest news"}</div>', unsafe_allow_html=True)
        if tk_news:
            render_items(tk_news, f"tkn_{tk}", show_score=False)
        else:
            st.info("Za ovu kompaniju još nema vesti - stižu pri sledećem osvežavanju." if ui == "sr" else
                    "No news for this company yet - it arrives with the next refresh.")


def _period_change(t_, days):
    s_ = stocks.series(con, t_, days=days + 7)
    if len(s_) < 2:
        return None, None
    start_d = (date.today() - timedelta(days=days)).isoformat()
    base = next((c_ for d_, c_ in s_ if d_ >= start_d), s_[0][1])
    v_ = s_[-1][1] / (10 if t_ == "^TNX" and s_[-1][1] > 20 else 1)
    return v_, (s_[-1][1] / base - 1) if base else None


def market_period(days):
    """Kretanje tržišta i najveći dobitnici/gubitnici sa liste praćenja u izabranom periodu."""
    L = (lambda a, b: a if ui == "sr" else b)
    tiles = ""
    for t_, name, dec in stocks.MARKETS:
        v_, ch = _period_change(t_, days)
        if v_ is None or ch is None:
            continue
        num = f"{v_:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".") if ui == "sr" else f"{v_:,.{dec}f}"
        tiles += (f'<div class="fn-stat"><span>{h(name)}</span><b>{num}</b>'
                  f'<i class="{"fn-up" if ch >= 0 else "fn-down"}">{"▲" if ch >= 0 else "▼"} {abs(ch) * 100:.1f}% · {PERIODS[days][0 if ui == "sr" else 1]}</i></div>')
    if tiles:
        st.markdown(f'<div class="fn-home-grid">{tiles}</div>', unsafe_allow_html=True)
    else:
        st.info(L("Još nema tržišnih podataka - osveži akcije u sekciji Akcije.", "No market data yet - refresh in Stocks."))
    mv = []
    for t_, name in stocks.watchlist():
        _, ch = _period_change(t_, days)
        if ch is not None:
            mv.append((ch, t_, (stocks.info(con, t_) or {}).get("shortName") or name))
    if mv:
        mv.sort()
        c1, c2 = st.columns(2, gap="large")
        for col, title_, rows_ in ((c1, L("Najveći rast", "Top gainers"), mv[::-1][:6]), (c2, L("Najveći pad", "Top losers"), mv[:6])):
            col.markdown(f'<div class="fn-section">{title_}</div>' + '<div class="fn-fbars" style="grid-template-columns:1fr">' + "".join(
                f'<div class="fn-fbar" style="grid-template-columns: 1fr 110px 64px"><span>{h(n_[:28])} <span class="fn-tk">{h(t_)}</span></span>'
                f'<div><i style="width:{min(100, abs(c_) * 250):.0f}%; background:{"#9CC79A" if c_ >= 0 else "#E07C8A"}"></i></div>'
                f'<span style="text-align:right" class="{"fn-up" if c_ >= 0 else "fn-down"}">{c_ * 100:+.1f}%</span></div>' for c_, t_, n_ in rows_)
                + "</div>", unsafe_allow_html=True)


def research_period(days):
    L = (lambda a, b: a if ui == "sr" else b)
    pool = [p for p in findings_pool(days, limit=24) if p["finding"]]
    if not pool:
        st.info(L("Nema studija za ovaj period - izaberi duži period ili osveži radove u Istraživanjima.",
                  "No studies for this period - pick a longer period or refresh papers in Research."))
        return
    rv = insights.review(pool, ui)
    chips_m = "".join(f'<span class="fn-chip">{h(k)} <b>{v}</b></span>' for k, v in rv["methods"])
    chips_d = "".join(f'<span class="fn-chip">{h(k)} <b>{v}</b></span>' for k, v in rv["data"])
    st.markdown(f'<div class="fn-kicker">{L("Najčešće metode", "Most used methods")}</div><div class="fn-chips">{chips_m or "-"}</div>'
                f'<div class="fn-kicker" style="margin-top:10px">{L("Podaci i tržišta", "Data & markets")}</div><div class="fn-chips">{chips_d or "-"}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="fn-section">{L("Najvažniji nalazi", "Key findings")} · {len(pool)}</div>', unsafe_allow_html=True)
    tr_ = ensure_translations([{"id": p["id"], "title": p["title"], "summary": ""} for p in pool], lang)
    st.markdown('<ul class="fn-bullets">' + "".join(
        f'<li><b>{h(p["finding"])}</b><br><a href="{h(p["link"])}" target="_blank" class="fn-sub">{h(tr_.get(p["id"], {}).get("title") or p["title"])}</a>'
        f'<small>{h((p.get("venue") or "")[:40])} · {h(p.get("pub_date") or "")}{" · ❝ " + str(p["cited_by"]) if p.get("cited_by") else ""}</small></li>'
        for p in pool) + "</ul>", unsafe_allow_html=True)


if page == "t_brief":
    L_ = (lambda a, b: a if ui == "sr" else b)
    bdays = period_pick("bper2", 7)
    b_end = datetime.now(timezone.utc)
    b_start = b_end - timedelta(days=bdays)
    st.markdown(f'<div class="fn-sub">{L_("Šta je bilo bitno", "What mattered")}: {b_start.astimezone().strftime("%d.%m.%Y.")} - {b_end.astimezone().strftime("%d.%m.%Y.")}</div>',
                unsafe_allow_html=True)
    tab_n, tab_r, tab_m = st.tabs(["📰 " + L_("Vesti", "News"), "🔬 " + L_("Istraživanja - nalazi", "Research - findings"), "📈 " + L_("Tržišta", "Markets")])
    with tab_n:
        news_summary(bdays, tuple(NEWS_CATS + ["Kompanije"] + GENERAL_CATS), THEMES + WTHEMES, "brief", n=8)
        brief_live(utc_iso(b_start), utc_iso(b_end), long=bdays > 1)
    with tab_r:
        research_period(bdays)
    with tab_m:
        market_period(bdays)

# ---------- Pregled 6 meseci ----------
if page == "t_6m":
    if not db.get_meta(con, "backfill_done"):
        st.info(t("bf_info"))
    if st.button(t("bf_btn") if not db.get_meta(con, "backfill_done") else t("bf_redo")):
        bar = st.progress(0.0)
        res = fetcher.backfill(con, months=6, progress=lambda x: bar.progress(min(x, 1.0)))
        st.success(f"{t('bf_done')}: {res['new']}" + (f" ({res['errors']}/{res['requests']} ✗)" if res["errors"] else ""))
    today = date.today()
    months = []
    y, m = today.year, today.month
    for _ in range(7):
        months.append((y, m))
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    ym = st.selectbox(t("month"), months, format_func=lambda v: f"{MONTHS[ui][v[1] - 1]} {v[0]}")
    m_start = date(ym[0], ym[1], 1)
    m_end = (date(ym[0] + (ym[1] == 12), ym[1] % 12 + 1, 1) - timedelta(days=1))
    ms, me = day_bounds(m_start, min(m_end, today))
    month_label = f"{MONTHS[ui][ym[1] - 1]} {ym[0]}"
    if ai_on:
        with st.expander(t("month_ai"), expanded=bool(db.get_brief(con, f"M-{ym[0]}-{ym[1]:02d}", ui))):
            with st.container(key="briefmd_m"):
                brief_block(f"M-{ym[0]}-{ym[1]:02d}", t("month_ai"),
                            lambda: (dedupe(db.query_items(con, ms, me, exclude_categories=[RESEARCH], limit=400), 60)[0], []),
                            month_label)
    st.markdown(f'<div class="fn-section">{t("top_month")}</div>', unsafe_allow_html=True)
    top, extra = dedupe(db.query_items(con, ms, me, exclude_categories=[RESEARCH], limit=300), 15)
    render_items(top, "m6", extra=extra, hero_first=True)
    st.markdown(f'<div class="fn-section">{t("by_week")}</div>', unsafe_allow_html=True)
    w = m_start - timedelta(days=m_start.weekday())
    while w <= min(m_end, today):
        ws, we = day_bounds(max(w, m_start), min(w + timedelta(days=6), m_end))
        witems, wextra = dedupe(db.query_items(con, ws, we, exclude_categories=[RESEARCH], limit=120), 5)
        with st.expander(f"{t('week')} {max(w, m_start):%d.%m.} - {min(w + timedelta(days=6), m_end):%d.%m.}"
                         f" ({len(witems)})"):
            render_items(witems, f"w{w.isoformat()}", extra=wextra)
        w += timedelta(days=7)
    st.divider()
    six_start = today - timedelta(days=183)

    def six_items():
        out = []
        y2, m2 = six_start.year, six_start.month
        while (y2, m2) <= (today.year, today.month):
            a = date(y2, m2, 1)
            b = date(y2 + (m2 == 12), m2 % 12 + 1, 1) - timedelta(days=1)
            s1, e1 = day_bounds(a, min(b, today))
            out += dedupe(db.query_items(con, s1, e1, exclude_categories=[RESEARCH], limit=200), 10)[0]
            y2, m2 = (y2 + 1, 1) if m2 == 12 else (y2, m2 + 1)
        return out, []

    if ai_on:
        with st.expander(t("six_ai"), expanded=bool(db.get_brief(con, f"6M-{today.isoformat()[:7]}", ui))):
            with st.container(key="briefmd_6"):
                brief_block(f"6M-{today.isoformat()[:7]}", t("six_ai"), six_items,
                            f"{six_start:%d.%m.%Y.} - {today:%d.%m.%Y.}")

# ---------- Istraživanja ----------
if page == "t_res":
    views = ["r_latest", "r_journals", "r_c6", "r_c24", "r_classic"]
    view = st.radio(t("view"), views, format_func=t, horizontal=True, key="rview")
    c1, c2 = st.columns([3, 1])
    rq = c1.text_input(t("search"), key="q_res", placeholder="neural network, fuzzy, portfolio, LLM...")
    if c2.button(t("r_refresh")):
        bar = st.progress(0.0)
        r = research.refresh(con, progress=lambda x: bar.progress(min(x, 1.0)))
        if r["errors"]:
            st.warning(f"{r['errors']}/{r['jobs']} ✗")
    if view == "r_latest":
        rdays = st.selectbox(t("period"), [7, 14, 30, 90, 180], format_func=lambda d: f"{d}d", key="rdays")
        rsrc = st.multiselect(t("sources"), [f["name"] for f in fetcher.load_feeds() if f.get("category") == RESEARCH],
                              placeholder=t("all_src"), key="rsrc")
        sort = st.radio(t("sort"), ["by_imp", "by_date"], format_func=t, horizontal=True, key="rsort")
        items = db.query_items(con, start_iso=utc_iso(datetime.now(timezone.utc) - timedelta(days=rdays)),
                               categories=[RESEARCH], sources=rsrc, search=rq or None,
                               order="score" if sort == "by_imp" else "date", limit=60)
        render_items(items, "res", show_score=sort == "by_imp")
    elif view == "r_classic":
        st.markdown(f'<div class="fn-section">{t("curated")}</div>', unsafe_allow_html=True)
        topics_c = sorted({c["topic"] for c in CLASSICS})
        ct = st.selectbox(t("topic"), [t("all")] + topics_c, key="ctopic")
        for c in CLASSICS:
            if ct != t("all") and c["topic"] != ct:
                continue
            if rq and rq.lower() not in (c["title"] + c["authors"] + c["sr"] + c["en"]).lower():
                continue
            link = "https://scholar.google.com/scholar?q=" + urllib.parse.quote_plus(f'"{c["title"]}" {c["authors"]}')
            with st.container(border=True, key=f"card_cl_{c['year']}_{abs(hash(c['title'])) % 10**8}"):
                card(c["title"], link,
                     f'<span class="fn-src" style="--c:{styles.src_color(c["topic"])}">{h(c["topic"])}</span>'
                     f'<span class="fn-cite">{c["year"]}</span><span>{h(c["authors"])}</span><span>{h(c["venue"])}</span>')
                st.markdown(f'<div class="fn-why"><b>{t("why")}:</b> {h(c[ui])}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="fn-section">{t("most_cited_all")}</div>', unsafe_allow_html=True)
        render_papers(db.papers_by_tag(con, "classic", search=rq or None, limit=60), "cl")
    else:
        tag = {"r_journals": "journals_new", "r_c6": "cited_6m", "r_c24": "cited_24m"}[view]
        st.caption(("Časopisi: " if ui == "sr" else "Journals: ") + ", ".join(research.TOP_JOURNALS) if view == "r_journals" else
                   ("Rangirano po broju citata, za teme iz Podešavanja." if ui == "sr" else "Ranked by citations, for the topics in Settings."))
        render_papers(db.papers_by_tag(con, tag, search=rq or None,
                                       order="date" if view == "r_journals" else "cited", limit=60), tag)

# ---------- Arhiva ----------
if page == "t_rr":
    st.markdown(f'<p class="fn-sub">{t("rr_intro")}</p>', unsafe_allow_html=True)
    topics_rr = research.phd_topics()
    c1, c2, c3 = st.columns([2.4, 1.6, 1.6], vertical_alignment="center")
    with c1:
        days_rr = period_pick("rr_days", 30)
    months_rr = days_rr
    sel_rr = c2.selectbox(t("topic"), [None] + [tp["q"] for tp in topics_rr], key="rr_topic", label_visibility="collapsed",
                          format_func=lambda q: t("all_topics") if q is None else next(tp[ui] for tp in topics_rr if tp["q"] == q))
    rq_rr = c3.text_input(t("search"), key="q_rr", label_visibility="collapsed", placeholder=t("search"))
    pool = findings_pool(days_rr, topic=sel_rr, search=rq_rr, limit=40)
    if not pool:
        st.info(t("rr_none"))
    else:
        # zbirni pregled
        label_rr = t("all_topics") if sel_rr is None else next(tp[ui] for tp in topics_rr if tp["q"] == sel_rr)
        key_rr = f"RR-{months_rr}-{abs(hash(sel_rr or 'all')) % 10**8}-{date.today().isoformat()[:7]}"
        with st.expander(t("rr_review"), expanded=True):
            if not ai_on:
                rv = insights.review(pool, ui)
                chips_m = "".join(f'<span class="fn-chip">{h(k)} <b>{v}</b></span>' for k, v in rv["methods"])
                chips_d = "".join(f'<span class="fn-chip">{h(k)} <b>{v}</b></span>' for k, v in rv["data"])
                st.markdown(f'<div class="fn-kicker">{"Dominantne metode" if ui == "sr" else "Dominant methods"}</div>'
                            f'<div class="fn-chips">{chips_m or "-"}</div>'
                            f'<div class="fn-kicker" style="margin-top:10px">{"Podaci i tržišta" if ui == "sr" else "Data & markets"}</div>'
                            f'<div class="fn-chips">{chips_d or "-"}</div>', unsafe_allow_html=True)
                if rv["highlights"]:
                    st.markdown(f'<div class="fn-kicker" style="margin-top:10px">{"Najjači nalazi" if ui == "sr" else "Strongest findings"}</div>'
                                + "".join(f'<div class="fn-why">{h(x.get("finding") or "")} <a class="fn-gap-src" href="{h(x["link"])}" target="_blank">'
                                          f'· {h((x.get("venue") or "")[:40])}</a></div>' for x in rv["highlights"] if x.get("finding")),
                                unsafe_allow_html=True)
                if rv["open"]:
                    opens = [o[0] for o in rv["open"]]
                    if lang == "sr":
                        opens = [x[0] for x in ai._free_translate([(o, "") for o in opens], "sr")]
                    st.markdown(f'<div class="fn-kicker" style="margin-top:10px">{"Otvorena pitanja" if ui == "sr" else "Open questions"}</div>'
                                + "".join(f'<div class="fn-why">{h(o)}</div>' for o in opens), unsafe_allow_html=True)
            else:
                ex_rr = db.get_brief(con, key_rr, ui)
                if st.button(t("rr_review") if not ex_rr else t("remake"), key="rr_btn", type="primary"):
                    with st.spinner(t("writing")):
                        content = ai.research_review(label_rr, PERIODS[days_rr][0 if ui == "sr" else 1], [p for p in pool if p["finding"]], ui)
                    db.save_brief(con, key_rr, ui, content, utc_iso(datetime.now(timezone.utc)))
                    ex_rr = db.get_brief(con, key_rr, ui)
                if ex_rr:
                    with st.container(key="briefmd_rr"):
                        st.markdown(ex_rr["content"].replace("$", "\\$"))
        tr_rr = ensure_translations([{"id": p["id"], "title": p["title"], "summary": ""} for p in pool], lang)
        saved_rr = db.saved_paper_ids(con)
        for p in pool:
            with st.container(border=True, key=f"card_rr_{p['id']}"):
                meta = (f'<span class="fn-src" style="--c:{styles.src_color(p["venue"])}">{h(p["venue"] or "-")}</span>'
                        f'<span>{h(p["pub_date"] or "")}</span>'
                        + (f'<span class="fn-cite">❝ {p["cited_by"]}</span>' if p.get("cited_by") is not None else ""))
                st.markdown(f'<div class="fn-meta">{meta}</div>'
                            f'<div class="fn-finding"><span>{t("rr_found")}</span>{h(p["finding"] or reader.result_sentences(p.get("abstract")) or "-")}</div>'
                            f'<a class="fn-title fn-small" href="{h(p["link"])}" target="_blank">{h(tr_rr.get(p["id"], {}).get("title") or p["title"])}</a>',
                            unsafe_allow_html=True)
                with st.container(horizontal=True, key=f"act_rr_{p['id']}"):
                    if st.button(t("read"), key=f"rr_rd_{p['id']}"):
                        paper_dialog(p)
                    if st.button(t("p_saved_b") if p["id"] in saved_rr else t("p_save"), key=f"rr_sv_{p['id']}"):
                        db.toggle_paper_saved(con, p["id"])
                        st.rerun()

if page == "t_phd":
    st.markdown(f'<p class="fn-sub">{t("p_intro")}</p>', unsafe_allow_html=True)
    if st.button(t("p_refresh"), type="primary" if not db.get_meta(con, "phd_refreshed") else "secondary"):
        bar = st.progress(0.0)
        r = research.refresh_phd(con, progress=lambda x: bar.progress(min(x, 1.0) * 0.6))
        r2 = research.refresh_gaps(con, progress=lambda x: bar.progress(0.6 + min(x, 1.0) * 0.4))
        if r["errors"] or r2["errors"]:
            st.warning(f"{r['errors'] + r2['errors']}/{r['steps'] + r2['steps']} ✗")
    topics_ph = research.phd_topics()
    trends = {r["topic"]: dict(r) for r in con.execute("SELECT * FROM phd_trends")}
    if trends:
        st.markdown(f'<div class="fn-section">{t("p_trends")}</div>', unsafe_allow_html=True)
        mx = max([trends[tp["q"]]["recent"] for tp in topics_ph if tp["q"] in trends] or [1]) or 1
        rows_html = ""
        for tp in sorted(topics_ph, key=lambda x: -(trends.get(x["q"], {}).get("recent") or 0)):
            tr_ = trends.get(tp["q"])
            if not tr_:
                continue
            g_raw = db.get_meta(con, f"trend_new_{tp['q']}")
            g = (int(g_raw) / tr_["prev"] - 1) * 100 if (g_raw and tr_["prev"]) else None
            rows_html += (f'<div class="fn-trend"><span>{h(tp[ui])}</span><div class="fn-trend-bar"><i style="width:{tr_["recent"] / mx * 100:.0f}%"></i></div>'
                          f'<b>{tr_["recent"]:,}</b>' + ('<em>-</em>' if g is None else f'<em class="{"up" if g >= 0 else "down"}">{"▲" if g >= 0 else "▼"} {abs(g):.0f}%</em>')
                          + '</div>').replace(",", ".")
        st.markdown(f'<div class="fn-trends">{rows_html}</div>', unsafe_allow_html=True)
    view_p = st.segmented_control("pview", ["p_top", "p_map", "p_saved", "p_gaps"], format_func=t, default="p_top",
                                  key="pview", label_visibility="collapsed") or "p_top"
    if view_p == "p_top":
        c1, c2 = st.columns([2, 3])
        opts = [None] + [tp["q"] for tp in topics_ph]
        sel = c1.selectbox(t("topic"), opts, format_func=lambda q: t("all_topics") if q is None else
                           next(tp[ui] for tp in topics_ph if tp["q"] == q), key="phd_topic")
        pq = c2.text_input(t("search"), key="q_phd", placeholder="LSTM, fuzzy, robo-advisor, SHAP...")
        render_papers(db.phd_papers(con, topic=sel, search=pq or None, limit=40) if db.get_meta(con, "phd_refreshed") else [],
                      "phd", show_topics=True)
    elif view_p == "p_map":
        cells = research.gap_cells(con)
        st.caption("Broj radova u poslednje 2 godine za svaku kombinaciju metode i problema (naslov i abstract, OpenAlex). "
                   "Tamnije polje = manje radova. Praznine su kombinacije koje su mnogo ređe nego što bi se očekivalo po veličini oba polja."
                   if ui == "sr" else "Papers in the last 2 years for each method x problem (title & abstract, OpenAlex). "
                   "Gaps are combinations far rarer than the size of both fields would predict.")
        if not cells:
            st.info(t("p_empty"))
        else:
            ideas = insights.gap_ideas(cells, ui)
            gap_keys = {(i["method"], i["problem"]) for i in ideas}
            mx = max(cells.values()) or 1
            import math as _m
            head = "".join(f'<th>{h(pp[0 if ui == "sr" else 1])}</th>' for pp in insights.GAP_PROBLEMS)
            body = ""
            for mi, mm in enumerate(insights.GAP_METHODS):
                ml = mm[0 if ui == "sr" else 1]
                tds = ""
                for pi, pp in enumerate(insights.GAP_PROBLEMS):
                    c = cells.get((mi, pi), 0)
                    a = 0.08 + 0.85 * (_m.log1p(c) / _m.log1p(mx))
                    g = (ml, pp[0 if ui == "sr" else 1]) in gap_keys
                    tds += f'<td class="{"gap" if g else ""}" style="--a:{a:.2f}">{c:,}</td>'.replace(",", ".")
                body += f"<tr><th>{h(ml)}</th>{tds}</tr>"
            st.markdown(f'<div class="fn-heat"><table><tr><th></th>{head}</tr>{body}</table></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="fn-section">{"Neistražene kombinacije - kandidati za doprinos" if ui == "sr" else "Under-researched combinations"}</div>',
                        unsafe_allow_html=True)
            for i_ in ideas:
                q_ = urllib.parse.quote_plus(i_["query"].replace('"', ""))
                with st.container(border=True, key=f"card_gap_{abs(hash(i_['method'] + i_['problem'])) % 10**8}"):
                    st.markdown(f'<div class="fn-meta"><span class="fn-badge">{"praznina" if ui == "sr" else "gap"}</span>'
                                f'<span class="fn-cite">{i_["count"]} {"radova" if ui == "sr" else "papers"} · '
                                f'{"očekivano" if ui == "sr" else "expected"} ~{i_["expected"]:.0f}</span></div>'
                                f'<div class="fn-title">{h(i_["method"])} × {h(i_["problem"])}</div>'
                                f'<p class="fn-sum">' + (f'Kombinacija je oko {1 / max(i_["ratio"], 0.01):.0f}x ređa nego što bi se očekivalo. '
                                f'Proveri postojeće radove i da li je praznina stvarna ili su metode nespojive.' if ui == "sr" else
                                f'About {1 / max(i_["ratio"], 0.01):.0f}x rarer than expected. Check existing work and whether the gap is real.')
                                + f' <a class="fn-gap-src" href="https://scholar.google.com/scholar?q={q_}&as_ylo={date.today().year - 2}" target="_blank">Google Scholar ↗</a></p>',
                                unsafe_allow_html=True)
    elif view_p == "p_saved":
        render_papers(db.phd_papers(con, saved_only=True, limit=200) or
                      [dict(r) for r in con.execute("SELECT * FROM papers WHERE id IN (SELECT paper_id FROM paper_tags WHERE tag='phd_saved')")],
                      "phds")
    else:
        st.caption(t("p_gaps_help"))
        rows = con.execute("SELECT a.item_id, a.text, p.title, p.link, p.venue FROM articles a JOIN papers p ON p.id = a.item_id "
                           "WHERE a.status = 'concl' ORDER BY a.fetched_at DESC LIMIT 80").fetchall()
        gaps = []
        for r in rows:
            for sent in reader.future_sentences(r["text"]):
                gaps.append((sent, r["title"], r["link"], r["venue"]))
        if gaps:
            shown = gaps[:40]
            if lang == "sr":
                trg = translated_full({"id": "gaps_" + str(abs(hash("".join(g[0] for g in shown))) % 10**10)},
                                      "\n".join(g[0] for g in shown), "sr").split("\n")
                if len(trg) == len(shown):
                    shown = [(trg[i], *shown[i][1:]) for i in range(len(shown))]
            st.markdown("".join(f'<div class="fn-why">{h(g[0])}<br><a href="{h(g[2])}" target="_blank" class="fn-gap-src">'
                                f'{h(g[1][:110])} · {h(g[3] or "")}</a></div>' for g in shown), unsafe_allow_html=True)
        st.markdown(f'<div class="fn-section">{t("p_ideas")[2:]}</div>', unsafe_allow_html=True)
        if not ai_on:
            st.info(t("p_ideas_need"))
        else:
            key_i = f"PHD-{date.today().isoformat()}"
            existing = db.get_brief(con, key_i, ui)
            if st.button(t("p_ideas") if not existing else t("remake"), type="primary"):
                top_p = db.phd_papers(con, limit=30)
                saved_p = db.phd_papers(con, saved_only=True, limit=20)
                ids = {x["id"] for x in top_p}
                with st.spinner(t("writing")):
                    content = ai.phd_ideas(research.thesis_text(), top_p + [x for x in saved_p if x["id"] not in ids],
                                           [g[0] for g in gaps], ui)
                db.save_brief(con, key_i, ui, content, utc_iso(datetime.now(timezone.utc)))
                existing = db.get_brief(con, key_i, ui)
            if existing:
                st.caption(f"{t('made')}: {fmt_time(existing['created_at'])}")
                with st.container(key="briefmd_phd"):
                    st.markdown(existing["content"].replace("$", "\\$"))
                st.download_button(t("dl_md"), existing["content"], file_name=f"teme_doktorat_{date.today()}.md")

if page == "t_arch":
    c1, c2, c3 = st.columns([2, 2, 2])
    rng = c1.date_input(t("range"), value=(date.today() - timedelta(days=7), date.today()),
                        max_value=date.today(), format="DD.MM.YYYY")
    acats = c2.multiselect(t("cats"), NEWS_CATS + [RESEARCH], key="arch_cats", placeholder=t("all"), format_func=cat_label)
    order = c3.radio(t("sort"), ["by_imp", "by_date"], format_func=t, horizontal=True)
    aq = st.text_input(t("search"), key="q_arch")
    if isinstance(rng, (tuple, list)):
        d1, d2 = (rng[0], rng[1]) if len(rng) == 2 else (rng[0], rng[0])
    else:
        d1 = d2 = rng
    a_start, a_end = day_bounds(d1, d2)
    items = db.query_items(con, a_start, a_end, categories=acats or None, search=aq or None,
                           order="score" if order == "by_imp" else "date", limit=1000)
    st.caption(f"{t('found')}: {len(items)}")
    if items:
        df = pd.DataFrame(items)[["published", "source", "category", "title", "link", "score"]]
        st.download_button(t("csv"), df.to_csv(index=False).encode("utf-8"), file_name="finnews_arhiva.csv")
    render_items(items[:60], "arch")

# ---------- Sačuvano ----------
if page == "t_saved":
    render_items(db.query_items(con, starred_only=True, order="date", limit=300), "saved")

# ---------- Podešavanja ----------

if page == "t_set":
    cfg = ai.load_config()
    _orig_new = st.toggle("Prikazuj vesti na originalnom jeziku (bez prevoda)" if ui == "sr" else "Show stories in their original language (no translation)",
                          value=bool(cfg.get("show_original")), key="orig_set")
    if _orig_new != bool(cfg.get("show_original")):
        cfg["show_original"] = _orig_new
        ai.save_config(cfg)
        st.rerun()
    st.markdown(f'<div class="fn-section">{"Lokalni AI (besplatno, bez ključa)" if ui == "sr" else "Local AI (free, no key)"}</div>',
                unsafe_allow_html=True)
    olm = st.selectbox("Model", ["gemma3:12b", "gemma3:4b", "qwen3:8b", "llama3.1:8b"],
                       index=["gemma3:12b", "gemma3:4b", "qwen3:8b", "llama3.1:8b"].index(cfg.get("ollama_model", "gemma3:12b"))
                       if cfg.get("ollama_model", "gemma3:12b") in ["gemma3:12b", "gemma3:4b", "qwen3:8b", "llama3.1:8b"] else 0,
                       help="gemma3:12b - najbolji kvalitet (treba 16 GB RAM); gemma3:4b - brži, za 8 GB RAM")
    st.caption(("✅ Aktivan: " + ai_name) if ai_on else
               ("Nije aktivan. Instaliraj ga jednom u Terminalu: bash ~/finnews/setup_local_ai.sh" if ui == "sr" else
                "Not active. Install once in Terminal: bash ~/finnews/setup_local_ai.sh"))
    with st.expander("Napredno" if ui == "sr" else "Advanced"):
        key = st.text_input(t("api") + (" - opciono" if ui == "sr" else " - optional"), value=cfg.get("anthropic_api_key", ""), type="password")
        oa = st.text_input(t("oa_key"), value=cfg.get("openalex_api_key", ""), type="password")
    scr = st.radio(t("script"), ["latinica", "ćirilica"], horizontal=True,
                   index=0 if cfg.get("sr_script", "latinica") == "latinica" else 1)
    auto_read = st.checkbox(t("auto_read"), value=cfg.get("auto_read", True))
    tps = st.text_area(t("topics"), value="\n".join(research.topics()), height=220)
    thesis_in = st.text_area(t("p_thesis"), value=research.thesis_text(), height=160)
    phd_in = st.text_area(t("p_topics_set"), value="\n".join(f'{tp["q"]} | {tp["sr"]}' for tp in research.phd_topics()), height=240)
    if st.button(t("save")):
        cfg.update({"anthropic_api_key": key.strip(), "openalex_api_key": oa.strip(), "sr_script": scr, "ollama_model": olm,
                    "research_topics": [x.strip() for x in tps.splitlines() if x.strip()], "auto_read": auto_read,
                    "thesis_text": thesis_in.strip(),
                    "phd_topics": [{"q": ln.split("|")[0].strip(), "sr": (ln.split("|")[1] if "|" in ln else ln).strip(),
                                    "en": (ln.split("|")[1] if "|" in ln else ln).strip()}
                                   for ln in phd_in.splitlines() if ln.strip()]})
        ai.save_config(cfg)
        st.success(t("saved"))
        st.rerun()

    st.markdown(f'<div class="fn-section">{"Deljenje i telefon" if ui == "sr" else "Sharing and phone"}</div>', unsafe_allow_html=True)
    st.caption(("Kada aplikaciju podeliš preko linka (bash ~/finnews/share.sh), svi vide vesti, akcije i istraživanja, a Portfolio i "
                "Podešavanja se otvaraju samo uz ovaj PIN. " + ("PIN je postavljen." if cfg.get("pin_hash") else "PIN još nije postavljen - dok ga ne postaviš, ti delovi su preko linka zaključani za sve."))
               if ui == "sr" else
               ("When you share the app by link (bash ~/finnews/share.sh), everyone sees news, stocks and research, while Portfolio and "
                "Settings open only with this PIN. " + ("A PIN is set." if cfg.get("pin_hash") else "No PIN yet - until you set one, those sections stay locked for everyone on the link.")))
    pc1, pc2 = st.columns([1, 3], vertical_alignment="bottom")
    new_pin = pc1.text_input("Novi PIN (najmanje 4 znaka)" if ui == "sr" else "New PIN (min. 4 characters)", type="password", key="new_pin")
    if pc2.button("🔒 " + ("Sačuvaj PIN" if ui == "sr" else "Save PIN"), key="pin_save"):
        if len(new_pin.strip()) < 4:
            st.error("PIN mora imati najmanje 4 znaka." if ui == "sr" else "The PIN needs at least 4 characters.")
        else:
            cfg["pin_hash"] = _pin_hash(new_pin)
            ai.save_config(cfg)
            st.success(t("saved"))
    import cloud_sync
    _L = (lambda a, b: a if ui == "sr" else b)
    st.markdown(f'<div class="fn-section">{_L("Telefon bez Mac-a (stalni link)", "Phone without the Mac (permanent link)")}</div>', unsafe_allow_html=True)
    if cloud_sync.enabled():
        _se = db.get_meta(con, "sync_error")
        st.markdown(f'<div class="fn-note">✅ {_L("Sinhronizacija portfolija je uključena", "Portfolio sync is on")}: '
                    f'<b>{h(cloud_sync.settings()[1])}</b> · {_L("poslednja izmena", "last change")} {fmt_time(db.get_meta(con, "portfolio_changed") or "")}'
                    + (f'<br><span class="fn-down">{h(_se)}</span>' if _se else "") + "</div>", unsafe_allow_html=True)
        if st.button("🔄 " + _L("Sinhronizuj sada", "Sync now"), key="sync_now"):
            try:
                st.success(cloud_sync.pull(con))
                db.set_meta(con, "sync_error", "")
            except Exception as ex:  # noqa: BLE001
                st.error(str(ex))
    st.markdown(_L("Jednom pokreni u Terminalu - dobićeš stalni link koji radi i kad je Mac ugašen, a portfolio se sinhronizuje sam:",
                   "Run once in Terminal - you get a permanent link that works even when the Mac is off, and the portfolio syncs itself:"))
    st.code("bash ~/finnews/deploy_cloud.sh", language="bash")
    st.markdown(_L("Privremeni link (radi dok je Mac uključen):", "Temporary link (works while the Mac is on):"))
    st.code("bash ~/finnews/share.sh", language="bash")
    st.markdown(f'<div class="fn-section">{_L("Portfolio u menu baru (SwiftBar)", "Portfolio in the menu bar (SwiftBar)")}</div>', unsafe_allow_html=True)
    st.code("bash ~/finnews/swiftbar.sh", language="bash")
    st.markdown(f'<div class="fn-section">{_L("Prevod", "Translation")}</div>', unsafe_allow_html=True)
    if st.button("🌐 " + _L("Proveri da li prevod radi", "Check that translation works"), key="tr_check"):
        with st.spinner("..."):
            ok_, out_ = ai.translate_check(ui if ui == "sr" else "sr")
        (st.success if ok_ else st.error)((_L("Radi: ", "Works: ") if ok_ else _L("Ne radi trenutno: ", "Not working right now: ")) + str(out_))
        if ok_:
            con.execute("DELETE FROM translations WHERE item_id IN (SELECT t.item_id FROM translations t JOIN items i ON i.id = t.item_id WHERE t.title = i.title)")
            con.commit()
    st.markdown(f'<div class="fn-section">{"Lista praćenja akcija" if ui == "sr" else "Stock watchlist"}</div>', unsafe_allow_html=True)
    wl_txt = st.text_area(("Jedna akcija po redu: TICKER | naziv (oznake kao na Yahoo Finance, npr. AAPL, SAP, MC.PA, NESN.SW)"
                           if ui == "sr" else "One stock per line: TICKER | name (Yahoo Finance symbols, e.g. AAPL, SAP, MC.PA)"),
                          value="\n".join(f"{t_} | {n_}" for t_, n_ in stocks.watchlist()), height=220, key="wl_txt")
    if st.button("💾 " + ("Sačuvaj listu akcija" if ui == "sr" else "Save watchlist"), key="wl_save"):
        stocks.save_watchlist(wl_txt)
        st.success(t("saved") + (" Klikni „Osveži akcije“ u tabu Akcije." if ui == "sr" else " Click 'Refresh stocks' in Stocks."))
    st.subheader(t("sources"))
    st.caption(t("feeds_help"))
    feeds = fetcher.load_feeds()
    fdf = pd.DataFrame(feeds)
    for col in ["name", "url", "category", "weight", "lang", "enabled"]:
        if col not in fdf:
            fdf[col] = None
    _L = (lambda a, b: a if ui == "sr" else b)
    edited = st.data_editor(fdf[["enabled", "name", "category", "weight", "lang", "url"]], num_rows="dynamic",
                            key="feeds_editor", column_config={
                                "enabled": st.column_config.CheckboxColumn(_L("Uključen", "On")),
                                "name": _L("Naziv", "Name"), "category": _L("Kategorija", "Category"),
                                "weight": st.column_config.NumberColumn(_L("Težina", "Weight"), min_value=0.1, max_value=3.0, step=0.1),
                                "lang": _L("Jezik", "Lang"), "url": "RSS URL"})
    if st.button(t("save_feeds")):
        old = {f["name"]: f for f in feeds}
        out = []
        for row in edited.to_dict("records"):
            if not row.get("name") or not row.get("url"):
                continue
            f = dict(old.get(row["name"], {}))
            f.update({k: row[k] for k in ["enabled", "name", "category", "weight", "lang", "url"]})
            f["enabled"] = bool(f.get("enabled", True))
            f["weight"] = float(f.get("weight") or 1.0)
            f["category"] = f.get("category") or "Vesti"
            f["lang"] = f.get("lang") or "en"
            out.append(f)
        fetcher.save_feeds(out)
        st.success(t("saved"))
    st.subheader(t("status"))
    log = db.fetch_log(con)
    if log:
        st.dataframe(pd.DataFrame(log), hide_index=True, column_config={
            "source": _L("Izvor", "Source"), "last_ok": _L("Poslednji uspeh", "Last success"),
            "last_error": _L("Poslednja greška", "Last error"), "last_count": _L("Broj stavki", "Items")})
