import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { BookMarked, ExternalLink, FlaskConical, GraduationCap, Search, Sparkles } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
import { cls } from "../lib/fmt";
import { useData } from "../lib/data";
import { periodOpts } from "../lib/sections";
import { PageHead, useRoute } from "../components/Shell";
import { Card, Chip, Empty, Segmented, Skeleton, Tabs } from "../components/ui";
import { TabPanel } from "../components/ui";
import { FindingCard, findingsIn } from "../components/Summary";

function PaperRow({ p, i }) {
  const { lang } = useLang();
  const [open, setOpen] = useState(false);
  const f = p.f && (p.f[lang] || p.f.sr || p.f.en);
  return (
    <Card delay={Math.min(i, 8) * 0.03} className="p-4" onClick={() => setOpen((x) => !x)}>
      <div className="flex items-center gap-2 text-[11px] text-cream-400">
        <span className="truncate">{p.v}</span><span>· {p.y}</span>{p.c ? <span className="text-gold-500">· ❝ {p.c}</span> : null}
      </div>
      <div className="mt-1.5 font-display text-[1.02rem] font-semibold leading-snug text-cream-50">{(lang === "sr" && p.ts) || p.t}</div>
      {f && <p className="mt-2 text-sm text-cream-300"><span className="mr-1 text-xs font-bold uppercase tracking-wider text-wine-400">{lang === "en" ? "Finding" : "Nalaz"}</span>{f}</p>}
      {open && p.ab && <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-3 border-t border-ink-600 pt-3 text-sm leading-relaxed text-cream-400">{p.ab}</motion.p>}
      <div className="mt-3 flex items-center gap-3 text-xs">
        <a href={p.u} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()} className="inline-flex items-center gap-1 text-cream-300 hover:text-wine-400"><ExternalLink size={12} />{lang === "en" ? "Open paper" : "Otvori rad"}</a>
        {p.ab && <span className="text-cream-500">{open ? "▲" : "▼"} {lang === "en" ? "abstract" : "apstrakt"}</span>}
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
