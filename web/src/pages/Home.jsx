import { motion } from "framer-motion";
import { ArrowRight, Briefcase, Flame, Lightbulb, Newspaper } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
import { cls, dateLong, eur, num, pct } from "../lib/fmt";
import { useData } from "../lib/data";
import { usePortfolio } from "../lib/usePortfolio";
import { assetValues, valuation } from "../lib/portfolio";
import { useRoute } from "../components/Shell";
import { Card, CountUp, Reveal, SectionTitle, Skeleton, SplitText } from "../components/ui";
import { PeriodSummary, findingsIn, FindingCard } from "../components/Summary";
import { OppCard, ThemeCard } from "../components/Stocks";

function Stat({ icon: I, label, children, sub, i, onClick }) {
  return (
    <Card delay={i * 0.06} onClick={onClick} className="group overflow-hidden p-4 md:p-5">
      <div className="pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full bg-wine-600/20 blur-2xl transition-opacity group-hover:opacity-100" />
      <div className="flex items-center gap-2 stat-label"><I size={13} className="text-wine-400" />{label}</div>
      <div className="mt-2 truncate font-display text-[1.5rem] font-bold text-cream-50 md:text-[1.75rem]">{children}</div>
      {sub && <div className="mt-1 truncate text-xs text-cream-400">{sub}</div>}
    </Card>
  );
}

export default function Home() {
  const { lang } = useLang();
  const t = useT();
  const { go } = useRoute();
  const { data: [periods, stocks, research, prices] } = useData(["periods.json", "stocks.json", "research.json", "prices_all.json"]);
  const pf = usePortfolio();
  const hr = new Date().getHours();
  const greet = hr < 11 ? t("goodMorning") : hr < 18 ? t("goodDay") : t("goodEvening");
  const smap = Object.fromEntries(((stocks && stocks.stocks) || []).map((s) => [s.ticker, s]));
  let pfv = null;
  if (pf.state && prices) {
    const v = valuation(pf.state, prices, smap), a = assetValues(pf.state, prices);
    const tv = v.reduce((x, r) => x + (r.value || 0), 0) + a.reduce((x, r) => x + (r.value || 0), 0);
    const tc = v.reduce((x, r) => x + r.cost, 0) + a.reduce((x, r) => x + r.base, 0);
    const td = v.reduce((x, r) => x + (r.dayEur || 0), 0) + a.reduce((x, r) => x + (r.dayEur || 0), 0);
    pfv = { tv, tc, td };
  }
  const smap2 = Object.fromEntries(((stocks && stocks.stocks) || []).map((s) => [s.ticker, s]));
  const opps = ((stocks && stocks.top20) || []).map((t) => smap2[t]).filter(Boolean);
  const themes = (stocks && stocks.themes) || [];
  const fin1 = periods && periods.periods.fin["1"];
  const block = fin1 && fin1.top.length ? fin1 : periods && periods.periods.fin["7"];
  const finds = findingsIn(research, 30, 3);
  return (
    <div>
      <div className="mb-7">
        <div className="kicker">{dateLong(new Date(), lang)}</div>
        <motion.h1 initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-2 font-display text-[2.3rem] font-bold leading-[1.1] md:text-[3.2rem]">
          <SplitText text={greet + "."} className="text-sheen" />
        </motion.h1>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }} className="mt-2 text-[15px] text-cream-400 md:text-base">{t("todayMatters")}</motion.p>
      </div>

      <div className="grid grid-cols-2 gap-3 md:gap-4 lg:grid-cols-4">
        {pfv ? (
          <Stat i={0} icon={Briefcase} label={t("portfolio")} onClick={() => go("/portfolio")}
            sub={<span className={pfv.td >= 0 ? "text-up" : "text-down"}>{pfv.td >= 0 ? "▲" : "▼"} {eur(Math.abs(pfv.td), 0, lang)} {t("today").toLowerCase()}</span>}>
            <CountUp value={pfv.tv} format={(x) => eur(x, 0, lang)} />
          </Stat>
        ) : (
          <Stat i={0} icon={Briefcase} label={t("portfolio")} onClick={() => go(pf.isOwner ? "/portfolio" : "/podesavanja")} sub={pf.isOwner ? t("loading") : t("ownerOnly")}>
            {pf.isOwner ? <Skeleton className="h-8 w-32" /> : "🔒"}
          </Stat>
        )}
        {pfv ? (
          <Stat i={1} icon={Briefcase} label={t("ret")} sub={`${t("invested")} ${eur(pfv.tc, 0, lang)}`}>
            <span className={pfv.tv >= pfv.tc ? "text-up" : "text-down"}>{pct(pfv.tc ? pfv.tv / pfv.tc - 1 : 0, 1, lang)}</span>
          </Stat>
        ) : (
          <Stat i={1} icon={Newspaper} label={lang === "en" ? "Stories, 7 days" : "Vesti za 7 dana"} onClick={() => go("/vesti")}
            sub={`${(periods && periods.periods.all["7"].nsrc) || 0} ${t("sources")}`}>
            <CountUp value={(periods && periods.periods.all["7"].n) || 0} format={(x) => num(x, 0, lang)} />
          </Stat>
        )}
        <Stat i={2} icon={Flame} label={t("risingThemes")} onClick={() => go("/akcije?tab=themes")}
          sub={themes[0] ? `${themes[0].n} ${t("stories")} · 7 ${lang === "en" ? "days" : "dana"}` : ""}>
          {themes[0] ? (lang === "en" ? themes[0].en : themes[0].sr) : "-"}
        </Stat>
        <Stat i={3} icon={Lightbulb} label={t("oppNow")} onClick={() => go("/akcije")}
          sub={lang === "en" ? "ideas, both US and Xetra" : "predloga, SAD i Xetra"}>
          <CountUp value={opps.length} format={(x) => num(x, 0, lang)} />
        </Stat>
      </div>

      <div className="mt-10 grid gap-8 lg:grid-cols-[1.35fr_1fr]">
        <section>
          <SectionTitle action={<button onClick={() => go("/vesti")} className="btn-ghost">{t("allNews")} <ArrowRight size={14} /></button>}>{t("todayBrief")}</SectionTitle>
          {periods ? <PeriodSummary block={block} items={periods.items} n={7} title={`${t("summary")} · ${fin1 && fin1.top.length ? t("d1") : t("d7")}`} /> : <Skeleton className="h-96" />}
        </section>
        <section>
          <SectionTitle action={<button onClick={() => go("/akcije")} className="btn-ghost">{t("seeAll")} <ArrowRight size={14} /></button>}>{t("opportunities")}</SectionTitle>
          <div className="space-y-3">
            {stocks ? opps.slice(0, 4).map((s, i) => <OppCard key={s.ticker} s={s} prices={prices} i={i} compact />) : <Skeleton className="h-64" />}
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
