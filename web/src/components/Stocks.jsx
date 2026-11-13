import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight, Check, ChevronRight, Copy, Minus, ShieldAlert, Sparkles, TrendingDown, TrendingUp, X } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
import { cls, num, pct, srcColor, upDown, itTitle, timeAgo } from "../lib/fmt";
import { series } from "../lib/data";
import { useRoute } from "./Shell";
import { useApp } from "./News";
import { Badge, Card, Gauge, Spark, toast } from "./ui";
import PriceChart from "./PriceChart";

export const secName = (s, lang, map) => (lang === "sr" ? (map && map[s.sector]) || s.sector_sr || s.sector : s.sector) || "ETF";
export const TIER_COLOR = { core: "#E6BC74", growth: "#DE4A6E", spec: "#B9A0C9" };
const TIER_TXT = { core: ["Blue chip", "Blue chip"], growth: ["Rast", "Growth"], spec: ["Spekulativno", "Speculative"] };
const usExchange = (t) => (t.includes(".") ? { ".DE": "XETRA", ".PA": "Pariz", ".AS": "Amsterdam", ".MI": "Milano", ".MC": "Madrid", ".SW": "Cirih", ".L": "London", ".CO": "Kopenhagen", ".BR": "Brisel", ".HE": "Helsinki" }[t.slice(t.indexOf("."))] || "EU" : "SAD");
const curSym = (c) => ({ USD: "$", EUR: "€", CHF: "CHF ", GBP: "£", GBp: "p ", DKK: "kr " }[c] || (c ? c + " " : ""));

export function TierBadge({ tier }) {
  const { lang } = useLang();
  if (!tier) return null;
  const c = TIER_COLOR[tier];
  return <span className="rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider" style={{ color: c, borderColor: c + "66", background: c + "14" }}>{TIER_TXT[tier][lang === "en" ? 1 : 0]}</span>;
}

function copy(txt, lang) {
  try { navigator.clipboard.writeText(txt); toast((lang === "en" ? "Copied: " : "Kopirano: ") + txt); } catch { /* */ }
}

// cena na matičnoj berzi i na Xetri (za Erste broker)
export function Listings({ s, compact = false }) {
  const { lang } = useLang();
  const home = usExchange(s.ticker);
  const rows = [[home === "SAD" ? (lang === "en" ? "US" : "SAD") : home, s.ticker, s.price, s.currency, s.r1d]];
  if (s.xetra && s.xetra.t !== s.ticker) rows.push([s.xetra.ex, s.xetra.t, s.xetra.px, s.xetra.ex === "XETRA" || s.xetra.ex === "Frankfurt" ? "EUR" : "", s.xetra.r1d]);
  return (
    <div className={cls("grid gap-1.5", compact ? "" : "sm:grid-cols-2")}>
      {rows.map(([ex, tk, px, cur, ch]) => (
        <button key={tk} onClick={(e) => { e.stopPropagation(); copy(tk, lang); }} title={lang === "en" ? "Copy symbol" : "Kopiraj oznaku"}
          className="group/l flex items-center gap-2 rounded-lg border border-ink-600 bg-ink-850/70 px-2.5 py-1.5 text-left transition hover:border-wine-500/60 hover:bg-wine-950/40">
          <span className={cls("rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider", ex === "XETRA" ? "bg-gold-500/15 text-gold-400" : "bg-wine-900/70 text-wine-300")}>{ex}</span>
          <span className="font-mono text-xs text-cream-200">{tk}</span>
          <span className="ml-auto font-mono text-xs text-cream-50">{px !== null && px !== undefined ? curSym(cur) + num(px, 2, lang) : "-"}</span>
          {ch !== null && ch !== undefined && <span className={cls("font-mono text-[10px]", upDown(ch))}>{pct(ch, 1, lang)}</span>}
          <Copy size={11} className="text-cream-500 opacity-0 transition group-hover/l:opacity-100" />
        </button>
      ))}
      {!compact && s.isin && (
        <button onClick={(e) => { e.stopPropagation(); copy(s.isin, lang); }} className="flex items-center gap-2 rounded-lg px-2.5 py-1 text-left text-[11px] text-cream-400 transition hover:text-cream-100">
          ISIN <span className="font-mono text-cream-200">{s.isin}</span><Copy size={11} />
        </button>
      )}
      {!compact && !s.xetra && !s.ticker.endsWith(".DE") && (
        <div className="px-1 text-[11px] text-cream-500">{lang === "en" ? "Xetra listing not found yet - search by name or ISIN in your broker." : "Xetra oznaka još nije pronađena - potraži po nazivu ili ISIN-u u brokeru."}</div>
      )}
    </div>
  );
}

