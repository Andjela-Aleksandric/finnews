import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, BookOpen, Check, ChevronDown, Compass, Flame, Info, LineChart, Search, Sparkles } from "lucide-react";
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
import CompareChart from "../components/CompareChart";

const CHART_PERIODS = [["1M", "1M"], ["6M", "6M"], ["YTD", "YTD"], ["1Y", "1Y"], ["3Y", "3Y"], ["5Y", "5Y"], ["10Y", "10Y"], ["MAX", "Max"]];

function filterPeriod(data, period, from, to) {
  if (!data || !data.length) return [];
  const end = to || data[data.length - 1].time;
  let start = from || "";
  if (!start && period === "YTD") start = `${new Date().getFullYear()}-01-01`;
  else if (!start && period !== "MAX") {
    const days = ({ "1M": 31, "6M": 183, "1Y": 365, "3Y": 1095, "5Y": 1825, "10Y": 3650 })[period];
    if (days) start = new Date(Date.now() - days * 864e5).toISOString().slice(0, 10);
  }
  return data.filter((p) => (!start || p.time >= start) && (!end || p.time <= end));
}

function groupSeries(data, interval) {
  if (interval === "D") return data;
  const groups = new Map();
  for (const point of data) {
    const d = new Date(`${point.time}T00:00:00Z`);
    let key = point.time;
    if (interval === "M") key = `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}-01`;
    if (interval === "W") {
      d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7));
      key = d.toISOString().slice(0, 10);
    }
    groups.set(key, point.value);
  }
  return [...groups.entries()].map(([time, value]) => ({ time, value })).sort((a, b) => a.time.localeCompare(b.time));
}

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

const FULL_INDICATOR_NAMES = {
  mcap: ["Tržišna kapitalizacija", "Market capitalization"],
  pe: ["Odnos tržišne cene i dobiti u poslednjih 12 meseci", "Price-to-earnings ratio (trailing 12 months)"],
  fpe: ["Odnos cene i očekivane dobiti", "Forward price-to-earnings ratio"],
  peg: ["Odnos P/E i očekivanog rasta dobiti", "Price/earnings-to-growth ratio"],
  ps: ["Odnos tržišne vrednosti i prihoda", "Price-to-sales ratio"],
  roe: ["Prinos na kapital akcionara", "Return on equity"],
  margin: ["Neto profitna marža", "Net profit margin"],
  de: ["Odnos duga i kapitala", "Debt-to-equity ratio"],
  growth: ["Međugodišnja promena prihoda", "Year-over-year revenue growth"],
  div: ["Prinos od dividende", "Dividend yield"],
  beta: ["Beta koeficijent: promenljivost u odnosu na tržište", "Beta: volatility relative to the market"],
  fcf_yield: ["Prinos slobodnog novčanog toka prema tržišnoj vrednosti", "Free cash flow yield"],
  upside: ["Potencijal do prosečne ciljne cene analitičara", "Analyst target-price upside"],
  rec: ["Prosečna ocena analitičara na skali 1-5", "Analyst consensus rating on a 1-5 scale"],
  analysts: ["Broj analitičara u konsenzusu", "Number of analysts in the consensus"],
  r1y: ["Promena cene tokom prethodnih 12 meseci", "Price return over the previous 12 months"],
  vol: ["Istorijska godišnja volatilnost", "Annualized historical volatility"],
  mdd: ["Najveći pad od vrha do dna tokom jedne godine", "Maximum one-year peak-to-trough drawdown"],
  trend: ["Cena u odnosu na 200-dnevni prosek", "Price relative to the 200-day moving average"],
  score: ["FinNews relativni faktorski skor", "FinNews relative factor score"],
  opp: ["FinNews skor prilike", "FinNews opportunity score"],
};
function fullIndicatorName(key, lang) {
  const pair = FULL_INDICATOR_NAMES[key] || ["Finansijski pokazatelj", "Financial indicator"];
  return pair[lang === "en" ? 1 : 0];
}
function indicatorNextStep(key, lang) {
  const actions = {
    mcap: ["Uporedi veličinu i likvidnost sa firmama iz istog sektora.", "Compare size and liquidity with peers in the same sector."],
    pe: ["Uporedi P/E sa sektorom i proveri da li je dobit održiva.", "Compare P/E with the sector and check whether earnings are recurring."],
    fpe: ["Uporedi prognozu sa prethodnim rezultatima i pogledaj broj analitičara.", "Compare forecasts with past results and check analyst coverage."],
    peg: ["Proveri pretpostavku rasta dobiti na kojoj se PEG zasniva.", "Check the earnings-growth forecast behind the PEG."],
    ps: ["Poredi ga sa firmama sličnih marži. P/S sam ne govori da li kompanija posluje profitabilno.", "Compare it with companies that have similar margins. P/S alone does not show whether a company is profitable."],
    roe: ["Pogledaj dug i kapital: visoka zaduženost može podići ROE.", "Check leverage and equity: high debt can inflate ROE."],
    margin: ["Uporedi maržu sa prethodnim godinama i firmama iz iste industrije.", "Compare margins with past years and same-industry peers."],
    de: ["Proveri kamatne troškove, rok duga i sektor kompanije.", "Check interest costs, debt maturities and the company's sector."],
    growth: ["Proveri rast kroz više godina i da li ga prati rast novčanog toka.", "Check multi-year growth and whether cash flow is growing too."],
    div: ["Proveri payout ratio, slobodan novčani tok i istoriju dividende.", "Check payout ratio, free cash flow and dividend history."],
    beta: ["Uskladi rizik oscilacija sa svojim horizontom i tolerancijom na rizik.", "Relate volatility to your time horizon and risk tolerance."],
    fcf_yield: ["Proveri da li je slobodan novčani tok održiv ili privremen.", "Check whether free cash flow is sustainable or temporary."],
    upside: ["Proveri datum ciljne cene, raspon procena i broj analitičara.", "Check target dates, estimate range and analyst count."],
    rec: ["Pogledaj broj analitičara i raspon preporuka, ne samo prosek.", "Check analyst count and rating spread, not only the average."],
    analysts: ["Mali uzorak tretiraj oprezno i uporedi procene sa drugim izvorima.", "Treat a small sample cautiously and compare estimates with other sources."],
    r1y: ["Uporedi isti period sa indeksom i sektorom. Dosadašnji prinos ne govori šta će se desiti.", "Compare the same period with an index and sector. Past returns don't tell you what comes next."],
    vol: ["Uskladi veličinu pozicije sa mogućim oscilacijama cene.", "Size a position with potential price swings in mind."],
    mdd: ["Pogledaj uzrok pada i kako su se poslovni pokazatelji tada menjali.", "Check what drove the drawdown and how the business changed during it."],
    trend: ["Koristi kao proveru trenda uz rezultate i novčani tok.", "Use as a trend check alongside earnings and cash flow."],
    score: ["Otvori faktorski profil da vidiš šta najviše podiže ili spušta skor.", "Open the factor profile to see which inputs drive the score."],
    opp: ["Proveri checklistu, rizike i vesti pre zaključka.", "Review the checklist, risks and news before drawing a conclusion."],
  };
  return (actions[key] || ["Uporedi sa firmama iz iste industrije i proveri izvorni podatak.", "Compare with peers and verify the source data."])[lang === "en" ? 1 : 0];
}

