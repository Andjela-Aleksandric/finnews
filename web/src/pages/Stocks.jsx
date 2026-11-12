import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, BookOpen, Compass, Flame, Info, LineChart, Search, Sparkles } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
import { big, cls, num, pct, srcColor, upDown } from "../lib/fmt";
import { getMeta, series, useData, useNews } from "../lib/data";
import { periodOpts } from "../lib/sections";
import { PageHead, useRoute } from "../components/Shell";
import { NewsCard } from "../components/News";
import { Badge, Card, Chip, Empty, Segmented, SectionTitle, Skeleton, Tabs } from "../components/ui";
import { TabPanel } from "../components/ui";
import { Brief, Checklist, Listings, OppCard, StockCard, ThemeCard, TierBadge, WhyRisk, secName } from "../components/Stocks";
import PriceChart from "../components/PriceChart";

export function changeOver(prices, t, days) {
  const s = series(prices, t);
  if (s.length < 2) return null;
  const cut = new Date(Date.now() - days * 864e5).toISOString().slice(0, 10);
  const base = (s.find((x) => x.time >= cut) || s[0]).value;
  return base ? s[s.length - 1].value / base - 1 : null;
}

export function MarketsPanel({ prices, stocks, days }) {
  const { lang } = useLang();
  const t = useT();
  const { go } = useRoute();
  const meta = getMeta();
  const list = (meta && meta.market_list) || [];
  const nameEn = { "Zlato $": "Gold $", "US 10g %": "US 10y %" };
  const movers = (stocks || []).map((s) => ({ s, ch: changeOver(prices, s.ticker, days) })).filter((x) => x.ch !== null).sort((a, b) => b.ch - a.ch);
  return (
    <div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
        {list.map(([tk, n, dec], i) => {
          const s = series(prices, tk);
          if (!s.length) return null;
          const ch = changeOver(prices, tk, days);
          const v = s[s.length - 1].value / (tk === "^TNX" && s[s.length - 1].value > 20 ? 10 : 1);
          const cut = new Date(Date.now() - days * 864e5).toISOString().slice(0, 10);
          return (
            <Card key={tk} delay={i * 0.03} className="p-3.5">
              <div className="stat-label">{lang === "en" ? nameEn[n] || n : n}</div>
              <div className="mt-1 font-mono text-lg text-cream-50">{num(v, dec, lang)}</div>
              <div className={cls("font-mono text-xs", upDown(ch))}>{pct(ch, 1, lang)}</div>
              <div className="mt-2"><SparkLite data={s.filter((x) => x.time >= cut)} /></div>
            </Card>
          );
        })}
      </div>
      <div className="mt-8 grid gap-6 md:grid-cols-2">
        {[[t("gainers"), movers.slice(0, 7)], [t("losers"), movers.slice(-7).reverse()]].map(([title, rows]) => (
          <div key={title}>
            <SectionTitle>{title}</SectionTitle>
            <div className="space-y-1">
              {rows.map(({ s, ch }, i) => (
                <motion.button key={s.ticker} initial={{ opacity: 0, x: -6 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.03 }}
                  onClick={() => go("/akcije/" + encodeURIComponent(s.ticker))}
                  className="group grid w-full grid-cols-[1fr_110px_64px] items-center gap-3 rounded-xl px-3 py-2.5 text-left transition hover:bg-ink-750">
                  <span className="truncate text-sm text-cream-100 group-hover:text-white">{s.name} <span className="font-mono text-[11px] text-cream-500">{s.ticker}</span></span>
                  <span className="h-1.5 overflow-hidden rounded-full bg-ink-700">
                    <motion.i initial={{ width: 0 }} whileInView={{ width: `${Math.min(100, Math.abs(ch) * 250)}%` }} viewport={{ once: true }} transition={{ duration: 0.8 }}
                      className={cls("block h-full rounded-full", ch >= 0 ? "bg-up" : "bg-down")} />
                  </span>
                  <span className={cls("text-right font-mono text-sm", upDown(ch))}>{pct(ch, 1, lang)}</span>
                </motion.button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
function SparkLite({ data }) {
  const vals = data.map((d) => d.value);
  if (vals.length < 2) return null;
  const lo = Math.min(...vals), hi = Math.max(...vals), rg = hi - lo || 1;
  const d = "M" + vals.map((v, i) => `${(i * 100) / (vals.length - 1)},${28 - ((v - lo) / rg) * 26}`).join(" L");
  return <svg viewBox="0 0 100 30" preserveAspectRatio="none" className="h-8 w-full"><path d={d} fill="none" stroke={vals[vals.length - 1] >= vals[0] ? "#7FDB97" : "#FF7A90"} strokeWidth="1.6" vectorEffect="non-scaling-stroke" /></svg>;
}

function Detail({ tk, data, prices }) {
  const { lang } = useLang();
  const t = useT();
  const { go, route } = useRoute();
  const [rng, setRng] = useState(183);
  const [mkt, setMkt] = useState("home");
  const { items } = useNews(30);
  const s = (data.stocks || []).find((x) => x.ticker === tk);
  if (!s) {
    const history = series(prices, tk);
    const last = history.length ? history[history.length - 1].value : null;
    const name = route.q.name || tk;
    const isin = route.q.isin || "";
    const short = lang === "en"
      ? `${name} is recorded in your portfolio under ticker ${tk}. A full company profile is not available in the tracked stock data yet.`
      : `${name} je evidentirana u tvom portfoliju pod tickerom ${tk}. Detaljan profil kompanije trenutno nije dostupan u podacima za ovu hartiju.`;
    return (
      <div>
        <button onClick={() => go("/portfolio")} className="btn-ghost -ml-3 mb-3"><ArrowLeft size={15} />{lang === "en" ? "Back to portfolio" : "Nazad u portfolio"}</button>
        <div className="mb-5">
          <div className="font-mono text-sm text-cream-400">{tk}{isin ? ` · ISIN ${isin}` : ""}</div>
          <h1 className="mt-2 font-display text-[2rem] font-bold text-cream-50 md:text-[2.6rem]">{name}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-cream-300">{short}</p>
        </div>
        {history.length ? (
          <Card hover={false} className="p-4 md:p-5">
            <div className="mb-2 font-semibold text-cream-100">{lang === "en" ? "Available price history" : "Dostupna istorija cene"}</div>
            <div className="font-mono text-2xl text-cream-50">{num(last, 2, lang)} <span className="text-sm text-cream-400">{tk.endsWith(".DE") ? "EUR" : ""}</span></div>
            <PriceChart data={history} days={183} height={300} valueFormat={(v) => num(v, 2, lang)} />
          </Card>
        ) : <Empty>{lang === "en" ? "No price history is available for this ticker yet. The holding is still saved in your portfolio." : "Za ovaj ticker još nema istorije cena. Pozicija je i dalje sačuvana u portfoliju."}</Empty>}
      </div>
    );
  }
  const xt = s && s.xetra && s.xetra.t !== tk ? s.xetra.t : null;
  const sp = series(prices, mkt === "x" && xt ? xt : tk);
  const news = items.filter((x) => x.tk === tk).slice(0, 6);
  const kpis = [["P/E", s.pe ? num(s.pe, 1, lang) : "-"], ["ROE", pct(s.roe, 0, lang, false)], [lang === "en" ? "Margin" : "Marža", pct(s.margin, 0, lang, false)],
    [lang === "en" ? "Revenue growth" : "Rast prihoda", pct(s.growth, 0, lang)], [lang === "en" ? "Dividend" : "Dividenda", s.div ? num(s.div > 1 ? s.div : s.div * 100, 2, lang) + "%" : "-"],
    [lang === "en" ? "Market cap" : "Tržišna vrednost", big(s.mcap, lang)], [t("target"), pct(s.upside, 0, lang)],
    [lang === "en" ? "Rating" : "Preporuka", s.rec ? num(s.rec, 1, lang) : "-"], [lang === "en" ? "Volatility" : "Volatilnost", pct(s.vol, 0, lang, false)],
    [lang === "en" ? "1 year" : "1 godina", pct(s.r1y, 1, lang)]];
  const factorNames = Object.fromEntries((data.factors || []).map(([k, w, sr, en]) => [k, lang === "en" ? en : sr]));
  return (
    <div>
      <button onClick={() => go("/akcije")} className="btn-ghost -ml-3 mb-3"><ArrowLeft size={15} />{t("back")}</button>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2"><Badge color={srcColor(s.sector || "ETF")}>{secName(s, lang, data.sectors_sr)}</Badge><span className="font-mono text-sm text-cream-400">{s.ticker}</span></div>
          <h1 className="mt-2 font-display text-[2rem] font-bold leading-tight text-cream-50 md:text-[2.6rem]">{s.name}</h1>
          <div className="mt-1 flex items-center gap-2"><TierBadge tier={s.tier} />{s.setup_txt && <span className="text-xs text-cream-400">{s.setup_txt[lang]}</span>}</div>
          <div className="max-w-2xl"><Brief s={s} lines={0} /></div>
        </div>
        <div className="text-right">
          <div className="font-mono text-3xl text-cream-50">{num(s.price, 2, lang)} <span className="text-base text-cream-400">{s.currency}</span></div>
          <div className={cls("font-mono text-sm", upDown(s.r1d))}>{pct(s.r1d, 2, lang)} {lang === "en" ? "today" : "danas"}</div>
        </div>
      </div>
      <div className="mt-4 max-w-2xl"><Listings s={s} /></div>
      <Card hover={false} className="mt-5 p-3 md:p-5">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          {xt ? <Segmented size="sm" value={mkt} onChange={setMkt} options={[["home", s.ticker.includes(".") ? s.ticker : (lang === "en" ? "US · " : "SAD · ") + s.ticker], ["x", "XETRA · " + xt]]} /> : <span />}
          <Segmented size="sm" value={rng} onChange={setRng} options={[[31, "1M"], [92, "3M"], [183, "6M"], [366, lang === "en" ? "1Y" : "1G"], [732, lang === "en" ? "2Y" : "2G"]]} />
        </div>
        <PriceChart data={sp} days={rng} height={340} sma valueFormat={(v) => num(v, 2, lang)} />
        <div className="mt-2 flex gap-4 text-[11px] text-cream-400"><span className="text-gold-500">- - {lang === "en" ? "50-day average" : "prosek 50 dana"}</span><span className="text-copper">- - {lang === "en" ? "200-day average" : "prosek 200 dana"}</span></div>
      </Card>
      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-5">
        {kpis.map(([l, v], i) => (
          <Card key={l} delay={i * 0.03} className="p-3"><div className="stat-label">{l}</div><div className="mt-1 font-mono text-[15px] text-cream-50">{v}</div></Card>
        ))}
      </div>
      {s.check && <Card hover={false} className="mt-6 p-5"><Checklist items={s.check} /></Card>}
      <WhyRisk s={s} />
      {s.tier && data.tier_size && (
        <div className="mt-3 rounded-xl border border-ink-600 bg-ink-850/60 p-3.5 text-sm text-cream-300">
          <span className="kicker mr-2">{lang === "en" ? "Position size" : "Veličina pozicije"}</span>{data.tier_size[s.tier][lang === "en" ? 1 : 0]}
        </div>
      )}
      {s.parts && (
        <div className="mt-8 grid gap-8 md:grid-cols-2">
          <div>
            <SectionTitle>{lang === "en" ? "Factor profile" : "Faktorski profil"}</SectionTitle>
            <div className="space-y-2.5">
              {Object.entries(s.parts).map(([k, v], i) => (
                <div key={k} className="grid grid-cols-[1fr_120px_40px] items-center gap-3 text-sm">
                  <span className="text-cream-300">{factorNames[k] || k}</span>
                  <span className="h-2 overflow-hidden rounded-full bg-ink-700">
                    <motion.i initial={{ width: 0 }} whileInView={{ width: `${v * 100}%` }} viewport={{ once: true }} transition={{ duration: 0.8, delay: i * 0.05 }}
                      className="block h-full rounded-full bg-gradient-to-r from-wine-600 to-gold-500" />
                  </span>
                  <span className="text-right font-mono text-xs text-cream-400">{Math.round(v * 100)}</span>
                </div>
              ))}
            </div>
            {s.why && <div className="mt-4 flex flex-wrap gap-1.5">{(s.why[lang] || []).map((w) => <span key={w} className="rounded-full border border-ink-500 px-2.5 py-1 text-xs text-cream-300">{w}</span>)}</div>}
          </div>
          {s.about && (
            <div>
              <SectionTitle>{t("aboutCompany")}</SectionTitle>
              <p className="text-sm leading-relaxed text-cream-300">{s.about}</p>
            </div>
          )}
        </div>
      )}
      <div className="mt-8">
        <SectionTitle>{t("latestNews")}</SectionTitle>
        {news.length ? <div className="grid gap-4 md:grid-cols-2">{news.map((n, i) => <NewsCard key={n.id} it={n} i={i} />)}</div>
          : <Empty>{lang === "en" ? "No news for this company in the last 30 days." : "Nema vesti o ovoj kompaniji u poslednjih 30 dana."}</Empty>}
      </div>
    </div>
  );
}

export default function StocksPage() {
  const { lang } = useLang();
  const t = useT();
  const { route, setQuery } = useRoute();
  const { data: [data, prices], loading } = useData(["stocks.json", "prices_all.json"]);
  const [themeF, setThemeF] = useState(null);
  const [tierF, setTierF] = useState(null);
  const [how, setHow] = useState(false);
  const tab = route.q.tab || "opp";
  const [q, setQ] = useState("");
  const [secs, setSecs] = useState([]);
  const [sort, setSort] = useState("opp");
  const [fallen, setFallen] = useState(false);
  const [noEtf, setNoEtf] = useState(true);
  const [show, setShow] = useState(12);
  const [days, setDays] = useState(30);
  const list = (data && data.stocks) || [];
  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    let r = list.filter((x) => (!noEtf || !x.etf) && (!secs.length || secs.includes(x.sector)) && (!themeF || x.theme === themeF) && (!tierF || x.tier === tierF) && (!fallen || (x.dd !== undefined && x.dd <= -0.08)) &&
      (!s || `${x.name} ${x.ticker} ${x.sector} ${x.sector_sr}`.toLowerCase().includes(s)));
    const k = { opp: (x) => -(x.opp ?? -1), score: (x) => -(x.score ?? -1), dd: (x) => x.dd ?? 0, up: (x) => -(x.upside ?? -9), r1y: (x) => -(x.r1y ?? -9), r1d: (x) => -(x.r1d ?? -9), div: (x) => -(x.div ?? 0) }[sort];
    return [...r].sort((a, b) => k(a) - k(b));
  }, [list, q, secs, sort, fallen, noEtf, themeF, tierF]);
  if (route.parts[1]) return data && prices ? <Detail tk={decodeURIComponent(route.parts[1])} data={data} prices={prices} /> : <Skeleton className="h-[500px]" />;
  const smap = Object.fromEntries(list.map((x) => [x.ticker, x]));
  const opps = ((data && (data.top25 || data.top20)) || []).map((t) => smap[t]).filter(Boolean);
  const sectors = [...new Set(list.filter((x) => x.sector).map((x) => x.sector))].sort();
  const tw = (data && data.tailwind) || {};
  const good = Object.entries(tw).filter(([, v]) => v > 0.1).sort((a, b) => b[1] - a[1]).slice(0, 3);
  const bad = Object.entries(tw).filter(([, v]) => v < -0.1).sort((a, b) => a[1] - b[1]).slice(0, 2);
  const sn = (k) => (lang === "sr" ? (data.sectors_sr || {})[k] || k : k);
  return (
    <div>
      <PageHead title={t("stocks")} sub={lang === "en" ? "Opportunities, every stock on your list with charts, and the themes moving the market." : "Prilike, sve akcije sa tvoje liste sa grafikonima i teme koje pokreću tržište."} />
      <Tabs value={tab} onChange={(v) => setQuery({ tab: v })} options={[["opp", t("oppNow"), <Sparkles size={15} key="i" />], ["all", t("explore"), <Compass size={15} key="i" />],
        ["markets", t("markets"), <LineChart size={15} key="i" />], ["themes", t("themes"), <Flame size={15} key="i" />]]} />
      <TabPanel k={tab}>
      {loading ? <Skeleton className="h-96" /> : !data ? <Empty>{lang === "en" ? "Stock data could not be loaded. Check your connection and try again." : "Podaci o akcijama nisu učitani. Proveri vezu i pokušaj ponovo."}<button className="btn mt-3" onClick={() => window.location.reload()}>{lang === "en" ? "Retry" : "Pokušaj ponovo"}</button></Empty> : tab === "opp" ? (
        <div>
          <div className="mb-6 flex items-start gap-3 rounded-2xl border border-gold-500/25 bg-gold-500/5 p-4 text-sm text-cream-300"><Info size={17} className="mt-0.5 shrink-0 text-gold-500" />{t("disclaimer")}</div>
          {(good.length > 0 || opps.length > 0) && (
            <Card hover={false} className="mb-8 p-5">
              <div className="kicker mb-3">{lang === "en" ? "Where it makes sense to look now" : "Gde ima smisla gledati sada"}</div>
              <ul className="space-y-2 text-[15px] text-cream-200">
                {good.length > 0 && <li>🟢 {lang === "en" ? "Sectors with a tailwind from the news: " : "Sektori sa vetrom u leđa iz vesti: "}<b className="text-cream-50">{good.map(([k]) => sn(k)).join(", ")}</b></li>}
                {bad.length > 0 && <li>🟠 {lang === "en" ? "Be careful with: " : "Oprez kod: "}{bad.map(([k]) => sn(k)).join(", ")}</li>}
                {opps.length > 0 && <li>💡 {lang === "en" ? "Most interesting for further research: " : "Najzanimljivije za dalju analizu: "}<b className="text-cream-50">{opps.slice(0, 3).map((o) => o.name).join(", ")}</b></li>}
              </ul>
            </Card>
          )}
          <Card hover={false} className="mb-6 p-5">
            <button onClick={() => setHow((x) => !x)} className="flex w-full items-center justify-between text-left">
              <span className="flex items-center gap-2 font-display text-lg font-semibold"><BookOpen size={18} className="text-gold-500" />{lang === "en" ? "How up to 25 ideas are ranked" : "Kako rangiramo do 25 predloga"}</span>
              <span className="text-cream-400">{how ? "▲" : "▼"}</span>
            </button>
            {how && (
              <motion.ul initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-4 space-y-2 text-sm text-cream-300">
                {(lang === "en" ? [
                  "Quality at a discount: profitable, growing companies that are at least 8% below their 52-week high, where analysts see upside.",
                  "Trend first: the 200-day average shows direction. A pullback inside an uptrend is preferred; a stock that keeps falling below its 200-day average (a 'falling knife') is ranked lower.",
                  "Entry timing: RSI 30-50 and turning up is the entry zone; above 70 means overheated - don't chase.",
                  "Growth, valuation and quality: revenue growth, margins, ROE, debt, forward P/E and PEG, plus free-cash-flow yield when Yahoo Finance supplies it. P/S is shown as context because it needs peer comparison.",
                  "Tailwinds: sectors helped by what the news is talking about now (AI, power, defence, rates...), plus the tone of company news.",
                  "Position size by risk tier: blue chip up to ~10%, growth 1-5%, speculative under 1% - and buy in parts (DCA), keeping 5-15% in cash. Metrics such as insider/13F activity, MACD and Bollinger Bands are not available in this app's current data feed, so they are not scored.",
                ] : [
                  "Kvalitet na popustu: profitabilne kompanije koje rastu, bar 8% ispod 52-nedeljnog maksimuma, gde analitičari vide rast.",
                  "Prvo trend: 200-dnevni prosek pokazuje pravac. Prednost ima povlačenje u rastućem trendu; akcija koja i dalje pada ispod 200-dnevnog proseka („nož koji pada“) rangira se niže.",
                  "Trenutak ulaza: RSI 30-50 koji se okreće naviše je zona za ulaz; iznad 70 je pregrejano - ne juriti.",
                  "Rast, vrednovanje i kvalitet: rast prihoda, marže, ROE, dug, forward P/E i PEG, kao i prinos slobodnog novčanog toka kada ga Yahoo Finance dostavi. P/S se prikazuje kao kontekst jer ga treba porediti sa sličnim kompanijama.",
                  "Vetar u leđa: sektori kojima pomažu teme iz aktuelnih vesti (AI, struja, odbrana, kamate...), i ton vesti o samoj kompaniji.",
                  "Veličina pozicije po nivou rizika: blue chip do ~10%, rast 1-5%, spekulativno ispod 1% - kupuj u delovima (DCA) i drži 5-15% u gotovini. Podaci poput insajderskih/13F transakcija, MACD-a i Bollingerovih opsega nisu dostupni u trenutnom izvoru aplikacije i zato ne ulaze u skor.",
                ]).map((x, i) => <li key={i} className="flex gap-2.5"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rotate-45 bg-gradient-to-br from-wine-500 to-gold-500" />{x}</li>)}
              </motion.ul>
            )}
          </Card>
          <div className="space-y-5">{opps.length ? opps.map((s, i) => <OppCard key={s.ticker} s={s} prices={prices} i={i} sectors={data.sectors_sr} tierSize={data.tier_size} />)
            : <Empty>{lang === "en" ? "No candidates have enough recent price history yet." : "Trenutno nema dovoljno istorijskih cena za rangiranje predloga."}</Empty>}</div>
        </div>
      ) : tab === "all" ? (
        <div>
          <div className="mb-3 flex flex-wrap gap-2">
            <div className="relative min-w-[220px] flex-1">
              <Search size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-cream-500" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={lang === "en" ? "Name, symbol or sector" : "Naziv, simbol ili sektor"} className="field pl-10" />
            </div>
            <select value={sort} onChange={(e) => setSort(e.target.value)} className="field w-auto">
              {[["opp", lang === "en" ? "Best opportunity" : "Najbolja prilika"], ["score", lang === "en" ? "Factor score" : "Faktorski skor"], ["dd", lang === "en" ? "Biggest drop" : "Najveći pad od maksimuma"],
                ["up", lang === "en" ? "Analyst upside" : "Najveći cilj analitičara"], ["r1y", lang === "en" ? "Best 1 year" : "Najveći rast za godinu"], ["r1d", lang === "en" ? "Best today" : "Najveći rast danas"],
                ["div", lang === "en" ? "Highest dividend" : "Najveća dividenda"]].map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select>
          </div>
          <div className="no-scrollbar mb-5 flex gap-1.5 overflow-x-auto pb-1">
            <Chip active={fallen} onClick={() => setFallen((x) => !x)}>{t("onlyFallen")}</Chip>
            <Chip active={noEtf} onClick={() => setNoEtf((x) => !x)}>{t("noEtf")}</Chip>
            <span className="mx-1 w-px shrink-0 bg-ink-600" />
            {sectors.map((s) => <Chip key={s} active={secs.includes(s)} onClick={() => setSecs((x) => (x.includes(s) ? x.filter((y) => y !== s) : [...x, s]))}>{sn(s)}</Chip>)}
          </div>
          <div className="no-scrollbar mb-2 flex gap-1.5 overflow-x-auto pb-1">
            <Chip active={!themeF} onClick={() => setThemeF(null)}>{lang === "en" ? "All themes" : "Sve teme"}</Chip>
            {Object.entries(data.theme_names || {}).filter(([k]) => list.some((x) => x.theme === k)).map(([k, v]) => <Chip key={k} active={themeF === k} onClick={() => setThemeF(themeF === k ? null : k)}>{v[lang === "en" ? 1 : 0]}</Chip>)}
          </div>
          <div className="no-scrollbar mb-5 flex gap-1.5 overflow-x-auto pb-1">
            {Object.entries(data.tiers || {}).map(([k, v]) => <Chip key={k} active={tierF === k} onClick={() => setTierF(tierF === k ? null : k)}>{v[lang === "en" ? 1 : 0]}</Chip>)}
          </div>
          <div className="mb-3 text-xs text-cream-500">{filtered.length} {lang === "en" ? "stocks" : "akcija"}</div>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{filtered.slice(0, show).map((s, i) => <StockCard key={s.ticker} s={s} i={i} sectors={data.sectors_sr} />)}</div>
          {filtered.length > show && <div className="mt-6 text-center"><button className="btn" onClick={() => setShow((x) => x + 12)}>{t("loadMore")}</button></div>}
        </div>
      ) : tab === "markets" ? (
        <div>
          <div className="mb-5"><Segmented size="sm" value={days} onChange={setDays} options={periodOpts(t)} /></div>
          <MarketsPanel prices={prices} stocks={list} days={days} />
        </div>
      ) : (
        <div>
          <p className="mb-5 text-sm text-cream-400">{lang === "en" ? "Last 7 days compared with the previous 4 weeks - and which sectors each theme helps or hurts." : "Poslednjih 7 dana u odnosu na prethodne 4 nedelje - i kojim sektorima svaka tema pomaže ili šteti."}</p>
          <div className="grid gap-4 md:grid-cols-2">{(data.themes || []).map((th, i) => <ThemeCard key={th.sr} th={th} i={i} sectors={data.sectors_sr} />)}</div>
        </div>
      )}
      </TabPanel>
    </div>
  );
}