export function Brief({ s, lines = 2 }) {
  const { lang } = useLang();
  const b = s.brief && (s.brief[lang] || s.brief.sr || s.brief.en);
  const ind = lang === "sr" ? s.industry_sr || s.industry : s.industry;
  const fallback = s.etf
    ? (lang === "en" ? `${s.name} is an exchange-traded fund. Its price follows the assets it holds. Detailed fund data is not available yet.` : `${s.name} je fond kojim se trguje na berzi. Cena prati vrednost imovine u fondu. Detaljni podaci o fondu još nisu dostupni.`)
    : ind
      ? (lang === "en" ? `${s.name} is tracked in the ${ind} industry. A more detailed company description is not available yet.` : `${s.name} je praćena u industriji ${ind}. Detaljniji opis kompanije trenutno nije dostupan.`)
      : (lang === "en" ? `${s.name} (${s.ticker}) is on the tracked securities list. A company description is not available yet.` : `${s.name} (${s.ticker}) nalazi se na listi praćenih hartija. Opis kompanije trenutno nije dostupan.`);
  return (
    <div className="mt-2.5">
      <p className={cls("text-[13px] leading-relaxed text-cream-300", lines === 2 ? "line-clamp-2" : lines === 3 ? "line-clamp-3" : "")}>{b || fallback}</p>
      {ind && <div className="mt-1 text-[11px] text-cream-500">{lang === "en" ? "Industry" : "Industrija"}: {ind}</div>}
    </div>
  );
}

export function StockCard({ s, i = 0, sectors }) {
  const { lang } = useLang();
  const t = useT();
  const { go } = useRoute();
  return (
    <Card delay={Math.min(i, 8) * 0.04} onClick={() => go("/akcije/" + encodeURIComponent(s.ticker))} className="group flex flex-col p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-1.5">
            <Badge color={srcColor(s.sector || "ETF")}>{secName(s, lang, sectors)}</Badge>
            <TierBadge tier={s.tier} />
            {s.qual && <span className="rounded-full bg-gradient-to-r from-wine-600 to-wine-800 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-cream-50">{lang === "en" ? "opportunity" : "prilika"}</span>}
          </div>
          <div className="mt-2 truncate font-display text-[1.1rem] font-semibold text-cream-50">{s.name}</div>
        </div>
        {s.opp !== undefined && <Gauge value={s.opp} size={48} />}
      </div>
      <Brief s={s} />
      <Spark data={s.spark} height={56} className="mt-3" />
      <div className="mt-2"><Listings s={s} compact /></div>
      <div className="mt-2 grid grid-cols-4 gap-1.5">
        {[[t("oneYear"), pct(s.r1y, 0, lang), s.r1y], [t("fromHigh"), s.dd !== undefined ? pct(s.dd, 0, lang) : "-", s.dd],
          [lang === "en" ? "target" : "cilj", pct(s.upside, 0, lang), s.upside], ["Fwd P/E", s.fpe ? num(s.fpe, 1, lang) : "-", null]].map(([l, v, c], k) => (
          <div key={k} className="rounded-lg border border-ink-600 bg-ink-850/60 px-2 py-1.5 transition-colors group-hover:border-ink-500">
            <div className="truncate text-[9px] font-semibold uppercase tracking-wider text-cream-500">{l}</div>
            <div className={cls("font-mono text-[13px]", c === null ? "text-cream-100" : upDown(c))}>{v}</div>
          </div>
        ))}
      </div>
      <div className="mt-auto flex items-center justify-end pt-3 text-xs font-medium text-cream-400 transition-colors group-hover:text-wine-400">
        {t("chartDetails")} <ChevronRight size={14} className="transition-transform group-hover:translate-x-1" />
      </div>
    </Card>
  );
}

