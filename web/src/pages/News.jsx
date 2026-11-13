import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Filter, Search, SlidersHorizontal, X } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
import { cls, itSum, itTitle } from "../lib/fmt";
import { dedupe, relevance, useData, useNews } from "../lib/data";
import { SECTIONS, periodOpts } from "../lib/sections";
import { PageHead, useRoute } from "../components/Shell";
import { NewsGrid, useApp } from "../components/News";
import { Chip, Empty, Segmented, SectionTitle, Skeleton } from "../components/ui";
import { FindingCard, PeriodSummary, findingsIn } from "../components/Summary";

export default function NewsPage() {
  const { lang } = useLang();
  const t = useT();
  const app = useApp();
  const { route, setQuery } = useRoute();
  const sec = route.q.sec || "fin";
  const days = +(route.q.p || 1);
  const [q, setQ] = useState("");
  const [sort, setSort] = useState("rel");
  const [show, setShow] = useState(20);
  const [filters, setFilters] = useState(false);
  const [srcs, setSrcs] = useState([]);
  const [onlyFull, setOnlyFull] = useState(false);
  const [multi, setMulti] = useState(false);
  const { data: [periods, research] } = useData(["periods.json", "research.json"]);
  const { loading, items } = useNews(days);
  useEffect(() => { setShow(20); }, [sec, days, q, sort]);
  useEffect(() => {
    if (route.q.open && items.length) {
      const it = items.find((x) => x.id === route.q.open);
      if (it) { app.open(it); setQuery({ open: undefined }); }
    }
  }, [route.q.open, items]); // eslint-disable-line
  const cats = SECTIONS[sec];
  const pool = useMemo(() => {
    const s = q.trim().toLowerCase();
    let p = items.filter((x) => cats.includes(x.c));
    if (srcs.length) p = p.filter((x) => srcs.includes(x.s));
    if (onlyFull && app.isOwner) p = p.filter((x) => x.f);
    if (s) p = p.filter((x) => (x.t + " " + itTitle(x, lang) + " " + itSum(x, lang)).toLowerCase().includes(s));
    if (sort === "new") p.sort((a, b) => b.p.localeCompare(a.p));
    else if (sort === "imp") p.sort((a, b) => b.k - a.k);
    else p.sort((a, b) => relevance(b, days) - relevance(a, days));
    return p;
  }, [items, cats, srcs, onlyFull, q, sort, days, lang, app.isOwner]);
  const { kept, extra } = useMemo(() => {
    const d = dedupe(pool, multi || sort === "src" ? 600 : show + 1);
    let k = d.kept;
    if (multi) k = k.filter((x) => d.extra[x.id]);
    if (sort === "src") k = [...k].sort((a, b) => (d.extra[b.id] || 0) - (d.extra[a.id] || 0));
    return { kept: k, extra: d.extra };
  }, [pool, multi, sort, show]);
  const allSrc = useMemo(() => [...new Set(items.filter((x) => cats.includes(x.c)).map((x) => x.s))].sort(), [items, cats]);
  const block = periods && periods.periods[sec] && periods.periods[sec][String(days)];
  const finds = sec === "fin" || sec === "comp" ? findingsIn(research, Math.max(days, 7), 3) : [];
  const secs = [["fin", t("fin")], ["comp", t("comp")], ["srb", t("srb")], ["svet", t("svet")]];
  const nFilters = srcs.length + (onlyFull ? 1 : 0) + (multi ? 1 : 0);
  return (
    <div>
      <PageHead title={t("news")} sub={lang === "en" ? "The most important stories, merged across outlets and ranked by relevance. Pick a section and a period." : "Najvažnije vesti, spojene iz više izvora i poređane po relevantnosti. Izaberi rubriku i period."} />
      <div className="sticky top-[60px] z-30 -mx-4 mb-6 flex flex-col gap-2.5 bg-ink-900/85 px-4 py-2.5 backdrop-blur-xl md:static md:mx-0 md:flex-row md:items-center md:justify-between md:bg-transparent md:p-0 md:backdrop-blur-0 lg:top-0">
        <Segmented options={secs} value={sec} onChange={(v) => setQuery({ sec: v })} />
        <Segmented options={periodOpts(t)} value={days} onChange={(v) => setQuery({ p: v })} size="sm" />
      </div>

      <div className={cls("grid gap-6", finds.length > 0 && "lg:grid-cols-[1.5fr_1fr]")}>
        {periods ? <PeriodSummary block={block} items={periods.items} n={6} title={`${t("summary")} · ${t("d" + days)}`} /> : <Skeleton className="h-80" />}
        {finds.length > 0 && (
          <div>
            <div className="kicker mb-3">🔬 {lang === "en" ? "From research - same period" : "Iz istraživanja - isti period"}</div>
            <div className="space-y-3">{finds.map((p, i) => <FindingCard key={p.id} p={p} i={i} />)}</div>
          </div>
        )}
      </div>

      <div className="mt-10">
        <SectionTitle>{lang === "en" ? "All stories in the period" : "Sve vesti u periodu"}</SectionTitle>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <div className="relative min-w-[220px] flex-1">
            <Search size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-cream-500" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Fed, inflacija, Nvidia, NBS..." className="field pl-10" />
            {q && <button onClick={() => setQ("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-cream-400 hover:text-cream-100"><X size={15} /></button>}
          </div>
          <select value={sort} onChange={(e) => setSort(e.target.value)} className="field w-auto">
            {[["rel", t("sortRel")], ["new", t("sortNew")], ["imp", t("sortImp")], ["src", t("sortSrc")]].map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </select>
          <button onClick={() => setFilters((x) => !x)} className={cls("btn", (filters || nFilters) && "border-white/15")}>
            <SlidersHorizontal size={15} />{t("filters")}{nFilters ? <span className="rounded-full bg-wine-600 px-1.5 text-[10px] text-cream-50">{nFilters}</span> : null}
          </button>
        </div>
        <AnimatePresence>
          {filters && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
              <div className="mb-5 rounded-2xl border border-ink-600 bg-ink-850/70 p-4">
                <div className="flex flex-wrap gap-2">
                  <Chip active={multi} onClick={() => setMulti((x) => !x)}><Filter size={12} />{t("onlyMulti")}</Chip>
                  {app.isOwner && <Chip active={onlyFull} onClick={() => setOnlyFull((x) => !x)}>{t("onlyFull")}</Chip>}
                </div>
                <div className="stat-label mb-2 mt-4">{lang === "en" ? "Sources" : "Izvori"}</div>
                <div className="flex flex-wrap gap-1.5">
                  {allSrc.map((s) => <Chip key={s} active={srcs.includes(s)} onClick={() => setSrcs((x) => (x.includes(s) ? x.filter((y) => y !== s) : [...x, s]))}>{s}</Chip>)}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        {loading ? <div className="grid gap-4 md:grid-cols-2"><Skeleton className="h-48" /><Skeleton className="h-48" /><Skeleton className="h-48" /></div>
          : kept.length ? (
            <>
              <div className="mb-3 text-xs text-cream-500">{t("showing")} {Math.min(show, kept.length)} {t("of")} {pool.length}</div>
              <NewsGrid items={kept.slice(0, show)} extra={extra} heroFirst={sort !== "new"} />
              {kept.length > show && <div className="mt-6 text-center"><button className="btn" onClick={() => setShow((x) => x + 20)}>{t("loadMore")}</button></div>}
            </>
          ) : <Empty>{t("nothing")}</Empty>}
      </div>
    </div>
  );
}
