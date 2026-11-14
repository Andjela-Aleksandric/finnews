import { useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { BookMarked, ExternalLink, FlaskConical, GraduationCap, Search, Sparkles } from "lucide-react";
import { countOf, plural, useLang, useT } from "../lib/i18n";
import { cls } from "../lib/fmt";
import { useData } from "../lib/data";
import { periodOpts } from "../lib/sections";
import { PageHead, useRoute } from "../components/Shell";
import { Card, Chip, Empty, Segmented, SectionTitle, Select, Skeleton, Tabs } from "../components/ui";
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
          <div className="mt-4 rounded-xl border border-white/15 bg-white/[0.04] p-3.5">
            <div className="stat-label">{lang === "en" ? "Key finding" : "Glavni nalaz"}</div>
            <p className="mt-1.5 text-[15px] leading-relaxed text-cream-100">{finding || (lang === "en" ? "Turn over for the available abstract and study details." : "Okreni karticu za dostupan apstrakt i detalje rada.")}</p>
            <div className="flip-hint mt-4">{lang === "en" ? "Turn over for abstract and conclusion synthesis ↻" : "Okreni karticu za apstrakt i sintezu zaključka ↻"}</div>
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
            <div className="flip-hint">{lang === "en" ? "Turn back to the study title ↻" : "Vrati karticu na naziv studije ↻"}</div>
          </div>
        )}
      </button>
      <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-ink-600 pt-3">
        {p.u && <a href={p.u} target="_blank" rel="noreferrer" className="inline-flex min-h-10 items-center gap-2 rounded-lg px-2 text-sm font-medium text-cream-200 transition hover:bg-ink-700 hover:text-cream-50"><ExternalLink size={15} />{lang === "en" ? "Open full paper" : "Otvori ceo rad"}</a>}
        <span className="text-xs text-cream-500">{lang === "en" ? "Synthesis uses the abstract and the conclusion when available." : "Sinteza koristi apstrakt i zaključak kada je dostupan."}</span>
      </div>
    </Card>
  );
}

const PERIOD_MONTHS = [1, 3, 6, 12, 24];
const studWord = (n) => { const d = n % 10, h = n % 100; return d >= 2 && d <= 4 && (h < 12 || h > 14) ? "studije" : "studija"; };
function monthsAgo(m) {
  const d = new Date();
  d.setMonth(d.getMonth() - m);
  return d.toISOString().slice(0, 10);
}
function monthLabel(m, lang) {
  if (lang === "en") return m === 12 ? "year" : m === 24 ? "2 years" : `${m} month${m === 1 ? "" : "s"}`;
  return m === 1 ? "mesec dana" : m === 12 ? "godinu dana" : m === 24 ? "dve godine" : `${m} meseca`.replace("6 meseca", "6 meseci");
}
const fmtN = (n, lang) => new Intl.NumberFormat(lang === "en" ? "en-US" : "sr-Latn-RS").format(n);

