import { ArrowRight, CalendarClock, Gauge as GaugeIcon } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
import { cls, num } from "../lib/fmt";
import { getMeta, useData } from "../lib/data";
import { usePortfolio } from "../lib/usePortfolio";
import { positions } from "../lib/portfolio";
import { useRoute } from "../components/Shell";
import { Card, SectionTitle, Skeleton } from "../components/ui";
import { PeriodSummary, StrategyBriefing } from "../components/Summary";
import { OppCard } from "../components/Stocks";

// Raspoloženje tržišta iz trake tržišta, po jednostavnim i proverljivim pravilima (nije AI)
function MarketPulse() {
  const { lang } = useLang();
  const meta = getMeta();
  const m = Object.fromEntries(((meta && meta.markets) || []).map((x) => [x.n, x]));
  const vix = m["VIX"], spx = m["S&P 500"], ust = m["US 10g %"], eur = m["EUR/USD"];
  if (!vix || !spx) return null;
  const v = vix.v, d = spx.ch;
  const state = v >= 30 || d <= -0.025 ? ["fear", "Strah na tržištu", "Fear in the market", "text-down"]
    : v >= 20 || d <= -0.012 ? ["nervous", "Povišena nervoza", "Elevated nerves", "text-gold-400"]
    : v < 15 && d >= 0 ? ["calm", "Mirno tržište, sklonost riziku", "Calm market, risk appetite", "text-up"]
    : ["normal", "Uobičajeni uslovi", "Normal conditions", "text-cream-100"];
  const why = lang === "en"
    ? `VIX ${num(v, 1, lang)} (${v < 15 ? "calm" : v < 20 ? "normal" : v < 30 ? "elevated" : "fear"}), S&P 500 ${d >= 0 ? "+" : ""}${num(d * 100, 2, lang)}% on the day.`
    : `VIX ${num(v, 1, lang)} (${v < 15 ? "mirno" : v < 20 ? "normalno" : v < 30 ? "povišeno" : "strah"}), S&P 500 ${d >= 0 ? "+" : ""}${num(d * 100, 2, lang)}% za dan.`;
  const cell = (label, x, dec, unit = "") => x && (
    <div className="min-w-0">
      <div className="stat-label">{label}</div>
      <div className="mt-1 font-mono text-[15px] text-cream-50">{num(x.v, dec, lang)}{unit}</div>
      <div className={cls("font-mono text-[11px]", x.ch >= 0 ? "text-up" : "text-down")}>{x.ch >= 0 ? "+" : ""}{num(x.ch * 100, 2, lang)}%</div>
    </div>
  );
  return (
    <Card hover={false} className="p-4 md:p-5">
      <div className="flex flex-wrap items-center justify-between gap-x-8 gap-y-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 stat-label"><GaugeIcon size={13} className="text-gold-500" />{lang === "en" ? "Market mood" : "Raspoloženje tržišta"}</div>
          <div className={cls("mt-1.5 font-display text-[1.35rem] font-semibold leading-tight", state[3])}>{lang === "en" ? state[2] : state[1]}</div>
          <div className="mt-1 text-xs text-cream-400">{why}</div>
        </div>
        <div className="grid grid-cols-4 gap-5 sm:gap-8">
          {cell("S&P 500", spx, 0)}{cell("VIX", vix, 1)}{cell(lang === "en" ? "US 10y" : "US 10g", ust, 2, "%")}{cell("EUR/USD", eur, 4)}
        </div>
      </div>
    </Card>
  );
}

