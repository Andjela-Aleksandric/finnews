import { BookOpen, Info } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
import { PageHead } from "../components/Shell";
import { Card, SectionTitle } from "../components/ui";

const GROUPS = [
  {
    sr: "Kretanje cene i trenutak", en: "Price action and timing",
    items: [
      {
        name: "SMA 50 / SMA 200",
        sr: "Prosečna cena poslednjih 50 ili 200 trgovačkih dana. SMA 200 je dugoročni trend; SMA 50 je kraći trend.",
        good: "Cena iznad SMA 200 prolazi proveru dugoročnog trenda. U faktorskoj oceni dodatni bod za trend dobija akcija iznad SMA 200 uz SMA 50 iznad SMA 200.",
        caution: "Cena ispod SMA 200 znači da je dugoročni trend slabiji. To je upozorenje, ne dokaz da će pad da se nastavi.",
        tag: "U skoru"
      },
      {
        name: "RSI (14)",
        sr: "Indeks relativne snage meri koliko su jaki nedavni dnevni pomaci cene, na skali od 0 do 100.",
        good: "Najbolji tehnički bod dobija RSI 30–50 koji raste, dok je cena iznad SMA 200. Kontrolna lista smatra 30–55 prihvatljivom zonom.",
        caution: "Iznad 70 aplikacija označava kao pregrejano i umanjuje skor. Ispod 30 uz RSI koji i dalje pada označava „nož koji pada“; nizak RSI sam po sebi nije signal za kupovinu.",
        tag: "U skoru"
      },
      {
        name: "Odmak od maksimuma za 52 nedelje",
        sr: "Pokazuje koliko je cena ispod najviše zabeležene cene tokom poslednjih godinu dana.",
        good: "Pad od najmanje 8% otvara mogućnost da akcija uđe u kandidate. Što je veći pad, do 40%, to je veći deo boda za popust.",
        caution: "Pad nije isto što i jeftina akcija: može da odražava pogoršanje poslovanja. Zato se gleda zajedno sa trendom, poslovnim podacima i vestima.",
        tag: "U skoru"
      },
      {
        name: "Momentum za 12–1 mesec",
        sr: "Promena cene tokom približno prethodne godine, izostavljajući poslednji mesec.",
        good: "Viši momentum u odnosu na ostale akcije sa liste podiže faktorsku ocenu.",
        caution: "Ovo je poređenje unutar trenutne liste, ne univerzalni prag. Visok prošli prinos ne garantuje budući.",
        tag: "Relativni skor"
      },
      {
        name: "Godišnja volatilnost",
        sr: "Procena koliko se dnevni prinosi akcije kolebaju, preračunata na godišnji nivo.",
        good: "Niža volatilnost dobija bolju faktorsku ocenu u odnosu na druge akcije.",
        caution: "Preko 45% godišnje aplikacija prikazuje kao rizik. Visoka volatilnost znači veće oscilacije, ne nužno lošu kompaniju.",
        tag: "U skoru"
      },
      {
        name: "Zlatni / mrtvački krst",
        sr: "Zlatni krst je prelazak SMA 50 iznad SMA 200; mrtvački krst je prelazak SMA 50 ispod SMA 200.",
        good: "Zlatni krst se dodaje kao pozitivan razlog kada se pojavi.",
        caution: "Mrtvački krst je upozorenje u listi rizika. Aplikacija poredi proseke sada i pre deset trgovačkih dana, pa signal može kasniti.",
        tag: "Dodatni signal"
      },
    ]
  },
  {
    sr: "Poslovanje i vrednovanje", en: "Business and valuation",
    items: [
      {
        name: "Rast prihoda",
        sr: "Godišnja promena prihoda kompanije, prema podacima Yahoo Finance.",
        good: "Više od 10% prolazi kontrolnu listu; više od 20% je brz rast prema vodiču.",
        caution: "Negativan rast prihoda se označava kao rizik. Proveri da li je pad privremen i uporedi kompanije iz iste industrije.",
        tag: "U skoru"
      },
      {
        name: "ROE — prinos na kapital",
        sr: "Neto dobit u odnosu na kapital akcionara; pokazuje koliko dobiti kompanija ostvaruje na taj kapital.",
        good: "Viši ROE doprinosi kvalitetu. Iznad 15% aplikacija ga navodi kao pozitivan razlog; doprinos skoru se ograničava na 25%.",
        caution: "Vrlo visok ROE može nastati i zbog velikog duga ili malog kapitala, zato ga gledaj uz zaduženost.",
        tag: "U skoru"
      },
      {
        name: "Profitna marža",
        sr: "Udeo prihoda koji ostaje kao neto dobit nakon troškova.",
        good: "Pozitivna marža prolazi kontrolnu listu. Viša marža doprinosi kvalitetu, do granice od 20%.",
        caution: "Nulta ili negativna marža ne prolazi proveru profitabilnosti. Poredi marže prvenstveno unutar iste industrije.",
        tag: "U skoru"
      },
      {
        name: "Slobodan novčani tok / tržišna vrednost",
        sr: "Slobodan novčani tok (FCF) podeljen tržišnom kapitalizacijom — koliko gotovine poslovanje generiše u odnosu na cenu kompanije.",
        good: "Prinos od najmanje 3% prolazi kontrolnu listu; 5% ili više je snažan orijentir iz vodiča. U oceni se koristi kada podatak postoji.",
        caution: "Negativan FCF može ukazivati da kompanija troši više gotovine nego što stvara. Kod brzorastućih firmi tumači ga uz ulaganja i fazu poslovanja.",
        tag: "U skoru ako postoji"
      },
      {
        name: "PEG",
        sr: "Odnos P/E i očekivanog rasta zarade; pomaže da se cena sagleda u odnosu na rast.",
        good: "U ovom skoru: ispod 1 dobija najviši bod; 1–1,5 povoljan; 1,5–2 srednji. PEG ispod 2 prolazi proveru vrednovanja.",
        caution: "Iznad 2 skor je slabiji; iznad 2,5 se dodaje rizik visoke cene. PEG zavisi od prognoza rasta i može biti nepouzdan ako je rast nestabilan.",
        tag: "U skoru"
      },
      {
        name: "Forward P/E i P/E",
        sr: "P/E deli cenu akcije zaradom po akciji. Forward P/E koristi očekivanu zaradu; obični P/E koristi ostvarenu zaradu.",
        good: "Kad nema PEG-a: forward P/E ispod 15 dobija najviši bod, 15–22 dobar, 22–30 srednji; ispod 30 prolazi kontrolnu listu.",
        caution: "Iznad 45 se dodaje rizik visoke cene. P/E nije uporediv bez konteksta rasta, industrije i kvaliteta zarade; negativan P/E se ne računa kao jeftin.",
        tag: "U skoru"
      },
      {
        name: "Dug / kapital (D/E)",
        sr: "Odnos duga i kapitala akcionara. Yahoo Finance ga prikazuje kao procenat.",
        good: "Ispod 150% prolazi kontrolnu listu.",
        caution: "Iznad 200% aplikacija označava visok dug. Pragovi su gruba provera i razlikuju se po industrijama, posebno kod banaka i komunalnih firmi.",
        tag: "Provera rizika"
      },
      {
        name: "P/S i dividenda",
        sr: "P/S poredi tržišnu vrednost sa prihodima. Dividenda je novac isplaćen akcionarima.",
        good: "Oba podatka su dostupna za pregled; dividenda se koristi za sortiranje liste akcija.",
        caution: "Trenutno ne ulaze u skor prilike. P/S ima smisla porediti sa sličnim kompanijama, a visoka dividenda sama po sebi ne znači sigurnu isplatu.",
        tag: "Prikaz, ne skor prilike"
      },
    ]
  },
  {
    sr: "Analitičari, vesti i sektor", en: "Analysts, news and sectors",
    items: [
      {
        name: "Potencijal do ciljne cene analitičara",
        sr: "Razlika između poslednje cene akcije i prosečne ciljne cene koju navode analitičari.",
        good: "Najmanje 5% uz pad od 8% ulazi u osnovni uslov kandidata; 10% prolazi kontrolnu listu. Viši potencijal povećava skor.",
        caution: "Ciljne cene su procene analitičara, mogu kasniti za tržištem i nisu obećanje prinosa.",
        tag: "U skoru"
      },
      {
        name: "Ocena analitičara",
        sr: "Yahoo Finance skala je obično 1 = snažna kupovina, 5 = prodaja.",
        good: "Ocena do 2,3 može da zameni ciljni rast u uslovu kandidata; niža ocena podiže skor.",
        caution: "Ocena iznad 3 isključuje akciju iz oznake „ispunjava uslove“. Broj analitičara i starost procene su važni.",
        tag: "U skoru"
      },
      {
        name: "Sentiment vesti o kompaniji",
        sr: "Jednostavan rečnik prepoznaje pozitivne i negativne izraze u do 21 danu vesti o kompaniji.",
        good: "Pozitivne vesti podižu komponentu sentimenta; neutralan sentiment je polazna vrednost ako nema vesti.",
        caution: "Ovo nije razumevanje punog konteksta: reč „rally“ ili „warning“ može biti pogrešno protumačena. Pročitaj povezane naslove.",
        tag: "U skoru"
      },
      {
        name: "Zamah teme i uticaj sektora",
        sr: "Broji koliko se o temama poput AI-ja, kamata, nafte ili odbrane piše poslednjih 7 dana u odnosu na prethodne periode.",
        good: "Pozitivan uticaj sektora podiže ocenu; uticaj iznad 0,05 prolazi kontrolnu listu.",
        caution: "Negativan uticaj ispod −0,15 se označava kao nepovoljan. Veći broj vesti nije dokaz da će cena rasti.",
        tag: "U skoru"
      },
    ]
  },
];

