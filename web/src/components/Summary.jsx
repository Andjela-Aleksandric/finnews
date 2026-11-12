import { motion } from "framer-motion";
import { FlaskConical, Quote } from "lucide-react";
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
  const f = (p.f && (p.f[lang] || p.f.sr || p.f.en)) || "";
  return (
    <motion.a href={p.u} target="_blank" rel="noreferrer" initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
      transition={{ delay: Math.min(i, 6) * 0.05 }} whileHover={{ y: -3 }}
      className="group block rounded-2xl border border-ink-600/80 bg-gradient-to-b from-ink-750/90 to-ink-800/90 p-4 transition-[border-color,box-shadow] hover:border-wine-500/50 hover:shadow-glow">
      <Quote size={18} className="text-wine-500/70" />
      <p className={cls("mt-1.5 leading-relaxed text-cream-100", big ? "text-[15px]" : "text-sm")}>{f}</p>
      <div className="mt-3 border-t border-ink-600 pt-2.5">
        <div className="line-clamp-2 text-xs text-cream-300 group-hover:text-cream-100">{(lang === "sr" && p.ts) || p.t}</div>
        <div className="mt-1 flex items-center gap-2 text-[11px] text-cream-500">
          <FlaskConical size={11} />{(p.v || "").slice(0, 40)} · {p.y}{p.c ? ` · ❝ ${p.c}` : ""}
        </div>
      </div>
    </motion.a>
  );
}