export function Checklist({ items }) {
  const { lang } = useLang();
  if (!items || !items.length) return null;
  const ok = items.filter((x) => x[2] === true).length, known = items.filter((x) => x[2] !== null).length;
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="kicker">{lang === "en" ? "Checklist before buying" : "Provera pre kupovine"}</span>
        <span className="font-mono text-xs text-cream-400">{ok}/{known}</span>
      </div>
      <div className="grid gap-1 sm:grid-cols-2">
        {items.map(([sr, en, v], i) => (
          <motion.div key={i} initial={{ opacity: 0, x: -6 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.03 }}
            className="flex items-center gap-2 rounded-md px-1.5 py-1 text-[13px] transition-colors hover:bg-ink-750">
            <span className={cls("grid h-5 w-5 shrink-0 place-items-center rounded-full", v === true ? "bg-up/15 text-up" : v === false ? "bg-down/15 text-down" : "bg-ink-600 text-cream-500")}>
              {v === true ? <Check size={12} /> : v === false ? <X size={12} /> : <Minus size={12} />}
            </span>
            <span className={v === null ? "text-cream-500" : "text-cream-200"}>{lang === "en" ? en : sr}</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

export function WhyRisk({ s }) {
  const { lang } = useLang();
  const t = useT();
  const reasons = (s.reasons && s.reasons[lang]) || [];
  const risks = (s.risks && s.risks[lang]) || [];
  if (!reasons.length && !risks.length) return null;
  return (
    <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div className="rounded-xl border-l-[3px] border-wine-500 bg-wine-950/40 p-3.5">
          <div className="mb-1.5 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-wine-300"><Sparkles size={13} />{t("whyNow")}</div>
          <ul className="space-y-1 text-sm text-cream-200">{reasons.map((r, k) => <li key={k} className="flex gap-2"><TrendingUp size={14} className="mt-0.5 shrink-0 text-up" />{r}</li>)}</ul>
        </div>
        {risks.length > 0 && (
          <div className="rounded-xl border-l-[3px] border-gold-500 bg-gold-500/5 p-3.5">
            <div className="mb-1.5 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-gold-400"><ShieldAlert size={13} />{t("watchOut")}</div>
            <ul className="space-y-1 text-sm text-cream-200">{risks.map((r, k) => <li key={k} className="flex gap-2"><TrendingDown size={14} className="mt-0.5 shrink-0 text-down" />{r}</li>)}</ul>
          </div>
        )}
      </div>
  );
}

const SETUP_COLOR = { pullback: "#7FDB97", uptrend: "#7FDB97", recovery: "#E6BC74", hot: "#E6BC74", downtrend: "#FF7A90", knife: "#FF7A90" };

export function OppCard({ s, prices, i = 0, compact = false, sectors, showChart = true, tierSize }) {
  const { lang } = useLang();
  const t = useT();
  const { go } = useRoute();
  const app = useApp();
  const [open, setOpen] = useState(false);
  if (compact) {
    return (
      <Card delay={i * 0.06} onClick={() => go("/akcije/" + encodeURIComponent(s.ticker))} className="group flex min-w-0 items-center gap-3 p-3 sm:gap-4 sm:p-4">
        <Gauge value={s.opp} size={56} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2"><span className="truncate font-display text-[1.02rem] font-semibold text-cream-50">{s.name}</span><TierBadge tier={s.tier} /></div>
          <div className="mt-0.5 line-clamp-1 text-xs text-cream-400">{s.brief && (s.brief[lang] || s.brief.sr)}</div>
          <div className="mt-0.5 flex items-center gap-2 text-xs"><span className="text-down">{pct(s.dd, 0, lang)} {t("fromHigh")}</span>
            {s.upside ? <span className="text-up">{lang === "en" ? "target" : "cilj"} {pct(s.upside, 0, lang)}</span> : null}</div>
        </div>
        <div className="hidden w-24 shrink-0 sm:block"><Spark data={s.spark} height={36} /></div>
      </Card>
    );
  }
  const st = s.setup_txt && s.setup_txt[lang];
  return (
    <Card delay={Math.min(i, 4) * 0.05} hover={false} glow={i < 3} className={cls("overflow-hidden p-5 md:p-6", i === 0 && "bg-gradient-to-br from-wine-900/50 via-ink-800 to-ink-800")}>
      <div className="flex items-start gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-full bg-gradient-to-r from-wine-500 to-wine-700 px-2 py-0.5 text-[10px] font-bold text-cream-50">#{i + 1}</span>
            <Badge color={srcColor(s.sector || "")}>{secName(s, lang, sectors)}</Badge>
            <TierBadge tier={s.tier} />
          </div>
          <button onClick={() => go("/akcije/" + encodeURIComponent(s.ticker))} className="mt-2 text-left font-display text-[1.5rem] font-bold leading-tight text-cream-50 hover:text-white">
            <span className="link-u">{s.name}</span>
          </button>
          <Brief s={s} lines={3} />
        </div>
        <Gauge value={s.opp} label={lang === "en" ? "score" : "ocena"} size={78} />
      </div>
      <div className="mt-3"><Listings s={s} /></div>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 font-mono text-sm">
        <span className="text-down">{pct(s.dd, 0, lang)} {t("fromHigh")}</span>
        {s.upside ? <span className="text-up">{t("target")} {pct(s.upside, 0, lang)}</span> : null}
        {s.fpe ? <span className="text-cream-300">Fwd P/E {num(s.fpe, 1, lang)}</span> : null}
        {s.peg ? <span className="text-cream-300">PEG {num(s.peg, 2, lang)}</span> : null}
        {s.rsi ? <span className="text-cream-300">RSI {num(s.rsi, 0, lang)}</span> : null}
      </div>
      {st && (
        <div className="mt-3 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold" style={{ color: SETUP_COLOR[s.setup], borderColor: SETUP_COLOR[s.setup] + "55", background: SETUP_COLOR[s.setup] + "12" }}>
          <span className="h-1.5 w-1.5 rounded-full" style={{ background: SETUP_COLOR[s.setup] }} />{st}
        </div>
      )}
      {showChart && prices && <div className="-mx-1 mt-4"><PriceChart data={series(prices, s.ticker)} days={183} height={190} sma /></div>}
      <WhyRisk s={s} />
      <button onClick={() => setOpen((x) => !x)} className="btn-ghost -ml-3 mt-3 text-xs">{open ? "▲" : "▼"} {lang === "en" ? "Checklist, news and position size" : "Provera, vesti i veličina pozicije"}</button>
      {open && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="overflow-hidden">
          <div className="mt-2 rounded-xl border border-ink-600 bg-ink-850/60 p-4"><Checklist items={s.check} /></div>
          {tierSize && s.tier && (
            <div className="mt-3 rounded-xl border border-ink-600 bg-ink-850/60 p-3.5 text-sm text-cream-300">
              <span className="kicker mr-2">{lang === "en" ? "Position size" : "Veličina pozicije"}</span>{tierSize[s.tier][lang === "en" ? 1 : 0]}
              {lang === "en" ? " - buy in parts (DCA), not all at once." : " - kupuj u delovima (DCA), ne sve odjednom."}
            </div>
          )}
          {s.news && s.news.length > 0 && (
            <div className="mt-3">
              <div className="kicker mb-1">{t("newsMove")}</div>
              <ul>
                {s.news.map((n) => (
                  <li key={n.id} onClick={() => app.open(n)} className="group/n flex cursor-pointer items-start gap-2.5 rounded-lg px-2 py-2 transition-colors hover:bg-ink-750">
                    {n.pos ? <ArrowUpRight size={16} className="mt-0.5 shrink-0 text-up" /> : <ArrowDownRight size={16} className="mt-0.5 shrink-0 text-down" />}
                    <span className="text-sm text-cream-200 group-hover/n:text-cream-50">{itTitle(n, lang)} <span className="text-xs text-cream-500">· {n.s} · {timeAgo(n.p, lang)}</span></span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}
    </Card>
  );
}

export function ThemeCard({ th, i = 0, sectors }) {
  const { lang } = useLang();
  const app = useApp();
  const effects = Object.entries(th.effects).sort((a, b) => b[1] - a[1]);
  return (
    <Card delay={i * 0.05} onClick={th.items?.length ? () => app.open(th.items[0]) : undefined} className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="font-display text-[1.08rem] font-semibold text-cream-50">{lang === "en" ? th.en : th.sr}</div>
        <span className="shrink-0 rounded-full bg-wine-900/60 px-2.5 py-1 font-mono text-[11px] text-wine-300">
          {th.n} · {th.prev ? `${num(th.ratio, 1, lang)}×` : lang === "en" ? "new" : "novo"}
        </span>
      </div>
      <p className="mt-1.5 text-sm text-cream-400">{lang === "en" ? th.why_en : th.why_sr}</p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {effects.map(([k, v]) => (
          <span key={k} className={cls("rounded-full border px-2.5 py-0.5 text-[11px]", v > 0 ? "border-up/40 text-up" : "border-down/40 text-down")}>
            {v > 0 ? "↑" : "↓"} {lang === "sr" ? (sectors && sectors[k]) || k : k}
          </span>
        ))}
      </div>
      {th.items && th.items.length > 0 && (
        <ul className="mt-3 border-t border-ink-600 pt-2">
          {th.items.slice(0, 2).map((n) => (
            <li key={n.id} onClick={(event) => { event.stopPropagation(); app.open(n); }} className="cursor-pointer truncate rounded-md px-1 py-1 text-xs text-cream-300 transition hover:bg-ink-750 hover:text-cream-50">
              · {itTitle(n, lang)}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