// Naredni rezultati kompanija i datumi dividendi: prvo tvoje pozicije i lista praćenja, zatim prilike
function Upcoming({ stocks, mine }) {
  const { lang } = useLang();
  const { go } = useRoute();
  const today = new Date().toISOString().slice(0, 10), end = new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10);
  const top = new Set((stocks.top20 || []).slice(0, 10));
  const ev = [];
  for (const s of stocks.stocks || []) {
    const rank = mine.has(s.ticker) ? 0 : top.has(s.ticker) ? 1 : 2;
    if (s.earn && s.earn >= today && s.earn <= end) ev.push({ s, d: s.earn, kind: "earn", rank });
    if (s.exdiv && s.exdiv >= today && s.exdiv <= end && rank < 2) ev.push({ s, d: s.exdiv, kind: "div", rank });
  }
  ev.sort((a, b) => a.rank - b.rank || a.d.localeCompare(b.d));
  const list = ev.slice(0, 6).sort((a, b) => a.d.localeCompare(b.d));
  const fmt = (d) => new Date(d + "T12:00:00Z").toLocaleDateString(lang === "en" ? "en-GB" : "sr-Latn-RS", { weekday: "short", day: "numeric", month: "short" });
  return (
    <Card hover={false} className="p-4 md:p-5">
      <div className="mb-3 flex items-center gap-2 stat-label"><CalendarClock size={13} className="text-gold-500" />{lang === "en" ? "Next 14 days" : "Narednih 14 dana"}</div>
      {!list.length ? <p className="text-sm text-cream-400">{lang === "en" ? "No earnings or dividend dates for your holdings, watchlist or top ideas." : "Nema rezultata ni datuma dividendi za tvoje pozicije, listu praćenja i glavne prilike."}</p> : (
        <ul className="divide-y divide-white/[0.06]">
          {list.map((e, i) => (
            <li key={i}>
              <button type="button" onClick={() => go("/akcije/" + encodeURIComponent(e.s.ticker))} className="flex w-full items-center gap-3 py-2 text-left transition hover:bg-white/[0.03]">
                <span className="w-20 shrink-0 text-xs text-cream-400">{fmt(e.d)}</span>
                <span className="min-w-0 flex-1 truncate text-sm text-cream-100"><b className="font-semibold">{e.s.ticker}</b> <span className="text-cream-400">{e.s.name}</span></span>
                <span className={cls("shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide", e.kind === "earn" ? "bg-white/10 text-cream-100" : "bg-gold-500/15 text-gold-400")}>
                  {e.kind === "earn" ? (lang === "en" ? "Earnings" : "Rezultati") + (e.s.earn_est ? "*" : "") : (lang === "en" ? "Ex-dividend" : "Ex-dividenda")}
                </span>
                {e.rank === 0 && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-gold-500" title={lang === "en" ? "In your portfolio or watchlist" : "U tvom portfoliju ili listi praćenja"} />}
              </button>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-[11px] text-cream-500">{lang === "en" ? "Dot = your holding or watchlist. * = date estimated by the company calendar." : "Tačka = tvoja pozicija ili lista praćenja. * = procenjen datum."}</p>
    </Card>
  );
}

export default function Home() {
  const { lang } = useLang();
  const t = useT();
  const { go } = useRoute();
  const { data: [periods, stocks] } = useData(["periods.json", "stocks.json"]);
  const pf = usePortfolio();
  const st = pf.state || {};
  const mine = new Set([...positions(st).map((p) => p.ticker), ...((st.watchlist || []).map((w) => (typeof w === "string" ? w : w && w.ticker)))].filter(Boolean));
  const smap = Object.fromEntries(((stocks && stocks.stocks) || []).map((s) => [s.ticker, s]));
  const opps = ((stocks && stocks.top20) || []).map((x) => smap[x]).filter(Boolean);
  const fin1 = periods && periods.periods.fin["1"];
  const today = fin1 && fin1.top.length;
  const block = today ? fin1 : periods && periods.periods.fin["7"];
  return (
    <div className="space-y-8">
      <MarketPulse />

      <div className="grid min-w-0 grid-cols-1 gap-8 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <section className="min-w-0">
          <SectionTitle action={<button onClick={() => go("/vesti")} className="btn-ghost">{t("allNews")} <ArrowRight size={14} /></button>}>
            {lang === "en" ? "Most important today" : "Najvažnije danas"}</SectionTitle>
          {periods ? <PeriodSummary compact block={block} items={periods.items} n={5} digest={periods.digests?.fin?.[today ? "1" : "7"]}
            title={today ? t("d1") : t("d7")} /> : <Skeleton className="h-80" />}
          {periods && periods.strategy && <div className="mt-4"><StrategyBriefing strategy={periods.strategy} items={periods.items} /></div>}
        </section>
        <section className="min-w-0 space-y-6">
          {stocks ? <Upcoming stocks={stocks} mine={mine} /> : <Skeleton className="h-48" />}
          <div>
            <SectionTitle action={<button onClick={() => go("/akcije")} className="btn-ghost">{t("seeAll")} <ArrowRight size={14} /></button>}>{t("opportunities")}</SectionTitle>
            <div className="space-y-3">{stocks ? opps.slice(0, 3).map((s, i) => <OppCard key={s.ticker} s={s} i={i} compact />) : <Skeleton className="h-48" />}</div>
          </div>
        </section>
      </div>
      <p className="text-[11px] text-cream-500">{lang === "en" ? "Information only, not financial advice." : "Samo informacija, nije finansijski savet."}</p>
    </div>
  );
}
