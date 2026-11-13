import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { BookMarked, ExternalLink, FlaskConical, GraduationCap, Search, Sparkles } from "lucide-react";
import { countOf, plural, useLang, useT } from "../lib/i18n";
import { cls } from "../lib/fmt";
import { useData } from "../lib/data";
import { periodOpts } from "../lib/sections";
import { PageHead, useRoute } from "../components/Shell";
import { Card, Chip, Empty, Segmented, SectionTitle, Skeleton, Tabs } from "../components/ui";
import { TabPanel } from "../components/ui";
import { FindingCard, findingsIn } from "../components/Summary";

function PaperRow({ p, i }) {
  const { lang } = useLang();
  const [open, setOpen] = useState(false);
  const finding = p.f && (p.f[lang] || p.f.sr || p.f.en);
  const title = (lang === "sr" && p.ts) || p.t;
  const titleOriginal = p.ts && p.t && p.ts !== p.t ? p.t : "";
  return (
    <Card delay={Math.min(i, 8) * 0.03} hover={false} className="research-entry min-w-0 max-w-full overflow-hidden p-4 md:p-5">
      <button type="button" onClick={() => setOpen((x) => !x)} aria-expanded={open}
        className="block w-full rounded-xl text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-gold-500">
        <div className="research-meta flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1 text-xs text-cream-400">
          <span className="font-semibold text-gold-300">{p.v || (lang === "en" ? "Research paper" : "Naučni rad")}</span>
          <span>· {p.y}</span>{p.c ? <span>· {countOf(p.c, "citations", lang)}</span> : null}
        </div>
        <h3 className="mt-2 min-w-0 break-words font-display text-lg font-semibold leading-snug text-cream-50 [overflow-wrap:anywhere] md:text-xl">{title}</h3>
        {titleOriginal && <p className="mt-1 break-words text-sm text-cream-400 [overflow-wrap:anywhere]">{titleOriginal}</p>}
        {p.a && <p className="mt-1 break-words text-sm text-cream-400 [overflow-wrap:anywhere]">{p.a}</p>}
        {!open ? (
          <div className="mt-4 rounded-xl border border-white/15 bg-white/[0.04]/30 p-3.5">
            <div className="stat-label">{lang === "en" ? "Key finding" : "Glavni nalaz"}</div>
            <p className="mt-1.5 text-[15px] leading-relaxed text-cream-100">{finding || (lang === "en" ? "Turn over for the available abstract and study details." : "Okreni karticu za dostupan apstrakt i detalje rada.")}</p>
            <div className="mt-3 text-sm font-medium text-gold-300">{lang === "en" ? "Turn over for abstract and conclusion synthesis ↻" : "Okreni karticu za apstrakt i sintezu zaključka ↻"}</div>
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            {finding && <div className="rounded-xl border border-gold-500/25 bg-gold-500/5 p-3.5">
              <div className="stat-label">{lang === "en" ? "Finding and conclusion synthesis" : "Sinteza nalaza i zaključka"}</div>
              <p className="mt-1.5 text-[15px] leading-relaxed text-cream-100">{finding}</p>
            </div>}
            {p.ab && <div className="rounded-xl border border-ink-600 bg-ink-900/60 p-3.5">
              <div className="stat-label">{lang === "en" ? "Abstract" : "Apstrakt"}</div>
              <p className="mt-1.5 max-h-52 overflow-y-auto whitespace-pre-line text-sm leading-relaxed text-cream-300">{p.ab}</p>
            </div>}
            <div className="text-sm font-medium text-gold-300">{lang === "en" ? "Turn back to the study title ↻" : "Vrati karticu na naziv studije ↻"}</div>
          </div>
        )}
      </button>
      <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-ink-600 pt-3">
        {p.u && <a href={p.u} target="_blank" rel="noreferrer" className="inline-flex min-h-10 items-center gap-2 rounded-lg px-2 text-sm font-medium text-cream-200 transition hover:bg-ink-700 hover:text-white"><ExternalLink size={15} />{lang === "en" ? "Open full paper" : "Otvori ceo rad"}</a>}
        <span className="text-xs text-cream-500">{lang === "en" ? "Synthesis uses the abstract and the conclusion when available." : "Sinteza koristi apstrakt i zaključak kada je dostupan."}</span>
      </div>
    </Card>
  );
}

