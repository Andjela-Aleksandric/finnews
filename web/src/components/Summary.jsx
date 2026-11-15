import { useState } from "react";
import { motion } from "framer-motion";
import { ExternalLink, FlaskConical, Quote, Sparkles } from "lucide-react";
import { countOf, plural, useLang, useT } from "../lib/i18n";
import { cls, itTitle, num } from "../lib/fmt";
import { themeTrend } from "../lib/sections";
import { NewsRow, useApp } from "./News";
import { Card, Empty } from "./ui";

// pregled perioda koji je napisao besplatan lokalni AI; [1][3] su vesti na koje se tačka oslanja (klik ih otvara)
export function AiDigest({ digest, items, onRef, titleOf, note }) {
  const { lang } = useLang();
  const app = useApp();
  if (!digest || !digest.en || !digest.en.length) return null;
  const pts = (lang === "en" ? digest.en : digest.sr) || digest.en;
  return (
    <div className="ai-digest mb-5">
      <div className="mb-2 flex items-center gap-2">
        <span className="ai-badge"><Sparkles size={12} />{lang === "en" ? "AI overview" : "AI pregled"}</span>
        {note && <span className="text-[11px] text-cream-500">{note}</span>}
      </div>
      <ol className="-mx-3">
        {pts.map((p, i) => {
          const refs = [...p.matchAll(/\[(\d+)\]/g)].map((m) => +m[1]);
          const text = p.replace(/\s*(\[\d+\])+\s*\.?$/, "").replace(/\s*\[\d+\]/g, "").replace(/^\s*\d+[.)]\s*/, "").replace(/^\s*\p{Ll}/u, (c) => c.toUpperCase());
          const linked = refs.map((r) => { const id = digest.ids && digest.ids[r - 1]; return [r, id && items && items[id]]; }).filter(([, it]) => it);
          const open = (it) => (onRef ? onRef(it) : app.open(it));
          const first = linked.length ? linked[0][1] : null;
          return <motion.li key={i} initial={{ opacity: 0, x: -8 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ delay: Math.min(i, 8) * 0.04 }}
            onClick={first ? () => open(first) : undefined} role={first ? "button" : undefined} tabIndex={first ? 0 : undefined}
            onKeyDown={first ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(first); } } : undefined}
            className={cls("ai-point row-accent group flex min-w-0 gap-3 rounded-xl px-3 py-3 transition-colors hover:bg-white/[0.03] sm:gap-4", first && "cursor-pointer")}>
            <span className="w-6 shrink-0 pt-0.5 font-display text-xl font-bold italic text-gold-500/80 transition group-hover:text-cream-50">{i + 1}</span>
            <div className="min-w-0 text-[15px] leading-snug text-cream-100 transition-colors group-hover:text-cream-50">
              <span className="link-u">{text}</span>
              {linked.map(([r, it]) => <button type="button" key={r} onClick={(e) => { e.stopPropagation(); open(it); }} className="ai-ref"
                data-tip={titleOf ? titleOf(it) : itTitle(it, lang)} aria-label={titleOf ? titleOf(it) : itTitle(it, lang)}>{r}</button>)}
            </div>
          </motion.li>;
        })}
      </ol>
    </div>
  );
}

export function PeriodSummary({ block, items, n = 7, title, digest }) {
  const { lang } = useLang();
  const t = useT();
  if (!block || !block.top || !block.top.length) return <Empty>{t("noNews")}</Empty>;
  const chg = block.prev ? block.n / block.prev - 1 : null;
  return (
    <Card hover={false} className="p-5 md:p-6">
      <AiDigest digest={digest} items={items} />
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
                  className="inline-flex items-center gap-1.5 rounded-full border border-ink-500 bg-ink-850 px-3 py-1 text-xs text-cream-200 transition hover:-translate-y-px hover:border-white/25">
                  {lang === "en" ? en : sr} <span className="text-cream-500">{c}</span>
                  <b className={cls("font-mono text-[10px]", tr.up ? "text-up" : "text-down")}>{tr.txt}</b>
                </motion.span>
              );
            })}
          </div>
        </>
      )}
      <div className="mt-4 text-xs text-cream-500">
        {countOf(block.n, "stories", lang)} · {countOf(block.nsrc, "sources", lang)}
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

