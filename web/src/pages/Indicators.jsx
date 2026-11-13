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
        sr: "Pokazuje prosečnu cenu za poslednjih 50 ili 200 trgovačkih dana. SMA 200 pomaže da vidiš dugoročniji smer, a SMA 50 kraći trend.",
        good: "Cena iznad SMA 200 prolazi proveru dugoročnog trenda. U faktorskoj oceni dodatni bod za trend dobija akcija iznad SMA 200 uz SMA 50 iznad SMA 200.",
        caution: "Cena ispod SMA 200 znači da je dugoročni trend slabiji. To je upozorenje, ne dokaz da će pad da se nastavi.",
        tag: "U skoru"
      },
      {
        name: "RSI (14)",
        sr: "Indeks relativne snage meri koliko su jaki nedavni dnevni pomaci cene, na skali od 0 do 100.",
        good: "Najbolji tehnički skor dobija RSI od 30-50 koji raste u odnosu na pre pet trgovačkih dana, dok je cena iznad SMA 200. Vrednosti od 30-55 prolaze osnovnu proveru.",
        caution: "Iznad 70 RSI se smatra pregrejanim i umanjuje skor. Ispod 30, uz RSI koji i dalje pada, može značiti da cena još slabi. Nizak RSI sam po sebi nije signal za kupovinu.",
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
        name: "Momentum za 12-1 mesec",
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
        sr: "Zlatni krst nastaje kada SMA 50 pređe iznad SMA 200. Mrtvački krst je prelazak ispod SMA 200.",
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
        good: "Rast veći od 10% prolazi osnovnu proveru. Iznad 20% vodič ga svrstava u brz rast.",
        caution: "Negativan rast prihoda se označava kao rizik. Proveri da li je pad privremen i uporedi kompanije iz iste industrije.",
        tag: "U skoru"
      },
      {
        name: "ROE - prinos na kapital",
        sr: "Neto dobit u odnosu na kapital akcionara. Pokazuje koliko dobiti kompanija ostvaruje na uloženi kapital.",
        good: "Viši ROE doprinosi oceni kvaliteta. Iznad 15% se računa kao pozitivan signal, ali njegov doprinos tom delu skora ne prelazi 25%.",
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
        sr: "Slobodan novčani tok (FCF) podeljen tržišnom kapitalizacijom - koliko gotovine poslovanje generiše u odnosu na cenu kompanije.",
        good: "Prinos od 3% ili više prolazi osnovnu proveru. Iznad 5% je snažan rezultat prema vodiču. Skor ga koristi kada su podaci dostupni.",
        caution: "Negativan FCF može ukazivati da kompanija troši više gotovine nego što stvara. Kod brzorastućih firmi tumači ga uz ulaganja i fazu poslovanja.",
        tag: "U skoru ako postoji"
      },
      {
        name: "PEG",
        sr: "Poredi P/E sa očekivanim rastom zarade. Tako možeš da sagledaš cenu u odnosu na očekivani rast.",
        good: "U ovom skoru, vrednost ispod 1 dobija najviše bodova. Od 1 do 1,5 se smatra povoljnom, a od 1,5 do 2 srednjom. PEG ispod 2 prolazi proveru vrednovanja.",
        caution: "Iznad 2 skor se smanjuje. Iznad 2,5 dodaje se upozorenje da je cena možda visoka. PEG zavisi od prognoza rasta, pa je manje pouzdan kada je rast nestabilan.",
        tag: "U skoru"
      },
      {
        name: "Forward P/E i P/E",
        sr: "P/E poredi cenu akcije sa zaradom po akciji. Forward P/E koristi očekivanu zaradu, a P/E ostvarenu zaradu.",
        good: "Kada PEG nije dostupan, forward P/E ispod 15 dobija najviši skor. Vrednost od 15 do 22 je dobra, a od 22 do 30 srednja. Ispod 30 prolazi osnovnu proveru.",
        caution: "Iznad 45 dodaje se upozorenje na visoku cenu. P/E uporedi uz rast, industriju i kvalitet zarade. Negativan P/E ne znači da je akcija jeftina.",
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
        good: "Oba podatka možeš da pregledaš. Prinos od dividende možeš da koristiš i za sortiranje akcija.",
        caution: "Trenutno ne ulaze u skor prilike. P/S ima smisla porediti sa sličnim kompanijama, a visoka dividenda sama po sebi ne znači sigurnu isplatu.",
        tag: "Prikaz, ne skor prilike"
      },
    ]
  },
  {
    sr: "Za prikaz i sortiranje", en: "For display and sorting",
    items: [
      {
        name: "Prinosi po periodima",
        sr: "Stranica akcija prikazuje promenu cene za 1 dan, 1 nedelju, 1 mesec, 6 meseci i 1 godinu.",
        good: "Pomažu da uporediš skorašnje i dugoročno kretanje cene.",
        caution: "Opisuju šta se već dogodilo, ne šta će se dogoditi. Skor prilike koristi posebne mere: momentum 12-1 mesec i pad od maksimuma.",
        tag: "Prikaz, ne skor prilike"
      }
    ]
  },
  {
    sr: "Analitičari, vesti i sektor", en: "Analysts, news and sectors",
    items: [
      {
        name: "Potencijal do ciljne cene analitičara",
        sr: "Razlika između poslednje cene akcije i prosečne ciljne cene koju navode analitičari.",
        good: "Potencijal rasta od najmanje 5% uz pad cene od 8% ispunjava osnovni uslov za kandidata. Potencijal od 10% prolazi proveru, a veći potencijal podiže skor.",
        caution: "Ciljne cene su procene analitičara, mogu kasniti za tržištem i nisu obećanje prinosa.",
        tag: "U skoru"
      },
      {
        name: "Ocena analitičara",
        sr: "Yahoo Finance skala je obično 1 = snažna kupovina, 5 = prodaja.",
        good: "Ocena do 2,3 može da zameni ciljni rast kada se bira kandidat. Što je ocena niža, skor je viši.",
        caution: "Ocena iznad 3 isključuje akciju iz oznake „ispunjava uslove“. Broj analitičara i starost procene su važni.",
        tag: "U skoru"
      },
      {
        name: "Sentiment vesti o kompaniji",
        sr: "Jednostavan rečnik prepoznaje pozitivne i negativne izraze u do 21 danu vesti o kompaniji.",
        good: "Pozitivne vesti podižu sentiment. Ako nema vesti, sentiment ostaje neutralan.",
        caution: "Ovo nije razumevanje punog konteksta: reč „rally“ ili „warning“ može biti pogrešno protumačena. Pročitaj povezane naslove.",
        tag: "U skoru"
      },
      {
        name: "Zamah teme i uticaj sektora",
        sr: "Broji koliko se o temama poput AI-ja, kamata, nafte ili odbrane piše poslednjih 7 dana u odnosu na četiri prethodna sedmodnevna perioda.",
        good: "Pozitivan uticaj sektora podiže ocenu. Vrednost iznad 0,05 prolazi osnovnu proveru.",
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
    desc: "Shows the average price over the last 50 or 200 trading days. SMA 200 helps you see the longer-term direction, while SMA 50 shows the shorter trend.",
    good: "A price above SMA 200 passes the long-term trend check. The factor score also rewards a price above SMA 200 with SMA 50 above SMA 200.",
    caution: "A price below SMA 200 means the long-term trend is weaker. It is a warning, not proof the decline will continue."
  },
  "RSI (14)": {
    desc: "The Relative Strength Index compares recent daily gains and losses on a 0-100 scale.",
    good: "The strongest technical score is an RSI of 30-50 that is higher than five trading days earlier, while price is above SMA 200. The checklist accepts 30-55.",
    caution: "Above 70, RSI is considered overheated and lowers the score. Below 30 while RSI is still falling may mean the price is still weakening. A low RSI alone is not a buy signal."
  },
  "Odmak od maksimuma za 52 nedelje": {
    desc: "Shows how far the price is below its highest level over the last year.",
    good: "A decline of at least 8% can enter the candidate list. The discount component increases with the drop, up to 40%.",
    caution: "A falling price is not automatically cheap. It may reflect a weaker business, so check the trend, company data, and news too."
  },
  "Momentum za 12-1 mesec": {
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
    desc: "A golden cross happens when SMA 50 moves above SMA 200. A death cross happens when it moves below SMA 200.",
    good: "A golden cross is added as a positive reason when detected.",
    caution: "A death cross is shown as a risk. The app compares the averages now and ten trading days earlier, so the signal can lag."
  },
  "Rast prihoda": {
    desc: "Year-over-year change in company revenue, based on Yahoo Finance data.",
    good: "Growth above 10% passes the basic check. The guide considers growth above 20% fast.",
    caution: "Negative revenue growth is flagged as a risk. Check whether the decline is temporary and compare companies in the same industry."
  },
  "ROE - prinos na kapital": {
    desc: "Net income compared with shareholder equity. It shows how much profit a company earns on its equity.",
    good: "Higher ROE contributes to the quality score. Above 15% counts as a positive signal, but its contribution to that part of the score is capped at 25%.",
    caution: "Very high ROE can also result from heavy debt or low equity, so read it alongside leverage."
  },
  "Profitna marža": {
    desc: "The share of revenue left as net income after expenses.",
    good: "A positive margin passes the checklist. Higher margins improve the quality component, up to a 20% cap.",
    caution: "Zero or negative margin fails the profitability check. Compare margins mainly within the same industry."
  },
  "Slobodan novčani tok / tržišna vrednost": {
    desc: "Free cash flow divided by market capitalization: how much cash the business generates relative to its market value.",
    good: "A yield of 3% or more passes the basic check. Above 5% is a strong result according to the guide. The score uses it when data is available.",
    caution: "Negative free cash flow may mean the company is using more cash than it generates. For fast-growing firms, consider investment needs and business stage."
  },
  "PEG": {
    desc: "PEG compares P/E with expected earnings growth. It helps you view a company's price in the context of that growth.",
    good: "In this score, below 1 gets the highest points. A value from 1 to 1.5 is favorable, and 1.5 to 2 is mid-range. Below 2 passes the valuation check.",
    caution: "Above 2 lowers the score. Above 2.5 is flagged as potentially expensive. PEG depends on growth forecasts, so it is less reliable when growth is unstable."
  },
  "Forward P/E i P/E": {
    desc: "P/E compares the share price with earnings per share. Forward P/E uses expected earnings, while trailing P/E uses reported earnings.",
    good: "When PEG is unavailable, forward P/E below 15 gets the highest score. A value from 15 to 22 is good, and 22 to 30 is mid-range. Below 30 passes the basic check.",
    caution: "Above 45 is flagged as potentially expensive. Read P/E alongside growth, industry, and earnings quality. A negative P/E does not mean a stock is cheap."
  },
  "Dug / kapital (D/E)": {
    desc: "Debt relative to shareholder equity. Yahoo Finance reports it as a percentage.",
    good: "Below 150% passes the checklist.",
    caution: "Above 200% is flagged as high debt. These are rough checks and vary by industry, especially for banks and utilities."
  },
  "P/S i dividenda": {
    desc: "P/S compares market value with revenue. A dividend is cash paid to shareholders.",
    good: "You can review both figures. Dividend yield can also help you sort the full stock list.",
    caution: "Neither affects the opportunity score. Compare P/S with similar companies. A high dividend yield does not guarantee that the payment will continue."
  },
  "Potencijal do ciljne cene analitičara": {
    desc: "The difference between the latest share price and the analysts' average target price.",
    good: "At least 5% upside plus an 8% price drop meets the basic candidate rule. 10% passes the check, and greater upside improves the score.",
    caution: "Targets are analyst estimates, can lag the market, and are not promised returns."
  },
  "Ocena analitičara": {
    desc: "Yahoo Finance's scale is generally 1 = strong buy and 5 = sell.",
    good: "A rating of 2.3 or better can stand in for target upside when selecting candidates. Lower ratings improve the score.",
    caution: "A rating above 3 prevents the stock from receiving the “qualifies” flag. The analyst count and estimate date matter."
  },
  "Sentiment vesti o kompaniji": {
    desc: "A simple word dictionary scores positive and negative phrases in company news from the last 21 days.",
    good: "Positive news raises the sentiment component. With no news, the component starts at neutral.",
    caution: "This does not understand full context: words such as “rally” or “warning” can be misread. Read the linked headlines."
  },
  "Zamah teme i uticaj sektora": {
    desc: "Counts how often themes such as AI, rates, oil, or defence appear in the last 7 days versus the four previous 7-day periods.",
    good: "A positive sector effect raises the score. An effect above 0.05 passes the basic check.",
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
        <p>{L("Ovo su pravila po kojima aplikacija rangira akcije, a ne univerzalne granice za dobre i loše akcije. Pragovi su okvirni i razlikuju se po industrijama. Nijedan indikator sam po sebi ne potvrđuje da je akcija za kupovinu. Podaci mogu da nedostaju ili kasne. Sadržaj služi za istraživanje, nije investicioni savet.", "These are the app's ranking rules, not universal cutoffs for good and bad stocks. Thresholds are approximate and vary by industry. No single indicator confirms that a stock is worth buying. Data may be missing or delayed. This is for research, not investment advice.")}</p>
      </Card>

      <section className="mb-10">
        <SectionTitle>{L("Kako nastaje skor prilike (0-100)", "How the opportunity score is built (0-100)")}</SectionTitle>
        <p className="mb-4 text-sm text-cream-400">{L("Skor prilike je ponderisani zbir. „Ispunjava uslove“ je zasebna oznaka: pad od najmanje 8% i ili potencijal analitičara od 5% ili ocena do 2,3, uz ocenu najviše 3. Lista prvo poređa one koji ispunjavaju uslove, pa ostale po skoru.", "The opportunity score is a weighted sum. “Qualifies” is a separate flag: at least an 8% drop and either 5% analyst upside or a rating of 2.3 or better, with rating no worse than 3. The list sorts qualifying names first, then the rest by score.")}</p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{SCORES.map((x) => (
          <Card key={x.value + x.sr} className="p-4">
            <div className="stat-label">{L(x.sr, x.en)}</div><div className="mt-1 font-mono text-2xl text-cream-50">{x.value}</div>
          </Card>
        ))}</div>
        <p className="mt-3 text-xs text-cream-500">{L("„Nož koji pada“ umanjuje skor za 25%. Pregrejana akcija sa RSI iznad 70 umanjuje ga za 15%.", "A falling-knife setup reduces the score by 25%. An overheated stock with RSI above 70 reduces it by 15%.")}</p>
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
          {L("U tabu „Istraži sve“ postoji i faktorski skor: momentum 25%, cilj analitičara 20%, P/E 15%, ROE 15%, rast prihoda 10% i niža volatilnost 15%. Faktori se porede sa drugim akcijama na listi. Dugoročni trend dodaje 10% konačnom skoru. Ovaj skor se zato razlikuje od skora prilike iznad.", "The “Explore all” tab also has a factor score: momentum 25%, analyst target 20%, P/E 15%, ROE 15%, revenue growth 10%, and lower volatility 15%. Factors are ranked against other stocks on the list. Long-term trend adds 10% to the final score. This is different from the opportunity score above.")}
        </Card>
      </section>

      <div className="mt-10 flex items-center gap-2 text-xs text-cream-500">
        <BookOpen size={14} />
        <span>{L("Za definiciju P/E pogledaj", "For a definition of P/E, see")} <a className="text-cream-300 underline" href="https://www.investor.gov/introduction-investing/investing-basics/glossary/price-earnings-pe-ratio" target="_blank" rel="noreferrer">Investor.gov</a>.</span>
      </div>
    </div>
  );
}