const SCORES = [
  { sr: "Pad od maksimuma", en: "Drop from high", value: "20%" },
  { sr: "Cilj analitičara", en: "Analyst upside", value: "17%" },
  { sr: "Kvalitet", en: "Quality", value: "12%" },
  { sr: "Vrednovanje", en: "Valuation", value: "12%" },
  { sr: "Ocena analitičara", en: "Analyst rating", value: "8%" },
  { sr: "Vesti o kompaniji", en: "Company news", value: "9%" },
  { sr: "Tehnički signal", en: "Technical setup", value: "14%" },
  { sr: "Zamah sektora", en: "Sector tailwind", value: "8%" },
];

const EN = {
  "SMA 50 / SMA 200": {
    desc: "The average price over the last 50 or 200 trading days. SMA 200 is the long-term trend; SMA 50 is the shorter trend.",
    good: "A price above SMA 200 passes the long-term trend check. The factor score also rewards a price above SMA 200 with SMA 50 above SMA 200.",
    caution: "A price below SMA 200 means the long-term trend is weaker. It is a warning, not proof the decline will continue."
  },
  "RSI (14)": {
    desc: "The Relative Strength Index compares recent daily gains and losses on a 0–100 scale.",
    good: "The strongest technical score is a rising RSI of 30–50 while price is above SMA 200. The checklist accepts 30–55.",
    caution: "Above 70 is marked overheated and lowers the score. Below 30 while RSI is still falling is a falling-knife warning; a low RSI alone is not a buy signal."
  },
  "Odmak od maksimuma za 52 nedelje": {
    desc: "Shows how far the price is below its highest level over the last year.",
    good: "A decline of at least 8% can enter the candidate list. The discount component increases with the drop, up to 40%.",
    caution: "A falling price is not automatically cheap; it may reflect a weaker business. Check the trend, company data, and news too."
  },
  "Momentum za 12–1 mesec": {
    desc: "Price change over roughly the prior year, excluding the most recent month.",
    good: "Higher momentum relative to other stocks on the watchlist improves the factor score.",
    caution: "This is a comparison within the current list, not a universal cutoff. Past returns do not guarantee future returns."
  },
  "Godišnja volatilnost": {
    desc: "An estimate of how much daily returns fluctuate, expressed on an annualized basis.",
    good: "Lower volatility receives a better factor score relative to other stocks.",
    caution: "Above 45% per year is flagged as a risk. High volatility means larger swings, not necessarily a bad company."
  },
  "Zlatni / mrtvački krst": {
    desc: "A golden cross is SMA 50 moving above SMA 200; a death cross is SMA 50 moving below SMA 200.",
    good: "A golden cross is added as a positive reason when detected.",
    caution: "A death cross is shown as a risk. The app compares the averages now and ten trading days earlier, so the signal can lag."
  },
  "Rast prihoda": {
    desc: "Year-over-year change in company revenue, based on Yahoo Finance data.",
    good: "Above 10% passes the checklist; above 20% is considered fast growth in the guide.",
    caution: "Negative revenue growth is flagged as a risk. Check whether the decline is temporary and compare companies in the same industry."
  },
  "ROE — prinos na kapital": {
    desc: "Net income relative to shareholder equity; it indicates how much profit a company earns on that equity.",
    good: "Higher ROE contributes to quality. Above 15% is shown as a positive reason; its score contribution is capped at 25%.",
    caution: "Very high ROE can also result from heavy debt or low equity, so read it alongside leverage."
  },
  "Profitna marža": {
    desc: "The share of revenue left as net income after expenses.",
    good: "A positive margin passes the checklist. Higher margins improve the quality component, up to a 20% cap.",
    caution: "Zero or negative margin fails the profitability check. Compare margins mainly within the same industry."
  },
  "Slobodan novčani tok / tržišna vrednost": {
    desc: "Free cash flow divided by market capitalization: how much cash the business generates relative to its market value.",
    good: "A yield of at least 3% passes the checklist; 5% or more is a strong guidepost. It is used when the data is available.",
    caution: "Negative free cash flow may mean the company is using more cash than it generates. For fast-growing firms, consider investment needs and business stage."
  },
  "PEG": {
    desc: "The P/E ratio relative to expected earnings growth; it helps put valuation in the context of growth.",
    good: "In this score, below 1 gets the highest value; 1–1.5 is favorable; 1.5–2 is mid-range. Below 2 passes the valuation check.",
    caution: "Above 2 lowers the score; above 2.5 is flagged as expensive. PEG depends on growth forecasts and can be unreliable when growth is unstable."
  },
  "Forward P/E i P/E": {
    desc: "P/E divides share price by earnings per share. Forward P/E uses expected earnings; trailing P/E uses reported earnings.",
    good: "When PEG is unavailable: forward P/E below 15 gets the highest score, 15–22 is good, 22–30 is mid-range; below 30 passes the checklist.",
    caution: "Above 45 is flagged as expensive. P/E needs context on growth, industry, and earnings quality; negative P/E is not treated as cheap."
  },
  "Dug / kapital (D/E)": {
    desc: "Debt relative to shareholder equity. Yahoo Finance reports it as a percentage.",
    good: "Below 150% passes the checklist.",
    caution: "Above 200% is flagged as high debt. These are rough checks and vary by industry, especially for banks and utilities."
  },
  "P/S i dividenda": {
    desc: "P/S compares market value with revenue. A dividend is cash paid to shareholders.",
    good: "Both are available for review; dividend yield can be used to sort the full stock list.",
    caution: "Neither affects the opportunity score. Compare P/S with similar companies; a high dividend yield alone does not guarantee the payment."
  },
  "Potencijal do ciljne cene analitičara": {
    desc: "The difference between the latest share price and the analysts' average target price.",
    good: "At least 5% upside plus an 8% drop meets the basic candidate rule; 10% passes the checklist. Higher upside improves the score.",
    caution: "Targets are analyst estimates, can lag the market, and are not promised returns."
  },
  "Ocena analitičara": {
    desc: "Yahoo Finance's scale is generally 1 = strong buy and 5 = sell.",
    good: "A rating of 2.3 or better can substitute for target upside in the candidate rule; lower ratings improve the score.",
    caution: "A rating above 3 prevents the stock from receiving the “qualifies” flag. The analyst count and estimate date matter."
  },
  "Sentiment vesti o kompaniji": {
    desc: "A simple word dictionary scores positive and negative phrases in company news from the last 21 days.",
    good: "Positive news raises the sentiment component. With no news, the component starts at neutral.",
    caution: "This does not understand full context: words such as “rally” or “warning” can be misread. Read the linked headlines."
  },
  "Zamah teme i uticaj sektora": {
    desc: "Counts how often themes such as AI, rates, oil, or defence appear in the last 7 days versus prior periods.",
    good: "A positive sector effect raises the score; an effect above 0.05 passes the checklist.",
    caution: "An effect below −0.15 is flagged as unfavorable. More headlines do not prove a stock price will rise."
  },
  "Prinosi po periodima": {
    desc: "The stock page shows 1-day, 1-week, 1-month, 6-month, and 1-year price changes.",
    good: "These make it easier to compare recent and longer-term performance.",
    caution: "They describe what happened, not what will happen. The opportunity score uses its own 12-to-1-month momentum and drawdown measures instead.",
  }
};