function indicatorGuide(key, s, lang) {
  const L = (sr, en) => lang === "en" ? en : sr;
  const raw = key === "trend" ? (s.price && s.sma200 ? s.price / s.sma200 - 1 : null) : key === "pe" ? s.tpe : s[key];
  const v = Number(raw);
  const missing = raw === null || raw === undefined || !Number.isFinite(v);
  if (missing && key !== "trend") return { grade: L("Nema podatka", "No data"), tone: "na", text: L("Izvor podataka ne daje ovu vrednost za ovu kompaniju. Crtica ne znači nulu.", "The data source does not provide this value for this company. A dash does not mean zero.") };
  if (key === "mcap") return { grade: L("Kontekst", "Context"), tone: "neutral", text: L("Tržišna vrednost svih akcija kompanije. Veća kapitalizacija često znači zreliju i likvidniju kompaniju, ali sama po sebi ne znači da je akcija jeftina ili kvalitetna.", "The market value of all company shares. Larger capitalization often means a more established and liquid company, but it does not by itself mean the stock is cheap or high quality.") };
  if (key === "pe" || key === "fpe") {
    const forward = key === "fpe";
    const grade = v <= 0 ? L("Zarada negativna", "Negative earnings") : v < 15 ? L("Niži multiplikator", "Lower multiple") : v <= 25 ? L("Umeren", "Moderate") : L("Povišen", "Elevated");
    const text = v <= 0
      ? L("Odnos cene i dobiti nije smislen kada su dobiti negativne ili blizu nule. Proveri profitabilnost i očekivanja.", "The price-to-earnings ratio is not meaningful when earnings are negative or near zero. Check profitability and expectations.")
      : L("Pokazuje koliko tržište plaća za jedinicu dobiti " + (forward ? "koja se očekuje u narednom periodu" : "ostvarene u poslednjih 12 meseci") + ". Niže može značiti nižu cenu, ali i slabiji očekivani rast ili veći rizik. Poredi sa firmama iz istog sektora.", "Shows how much the market pays for a unit of " + (forward ? "forecast earnings" : "trailing 12-month earnings") + ". A lower multiple can mean a cheaper price, but also weaker growth expectations or higher risk. Compare with companies in the same sector.");
    return { grade, tone: v <= 0 ? "bad" : v < 15 ? "positive" : v <= 25 ? "neutral" : "caution", text };
  }
  if (key === "peg") return { grade: v <= 0 ? L("Neupotrebljiv", "Not meaningful") : v < 1 ? L("Niži prema rastu", "Low vs. growth") : v <= 2 ? L("Umeren", "Moderate") : L("Povišen", "Elevated"),
    tone: v <= 0 ? "na" : v < 1 ? "positive" : v <= 2 ? "neutral" : "caution",
    text: L("P/E prilagođen očekivanom rastu dobiti. Ispod 1 može ukazivati na nižu cenu u odnosu na prognozirani rast. iznad 2 na visoka očekivanja. Prognoze mogu biti pogrešne, pa PEG nije samostalna odluka.", "P/E adjusted for expected earnings growth. Below 1 may indicate a lower price relative to forecast growth. above 2 may reflect high expectations. Forecasts can be wrong, so PEG should not be used alone.") };
  if (key === "ps") return { grade: v < 2 ? L("Niži odnos", "Lower ratio") : v <= 10 ? L("Kontekst", "Context") : L("Povišen", "Elevated"), tone: v < 2 ? "positive" : v <= 10 ? "neutral" : "caution",
    text: L("Cena u odnosu na godišnju prodaju. Koristan je i za firme sa malom dobiti, ali normalne vrednosti se mnogo razlikuju po sektoru. uporedi sa sličnim firmama i maržama.", "Price relative to annual sales. It can help assess companies with low earnings, but normal values vary widely by sector. compare similar companies and their margins.") };
  if (key === "roe") return { grade: v < 0 ? L("Negativan", "Negative") : v >= .15 ? L("Visok", "High") : v >= .05 ? L("Umeren", "Moderate") : L("Nizak", "Low"), tone: v < 0 ? "bad" : v >= .15 ? "positive" : v >= .05 ? "neutral" : "caution",
    text: L("Povrat na kapital: koliko dobiti kompanija ostvaruje na kapital akcionara. Više je često bolje, ali veoma visok ROE može nastati i zbog velikog duga ili malog kapitala.", "Return on equity: how much profit the company generates from shareholder equity. Higher is often better, but very high ROE can also result from heavy debt or a small equity base.") };
  if (key === "margin") return { grade: v < 0 ? L("Gubitak", "Loss-making") : v >= .2 ? L("Visoka", "High") : v >= .1 ? L("Solidna", "Solid") : L("Niska", "Low"), tone: v < 0 ? "bad" : v >= .2 ? "positive" : v >= .1 ? "neutral" : "caution",
    text: L("Neto marža je deo prihoda koji ostaje kao dobit. Viša marža može ukazivati na veću otpornost, ali se normalna marža razlikuje između industrija.", "Net margin is the share of revenue left as profit. A higher margin can indicate resilience, but normal margins vary across industries.") };
  if (key === "de") return { grade: v < 100 ? L("Niži dug", "Lower debt") : v <= 200 ? L("Umeren", "Moderate") : L("Visok", "High"), tone: v < 100 ? "positive" : v <= 200 ? "neutral" : "caution",
    text: L("Dug u odnosu na kapital, najčešće prikazan kao procenat. Veći odnos znači veće oslanjanje na dug. Pragovi nisu direktno uporedivi za banke, komunalna preduzeća i različite industrije.", "Debt relative to equity, usually shown as a percentage. A higher ratio means more reliance on borrowing. Thresholds are not directly comparable across banks, utilities and other industries.") };
  if (key === "growth") return { grade: v < 0 ? L("Prihod opada", "Revenue declining") : v >= .1 ? L("Brži rast", "Faster growth") : L("Sporiji rast", "Slower growth"), tone: v < 0 ? "bad" : v >= .1 ? "positive" : "neutral",
    text: L("Promena prihoda u odnosu na prethodni uporedivi period. Proveri da li je rast održiv i da li se pretvara u dobit i novčani tok.", "Revenue change versus the comparable prior period. Check whether growth is sustainable and converts into profit and cash flow.") };
  if (key === "div") return { grade: v >= .05 ? L("Visok prinos", "High yield") : v >= .02 ? L("Umeren prinos", "Moderate yield") : L("Nizak prinos", "Low yield"), tone: v >= .05 ? "caution" : v >= .02 ? "positive" : "neutral",
    text: L("Godišnja dividenda kao procenat cene. Visok prinos nije automatski povoljan - može porasti zato što je cena akcije pala, a dividenda može biti smanjena.", "Annual dividend as a share of price. A high yield is not automatically favorable: it can rise because the share price fell, and the dividend may be cut.") };
  if (key === "beta") return { grade: v < .8 ? L("Mirnija od tržišta", "Less volatile than market") : v <= 1.2 ? L("Blizu tržišta", "Near market") : L("Promenljivija", "More volatile"), tone: v < .8 ? "positive" : v <= 1.2 ? "neutral" : "caution",
    text: L("Procena kretanja u odnosu na tržište: oko 1 znači slično tržištu. iznad 1 obično veće oscilacije, ispod 1 manje. Beta ne pokazuje smer budućeg prinosa.", "Estimated movement relative to the market: around 1 means similar movement. above 1 usually means larger swings, below 1 smaller ones. Beta does not predict return direction.") };
  if (key === "fcf_yield") return { grade: v < 0 ? L("Negativan tok", "Negative cash flow") : v >= .05 ? L("Visok", "High") : v >= .02 ? L("Umeren", "Moderate") : L("Nizak", "Low"), tone: v < 0 ? "bad" : v >= .05 ? "positive" : v >= .02 ? "neutral" : "caution",
    text: L("Slobodan novčani tok kao deo tržišne kapitalizacije. Viši može značiti više novca u odnosu na cenu, ali zavisi od ciklusa ulaganja i sektora.", "Free cash flow as a share of market capitalization. Higher can mean more cash relative to price, but depends on investment cycles and sector.") };
  if (key === "upside") return { grade: v >= .15 ? L("Analitičari vide rast", "Analysts see upside") : v >= 0 ? L("Mali potencijal", "Limited upside") : L("Cilj ispod cene", "Target below price"), tone: v >= .15 ? "positive" : v >= 0 ? "neutral" : "caution",
    text: L("Razlika između trenutne cene i prosečne ciljne cene analitičara. To je prognoza, ne obećanje. zavisi od broja analitičara i može kasniti za tržištem.", "Difference between the current price and analysts' average target. It is a forecast, not a promise. it depends on analyst coverage and can lag the market.") };
  if (key === "rec") return { grade: v <= 1.5 ? L("Pretežno kupi", "Mostly buy") : v <= 2.5 ? L("Nagib ka kupovini", "Buy-leaning") : v <= 3.5 ? L("Drži", "Hold") : L("Nagib ka prodaji", "Sell-leaning"), tone: v <= 2 ? "positive" : v <= 3.2 ? "neutral" : "caution",
    text: L("Prosečna preporuka analitičara na skali 1 (snažna kupovina) do 5 (prodaja). Prikaži i broj analitičara: mali uzorak može biti nepouzdan. Ovo nije preporuka aplikacije.", "Average analyst recommendation on a 1 (strong buy) to 5 (sell) scale. Consider the number of analysts: a small sample can be unreliable. This is not the app's recommendation.") };
  if (key === "analysts") return { grade: v >= 10 ? L("Šira pokrivenost", "Broader coverage") : L("Mala pokrivenost", "Limited coverage"), tone: v >= 10 ? "neutral" : "caution",
    text: L("Broj analitičara uključenih u konsenzus. Veći broj znači širi uzorak mišljenja, ali ne garantuje tačnost ciljne cene.", "Number of analysts included in the consensus. A larger group gives a broader sample, but does not guarantee target accuracy.") };
  if (key === "r1y") return { grade: v > .1 ? L("Rast u periodu", "Positive period") : v >= 0 ? L("Blizu početne cene", "Near flat") : L("Pad u periodu", "Negative period"), tone: v > .1 ? "positive" : v >= 0 ? "neutral" : "caution",
    text: L("Promena cene u prethodnih 12 meseci. Opisuje prošlost, ne predviđa budući prinos.", "Price change over the past 12 months. It describes the past and does not forecast future returns.") };
  if (key === "vol") return { grade: v < .2 ? L("Niža oscilacija", "Lower volatility") : v < .4 ? L("Umerena", "Moderate") : L("Visoka", "High"), tone: v < .2 ? "positive" : v < .4 ? "neutral" : "caution",
    text: L("Godišnja istorijska volatilnost, procenjena iz nedavnih dnevnih promena. Veća vrednost znači veće oscilacije, ne nužno veći gubitak ili dobit.", "Annualized historical volatility estimated from recent daily moves. Higher means wider swings, not necessarily a larger loss or gain.") };
  if (key === "mdd") return { grade: v <= -.4 ? L("Dubok pad", "Deep drawdown") : v <= -.2 ? L("Značajan pad", "Meaningful drawdown") : L("Manji pad", "Shallower drawdown"), tone: v <= -.4 ? "bad" : v <= -.2 ? "caution" : "neutral",
    text: L("Najveći pad od lokalnog maksimuma tokom približno poslednjih 12 meseci. Pokazuje istorijski rizik pada. ne govori da li je akcija sada jeftina.", "Largest peak-to-trough decline over roughly the last 12 months. It shows historical downside risk, not whether the stock is cheap now.") };
  if (key === "trend") return { grade: v >= 0 ? L("Iznad proseka", "Above average") : L("Ispod proseka", "Below average"), tone: v >= 0 ? "positive" : "caution",
    text: L("Poredi trenutnu cenu sa prosekom poslednjih 200 trgovačkih dana. Iznad proseka ukazuje na pozitivniji dugoročni trend. ispod na slabiji trend. To nije procena vrednosti kompanije.", "Compares the current price with its 200-trading-day average. Above suggests a stronger long-term trend. below suggests a weaker trend. It does not measure company value.") };
  if (key === "score") return { grade: v >= 70 ? L("Viši u praćenoj grupi", "Higher in tracked group") : v >= 40 ? L("Srednji u grupi", "Mid-range in group") : L("Niži u grupi", "Lower in group"), tone: v >= 70 ? "positive" : v >= 40 ? "neutral" : "caution",
    text: L("FinNews kompozitni skor 0-100 poredi akcije na listi prema momentumu, potencijalu do ciljne cene, P/E, ROE, rastu prihoda, volatilnosti i dugoročnom trendu. Skor je relativan, zavisi od dostupnih podataka i nije verovatnoća prinosa niti preporuka za kupovinu.", "FinNews composite score (0-100) ranks stocks on the watchlist using momentum, analyst-target upside, P/E, ROE, revenue growth, volatility and long-term trend. It is relative, depends on available data, and is neither a return probability nor a buy recommendation.") };
  if (key === "opp") return { grade: v >= 70 ? L("Viši signal", "Higher signal") : v >= 50 ? L("Srednji signal", "Moderate signal") : L("Niži signal", "Lower signal"), tone: v >= 70 ? "positive" : v >= 50 ? "neutral" : "caution",
    text: L("FinNews skor prilike 0-100 kombinuje pad od maksimuma, konsenzusnu ciljnu cenu, kvalitet, vrednovanje, vesti, trend i sektor. Pomaže da se ideje rangiraju za dalju proveru. ne predviđa ishod i nije preporuka za kupovinu.", "FinNews opportunity score (0-100) combines drawdown, analyst target, quality, valuation, news, trend and sector. It ranks ideas for further research. it does not predict outcomes and is not a buy recommendation.") };
  return { grade: L("Kontekst", "Context"), tone: "neutral", text: L("Vrednost treba tumačiti zajedno sa poslovnim modelom, sektorom, istorijom kompanije i ostalim pokazateljima.", "Interpret this value alongside the business model, sector, company history and other indicators.") };
}

