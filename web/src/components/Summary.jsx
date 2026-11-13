import { useState } from "react";
import { motion } from "framer-motion";
import { ExternalLink, FlaskConical, Quote } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
import { cls, num } from "../lib/fmt";
import { themeTrend } from "../lib/sections";
import { NewsRow } from "./News";
import { Card, Empty } from "./ui";

export function PeriodSummary({ block, items, n = 7, title }) {
  const { lang } = useLang();
  const t = useT();
  if (!block || !block.top || !block.top.length) return <Empty>{t("noNews")}</Empty>;
  const chg = block.prev ? block.n / block.prev - 1 : null;
  return (
    <Card hover={false} className="p-5 md:p-6">
      <div className="kicker mb-2">{title || t("summary")}</div>
      <ol className="-mx-3">
        {block.top.slice(0, n).map(([id, x], i) => items[id] && <NewsRow key={id} it={items[id]} extra={x} n={i} />)}
      </ol>
      {block.themes && block.themes.length > 0 && (
        <>
          <div className="kicker mb-2 mt-4">{t("themesTrend")}</div>
          <div className="flex flex-wrap gap-1.5">
            {block.themes.map(([sr, en, c, p], i) => {
              const tr = themeTrend(c, p, lang);
              return (
                <motion.span key={sr} initial={{ opacity: 0, scale: 0.9 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} transition={{ delay: i * 0.04 }}
                  className="inline-flex items-center gap-1.5 rounded-full border border-ink-500 bg-ink-850 px-3 py-1 text-xs text-cream-200 transition hover:-translate-y-px hover:border-wine-500/60">
                  {lang === "en" ? en : sr} <span className="text-cream-500">{c}</span>
                  <b className={cls("font-mono text-[10px]", tr.up ? "text-up" : "text-down")}>{tr.txt}</b>
                </motion.span>
              );
            })}
          </div>
        </>
      )}
      <div className="mt-4 text-xs text-cream-500">
        {block.n} {t("stories")} · {block.nsrc} {t("sources")}
        {chg !== null && <span className={chg >= 0 ? "text-up" : "text-down"}> · {chg >= 0 ? "+" : ""}{num(chg * 100, 0, lang)}% {lang === "en" ? "vs previous period" : "u odnosu na prethodni period"}</span>}
      </div>
    </Card>
  );
}

export function findingsIn(research, days, limit = 6, topic = null, q = "") {
  if (!research) return [];
  const cut = new Date(Date.now() - days * 864e5).toISOString().slice(0, 10);
  const s = q.trim().toLowerCase();
  return research.papers
    .filter((p) => p.f && (p.f.sr || p.f.en) && (p.y || "") >= cut && (!topic || (p.tp || []).includes(topic)) &&
      (!s || (p.t + " " + (p.ts || "") + " " + (p.f.sr || "") + " " + (p.f.en || "")).toLowerCase().includes(s)))
    .sort((a, b) => (b.ps || 0) + (b.c || 0) / 200 - (a.ps || 0) - (a.c || 0) / 200)
    .slice(0, limit);
}

export function FindingCard({ p, i = 0, big = false }) {
  const { lang } = useLang();
  const [open, setOpen] = useState(false);
  const finding = (p.f && (p.f[lang] || p.f.sr || p.f.en)) || "";
  const title = (lang === "sr" && p.ts) || p.t;
  const originalTitle = p.ts && p.t && p.ts !== p.t ? p.t : "";
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
      transition={{ delay: Math.min(i, 6) * 0.05 }} whileHover={{ y: -2 }}
      className="group rounded-2xl border border-ink-600/80 bg-gradient-to-b from-ink-750/95 to-ink-800/95 p-4 transition-[border-color,box-shadow] hover:border-wine-500/50 hover:shadow-glow">
      <button type="button" onClick={() => setOpen((x) => !x)} aria-expanded={open}
        className="block w-full rounded-xl text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-wine-400">
        <div className="flex items-center gap-2 text-xs text-cream-400"><FlaskConical size={14} className="text-wine-400" />
          <span className="truncate">{p.v || (lang === "en" ? "Research paper" : "Naučni rad")}</span><span>· {p.y}</span>{p.c ? <span>· {p.c} {lang === "en" ? "citations" : "citata"}</span> : null}
        </div>
        <h3 className={cls("mt-2 font-display font-semibold leading-snug text-cream-50", big ? "text-lg md:text-xl" : "text-base")}>{title}</h3>
        {originalTitle && <p className="mt-1 text-sm leading-snug text-cream-400">{originalTitle}</p>}
        {!open ? (
          <>
            <div className="mt-3 rounded-xl border border-wine-500/25 bg-wine-950/30 p-3.5">
              <div className="stat-label">{lang === "en" ? "Key finding" : "Glavni nalaz"}</div>
              <p className={cls("mt-1.5 leading-relaxed text-cream-100", big ? "text-[15px]" : "text-sm")}>{finding}</p>
            </div>
            <div className="mt-3 text-sm font-medium text-gold-300">{lang === "en" ? "Turn over for abstract and conclusion synthesis ↻" : "Okreni za apstrakt i sintezu zaključka ↻"}</div>
          </>
        ) : (
          <div className="mt-3 space-y-3">
            <div className="rounded-xl border border-gold-500/25 bg-gold-500/5 p-3.5">
              <div className="stat-label">{lang === "en" ? "Finding and conclusion synthesis" : "Sinteza nalaza i zaključka"}</div>
              <p className="mt-1.5 text-[15px] leading-relaxed text-cream-100">{finding}</p>
            </div>
            {p.ab && <div className="rounded-xl border border-ink-600 bg-ink-900/60 p-3.5">
              <div className="stat-label">{lang === "en" ? "Abstract" : "Apstrakt"}</div>
              <p className="mt-1.5 max-h-52 overflow-y-auto whitespace-pre-line text-sm leading-relaxed text-cream-300">{p.ab}</p>
            </div>}
            <div className="text-sm font-medium text-gold-300">{lang === "en" ? "Turn back to the study title ↻" : "Vrati na naziv studije ↻"}</div>
          </div>
        )}
      </button>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-ink-600 pt-3">
        <span className="text-xs text-cream-500">{lang === "en" ? "Abstract and conclusion synthesis where available." : "Sinteza apstrakta i zaključka kada su dostupni."}</span>
        <a href={p.u} target="_blank" rel="noreferrer" className="inline-flex min-h-10 shrink-0 items-center gap-2 rounded-lg px-2 text-sm font-medium text-cream-200 transition hover:bg-ink-700 hover:text-gold-300">
          <ExternalLink size={15} />{lang === "en" ? "Open paper" : "Otvori rad"}
        </a>
      </div>
    </motion.div>
  );
}