export default function ResearchPage() {
  const { lang } = useLang();
  const t = useT();
  const { route, setQuery } = useRoute();
  const tab = route.q.tab || "find";
  const days = +(route.q.p || 30);
  const [topic, setTopic] = useState(null);
  const [topicMonths, setTopicMonths] = useState(6);
  const [q, setQ] = useState("");
  const { data: [r] } = useData(["research.json"]);
  const finds = useMemo(() => findingsIn(r, days, 30, topic, q), [r, days, topic, q]);
  const papers = useMemo(() => {
    if (!r) return [];
    const s = q.trim().toLowerCase();
    return r.papers.filter((p) => (!topic || (p.tp || []).includes(topic)) && (!s || (p.t + " " + (p.ts || "") + " " + p.v).toLowerCase().includes(s)))
      .sort((a, b) => (tab === "phd" ? b.ps - a.ps : (b.y || "").localeCompare(a.y || ""))).slice(0, 60);
  }, [r, q, topic, tab]);
  return (
    <div>
      <PageHead title={t("research")} sub={lang === "en" ? "What the studies actually found - each one's key result in a sentence or two - plus the newest papers, the classics and PhD ideas." : "Šta su studije zaista pokazale - ključni rezultat svake u rečenici-dve - uz najnovije radove, klasike i ideje za doktorat."} />
      <Tabs value={tab} onChange={(v) => setQuery({ tab: v })} options={[["find", t("keyFindings"), <Sparkles size={15} key="a" />], ["papers", t("papers"), <FlaskConical size={15} key="b" />],
        ["phd", t("phd"), <GraduationCap size={15} key="c" />], ["classics", t("classics"), <BookMarked size={15} key="d" />]]} />
      <TabPanel k={tab}>
      {!r ? <Skeleton className="h-96" /> : tab === "classics" ? (
        <div className="grid gap-4 md:grid-cols-2">
          {r.classics.map((c, i) => (
            <Card key={c.title} delay={Math.min(i, 8) * 0.03} className="p-5">
              <div className="flex items-baseline gap-3"><span className="font-display text-3xl font-bold italic text-gold-500">{c.year}</span><span className="text-xs text-cream-400">{c.authors} · {c.venue}</span></div>
              <div className="mt-2 font-display text-lg font-semibold text-cream-50">{c.title}</div>
              <p className="mt-1.5 text-sm text-cream-300">{lang === "en" ? c.en : c.sr}</p>
            </Card>
          ))}
        </div>
      ) : (
        <>
          {tab === "phd" && (
            <section className="mb-6">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm leading-relaxed text-cream-300">{lang === "en" ? "Compare how often each topic appears in the indexed papers. The count uses publication dates, not citations." : "Uporedi koliko se često svaka tema pojavljuje u pronađenim radovima. Broj se računa po datumu objave, ne po citatima."}</p>
                <label className="inline-flex items-center gap-2 text-sm text-cream-300">
                  <span>{lang === "en" ? "Period" : "Period"}</span>
                  <select className="field min-h-10 w-auto border-ink-500 bg-ink-950 px-3 py-2 text-sm transition hover:border-white/25 focus:border-gold-400" value={topicMonths} onChange={(e) => setTopicMonths(Number(e.target.value))}>
                    {[1, 3, 6, 12, 24].map((months) => <option key={months} value={months}>{months} {lang === "en" ? (months === 1 ? "month" : "months") : (months === 1 ? "mesec" : "meseci")}</option>)}
                  </select>
                </label>
              </div>
              {(() => {
                const cutoff = new Date();
                cutoff.setMonth(cutoff.getMonth() - topicMonths);
                const cutoffDay = cutoff.toISOString().slice(0, 10);
                const counts = r.topics.map((tp) => ({ tp, count: r.papers.filter((paper) => (paper.tp || []).includes(tp.q) && (paper.y || "") >= cutoffDay).length }))
                  .sort((a, b) => b.count - a.count || (lang === "en" ? a.tp.en.localeCompare(b.tp.en) : a.tp.sr.localeCompare(b.tp.sr)));
                const maxCount = Math.max(1, ...counts.map((item) => item.count));
                return <div className="space-y-2">
                  {counts.map(({ tp, count }, index) => (
                    <motion.div key={tp.q} initial={{ opacity: 0, x: -8 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ delay: Math.min(index, 8) * 0.035 }}
                      whileHover={{ x: 3 }} className="group/topic grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-2 rounded-xl border border-ink-600/80 bg-ink-950/90 p-3 transition-[border-color,background-color,box-shadow] hover:border-gold-500/45 hover:bg-ink-900 hover:shadow-[0_8px_24px_rgba(0,0,0,.24)] sm:grid-cols-[minmax(180px,260px)_minmax(0,1fr)_auto]">
                      <span className="min-w-0 text-sm font-medium text-cream-100 transition-colors group-hover/topic:text-white">{lang === "en" ? tp.en : tp.sr}</span>
                      <span className="col-span-2 h-2 overflow-hidden rounded-full bg-ink-700 sm:col-span-1">
                        <motion.i initial={{ width: 0 }} whileInView={{ width: `${(count / maxCount) * 100}%` }} viewport={{ once: true }} transition={{ duration: 0.65, delay: Math.min(index, 8) * 0.035, ease: "easeOut" }}
                          className="block h-full rounded-full bg-gold-500" />
                      </span>
                      <span className="min-w-[88px] text-right font-mono text-sm font-semibold text-gold-300">{count} {lang === "en" ? (count === 1 ? "study" : "studies") : (count === 1 ? "studija" : "studija")}</span>
                    </motion.div>
                  ))}
                </div>;
              })()}
            </section>
          )}
          <div className="mb-4 flex flex-wrap items-center gap-2">
            {tab === "find" && <Segmented size="sm" value={days} onChange={(v) => setQuery({ p: v })} options={periodOpts(t)} />}
            <div className="relative min-w-[220px] flex-1">
              <Search size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-cream-500" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="neural network, fuzzy, portfolio, LLM..." className="field pl-10" />
            </div>
          </div>
          {r.topics.length > 0 && (
            <div className="no-scrollbar mb-6 flex gap-1.5 overflow-x-auto pb-1">
              <Chip active={!topic} onClick={() => setTopic(null)}>{lang === "en" ? "All topics" : "Sve teme"}</Chip>
              {r.topics.map((tp) => <Chip key={tp.q} active={topic === tp.q} onClick={() => setTopic(tp.q)}>{lang === "en" ? tp.en : tp.sr}</Chip>)}
            </div>
          )}
          {tab === "find" ? (finds.length ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{finds.map((p, i) => <FindingCard key={p.id} p={p} i={i} big />)}</div>
            : <Empty>{lang === "en" ? "Nothing for this period yet - try a longer one." : "Za ovaj period još nema nalaza - probaj duži."}</Empty>)
            : papers.length ? <div className={cls("grid gap-3", "md:grid-cols-2")}>{papers.map((p, i) => <PaperRow key={p.id} p={p} i={i} />)}</div> : <Empty>{t("nothing")}</Empty>}
        </>
      )}
      </TabPanel>
    </div>
  );
}