// nalaz: prvo rezultat, zatim (posle praznog reda) ključni doprinos sa istaknutom oznakom
export function FindingText({ text, className, clamp = false }) {
  const { lang } = useLang();
  const [res, rest] = String(text || "").split(/\n\n/);
  const m = rest && rest.match(/^([^:]{3,30}):\s*([\s\S]*)$/);
  const idea = m ? m[2] : rest;
  if (!idea) return <div className={className}><p className={cls(clamp && "line-clamp-6")}>{res}</p></div>;
  return <div className={cls(className, "space-y-2.5")}>
    <p className="finding-part"><b>{lang === "en" ? "Main idea" : "Glavna ideja"}</b><span className={cls(clamp && "line-clamp-3")}>{idea}</span></p>
    <p className="finding-part is-result"><b>{lang === "en" ? "Conclusion" : "Zaključak"}</b><span className={cls(clamp && "line-clamp-4")}>{res}</span></p>
  </div>;
}

export function FindingCard({ p, i = 0, big = false }) {
  const { lang } = useLang();
  const [open, setOpen] = useState(false);
  const finding = (p.f && (p.f[lang] || p.f.sr || p.f.en)) || "";
  const title = (lang === "sr" && p.ts) || p.t;
  const originalTitle = p.ts && p.t && p.ts !== p.t ? p.t : "";
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
      transition={{ delay: Math.min(i, 6) * 0.05 }}
      className="research-entry group flex h-full min-w-0 max-w-full flex-col overflow-hidden rounded-2xl border border-ink-600/80 bg-ink-850 p-4 transition-[border-color,box-shadow] hover:border-white/25">
      <button type="button" onClick={() => setOpen((x) => !x)} aria-expanded={open}
        className="flex w-full flex-1 flex-col rounded-xl text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-gold-500">
        <div className="research-meta flex min-w-0 flex-wrap items-center gap-2 text-xs text-cream-400"><FlaskConical size={14} className="text-gold-500" />
          <span className="truncate">{p.v || (lang === "en" ? "Research paper" : "Naučni rad")}</span><span>· {p.y}</span>{p.c ? <span>· {countOf(p.c, "citations", lang)}</span> : null}
        </div>
        <h3 title={title} className={cls("mt-2 min-w-0 break-words font-display font-semibold leading-snug text-cream-50 [overflow-wrap:anywhere]", !open && "line-clamp-3", big ? "text-lg md:text-xl" : "text-base")}>{title}</h3>
        {originalTitle && <p className={cls("mt-1 break-words text-sm leading-snug text-cream-400 [overflow-wrap:anywhere]", !open && "line-clamp-2")}>{originalTitle}</p>}
        {!open ? (
          <>
            <div className="mt-3 flex-1 rounded-xl border border-white/15 bg-white/[0.04] p-3.5">
              <FindingText clamp text={finding} className={cls("break-words leading-relaxed text-cream-100 [overflow-wrap:anywhere]", big ? "text-[15px]" : "text-sm")} />
            </div>
            <div className="flip-hint mt-4">{lang === "en" ? "Abstract and details ↻" : "Apstrakt i detalji ↻"}</div>
          </>
        ) : (
          <div className="mt-3 space-y-3">
            <div className="rounded-xl border border-gold-500/25 bg-gold-500/5 p-3.5">
              <div className="stat-label">{lang === "en" ? "What the study found" : "Šta je studija pokazala"}</div>
              <FindingText text={finding} className="mt-1.5 text-[15px] leading-relaxed text-cream-100" />
            </div>
            {p.ab && <div className="rounded-xl border border-ink-600 bg-ink-900/60 p-3.5">
              <div className="stat-label">{lang === "en" ? "Abstract" : "Apstrakt"}</div>
              <p className="mt-1.5 max-h-52 overflow-y-auto whitespace-pre-line text-sm leading-relaxed text-cream-300">{p.ab}</p>
            </div>}
            <div className="flip-hint">{lang === "en" ? "Click to return to the key finding ↻" : "Vrati se na glavni nalaz ↻"}</div>
          </div>
        )}
      </button>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-ink-600 pt-3">
        <span className="text-xs text-cream-500">{lang === "en" ? "From the abstract and conclusion" : "Iz apstrakta i zaključka"}</span>
        <a href={p.u} target="_blank" rel="noreferrer" className="inline-flex min-h-10 shrink-0 items-center gap-2 rounded-lg px-2 text-sm font-medium text-cream-200 transition hover:bg-ink-700 hover:text-cream-50">
          <ExternalLink size={15} />{lang === "en" ? "Open paper" : "Otvori rad"}
        </a>
      </div>
    </motion.div>
  );
}