const TAGS_EN = {
  "U skoru": "In score",
  "Relativni skor": "Relative score",
  "Dodatni signal": "Additional signal",
  "U skoru ako postoji": "In score when available",
  "Provera rizika": "Risk check",
  "Prikaz, ne skor prilike": "Displayed, not in opportunity score",
};

export default function IndicatorsPage() {
  const { lang } = useLang();
  const t = useT();
  const en = lang === "en";
  const L = (sr, english) => en ? english : sr;
  return (
    <div className="max-w-6xl">
      <PageHead title={t("indicators")} sub={L("Šta meri svaki pokazatelj, kako ga FinNews koristi i kada rezultat traži oprez.", "What each indicator measures, how FinNews uses it, and when to be cautious.")} />
      <Card hover={false} className="mb-8 flex gap-3 border-gold-500/25 bg-gold-500/5 p-4 text-sm leading-relaxed text-cream-300">
        <Info size={18} className="mt-0.5 shrink-0 text-gold-500" />
        <p>{L("Ovo su pravila rangiranja aplikacije, ne univerzalne granice za dobre i loše akcije. Pragovi su orijentacioni i zavise od industrije; nijedan indikator sam ne potvrđuje kupovinu. Podaci mogu nedostajati ili kasniti. Sadržaj služi za istraživanje, nije investicioni savet.", "These are the app's ranking rules, not universal cutoffs for good and bad stocks. Thresholds are approximate and depend on industry; no single indicator confirms a buy. Data may be missing or delayed. For research only, not investment advice.")}</p>
      </Card>

      <section className="mb-10">
        <SectionTitle>{L("Kako nastaje skor prilike (0–100)", "How the opportunity score is built (0–100)")}</SectionTitle>
        <p className="mb-4 text-sm text-cream-400">{L("Skor prilike je ponderisani zbir. „Ispunjava uslove“ je zasebna oznaka: pad od najmanje 8% i ili potencijal analitičara od 5% ili ocena do 2,3, uz ocenu najviše 3. Lista prvo poređa one koji ispunjavaju uslove, pa ostale po skoru.", "The opportunity score is a weighted sum. “Qualifies” is a separate flag: at least an 8% drop and either 5% analyst upside or a rating of 2.3 or better, with rating no worse than 3. The list sorts qualifying names first, then the rest by score.")}</p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{SCORES.map((x) => (
          <Card key={x.value + x.sr} className="p-4">
            <div className="stat-label">{L(x.sr, x.en)}</div><div className="mt-1 font-mono text-2xl text-cream-50">{x.value}</div>
          </Card>
        ))}</div>
        <p className="mt-3 text-xs text-cream-500">{L("„Nož koji pada“ umanjuje skor 25%; pregrejana akcija sa RSI iznad 70 umanjuje ga 15%.", "A falling-knife setup reduces the score by 25%; an overheated stock with RSI above 70 reduces it by 15%.")}</p>
      </section>

      <section className="space-y-10">
        {GROUPS.map((group) => (
          <div key={group.sr}>
            <SectionTitle>{L(group.sr, group.en)}</SectionTitle>
            <div className="grid gap-3 md:grid-cols-2">
              {group.items.map((item) => (
                <Card key={item.name} hover={false} className="p-4 md:p-5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="font-display text-lg font-semibold text-cream-50">{item.name}</h3>
                    <span className="rounded-full border border-ink-500 px-2 py-1 text-[10px] uppercase tracking-wider text-cream-400">{item.tag}</span>
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-cream-300">{en ? (EN[item.name] || {}).desc || item.sr : item.sr}</p>
                  <div className="mt-3 space-y-2 text-sm">
                    <p><b className="text-up">{L("Povoljnije:", "More favorable:")}</b> <span className="text-cream-300">{en ? (EN[item.name] || {}).good || item.good : item.good}</span></p>
                    <p><b className="text-gold-400">{L("Oprez:", "Caution:")}</b> <span className="text-cream-300">{en ? (EN[item.name] || {}).caution || item.caution : item.caution}</span></p>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        ))}
      </section>

      <section className="mt-10">
        <SectionTitle>{L("Šta trenutno nije u skoru prilika", "Not currently included in the opportunity score")}</SectionTitle>
        <Card hover={false} className="p-4 text-sm leading-relaxed text-cream-300">
          {L("MACD, Bollingerovi opsezi i transakcije insajdera ili fondova (13F) nisu u podacima koje ovaj prikaz koristi. P/S i dividenda se mogu prikazati ili koristiti za sortiranje, ali ne utiču na skor prilike.", "MACD, Bollinger Bands, and insider or fund transactions (13F) are not in the data used by this view. P/S and dividends may be displayed or used for sorting, but do not affect the opportunity score.")}
        </Card>
      </section>

      <section className="mt-10">
        <SectionTitle>{L("Skor za poređenje svih akcija", "Score for comparing all stocks")}</SectionTitle>
        <Card hover={false} className="p-4 text-sm leading-relaxed text-cream-300">
          {L("U tabu „Istraži sve“ postoji i faktorski skor: momentum 25%, cilj analitičara 20%, P/E 15%, ROE 15%, rast prihoda 10% i niža volatilnost 15%. Faktori se porede relativno među akcijama sa liste; dugoročni trend dodaje 10% konačnom skoru. Zato ovaj skor nije isto što i skor prilike iznad.", "The “Explore all” tab also has a factor score: momentum 25%, analyst target 20%, P/E 15%, ROE 15%, revenue growth 10%, and lower volatility 15%. Factors are ranked relative to the current watchlist; long-term trend contributes an extra 10% to the final score. This is different from the opportunity score above.")}
        </Card>
      </section>

      <div className="mt-10 flex items-center gap-2 text-xs text-cream-500">
        <BookOpen size={14} />
        <span>{L("Za definiciju P/E pogledaj", "For a definition of P/E, see")} <a className="text-cream-300 underline" href="https://www.investor.gov/introduction-investing/investing-basics/glossary/price-earnings-pe-ratio" target="_blank" rel="noreferrer">Investor.gov</a>.</span>
      </div>
    </div>
  );
}
