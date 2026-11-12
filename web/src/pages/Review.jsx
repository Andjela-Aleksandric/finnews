import { useLang, useT } from "../lib/i18n";
import { useData } from "../lib/data";
import { periodOpts } from "../lib/sections";
import { PageHead, useRoute } from "../components/Shell";
import { Empty, Segmented, SectionTitle, Skeleton, Tabs } from "../components/ui";
import { TabPanel } from "../components/ui";
import { FindingCard, PeriodSummary, findingsIn } from "../components/Summary";
import { MarketsPanel } from "./Stocks";
import { CalendarRange, FlaskConical, LineChart, Newspaper } from "lucide-react";

export default function Review() {
  const { lang } = useLang();
  const t = useT();
  const { route, setQuery } = useRoute();
  const days = +(route.q.p || 7);
  const tab = route.q.tab || "news";
  const { data: [periods, research, stocks, prices] } = useData(["periods.json", "research.json", "stocks.json", "prices_all.json"]);
  const from = new Date(Date.now() - days * 864e5), to = new Date();
  const fmt = (d) => d.toLocaleDateString(lang === "en" ? "en-GB" : "sr-Latn-RS", { day: "numeric", month: "short", year: "numeric" });
  const finds = findingsIn(research, days, 18);
  return (
    <div>
      <PageHead title={lang === "en" ? "Period review" : "Pregled perioda"}
        sub={lang === "en" ? "What mattered - news, research findings and markets for any period up to 6 months." : "Šta je bilo bitno - vesti, naučni nalazi i tržišta za bilo koji period do 6 meseci."} />
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <Segmented value={days} onChange={(v) => setQuery({ p: v })} options={periodOpts(t)} />
        <span className="inline-flex items-center gap-1.5 text-sm text-cream-400"><CalendarRange size={15} />{fmt(from)} - {fmt(to)}</span>
      </div>
      <Tabs value={tab} onChange={(v) => setQuery({ tab: v })} options={[["news", t("news"), <Newspaper size={15} key="n" />],
        ["res", t("keyFindings"), <FlaskConical size={15} key="r" />], ["mk", t("markets"), <LineChart size={15} key="m" />]]} />
      <TabPanel k={tab}>
      {tab === "news" && (periods ? (
        <div className="space-y-8">
          <PeriodSummary block={periods.periods.all[String(days)]} items={periods.items} n={8} title={`${t("summary")} · ${t("d" + days)}`} />
          <div className="grid gap-6 md:grid-cols-2">
            {[["fin", t("fin")], ["comp", t("comp")], ["srb", t("srb")], ["svet", t("svet")]].map(([k, l]) => (
              <div key={k}><SectionTitle>{l}</SectionTitle><PeriodSummary block={periods.periods[k][String(days)]} items={periods.items} n={5} title={l} /></div>
            ))}
          </div>
        </div>
      ) : <Skeleton className="h-96" />)}
      {tab === "res" && (research ? (finds.length ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{finds.map((p, i) => <FindingCard key={p.id} p={p} i={i} big />)}</div>
        : <Empty>{lang === "en" ? "No studies in this period - pick a longer one." : "Nema studija u ovom periodu - izaberi duži."}</Empty>) : <Skeleton className="h-96" />)}
      {tab === "mk" && (stocks && prices ? <MarketsPanel prices={prices} stocks={stocks.stocks} days={days} /> : <Skeleton className="h-96" />)}
      </TabPanel>
    </div>
  );
}
