import { ArrowRight, Briefcase, Flame, Lightbulb, Newspaper } from "lucide-react";
import { countOf, plural, useLang, useT } from "../lib/i18n";
import { cls, num } from "../lib/fmt";
import { useData } from "../lib/data";
import { usePortfolio } from "../lib/usePortfolio";
import { useRoute } from "../components/Shell";
import { Card, CountUp, Reveal, SectionTitle, Skeleton } from "../components/ui";
import { PeriodSummary, findingsIn, FindingCard } from "../components/Summary";
import { OppCard, ThemeCard } from "../components/Stocks";

function Stat({ icon: I, label, children, sub, i, onClick }) {
  return (
    <Card delay={i * 0.06} onClick={onClick} className="group overflow-hidden p-4 md:p-5">
      
      <div className="flex items-center gap-2 stat-label"><I size={13} className="text-gold-500" />{label}</div>
      <div className="mt-3 break-words font-display text-[1.3rem] font-semibold leading-tight tracking-tight text-white md:text-[1.75rem]">{children}</div>
      {sub && <div className="mt-1.5 line-clamp-2 text-xs leading-snug text-cream-400">{sub}</div>}
    </Card>
  );
}

export default function Home() {
  const { lang } = useLang();
  const t = useT();
  const { go } = useRoute();
  const { data: [periods, stocks, research] } = useData(["periods.json", "stocks.json", "research.json"]);
  const pf = usePortfolio();
  const smap2 = Object.fromEntries(((stocks && stocks.stocks) || []).map((s) => [s.ticker, s]));
  const opps = ((stocks && stocks.top20) || []).map((t) => smap2[t]).filter(Boolean);
  const themes = (stocks && stocks.themes) || [];
  const fin1 = periods && periods.periods.fin["1"];
  const block = fin1 && fin1.top.length ? fin1 : periods && periods.periods.fin["7"];
  const finds = findingsIn(research, 30, 3);
  return (
    <div>
      <div className="grid grid-cols-2 gap-3 md:gap-4 lg:grid-cols-4">
        <Stat i={0} icon={Briefcase} label={t("portfolio")} onClick={() => go("/portfolio")}
          sub={pf.loading ? t("loading") : (lang === "en" ? "See how they're doing today" : "Pogledaj kako danas stoje")}>
          {pf.loading ? <Skeleton className="h-8 w-32" /> : (lang === "en" ? "Your holdings" : "Tvoje pozicije")}
        </Stat>
        <Stat i={1} icon={Newspaper} label={lang === "en" ? "Stories, 7 days" : "Vesti za 7 dana"} onClick={() => go("/vesti")}
          sub={lang === "en" ? `from ${countOf((periods && periods.periods.all["7"].nsrc) || 0, "sources", lang)}` : `iz ${countOf((periods && periods.periods.all["7"].nsrc) || 0, "sources", lang).replace(/izvor$/, "izvora")}`}>
          <CountUp value={(periods && periods.periods.all["7"].n) || 0} format={(x) => num(x, 0, lang)} />
        </Stat>
        <Stat i={2} icon={Flame} label={t("risingThemes")} onClick={() => go("/akcije?tab=themes")}
          sub={themes[0] ? `${countOf(themes[0].n, "stories", lang)} ${lang === "en" ? "this week" : "ove nedelje"}` : (lang === "en" ? "Shows up as soon as new stories arrive" : "Pojaviće se čim stignu nove vesti")}>
          {themes[0] ? (lang === "en" ? themes[0].en : themes[0].sr) : (lang === "en" ? "Still quiet" : "Još je mirno")}
        </Stat>
        <Stat i={3} icon={Lightbulb} label={t("oppNow")} onClick={() => go("/akcije")}
          sub={lang === "en" ? `${plural(opps.length, "ideas", lang)} - US and Xetra tickers` : `${plural(opps.length, "ideas", lang)} - oznake za SAD i Xetru`}>
          <CountUp value={opps.length} format={(x) => num(x, 0, lang)} />
        </Stat>
      </div>

      <div className="mt-10 grid min-w-0 grid-cols-1 gap-8 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
        <section className="min-w-0">
          <SectionTitle action={<button onClick={() => go("/vesti")} className="btn-ghost">{t("allNews")} <ArrowRight size={14} /></button>}>{t("todayBrief")}</SectionTitle>
          {periods ? <PeriodSummary block={block} items={periods.items} n={7} title={`${t("summary")} · ${fin1 && fin1.top.length ? t("d1") : t("d7")}`} /> : <Skeleton className="h-96" />}
        </section>
        <section className="min-w-0">
          <SectionTitle action={<button onClick={() => go("/akcije")} className="btn-ghost">{t("seeAll")} <ArrowRight size={14} /></button>}>{t("opportunities")}</SectionTitle>
          <div className="space-y-3">
            {stocks ? opps.slice(0, 4).map((s, i) => <OppCard key={s.ticker} s={s} i={i} compact />) : <Skeleton className="h-64" />}
          </div>
          <div className="mt-8"><SectionTitle>{t("risingThemes")}</SectionTitle></div>
          <div className="space-y-3">{themes.slice(0, 2).map((th, i) => <ThemeCard key={th.sr} th={th} i={i} sectors={stocks.sectors_sr} />)}</div>
        </section>
      </div>

      <section className="mt-10">
        <SectionTitle kicker={lang === "en" ? "Last 30 days" : "Poslednjih 30 dana"}
          action={<button onClick={() => go("/istrazivanja")} className="btn-ghost">{t("seeAll")} <ArrowRight size={14} /></button>}>{t("fromResearch")}</SectionTitle>
        <div className={cls("grid gap-4", finds.length > 1 && "md:grid-cols-3")}>
          {research ? finds.map((p, i) => <FindingCard key={p.id} p={p} i={i} />) : <Skeleton className="h-40" />}
        </div>
      </section>
    </div>
  );
}
