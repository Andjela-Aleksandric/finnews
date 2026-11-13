import { useMemo, useState } from "react";
import { Bookmark, Search } from "lucide-react";
import { countOf, plural, useLang, useT } from "../lib/i18n";
import { itSum, itTitle } from "../lib/fmt";
import { getMeta, useData } from "../lib/data";
import { PageHead, useRoute } from "../components/Shell";
import { NewsCard, NewsRow, useApp } from "../components/News";
import { Empty, Skeleton, Tabs } from "../components/ui";
import { TabPanel } from "../components/ui";

export default function ArchivePage() {
  const { lang } = useLang();
  const t = useT();
  const app = useApp();
  const { route, setQuery } = useRoute();
  const tab = route.q.tab || "search";
  const meta = getMeta();
  const months = ["recent", ...[...((meta && meta.months) || [])].reverse()];
  const [m, setM] = useState("recent");
  const [q, setQ] = useState("");
  const { loading, data: [items] } = useData([m === "recent" ? "news/recent.json" : `news/${m}.json`]);
  const res = useMemo(() => {
    const s = q.trim().toLowerCase();
    return (items || []).filter((x) => !s || (x.t + " " + itTitle(x, lang) + " " + itSum(x, lang) + " " + x.s).toLowerCase().includes(s))
      .sort((a, b) => b.p.localeCompare(a.p)).slice(0, 150);
  }, [items, q, lang]);
  const mLabel = (k) => (k === "recent" ? (lang === "en" ? "Last 8 days" : "Poslednjih 8 dana")
    : new Date(k + "-15").toLocaleDateString(lang === "en" ? "en-GB" : "sr-Latn-RS", { month: "long", year: "numeric" }));
  return (
    <div>
      <PageHead title={t("archive")} sub={lang === "en" ? "Search every story from the last 6 months, and your saved stories." : "Pretraži sve vesti iz poslednjih 6 meseci i svoje sačuvane vesti."} />
      <Tabs value={tab} onChange={(v) => setQuery({ tab: v })} options={[["search", t("search"), <Search size={15} key="s" />], ["saved", `${t("savedItems")} · ${app.starredItems.length}`, <Bookmark size={15} key="b" />]]} />
      <TabPanel k={tab}>
      {tab === "saved" ? (app.starredItems.length ? <div className="grid gap-4 md:grid-cols-2">{app.starredItems.map((it, i) => <NewsCard key={it.id} it={it} i={i} />)}</div>
        : <Empty icon={<Bookmark className="text-cream-500" />}>{lang === "en" ? "Tap the bookmark on any story and it will show up here." : "Klikni na znak za čuvanje kod bilo koje vesti i ona će se pojaviti ovde."}</Empty>) : (
        <>
          <div className="mb-5 flex flex-wrap gap-2">
            <div className="relative min-w-[220px] flex-1">
              <Search size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-cream-500" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={lang === "en" ? "Search titles and summaries" : "Pretraži naslove i opise"} className="field pl-10" />
            </div>
            <select className="field w-auto" value={m} onChange={(e) => setM(e.target.value)}>{months.map((k) => <option key={k} value={k}>{mLabel(k)}</option>)}</select>
          </div>
          {loading ? <Skeleton className="h-96" /> : res.length ? (
            <>
              <div className="mb-2 text-xs text-cream-500">{countOf(res.length, "stories", lang)}</div>
              <ul className="-mx-3 divide-y divide-ink-600/50">{res.map((it) => <NewsRow key={it.id} it={it} />)}</ul>
            </>
          ) : <Empty>{t("nothing")}</Empty>}
        </>
      )}
      </TabPanel>
    </div>
  );
}
