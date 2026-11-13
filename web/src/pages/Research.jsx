import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { BookMarked, ExternalLink, FlaskConical, GraduationCap, Search, Sparkles } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
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
        className="block w-full rounded-xl text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-wine-400">
        <div className="research-meta flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1 text-xs text-cream-400">
          <span className="font-semibold text-gold-300">{p.v || (lang === "en" ? "Research paper" : "Naučni rad")}</span>
          <span>· {p.y}</span>{p.c ? <span>· {p.c} {lang === "en" ? "citations" : "citata"}</span> : null}
        </div>
        <h3 className="mt-2 min-w-0 break-words font-display text-lg font-semibold leading-snug text-cream-50 [overflow-wrap:anywhere] md:text-xl">{title}</h3>
        {titleOriginal && <p className="mt-1 break-words text-sm text-cream-400 [overflow-wrap:anywhere]">{titleOriginal}</p>}
        {p.a && <p className="mt-1 break-words text-sm text-cream-400 [overflow-wrap:anywhere]">{p.a}</p>}
        {!open ? (
          <div className="mt-4 rounded-xl border border-wine-500/25 bg-wine-950/30 p-3.5">
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
        {p.u && <a href={p.u} target="_blank" rel="noreferrer" className="inline-flex min-h-10 items-center gap-2 rounded-lg px-2 text-sm font-medium text-cream-200 transition hover:bg-ink-700 hover:text-gold-300"><ExternalLink size={15} />{lang === "en" ? "Open full paper" : "Otvori ceo rad"}</a>}
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
      <PageHead title={t("research")} sub={lang === "en" ? "What studies found - the key result of each in one or two sentences - plus the newest papers, classics and PhD ideas." : "Šta su studije pronašle - ključni rezultat svake u jednoj-dve rečenice - plus najnoviji radovi, klasici i ideje za doktorat."} />
      <Tabs value={tab} onChange={(v) => setQuery({ tab: v })} options={[["find", t("keyFindings"), <Sparkles size={15} key="a" />], ["papers", t("papers"), <FlaskConical size={15} key="b" />],
        ["phd", t("phd"), <GraduationCap size={15} key="c" />], ["classics", t("classics"), <BookMarked size={15} key="d" />]]} />
      <TabPanel k={tab}>
      {!r ? <Skeleton className="h-96" /> : tab === "classics" ? (
        <div className="grid gap-4 md:grid-cols-2">
          {r.classics.map((c, i) => (
            <Card key={c.title} delay={Math.min(i, 8) * 0.03} className="p-5">
              <div className="flex items-baseline gap-3"><span className="font-display text-3xl font-bold italic text-wine-500">{c.year}</span><span className="text-xs text-cream-400">{c.authors} · {c.venue}</span></div>
              <div className="mt-2 font-display text-lg font-semibold text-cream-50">{c.title}</div>
              <p className="mt-1.5 text-sm text-cream-300">{lang === "en" ? c.en : c.sr}</p>
            </Card>
          ))}
        </div>
      ) : (
        <>
          {tab === "phd" && (
            <section className="mb-6">
              <SectionTitle>{lang === "en" ? "Topic frequency in recent studies" : "Učestalost tema u novijim studijama"}</SectionTitle>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {r.topics.map((tp) => {
                  const count = r.papers.filter((paper) => (paper.tp || []).includes(tp.q)).length;
                  return (
                    <Card key={tp.q} hover={false} className="flex items-center justify-between gap-3 p-3">
                      <span className="min-w-0 text-sm text-cream-200">{lang === "en" ? tp.en : tp.sr}</span>
                      <span className="shrink-0 font-mono text-sm text-gold-400">{count} {lang === "en" ? "studies" : "studija"}</span>
                    </Card>
                  );
                })}
              </div>
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
            : <Empty>{lang === "en" ? "No findings for this period - try a longer one." : "Nema nalaza za ovaj period - probaj duži."}</Empty>)
            : papers.length ? <div className={cls("grid gap-3", "md:grid-cols-2")}>{papers.map((p, i) => <PaperRow key={p.id} p={p} i={i} />)}</div> : <Empty>{t("nothing")}</Empty>}
        </>
      )}
      </TabPanel>
    </div>
  );
}