function Detail({ tk, data, prices }) {
  const { lang } = useLang();
  const t = useT();
  const { go, route } = useRoute();
  const [rng, setRng] = useState("6M");
  const [interval, setInterval] = useState("D");
  const [customFrom, setCustomFrom] = useState("");
  const [customTo, setCustomTo] = useState("");
  const [comparePicker, setComparePicker] = useState("");
  const [compareQuery, setCompareQuery] = useState("");
  const [compareOpen, setCompareOpen] = useState(false);
  const [compareTickers, setCompareTickers] = useState([]);
  const [mkt, setMkt] = useState("home");
  const [flippedMetric, setFlippedMetric] = useState(null);
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

  const chartTicker = mkt === "x" && xt ? xt : tk;
  const sourceSeries = series(prices, chartTicker);
  const selectedDaily = filterPeriod(sourceSeries, rng, customFrom, customTo);
  const chartData = groupSeries(selectedDaily, interval);
  const firstValue = selectedDaily.length ? selectedDaily[0].value : null;
  const lastValue = selectedDaily.length ? selectedDaily[selectedDaily.length - 1].value : null;
  const selectedChange = firstValue && lastValue ? lastValue / firstValue - 1 : null;
  const rangeRequestedStart = customFrom || (rng === "YTD" ? `${new Date().getFullYear()}-01-01` : rng === "CUSTOM" ? "" : rng === "MAX" ? "" : new Date(Date.now() - ({ "1M": 31, "6M": 183, "1Y": 365, "3Y": 1095, "5Y": 1825, "10Y": 3650 }[rng] || 183) * 864e5).toISOString().slice(0, 10));
  const comparisonRaw = [chartTicker, ...compareTickers].map((ticker) => ({ ticker, data: filterPeriod(series(prices, ticker), rng, customFrom, customTo) })).filter((x) => x.data.length > 1);
  const commonStart = comparisonRaw.length ? comparisonRaw.reduce((d, x) => x.data[0].time > d ? x.data[0].time : d, comparisonRaw[0].data[0].time) : "";
  const compareItems = comparisonRaw.map((x) => ({ ticker: x.ticker, data: groupSeries(x.data.filter((p) => p.time >= commonStart), interval) })).filter((x) => x.data.length > 1);
  const compareOptions = (data.stocks || []).filter((x) => x.ticker !== s.ticker && !compareTickers.includes(x.ticker) && series(prices, x.ticker).length)
    .sort((a, b) => a.ticker.localeCompare(b.ticker));
  const searchKey = (value) => (value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
  const compareMatches = compareOptions.filter((x) => !compareQuery.trim() || searchKey(x.ticker + " " + x.name).includes(searchKey(compareQuery))).slice(0, 18);
  const valueOrDash = (v, digits = 1) => v === null || v === undefined ? "-" : num(v, digits, lang);
  const metricOverview = [
    { key: "mcap", raw: s.mcap, label: "Market cap", value: big(s.mcap, lang) },
    { key: "pe", raw: s.tpe, label: "P/E (TTM)", value: s.tpe !== null && s.tpe !== undefined ? `${valueOrDash(s.tpe)}×` : "-" },
    { key: "fpe", raw: s.fpe, label: "Forward P/E", value: s.fpe !== null && s.fpe !== undefined ? `${valueOrDash(s.fpe)}×` : "-" },
    { key: "peg", raw: s.peg, label: "PEG", value: valueOrDash(s.peg) },
    { key: "ps", raw: s.ps, label: "P/S", value: s.ps !== null && s.ps !== undefined ? `${valueOrDash(s.ps)}×` : "-" },
    { key: "roe", raw: s.roe, label: "ROE", value: s.roe !== null && s.roe !== undefined ? pct(s.roe, 1, lang, false) : "-" },
    { key: "margin", raw: s.margin, label: "Net margin", value: s.margin !== null && s.margin !== undefined ? pct(s.margin, 1, lang, false) : "-" },
    { key: "de", raw: s.de, label: "Debt / equity (D/E)", value: valueOrDash(s.de, 0) + (s.de !== null && s.de !== undefined ? "%" : "") },
    { key: "growth", raw: s.growth, label: "Revenue growth", value: s.growth !== null && s.growth !== undefined ? pct(s.growth, 1, lang) : "-" },
    { key: "div", raw: s.div, label: "Dividend yield", value: s.div !== null && s.div !== undefined ? pct(s.div, 1, lang, false) : "-" },
    { key: "beta", raw: s.beta, label: "Beta", value: valueOrDash(s.beta, 2) },
    { key: "fcf_yield", raw: s.fcf_yield, label: "Free cash flow yield", value: s.fcf_yield !== null && s.fcf_yield !== undefined ? pct(s.fcf_yield, 1, lang) : "-" },
    { key: "upside", raw: s.upside, label: "Analyst target upside", value: s.upside !== null && s.upside !== undefined ? pct(s.upside, 1, lang) : "-" },
    { key: "rec", raw: s.rec, label: "Analyst consensus (1-5)", value: s.rec !== null && s.rec !== undefined ? valueOrDash(s.rec, 2) : "-" },
    { key: "analysts", raw: s.analysts, label: "Analyst coverage", value: valueOrDash(s.analysts, 0) },
    { key: "r1y", raw: s.r1y, label: "1-year return", value: s.r1y !== null && s.r1y !== undefined ? pct(s.r1y, 1, lang) : "-" },
    { key: "vol", raw: s.vol, label: "Annualized volatility", value: s.vol !== null && s.vol !== undefined ? pct(s.vol, 1, lang, false) : "-" },
    { key: "mdd", raw: s.mdd, label: "Max drawdown (1y)", value: s.mdd !== null && s.mdd !== undefined ? pct(s.mdd, 1, lang) : "-" },
    { key: "trend", raw: s.price && s.sma200 ? s.price / s.sma200 - 1 : null, label: "Price vs. 200-day SMA", value: s.price && s.sma200 ? pct(s.price / s.sma200 - 1, 1, lang) : "-" },
    { key: "score", raw: s.score, label: "FinNews factor score", value: s.score !== null && s.score !== undefined ? `${Math.round(s.score)}/100` : "-" },
    { key: "opp", raw: s.opp, label: "Opportunity score", value: s.opp !== null && s.opp !== undefined ? `${Math.round(s.opp)}/100` : "-" },
  ];
  const factorNames = Object.fromEntries((data.factors || []).map(([k, w, sr, en]) => [k, lang === "en" ? en : sr]));
  const availableMetrics = metricOverview.filter((m) => m.raw !== null && m.raw !== undefined && m.raw !== "" && Number.isFinite(Number(m.raw)) && m.value !== "-");
  const has = (key) => availableMetrics.some((m) => m.key === key);
  const metricValue = (key) => metricOverview.find((m) => m.key === key)?.value;
  const summaryCards = [
    has("opp") ? { title: lang === "en" ? "FinNews screening" : "FinNews pregled", value: metricValue("opp"),
      note: lang === "en" ? "Relative screening score. Use it to prioritize further research, not as a buy signal." : "Relativni skor za rangiranje. Koristi ga da odrediš šta dalje istražiti, ne kao signal za kupovinu." } : null,
    (has("pe") || has("fpe") || has("peg")) ? { title: lang === "en" ? "Valuation" : "Vrednovanje",
      value: [has("pe") && "P/E " + metricValue("pe"), has("fpe") && "Forward P/E " + metricValue("fpe"), has("peg") && "PEG " + metricValue("peg")].filter(Boolean).join(" · "),
      note: lang === "en" ? "Compare with similar companies and check whether earnings support the valuation." : "Uporedi sa sličnim firmama i proveri da li ostvarena i očekivana dobit podržavaju ovu cenu." } : null,
    (has("roe") || has("margin") || has("growth")) ? { title: lang === "en" ? "Business quality" : "Kvalitet poslovanja",
      value: [has("roe") && "ROE " + metricValue("roe"), has("margin") && "Margin " + metricValue("margin"), has("growth") && "Revenue growth " + metricValue("growth")].filter(Boolean).join(" · "),
      note: lang === "en" ? "Check whether growth is turning into profit and cash flow. Compare margins within the same industry." : "Proveri da li se rast vidi i u dobiti i novčanom toku. Marže poredi sa firmama iz iste industrije." } : null,
    (has("vol") || has("mdd") || has("trend") || has("beta")) ? { title: lang === "en" ? "Risk and trend" : "Rizik i trend",
      value: [has("vol") && "Volatility " + metricValue("vol"), has("mdd") && "1y drawdown " + metricValue("mdd"), has("trend") && "vs 200d " + metricValue("trend"), has("beta") && "Beta " + metricValue("beta")].filter(Boolean).join(" · "),
      note: lang === "en" ? "These show the size of past swings and whether the longer trend supported the price." : "Ovo pokazuje kolika su bila kolebanja i da li je duži trend podržavao cenu." } : null,
    (has("upside") || has("rec") || has("analysts")) ? { title: lang === "en" ? "Analyst view" : "Procene analitičara",
      value: [has("upside") && "Target upside " + metricValue("upside"), has("rec") && "Consensus " + metricValue("rec"), has("analysts") && metricValue("analysts") + " analysts"].filter(Boolean).join(" · "),
      note: lang === "en" ? "Targets and ratings are estimates. Check how many analysts contributed and treat them as one input." : "Ciljne cene i ocene su procene. Proveri koliko analitičara ih je dalo i posmatraj ih kao samo jedan od izvora." } : null,
  ].filter(Boolean);
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
      <Card hover={false} className="mt-4 p-4 md:p-5">
        <div className="mb-1 font-display text-xl font-semibold text-cream-50">{lang === "en" ? "Key financial indicators" : "Ključni finansijski pokazatelji"}</div>
        <p className="mb-4 text-sm text-cream-300">{lang === "en" ? "Indicator names are shown in English. Turn a card over for its full name, practical interpretation, and what to check next." : "Nazivi indikatora su na engleskom. Okreni karticu za puni naziv, praktično tumačenje i šta sledeće da proveriš."}</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {availableMetrics.map((m) => {
            const flipped = flippedMetric === m.key;
            const guide = indicatorGuide(m.key, s, lang);
            const tone = guide.tone === "positive" ? "text-up" : guide.tone === "caution" ? "text-gold-400" : guide.tone === "bad" ? "text-down" : "text-cream-300";
            return (
              <button key={m.key} type="button" onClick={() => setFlippedMetric((x) => x === m.key ? null : m.key)}
                aria-expanded={flipped} aria-label={`${m.label}: ${m.value}. ${lang === "en" ? "Click for interpretation" : "Klikni za tumačenje"}`}
                className="h-[208px] w-full text-left [perspective:900px] focus-visible:outline focus-visible:outline-2 focus-visible:outline-wine-400">
                <span className="relative block h-full rounded-xl text-left transition-transform duration-500 [transform-style:preserve-3d]"
                  style={{ transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)" }}>
                  <span className="absolute inset-0 flex flex-col justify-center overflow-hidden rounded-xl border border-ink-600 bg-ink-850/70 p-3 transition-colors hover:border-wine-500/60"
                    style={{ backfaceVisibility: "hidden" }}>
                    <span className="stat-label line-clamp-2">{m.label}</span>
                    <span className="mt-2 font-mono text-lg text-cream-50">{m.value}</span>
                    <span className="mt-3 text-xs text-cream-400">{lang === "en" ? "Tap for definition and practical use ↻" : "Klikni za puno značenje i praktičnu primenu ↻"}</span>
                  </span>
                  <span className="absolute inset-0 flex flex-col overflow-y-auto rounded-xl border border-wine-500/50 bg-ink-900 p-3"
                    style={{ transform: "rotateY(180deg)", backfaceVisibility: "hidden" }}>
                    <span className={`mb-1 text-xs font-bold uppercase tracking-wider ${tone}`}>{lang === "en" ? "Practical reading" : "Praktično tumačenje"}: {guide.grade}</span>
                    <span className="text-sm font-semibold text-cream-100">{fullIndicatorName(m.key, "sr")}</span>
                    <span className="text-xs text-cream-400">{fullIndicatorName(m.key, "en")} · {m.value}</span>
                    <span className="mt-2 text-[13px] leading-relaxed text-cream-200">{guide.text}</span>
                    <span className="mt-2 rounded-lg bg-ink-800/80 p-2.5 text-[13px] leading-relaxed text-gold-300"><b>{lang === "en" ? "Next check: " : "Sledeće proveri: "}</b>{indicatorNextStep(m.key, lang)}</span>
                  </span>
                </span>
              </button>
            );
          })}
        </div>
      </Card>
      {summaryCards.length > 0 && <Card hover={false} className="mt-5 p-4 md:p-5">
        <div className="mb-1 font-display text-xl font-semibold text-cream-50">{lang === "en" ? "Practical stock summary" : "Praktičan sažetak akcije"}</div>
        <p className="mb-4 text-sm leading-relaxed text-cream-300">{lang === "en" ? "A quick reading of available data. Each section suggests a useful follow-up check. it is not a recommendation." : "Brzi pregled dostupnih podataka. Svaka stavka predlaže šta vredi dodatno proveriti. ovo nije preporuka."}</p>
        <div className="grid gap-3 sm:grid-cols-2">
          {summaryCards.map((item) => <div key={item.title} className="rounded-xl border border-ink-600 bg-ink-850/70 p-4">
            <div className="text-sm font-semibold text-gold-300">{item.title}</div>
            <div className="mt-1 font-mono text-[15px] text-cream-50">{item.value}</div>
            <p className="mt-2 text-sm leading-relaxed text-cream-300">{item.note}</p>
          </div>)}
        </div>
        <p className="mt-3 text-xs leading-relaxed text-cream-500">{lang === "en" ? "Only values supplied by the data source are summarized. Data may be delayed or incomplete." : "Sažeti su samo podaci koje izvor dostavlja. Podaci mogu kasniti ili biti nepotpuni."}</p>
      </Card>}
      <Card hover={false} className="mt-5 overflow-hidden p-4 md:p-5">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="font-display text-3xl font-bold text-cream-50">{num((selectedDaily[selectedDaily.length - 1] || {}).value || s.price, 2, lang)} <span className="text-base font-medium text-cream-400">{s.currency}</span></div>
            <div className={cls("mt-1 font-mono text-sm", upDown(selectedChange))}>{pct(selectedChange, 2, lang)} · {lang === "en" ? "selected period" : "izabrani period"}</div>
            <div className="mt-1 text-xs text-cream-500">{chartTicker} · {selectedDaily.length ? `${selectedDaily[0].time} - ${selectedDaily[selectedDaily.length - 1].time}` : (lang === "en" ? "No data for this period" : "Nema podataka za ovaj period")}</div>
          </div>
          {xt && <Segmented size="sm" value={mkt} onChange={setMkt} options={[["home", s.ticker.includes(".") ? s.ticker : (lang === "en" ? "US · " : "SAD · ") + s.ticker], ["x", "XETRA · " + xt]]} />}
        </div>
        <div className="no-scrollbar mb-3 flex gap-1 overflow-x-auto pb-1">
          {CHART_PERIODS.map(([key, label]) => <button key={key} onClick={() => { setRng(key); setCustomFrom(""); setCustomTo(""); }}
            className={cls("shrink-0 rounded-lg px-3 py-2 text-xs font-semibold transition", rng === key ? "bg-wine-700 text-cream-50" : "text-cream-400 hover:bg-ink-700 hover:text-cream-100")}>{label}</button>)}
          <button onClick={() => setRng("CUSTOM")} className={cls("shrink-0 rounded-lg px-3 py-2 text-xs font-semibold transition", rng === "CUSTOM" ? "bg-wine-700 text-cream-50" : "text-cream-400 hover:bg-ink-700 hover:text-cream-100")}>{lang === "en" ? "Custom" : "Datumi"}</button>
        </div>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-cream-500">{lang === "en" ? "From" : "Od"}</span>
            <input aria-label={lang === "en" ? "Start date" : "Početni datum"} type="date" className="field w-auto min-w-0 py-2 text-xs" value={customFrom} onChange={(e) => { setCustomFrom(e.target.value); setRng("CUSTOM"); }} />
            <span className="text-xs text-cream-500">{lang === "en" ? "to" : "do"}</span>
            <input aria-label={lang === "en" ? "End date" : "Krajnji datum"} type="date" className="field w-auto min-w-0 py-2 text-xs" value={customTo} onChange={(e) => { setCustomTo(e.target.value); setRng("CUSTOM"); }} />
          </div>
          <Segmented size="sm" value={interval} onChange={setInterval} options={[["D", lang === "en" ? "Day" : "Dan"], ["W", lang === "en" ? "Week" : "Nedelja"], ["M", lang === "en" ? "Month" : "Mesec"]]} />
        </div>
        {chartData.length > 1 ? <PriceChart data={chartData} height={330} sma={interval === "D"} valueFormat={(v) => num(v, 2, lang)} />
          : <Empty>{lang === "en" ? "There is no price history for this range." : "Nema istorije cena za ovaj period."}</Empty>}
        {interval === "D" && <div className="mt-2 flex gap-4 text-[11px] text-cream-400"><span className="text-gold-500">- - {lang === "en" ? "50-day average" : "prosek 50 dana"}</span><span className="text-copper">- - {lang === "en" ? "200-day average" : "prosek 200 dana"}</span></div>}
        {rng !== "MAX" && rng !== "CUSTOM" && selectedDaily.length > 1 && selectedDaily[0].time > (rangeRequestedStart || selectedDaily[0].time) && <p className="mt-2 text-[11px] text-cream-500">{lang === "en" ? "Showing available history. this security may not have existed for the full selected period." : "Prikazana je dostupna istorija. ova hartija možda ne postoji tokom celog izabranog perioda."}</p>}
      </Card>

      <Card hover={false} className="mt-4 p-4 md:p-5">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div><div className="font-display text-lg font-semibold text-cream-50">{lang === "en" ? "Compare stocks and ETFs" : "Poređenje akcija i ETF-ova"}</div>
            <p className="mt-1 text-xs text-cream-400">{lang === "en" ? "All lines are normalized to the first shared available date in the selected range." : "Linije se porede procentualno od prvog zajedničkog datuma sa dostupnim cenama u izabranom periodu."}</p></div>
          <div className="flex w-full min-w-0 flex-col gap-2 sm:w-auto sm:flex-row">
            <div className="relative min-w-0 flex-1 sm:w-[320px] sm:flex-none" onBlur={(e) => { if (!e.currentTarget.contains(e.relatedTarget)) setCompareOpen(false); }}>
              <Search size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-cream-500" />
              <input className="field pl-10 text-base" role="combobox" aria-autocomplete="list" aria-expanded={compareOpen}
                aria-label={lang === "en" ? "Search stock or ETF" : "Pretraži akciju ili ETF"}
                value={compareQuery} onFocus={() => setCompareOpen(true)}
                onChange={(e) => { setCompareQuery(e.target.value); setComparePicker(""); setCompareOpen(true); }}
                onKeyDown={(e) => {
                  if (e.key === "Escape") setCompareOpen(false);
                  if (e.key === "Enter" && compareMatches.length) { e.preventDefault(); setComparePicker(compareMatches[0].ticker); setCompareQuery(compareMatches[0].ticker + " · " + compareMatches[0].name); setCompareOpen(false); }
                }}
                placeholder={lang === "en" ? "Search by name or ticker…" : "Pretraži po nazivu ili tickeru…"} />
              {compareOpen && <div role="listbox" className="absolute z-40 mt-2 max-h-72 w-full overflow-y-auto rounded-2xl border border-ink-500 bg-ink-850 p-1.5 shadow-2xl">
                {compareMatches.length ? compareMatches.map((x) => <button type="button" role="option" key={x.ticker}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => { setComparePicker(x.ticker); setCompareQuery(x.ticker + " · " + x.name); setCompareOpen(false); }}
                  className="flex w-full items-center justify-between gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-cream-100 transition hover:bg-wine-900/60 focus:bg-wine-900/60">
                  <span className="min-w-0"><b className="font-mono text-gold-300">{x.ticker}</b><span className="ml-2">{x.name}</span></span>
                  {x.etf && <span className="shrink-0 rounded-full border border-ink-500 px-2 py-0.5 text-xs text-cream-400">ETF</span>}
                </button>) : <div className="px-3 py-3 text-sm text-cream-400">{lang === "en" ? "No matching securities with available price history." : "Nema poklapanja sa dostupnom istorijom cena."}</div>}
              </div>}
            </div>
            <button disabled={!comparePicker || compareTickers.length >= 3} onClick={() => {
              if (comparePicker && !compareTickers.includes(comparePicker)) setCompareTickers((x) => [...x, comparePicker]);
              setComparePicker(""); setCompareQuery(""); setCompareOpen(false);
            }} className={cls("btn min-h-11 text-base", (!comparePicker || compareTickers.length >= 3) && "pointer-events-none opacity-40")}>+ {lang === "en" ? "Compare" : "Uporedi"}</button>
          </div>
        </div>
        <div className="mb-3 flex flex-wrap gap-2">
          {[s.ticker, ...compareTickers].map((ticker, i) => {
            const item = (data.stocks || []).find((x) => x.ticker === ticker);
            const colors = ["#DE4A6E", "#E6BC74", "#7FDB97", "#8FB8B0"];
            return <span key={ticker} className="inline-flex items-center gap-2 rounded-full border border-ink-500 px-3 py-1 text-xs text-cream-200"><i className="h-2 w-2 rounded-full" style={{ background: colors[i % colors.length] }} />{ticker}{item && item.etf ? " · ETF" : ""}{ticker !== s.ticker && <button aria-label={lang === "en" ? "Remove comparison" : "Ukloni poređenje"} onClick={() => setCompareTickers((x) => x.filter((v) => v !== ticker))} className="text-cream-400 hover:text-cream-100">×</button>}</span>;
          })}
        </div>
        {compareItems.length ? <CompareChart items={compareItems} height={300} lang={lang} />
          : <p className="rounded-xl border border-dashed border-ink-500 p-4 text-sm text-cream-400">{lang === "en" ? "Choose up to three stocks or ETFs with available price history." : "Izaberi do tri akcije ili ETF-a sa dostupnom istorijom cena."}</p>}
      </Card>
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
  const [tierF, setTierF] = useState(null);
  const [how, setHow] = useState(false);
  const tab = route.q.tab || "opp";
  const [q, setQ] = useState(route.q.q || "");
  const [secs, setSecs] = useState([]);
  const [sectorSearch, setSectorSearch] = useState("");
  const [sort, setSort] = useState("opp");
  const [fallen, setFallen] = useState(false);
  const [instrumentFilter, setInstrumentFilter] = useState("stocks");
  const [show, setShow] = useState(12);
  const [days, setDays] = useState(30);
  const list = (data && data.stocks) || [];
  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    let r = list.filter((x) => {
      const themeName = data?.theme_names?.[x.theme]?.[lang === "en" ? 1 : 0] || "";
      const focusMatch = !secs.length || secs.some((focus) => focus.startsWith("theme:")
        ? x.theme === focus.slice(6)
        : x.sector === focus.slice(7));
      return (instrumentFilter === "all" || (instrumentFilter === "etf" ? !!x.etf : !x.etf)) && focusMatch
        && (!tierF || x.tier === tierF) && (!fallen || (x.dd !== undefined && x.dd <= -0.08))
        && (!s || [x.name, x.ticker, x.sector, x.sector_sr, x.industry, x.industry_sr, themeName].join(" ").toLowerCase().includes(s));
    });
    const k = { opp: (x) => -(x.opp ?? -1), score: (x) => -(x.score ?? -1), dd: (x) => x.dd ?? 0, up: (x) => -(x.upside ?? -9), r1y: (x) => -(x.r1y ?? -9), r1d: (x) => -(x.r1d ?? -9), div: (x) => -(x.div ?? 0) }[sort];
    return [...r].sort((a, b) => k(a) - k(b));
  }, [list, data, lang, q, secs, sort, fallen, instrumentFilter, tierF]);
  if (route.parts[1]) return data && prices ? <Detail tk={decodeURIComponent(route.parts[1])} data={data} prices={prices} /> : <Skeleton className="h-[500px]" />;
  const smap = Object.fromEntries(list.map((x) => [x.ticker, x]));
  const opps = ((data && (data.top25 || data.top20)) || []).map((t) => smap[t]).filter(Boolean);
  const sectors = [...new Set(list.filter((x) => x.sector).map((x) => x.sector))].sort();
  const tw = (data && data.tailwind) || {};
  const good = Object.entries(tw).filter(([, v]) => v > 0.1).sort((a, b) => b[1] - a[1]).slice(0, 3);
  const bad = Object.entries(tw).filter(([, v]) => v < -0.1).sort((a, b) => a[1] - b[1]).slice(0, 2);
  const sectorProspects = sectors.map((sector) => {
    const members = list.filter((stock) => stock.sector === sector && !stock.etf);
    const scores = members.map((stock) => +stock.opp).filter(Number.isFinite);
    return { sector, count: members.length, score: scores.length ? scores.reduce((sum, value) => sum + value, 0) / scores.length : null, tailwind: +(tw[sector] || 0) };
  }).sort((a, b) => {
    const signal = (item) => (item.tailwind > 0.1 ? 2 : item.tailwind < -0.1 ? 0 : 1);
    return signal(b) - signal(a) || (b.score ?? -1) - (a.score ?? -1);
  });
  const sn = (k) => (lang === "sr" ? (data.sectors_sr || {})[k] || k : k);
  const themeOptions = Object.entries(data.theme_names || {}).filter(([key]) => list.some((stock) => stock.theme === key))
    .map(([key, names]) => ({ value: "theme:" + key, label: names[lang === "en" ? 1 : 0] }))
    .filter((option) => !sectorSearch.trim() || option.label.toLocaleLowerCase().includes(sectorSearch.trim().toLocaleLowerCase()) || option.value.toLocaleLowerCase().includes(sectorSearch.trim().toLocaleLowerCase()));
  const visibleSectors = sectors.filter((sector) => !sectorSearch.trim() || sn(sector).toLocaleLowerCase().includes(sectorSearch.trim().toLocaleLowerCase()) || sector.toLocaleLowerCase().includes(sectorSearch.trim().toLocaleLowerCase()));
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
                  "Trend first: the 200-day average shows direction. A pullback inside an uptrend is preferred. a stock that keeps falling below its 200-day average (a 'falling knife') is ranked lower.",
                  "Entry timing: RSI 30-50 and turning up is the entry zone. above 70 means overheated - don't chase.",
                  "Growth, valuation and quality: revenue growth, margins, ROE, debt, forward P/E and PEG, plus free-cash-flow yield when Yahoo Finance supplies it. P/S is shown as context because it needs peer comparison.",
                  "Tailwinds: sectors helped by what the news is talking about now (AI, power, defence, rates...), plus the tone of company news.",
                  "Position size by risk tier: blue chip up to ~10%, growth 1-5%, speculative under 1% - and buy in parts (DCA), keeping 5-15% in cash. Metrics such as insider/13F activity, MACD and Bollinger Bands are not available in this app's current data feed, so they are not scored.",
                ] : [
                  "Kvalitet na popustu: profitabilne kompanije koje rastu, bar 8% ispod 52-nedeljnog maksimuma, gde analitičari vide rast.",
                  "Prvo trend: 200-dnevni prosek pokazuje pravac. Prednost ima povlačenje u rastućem trendu. akcija koja i dalje pada ispod 200-dnevnog proseka („nož koji pada“) rangira se niže.",
                  "Trenutak ulaza: RSI 30-50 koji se okreće naviše je zona za ulaz. iznad 70 je pregrejano - ne juriti.",
                  "Rast, vrednovanje i kvalitet: rast prihoda, marže, ROE, dug, forward P/E i PEG, kao i prinos slobodnog novčanog toka kada ga Yahoo Finance dostavi. P/S se prikazuje kao kontekst jer ga treba porediti sa sličnim kompanijama.",
                  "Vetar u leđa: sektori kojima pomažu teme iz aktuelnih vesti (AI, struja, odbrana, kamate...), i ton vesti o samoj kompaniji.",
                  "Veličina pozicije po nivou rizika: blue chip do ~10%, rast 1-5%, spekulativno ispod 1% - kupuj u delovima (DCA) i drži 5-15% u gotovini. Podaci poput insajderskih/13F transakcija, MACD-a i Bollingerovih opsega nisu dostupni u trenutnom izvoru aplikacije i zato ne ulaze u skor.",
                ]).map((x, i) => <li key={i} className="flex gap-2.5"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rotate-45 bg-gradient-to-br from-wine-500 to-gold-500" />{x}</li>)}
              </motion.ul>
            )}
          </Card>
          <Card hover={false} className="mb-6 p-5">
            <div className="mb-1 font-display text-lg font-semibold text-cream-50">{lang === "en" ? "Sector outlook" : "Pregled sektora"}</div>
            <p className="mb-4 text-sm leading-relaxed text-cream-400">{lang === "en" ? "Every sector in the tracked universe, ranked by recent news tailwind and average opportunity score of tracked companies. These are research signals, not forecasts." : "Svi sektori iz baze, poređani prema podršci iz aktuelnih vesti i prosečnom skoru prilike praćenih kompanija. Ovo su signali za istraživanje, ne prognoze."}</p>
            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
              {sectorProspects.map((item) => <button type="button" key={item.sector} onClick={() => { setSecs(["sector:" + item.sector]); setQuery({ tab: "all" }); }}
                className="group rounded-xl border border-ink-600 bg-ink-850/70 p-3 text-left transition hover:-translate-y-0.5 hover:border-wine-400/70 hover:bg-wine-950/40 focus:outline-none focus:ring-2 focus:ring-gold-400/60">
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm font-semibold text-cream-50">{sn(item.sector)}</span>
                  {item.score !== null && <span className="shrink-0 font-mono text-xs text-gold-300">{lang === "en" ? "avg score" : "prosek"} {num(item.score, 0, lang)}</span>}
                </div>
                <div className="mt-1 flex items-center justify-between gap-2 text-xs">
                  <span className={item.tailwind > 0.1 ? "text-up" : item.tailwind < -0.1 ? "text-down" : "text-cream-400"}>
                    {item.tailwind > 0.1 ? (lang === "en" ? "Positive news signal" : "Pozitivan signal iz vesti") : item.tailwind < -0.1 ? (lang === "en" ? "News headwind" : "Negativan signal iz vesti") : (lang === "en" ? "No clear news signal" : "Bez jasnog signala iz vesti")}
                  </span>
                  <span className="text-cream-500">{item.count} {lang === "en" ? "companies" : "kompanija"}</span>
                </div>
                <span className="mt-2 inline-flex text-xs font-medium text-wine-300 group-hover:text-gold-300">{lang === "en" ? "View this sector" : "Prikaži sektor"} →</span>
              </button>)}
            </div>
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
            <Chip active={instrumentFilter === "stocks"} onClick={() => setInstrumentFilter("stocks")}>{lang === "en" ? "Stocks" : "Akcije"}</Chip>
            <Chip active={instrumentFilter === "etf"} onClick={() => setInstrumentFilter("etf")}>ETF-ovi</Chip>
            <Chip active={instrumentFilter === "all"} onClick={() => setInstrumentFilter("all")}>{lang === "en" ? "All instruments" : "Sve hartije"}</Chip>
            <span className="mx-1 w-px shrink-0 bg-ink-600" />
            <details className="group relative shrink-0">
              <summary className="flex min-h-10 cursor-pointer list-none items-center gap-2 rounded-full border border-ink-500 bg-ink-800/80 px-4 py-2 text-sm font-medium text-cream-100 transition hover:border-gold-400/70 hover:bg-ink-700 [&::-webkit-details-marker]:hidden">
                {lang === "en" ? "Sector or theme" : "Sektor ili tema"}{secs.length ? <span className="rounded-full bg-wine-600/70 px-2 py-0.5 text-xs text-white">{secs.length}</span> : <span className="text-xs text-cream-400">{lang === "en" ? "all" : "svi"}</span>}
                <ChevronDown size={15} className="text-gold-300 transition-transform duration-300 group-open:rotate-180" />
              </summary>
              <div className="absolute left-0 top-full z-40 mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-2xl border border-wine-500/45 bg-[#0b080a] p-3 shadow-[0_22px_60px_-18px_rgba(0,0,0,.9)]">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-cream-50">{lang === "en" ? "Choose sectors or themes" : "Izaberi sektore ili teme"}</span>
                  <button type="button" onClick={() => setSecs([])} className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-gold-300 transition hover:bg-wine-950 hover:text-gold-200">
                    {lang === "en" ? "Clear" : "Očisti"}
                  </button>
                </div>
                <div className="relative mb-2">
                  <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gold-400" />
                  <input className="field min-h-10 py-2 pl-9 text-sm" value={sectorSearch} onChange={(event) => setSectorSearch(event.target.value)}
                    placeholder={lang === "en" ? "Search sectors or themes" : "Pretraži sektore ili teme"} aria-label={lang === "en" ? "Search sectors or themes" : "Pretraži sektore ili teme"} />
                </div>
                <div className="no-scrollbar max-h-72 space-y-1 overflow-y-auto">
                  {visibleSectors.length > 0 && <p className="px-3 pb-1 pt-2 text-[10px] font-semibold uppercase tracking-widest text-gold-400">{lang === "en" ? "Company sectors" : "Sektori kompanija"}</p>}
                  {visibleSectors.map((sector) => {
                    const value = "sector:" + sector;
                    return <label key={value} className="flex min-h-10 cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm text-cream-200 transition hover:bg-wine-950/80 hover:text-white">
                      <input type="checkbox" checked={secs.includes(value)} onChange={() => setSecs((current) => current.includes(value) ? current.filter((item) => item !== value) : [...current, value])}
                        className="h-4 w-4 accent-[#f4b942]" />
                      <span className="flex-1">{sn(sector)}</span>
                      {secs.includes(value) && <Check size={15} className="text-gold-300" />}
                    </label>;
                  })}
                  {themeOptions.length > 0 && <p className="px-3 pb-1 pt-3 text-[10px] font-semibold uppercase tracking-widest text-gold-400">{lang === "en" ? "Investment themes" : "Teme i izloženost"}</p>}
                  {themeOptions.map((option) => <label key={option.value} className="flex min-h-10 cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm text-cream-200 transition hover:bg-wine-950/80 hover:text-white">
                    <input type="checkbox" checked={secs.includes(option.value)} onChange={() => setSecs((current) => current.includes(option.value) ? current.filter((item) => item !== option.value) : [...current, option.value])}
                      className="h-4 w-4 accent-[#f4b942]" />
                    <span className="flex-1">{option.label}</span>
                    {secs.includes(option.value) && <Check size={15} className="text-gold-300" />}
                  </label>)}
                </div>
                {!visibleSectors.length && !themeOptions.length &&
                  <p className="px-3 py-4 text-sm text-cream-400">{lang === "en" ? "No matching sectors or themes." : "Nema sektora ili tema za ovu pretragu."}</p>}
              </div>
            </details>
          </div>
          <p className="-mt-3 mb-4 text-xs text-cream-500">{lang === "en" ? "Instrument type and selected sectors or themes combine. For example, ETFs + Semiconductors shows SMH and SOXX." : "Tip hartije i izabrani sektori ili teme rade zajedno. Na primer, ETF-ovi + Poluprovodnici prikazuju SMH i SOXX."}</p>

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