function TopicPopularity({ r, lang, months, setMonths, topic, onPick }) {
  const [hov, setHov] = useState(null);
  const cut = monthsAgo(months);
  const rows = r.topics.map((tp) => {
    const n = tp.n && tp.n[String(months)];
    const local = r.papers.filter((p) => (p.tp || []).includes(tp.q) && (p.y || "") >= cut).length;
    return { tp, count: n ? n[0] : local, prev: n ? n[1] : null, local, src: n ? "oa" : "local" };
  }).sort((a, b) => b.count - a.count);
  const max = Math.max(1, ...rows.map((x) => x.count));
  const total = rows.reduce((a, x) => a + x.count, 0) || 1;
  const fromOA = rows.some((x) => x.src === "oa");
  const L = (a, b) => (lang === "en" ? b : a);
  return (
    <section className="topic-pop mb-6">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-display text-lg font-semibold text-cream-50">{L("Popularnost tema", "Topic popularity")}</h3>
          <p className="mt-0.5 text-xs text-cream-400">{fromOA
            ? L(`Broj objavljenih radova u OpenAlex bazi za poslednjih ${monthLabel(months, "sr")}, uz promenu u odnosu na prethodni period iste dužine. Klikni na temu da vidiš njene studije.`, `Papers published in OpenAlex over the last ${monthLabel(months, "en")}, with the change vs the previous period of the same length. Click a topic to see its studies.`)
            : L("Broj pronađenih radova po temi. Klikni na temu da vidiš njene studije.", "Papers found per topic. Click a topic to see its studies.")}</p>
        </div>
        <Segmented size="sm" value={months} onChange={(v) => setMonths(Number(v))}
          options={PERIOD_MONTHS.map((m) => [m, lang === "en" ? (m >= 12 ? `${m / 12}y` : `${m}m`) : (m >= 12 ? `${m / 12} god.` : `${m} mes.`)])} />
      </div>
      <div className="space-y-1" onMouseLeave={() => setHov(null)}>
        {rows.map((row, i) => {
          const on = topic === row.tp.q, h = hov === row.tp.q;
          const ch = row.prev ? row.count / row.prev - 1 : null;
          return (
            <motion.button type="button" key={row.tp.q} layout="position" transition={{ type: "spring", stiffness: 380, damping: 36 }}
              onPointerEnter={(e) => e.pointerType === "mouse" && setHov(row.tp.q)} onFocus={() => setHov(row.tp.q)} onClick={() => onPick(row.tp.q)} aria-pressed={on}
              className={cls("topic-row grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-1.5 text-left sm:grid-cols-[minmax(220px,360px)_minmax(0,1fr)_auto]", on && "is-sel", h && "is-hov")}>
              <span className="flex min-w-0 items-center gap-2">
                <span className="w-5 shrink-0 text-right font-mono text-[11px] text-cream-500">{i + 1}</span>
                <span className="text-sm font-medium leading-snug text-cream-100">{lang === "en" ? row.tp.en : row.tp.sr}</span>
              </span>
              <span className="topic-bar col-span-2 sm:col-span-1">
                <motion.i initial={{ width: 0 }} animate={{ width: `${(row.count / max) * 100}%` }} transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }} />
              </span>
              <span className="flex min-w-[118px] items-center justify-end gap-2 text-right">
                <span className="font-mono text-sm font-semibold text-cream-50">{fmtN(row.count, lang)}</span>
                {ch !== null && Number.isFinite(ch) && <span className={cls("font-mono text-[11px]", ch >= 0 ? "text-up" : "text-down")}>{ch >= 0 ? "▲" : "▼"}{Math.abs(Math.round(ch * 100))}%</span>}
              </span>
              <AnimatePresence initial={false}>
                {(h || on) && <motion.span initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}
                  className="col-span-2 overflow-hidden text-xs text-cream-400 sm:col-span-3 sm:pl-7">
                  {L(`${Math.round(row.count / total * 100)}% svih radova u ovim temama`, `${Math.round(row.count / total * 100)}% of all papers across these topics`)}
                  {row.prev !== null ? L(` · prethodni period: ${fmtN(row.prev, "sr")}`, ` · previous period: ${fmtN(row.prev, "en")}`) : ""}
                  {L(` · u FinNews-u: ${row.local} izdvojenih studija`, ` · in FinNews: ${row.local} selected studies`)}
                  <b className="ml-2 font-medium text-wine-300">{on ? L("prikazane ispod ↓", "shown below ↓") : L("klikni za studije →", "click for studies →")}</b>
                </motion.span>}
              </AnimatePresence>
            </motion.button>
          );
        })}
      </div>
    </section>
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
  const listRef = useRef(null);
  const { data: [r] } = useData(["research.json"]);
  const [more, setMore] = useState(24);
  const allFinds = useMemo(() => findingsIn(r, days, 100000, topic, q), [r, days, topic, q]);
  const finds = allFinds.slice(0, more);
  const papers = useMemo(() => {
    if (!r) return [];
    const s = q.trim().toLowerCase();
    const cut = tab === "phd" ? monthsAgo(topicMonths) : "";
    return r.papers.filter((p) => (!topic || (p.tp || []).includes(topic)) && (!cut || (p.y || "") >= cut) && (!s || (p.t + " " + (p.ts || "") + " " + p.v).toLowerCase().includes(s)))
      .sort((a, b) => (tab === "phd" ? b.ps - a.ps : (b.y || "").localeCompare(a.y || ""))).slice(0, 60);
  }, [r, q, topic, tab, topicMonths]);
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
          {tab === "phd" && <TopicPopularity r={r} lang={lang} months={topicMonths} setMonths={setTopicMonths} topic={topic}
            onPick={(q2) => { setTopic((x) => (x === q2 ? null : q2)); setTimeout(() => listRef.current && listRef.current.scrollIntoView({ behavior: "smooth", block: "start" }), 60); }} />}
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
          <div ref={listRef} className="scroll-mt-24" />
          {tab === "phd" && topic && (() => { const tp = r.topics.find((x) => x.q === topic); return tp && (
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3">
              <span className="text-sm text-cream-200">{lang === "en" ? "Studies on" : "Studije o temi"} <b className="text-cream-50">{lang === "en" ? tp.en : tp.sr}</b> · {lang === "en" ? `last ${monthLabel(topicMonths, "en")}` : `poslednjih ${monthLabel(topicMonths, "sr")}`} · {papers.length}</span>
              <button type="button" onClick={() => setTopic(null)} className="btn-ghost text-xs">{lang === "en" ? "Show all topics" : "Prikaži sve teme"} ×</button>
            </div>); })()}
          {tab === "find" && allFinds.length > 0 && <p className="mb-3 text-sm text-cream-300"><b className="font-mono text-cream-50">{allFinds.length}</b> {lang === "en" ? (days === 1 ? "studies with a key finding in the last 24 hours" : `studies with a key finding in the last ${days} days`) : `${studWord(allFinds.length)} sa ključnim nalazom ${days === 1 ? "u poslednja 24 sata" : `u poslednjih ${days} dana`}`}{allFinds.length > finds.length ? (lang === "en" ? ` · showing ${finds.length}` : ` · prikazano ${finds.length}`) : ""}</p>}
          {tab === "find" ? (finds.length ? <><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{finds.map((p, i) => <FindingCard key={p.id} p={p} i={i} big />)}</div>
            {allFinds.length > finds.length && <div className="mt-5 flex justify-center"><button type="button" className="btn" onClick={() => setMore((x) => x + 24)}>{lang === "en" ? "Show more" : "Prikaži još"}</button></div>}</>
            : <Empty>{lang === "en" ? "Nothing for this period yet - try a longer one." : "Za ovaj period još nema nalaza - probaj duži."}</Empty>)
            : papers.length ? <div className={cls("grid gap-3", "md:grid-cols-2")}>{papers.map((p, i) => <PaperRow key={p.id} p={p} i={i} />)}</div> : <Empty>{t("nothing")}</Empty>}
        </>
      )}
      </TabPanel>
    </div>
  );
}
