import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { BookOpen, Info, RotateCw } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
import { PageHead } from "../components/Shell";
import { Card, SectionTitle } from "../components/ui";
import Tex from "../components/Tex";
import { FORMULAS, texFor } from "../lib/formulas";

const GROUPS = [
  {
    sr: "Kretanje cene i trenutak", en: "Price action and timing",
    items: [
      {
        name: "SMA 50 / SMA 200",
        sr: "Prosečna cena u poslednjih 50, odnosno 200 trgovačkih dana. SMA 200 ti kaže kuda akcija ide na duže staze, a SMA 50 kakav je trend poslednjih par meseci.",
        good: "Ako je cena iznad SMA 200, dugoročni trend je na tvojoj strani. Kad je uz to i SMA 50 iznad SMA 200, akcija dobija dodatni bod u faktorskoj oceni.",
        caution: "Cena ispod SMA 200 znači da dugoročni trend slabi. To je znak za oprez, a ne dokaz da će pad da se nastavi - pogledaj da li se cena vraća ka proseku.",
        tag: "Ulazi u ocenu"
      },
      {
        name: "RSI (14)",
        sr: "Pokazuje koliko su snažni dnevni skokovi u odnosu na dnevne padove u poslednje dve nedelje, na skali od 0 do 100.",
        good: "Najbolji trenutak za ulaz po ovoj aplikaciji: RSI između 30 i 50 koji je viši nego pre pet dana, dok je cena iznad SMA 200. Vrednosti od 30 do 55 prolaze osnovnu proveru.",
        caution: "Iznad 70 akcija je pregrejana i ocena joj se smanjuje - bolje sačekaj povlačenje. Ispod 30, ako RSI i dalje pada, prodavci još nisu završili. Nizak RSI sam po sebi nije razlog za kupovinu.",
        tag: "Ulazi u ocenu"
      },
      {
        name: "Odmak od maksimuma za 52 nedelje",
        sr: "Koliko je cena danas ispod najviše cene iz poslednjih godinu dana.",
        good: "Akcija postaje kandidat kad je bar 8% ispod maksimuma. Što je pad veći, do 40%, to više bodova dobija za „popust“.",
        caution: "Pad ne znači automatski da je akcija jeftina - nekad tržište s razlogom kažnjava lošije poslovanje. Zato uvek pogledaj i trend, rezultate i vesti.",
        tag: "Ulazi u ocenu"
      },
      {
        name: "Momentum za 12-1 mesec",
        sr: "Koliko je cena porasla ili pala tokom prethodne godine, bez poslednjeg meseca (on se izostavlja jer kratkoročno često skreće).",
        good: "Akcije koje su u toku godine bile jače od ostalih sa liste dobijaju višu faktorsku ocenu - jak trend ume da potraje.",
        caution: "Ovo je poređenje unutar tvoje liste, ne opšti prag. Dobar prošli prinos ne garantuje dobar budući.",
        tag: "Relativna ocena"
      },
      {
        name: "Godišnja volatilnost",
        sr: "Koliko se cena akcije ljulja, preračunato na godinu. Volatilnost od 30% znači da su pomeranja od ±30% u toku godine sasvim moguća.",
        good: "Mirnije akcije dobijaju bolju faktorsku ocenu u poređenju sa ostalima.",
        caution: "Iznad 45% godišnje aplikacija ovo označava kao rizik. Visoka volatilnost ne znači lošu kompaniju, već da treba manja pozicija i jači živci.",
        tag: "Ulazi u ocenu"
      },
      {
        name: "Zlatni / mrtvački krst",
        sr: "Trenutak kada prosek od 50 dana pređe iznad proseka od 200 dana (trend se okreće naviše) ili padne ispod njega (trend se okreće naniže).",
        good: "Kad kratkoročni prosek pređe iznad dugoročnog, aplikacija to navodi kao jedan od razloga za akciju.",
        caution: "Pad kratkoročnog proseka ispod dugoročnog ide u listu rizika. Aplikacija poredi proseke danas i pre deset dana, pa signal stiže sa malim zakašnjenjem.",
        tag: "Dodatni signal"
      },
    ]
  },
  {
    sr: "Poslovanje i vrednovanje", en: "Business and valuation",
    items: [
      {
        name: "Rast prihoda",
        sr: "Za koliko su prihodi kompanije veći (ili manji) nego u istom periodu prošle godine, prema Yahoo Finance.",
        good: "Rast iznad 10% prolazi osnovnu proveru, a iznad 20% se smatra brzim rastom.",
        caution: "Pad prihoda se označava kao rizik. Proveri da li je privremen (npr. jedan loš kvartal) i kako stoje konkurenti iz iste industrije.",
        tag: "Ulazi u ocenu"
      },
      {
        name: "ROE - prinos na kapital",
        sr: "Koliko dobiti kompanija zaradi na novac akcionara. ROE od 20% znači 20 € dobiti na svakih 100 € kapitala.",
        good: "ROE iznad 15% je dobar znak i podiže ocenu kvaliteta (najviše do četvrtine tog dela ocene).",
        caution: "Vrlo visok ROE ponekad dolazi od velikog duga ili malog kapitala, a ne od dobrog poslovanja - zato ga uvek gledaj zajedno sa D/E.",
        tag: "Ulazi u ocenu"
      },
      {
        name: "Profitna marža",
        sr: "Koliko od svakog evra prihoda ostane kao čista dobit kada se plate svi troškovi.",
        good: "Pozitivna marža prolazi proveru, a što je viša (do 20%), to bolje za ocenu kvaliteta.",
        caution: "Nulta ili negativna marža znači da kompanija trenutno ne zarađuje. Marže poredi samo unutar iste industrije - trgovina i softver imaju sasvim različite normalne nivoe.",
        tag: "Ulazi u ocenu"
      },
      {
        name: "Slobodan novčani tok / tržišna vrednost",
        sr: "Koliko slobodnog novca poslovanje donese u odnosu na cenu cele kompanije - koliko „prave“ gotovine dobijaš za cenu koju plaćaš.",
        good: "Prinos od 3% ili više prolazi proveru, a iznad 5% je odličan. Ulazi u ocenu kad podaci postoje.",
        caution: "Negativan FCF znači da kompanija troši više gotovine nego što stvara. Kod firmi koje brzo rastu to može biti privremeno zbog ulaganja - proveri da li se jaz smanjuje.",
        tag: "U oceni kad postoji"
      },
      {
        name: "PEG",
        sr: "P/E podeljen očekivanim rastom dobiti. Pomaže da proceniš da li je visoka cena opravdana brzim rastom.",
        good: "PEG ispod 1 dobija najviše bodova, od 1 do 1,5 je povoljan, a od 1,5 do 2 prihvatljiv. Sve ispod 2 prolazi proveru vrednovanja.",
        caution: "Iznad 2 ocena pada, a iznad 2,5 aplikacija upozorava da je cena verovatno visoka. PEG počiva na prognozama rasta, pa je nepouzdan kad je rast neujednačen.",
        tag: "Ulazi u ocenu"
      },
      {
        name: "Forward P/E i P/E",
        sr: "Koliko puta je cena akcije veća od dobiti po akciji. P/E koristi ostvarenu dobit, a forward P/E očekivanu za narednu godinu.",
        good: "Ako PEG ne postoji, forward P/E ispod 15 dobija najviše bodova, od 15 do 22 je dobar, a od 22 do 30 prosečan. Ispod 30 prolazi osnovnu proveru.",
        caution: "Iznad 45 aplikacija upozorava na visoku cenu. Negativan P/E znači gubitak, a ne jeftinu akciju. P/E uvek poredi sa rastom i sa firmama iz iste branše.",
        tag: "Ulazi u ocenu"
      },
      {
        name: "Dug / kapital (D/E)",
        sr: "Koliki je dug kompanije u odnosu na kapital akcionara, u procentima. D/E od 100% znači da je dug jednak kapitalu.",
        good: "Ispod 150% prolazi proveru.",
        caution: "Iznad 200% aplikacija označava visok dug. Ovo je gruba provera - banke i komunalna preduzeća normalno imaju više duga od tehnoloških firmi.",
        tag: "Provera rizika"
      },
      {
        name: "P/S i dividenda",
        sr: "P/S pokazuje koliko je tržišna vrednost veća od godišnjeg prihoda. Dividenda je deo dobiti koji kompanija isplaćuje akcionarima.",
        good: "Oba podatka vidiš kod svake akcije, a po prinosu od dividende možeš i da sortiraš listu.",
        caution: "Trenutno ne ulaze u ocenu prilike. P/S ima smisla samo u poređenju sa sličnim firmama, a visoka dividenda ne garantuje da će isplata ostati ista.",
        tag: "Samo za prikaz"
      },
    ]
  },
  {
    sr: "Za prikaz i sortiranje", en: "For display and sorting",
    items: [
      {
        name: "Prinosi po periodima",
        sr: "Promena cene za 1 dan, 1 nedelju, 1 mesec, 6 meseci i 1 godinu - prikazana kod svake akcije.",
        good: "Brzo vidiš da li je skorašnje kretanje u skladu sa dugoročnim.",
        caution: "Pokazuju šta se već desilo, ne šta će se desiti. Za ocenu prilike koriste se momentum 12-1 mesec i pad od maksimuma.",
        tag: "Samo za prikaz"
      }
    ]
  },
  {
    sr: "Analitičari, vesti i sektor", en: "Analysts, news and sectors",
    items: [
      {
        name: "Potencijal do ciljne cene analitičara",
        sr: "Koliko je prosečna ciljna cena analitičara iznad (ili ispod) današnje cene.",
        good: "Akcija postaje kandidat kad je potencijal bar 5% uz pad od 8%. Potencijal od 10% prolazi proveru, a svaki veći dodatno podiže ocenu.",
        caution: "Ciljne cene su procene koje često kasne za tržištem - nisu obećanje prinosa. Pogledaj kada su postavljene.",
        tag: "Ulazi u ocenu"
      },
      {
        name: "Ocena analitičara",
        sr: "Prosečna preporuka analitičara na skali Yahoo Finance: 1 = snažna kupovina, 3 = drži, 5 = prodaj.",
        good: "Ocena do 2,3 može da zameni uslov o potencijalu pri izboru kandidata. Što je bliža 1, to je ocena prilike viša.",
        caution: "Iznad 3 akcija ne dobija oznaku „ispunjava uslove“. Bitni su i broj analitičara i to koliko su procene stare.",
        tag: "Ulazi u ocenu"
      },
      {
        name: "Sentiment vesti o kompaniji",
        sr: "Ton vesti o kompaniji iz poslednjih 21 dan, prepoznat po pozitivnim i negativnim izrazima.",
        good: "Dobre vesti podižu sentiment. Kad vesti nema, ostaje neutralan.",
        caution: "Ovo nije čitanje sa razumevanjem - reč poput „rally“ ili „warning“ može da se pogrešno protumači. Pročitaj bar naslove pre odluke.",
        tag: "Ulazi u ocenu"
      },
      {
        name: "Zamah teme i uticaj sektora",
        sr: "Koliko se o temama kao što su AI, kamate, nafta ili odbrana piše u poslednjih 7 dana, u poređenju sa prethodne četiri nedelje.",
        good: "Kad tema koja pomaže sektoru dobija na značaju, ocena raste. Vrednost iznad 0,05 prolazi proveru.",
        caution: "Ispod -0,15 uticaj se smatra nepovoljnim. Više vesti o nekoj temi nije dokaz da će cena rasti.",
        tag: "Ulazi u ocenu"
      },
    ]
  },
  {
    sr: "Pokazatelji van ocene prilike", en: "Indicators outside the opportunity score",
    items: [
      { name: "MACD", sr: "Razlika između brzog i sporog eksponencijalnog proseka cene - pokazuje smer i snagu trenda.", good: "Kad MACD pređe iznad signalne linije, zamah možda jača. Potvrdu traži u ceni i obimu trgovanja.", caution: "Kasni i često daje lažne signale kad cena ide bočno. Aplikacija ga ne računa.", tag: "Ne ulazi u ocenu" },
      { name: "Bollingerovi opsezi", sr: "Pojas oko 20-dnevnog proseka, širok dve standardne devijacije - pokazuje koliko je cena odmakla od uobičajenog.", good: "Kad se pojas suzi, tržište se smirilo, a to često prethodi većem pomeranju. Smer moraš da potvrdiš na drugi način.", caution: "Dodir gornje ili donje ivice nije sam po sebi signal za kupovinu ili prodaju. Aplikacija ih ne računa.", tag: "Ne ulazi u ocenu" },
      { name: "Transakcije insajdera", sr: "Prijave Form 4 u SAD pokazuju kada direktori i drugi insajderi kupuju ili prodaju akcije svoje kompanije.", good: "Kupovina na otvorenom tržištu, naročito kad kupuje više insajdera odjednom, može biti koristan dodatni signal.", caution: "Nagrade, opcije i prodaja zbog poreza nisu isto što i dobrovoljna kupovina. Ove prijave nisu u podacima aplikacije.", tag: "Ne ulazi u ocenu" },
      { name: "Ulaganja fondova (13F)", sr: "Kvartalni izveštaji 13F pokazuju koje akcije drže veliki američki fondovi.", good: "Promena broja akcija između dva izveštaja pokazuje da li fond povećava ili smanjuje poziciju.", caution: "Izveštaji stižu i do 45 dana posle kraja kvartala, ne pokazuju kratke pozicije i nisu cela slika portfolija.", tag: "Ne ulazi u ocenu" },
    ]
  },
];

const EXCLUDED_INDICATORS = GROUPS.find((group) => group.sr === "Pokazatelji van ocene prilike").items;

const DISPLAY_NAMES = {"SMA 50 / SMA 200":["Prosti pokretni prosek (Simple Moving Average, SMA 50 / SMA 200)","Simple Moving Average (SMA 50 / SMA 200)"],"RSI (14)":["Indeks relativne snage (Relative Strength Index, RSI 14)","Relative Strength Index (RSI 14)"],"Odmak od maksimuma za 52 nedelje":["Pad od maksimuma za 52 nedelje (52-Week Drawdown, 52W DD)","52-Week Drawdown (52W DD)"],"Momentum za 12-1 mesec":["Momentum za 12-1 mesec (12-1 Month Momentum, 12-1M)","12-1 Month Momentum (12-1M)"],"Godišnja volatilnost":["Godišnja volatilnost (Annualized Volatility, Vol)","Annualized Volatility (Vol)"],"Zlatni / mrtvački krst":["Ukrštanje proseka 50 i 200 dana (Golden / Death Cross)","Golden Cross / Death Cross (SMA 50 / SMA 200)"],"Rast prihoda":["Rast prihoda (Revenue Growth, YoY)","Revenue Growth (YoY)"],"ROE - prinos na kapital":["Prinos na kapital (Return on Equity, ROE)","Return on Equity (ROE)"],"Profitna marža":["Neto profitna marža (Net Profit Margin, NPM)","Net Profit Margin (NPM)"],"Slobodan novčani tok / tržišna vrednost":["Prinos slobodnog novčanog toka (Free Cash Flow Yield, FCF Yield)","Free Cash Flow Yield (FCF Yield)"],"PEG":["Odnos cene i rasta zarade (Price/Earnings-to-Growth, PEG)","Price/Earnings-to-Growth (PEG)"],"Forward P/E i P/E":["Očekivani i ostvareni P/E (Forward P/E and Trailing P/E, P/E)","Forward P/E and Trailing P/E (P/E)"],"Dug / kapital (D/E)":["Dug u odnosu na kapital (Debt-to-Equity Ratio, D/E)","Debt-to-Equity Ratio (D/E)"],"P/S i dividenda":["Cena u odnosu na prodaju i prinos dividende (Price-to-Sales and Dividend Yield, P/S and DY)","Price-to-Sales and Dividend Yield (P/S and DY)"],"Prinosi po periodima":["Prinosi po periodima (Period Returns, 1D / 1W / 1M / 6M / 1Y)","Period Returns (1D / 1W / 1M / 6M / 1Y)"],"Potencijal do ciljne cene analitičara":["Potencijal do ciljne cene (Analyst Target Upside, Target Upside)","Analyst Target Upside (Target Upside)"],"Ocena analitičara":["Konsenzus analitičara (Analyst Consensus Rating, Rating)","Analyst Consensus Rating (Rating)"],"Sentiment vesti o kompaniji":["Sentiment vesti (Company News Sentiment, Sentiment)","Company News Sentiment (Sentiment)"],"Zamah teme i uticaj sektora":["Zamah tema i uticaj sektora (Sector Momentum and Tailwind, Tailwind)","Sector Momentum and Tailwind (Tailwind)"],"MACD":["Pokretni prosek konvergencije i divergencije (Moving Average Convergence Divergence, MACD)","Moving Average Convergence Divergence (MACD)"],"Bollingerovi opsezi":["Bollingerovi opsezi (Bollinger Bands, BB)","Bollinger Bands (BB)"],"Transakcije insajdera":["Transakcije insajdera (Insider Transactions, Form 4)","Insider Transactions (Form 4)"],"Ulaganja fondova (13F)":["Prijavljene pozicije fondova (Institutional Holdings, Form 13F)","Institutional Holdings (Form 13F)"]};

const DETAILS = {"SMA 50 / SMA 200":["SMA n = prosek zaključnih cena za poslednjih n dana", "SMA n = average closing price over the last n trading days", "Primer: cena je 120 $, SMA 200 je 100 $, a SMA 50 je 115 $. Cena je 20% iznad dugoročnog proseka, a kratkoročni prosek je iznad dugoročnog - trend je zdrav. Proseci kasne, pa nagli pad vide tek posle nekoliko dana.", "Compare price with SMA 200 to see whether the long-term trend is stronger or weaker. SMA 50 above SMA 200 points to stronger shorter-term momentum. Moving averages lag sudden price changes."],"RSI (14)":["RSI = 100 - 100 / (1 + RS). RS je prosek rasta podeljen prosekom pada tokom 14 dana.", "RSI = 100 - 100 / (1 + RS). RS is average gains divided by average losses over 14 days.", "Primer: RSI je pre pet dana bio 35, a danas je 42, dok je cena iznad SMA 200. To je povlačenje u rastućem trendu - najbolji tehnički signal u ovoj oceni. RSI od 75 bi značio da je cena verovatno prebrzo porasla.", "Example: an RSI of 42 that is rising while price is above SMA 200 fits the more favorable technical setup in this score. Above 70 may warn that price has risen too quickly. RSI alone is not a buy signal."],"Odmak od maksimuma za 52 nedelje":["Pad (%) = (trenutna cena / najviša cena u 52 nedelje - 1) × 100","Drawdown (%) = (current price / 52-week high - 1) × 100","Primer: cena je 90 €, a maksimum 100 €. Pad je 10%. To može otvoriti proveru kandidata, ali prvo pogledaj da li se poslovanje pogoršalo.","Example: price is €90 and the 52-week high is €100. The drawdown is 10%. That may qualify the stock for a closer look, but first check whether the business has weakened."],"Momentum za 12-1 mesec":["Momentum = cena pre 1 mesec / cena pre 12 meseci - 1", "Momentum = price 1 month ago / price 12 months ago - 1", "Primer: pre 12 meseci cena je bila 80 $, a pre mesec dana 100 $ - momentum je +25%. Ako je većina akcija na listi porasla manje, ova dobija visok rang, bez obzira na to šta se desilo poslednjih 30 dana.", "The latest month is excluded so a short-term jump or drop has less influence. This is a relative measure - compare the stock with others on the list."],"Godišnja volatilnost":["Volatilnost ≈ standardna devijacija dnevnih prinosa × √252", "Volatility ≈ standard deviation of daily returns × √252", "Primer: volatilnost od 40% znači da su pomeranja od ±40% tokom godine sasvim uobičajena. Kod takve akcije uzmi manju poziciju i kupuj u delovima, da te jedan loš mesec ne izbaci iz takta.", "Use it to gauge how widely the price tends to swing. A high value means larger ups and downs, so consider position size and your risk tolerance."],"Zlatni / mrtvački krst":["Naviše: SMA 50 prelazi iznad SMA 200. Naniže: SMA 50 prelazi ispod SMA 200.", "Golden cross: SMA 50 crosses above SMA 200. Death cross: SMA 50 crosses below SMA 200.", "Primer: SMA 50 je pre deset dana bio 98 $ ispod SMA 200 od 100 $, a danas je 101 $ - prosek od 50 dana je upravo prešao iznad dugoročnog. Signal potvrđuje promenu tek kad se dogodi, pa obično kasni nekoliko nedelja za samim preokretom.", "The signal confirms a trend change only after the averages cross. The app compares the averages now with their levels 10 trading days ago, so the signal can lag."],"Rast prihoda":["Rast prihoda (%) = (prihod u periodu / prihod u istom periodu prošle godine - 1) × 100","Revenue growth (%) = (revenue this period / revenue in the same period last year - 1) × 100","Primer: prihod je porastao sa 100 na 110 miliona. Rast je 10%. Zatim proveri da li rast prate dobit i novčani tok.","Example: revenue grew from 100 to 110 million. Growth is 10%. Then check whether profit and cash flow are growing too."],"ROE - prinos na kapital":["ROE (%) = neto dobit / kapital akcionara × 100", "ROE (%) = net income / shareholder equity × 100", "Primer: dobit 25 miliona, kapital akcionara 100 miliona - ROE je 25%. Ako je D/E u isto vreme 300%, deo tog ROE dolazi od duga, a ne od samog poslovanja.", "Shows how much profit a company generates relative to shareholder equity. Compare companies in the same industry. Check very high ROE against debt, which can inflate it."],"Profitna marža":["Neto marža (%) = neto dobit / prihod × 100","Net margin (%) = net income / revenue × 100","Primer: od 100 € prihoda ostane 12 € neto dobiti. Marža je 12%. Poredi je sa sličnim firmama, jer se uobičajene marže razlikuju po industrijama.","Example: a company keeps €12 of net profit from €100 in revenue. Its margin is 12%. Compare it with similar companies because normal margins vary by industry."],"Slobodan novčani tok / tržišna vrednost":["FCF yield (%) = slobodan novčani tok / tržišna kapitalizacija × 100", "FCF yield (%) = free cash flow / market capitalization × 100", "Primer: kompanija vredi 10 milijardi, a godišnje joj ostane 500 miliona slobodnog novca - prinos je 5%. Kad bi je kupila celu, to bi bilo kao kamata od 5% u gotovini.", "Shows how much cash the business generates relative to its market value. A negative result calls for a closer look at investment and cash needs."],"PEG":["PEG ≈ forward P/E / očekivani godišnji rast zarade izražen u procentima","PEG ≈ forward P/E / expected annual earnings growth expressed as a percentage","Primer: P/E je 20, a očekivani rast zarade 20% - PEG je približno 1. Prognoza rasta može biti pogrešna, zato PEG uporedi sa ostalim pokazateljima.","Example: P/E is 20 and expected earnings growth is 20% - PEG is about 1. Growth forecasts can be wrong, so read PEG alongside other indicators."],"Forward P/E i P/E":["Forward P/E = cena / očekivana zarada po akciji. P/E = cena / ostvarena zarada po akciji.", "Forward P/E = price / forecast earnings per share. P/E = price / reported earnings per share.", "Primer: P/E je 30, a forward P/E 20. Tržište očekuje da dobit poraste oko 50% u narednoj godini. Ako se to ne ostvari, akcija je zapravo skuplja nego što izgleda.", "Compare both measures. A lower forward P/E than trailing P/E may point to expected earnings growth, but check the forecasts and compare companies in the same sector."],"Dug / kapital (D/E)":["D/E (%) = ukupan dug / kapital akcionara × 100","D/E (%) = total debt / shareholder equity × 100","Primer: dug od 50 miliona prema kapitalu od 100 miliona daje D/E od 50%. Viši odnos znači veće oslanjanje na dug. Pragove poredi unutar industrije.","Example: €50 million of debt against €100 million of equity gives a D/E of 50%. A higher ratio means more reliance on debt. Compare thresholds within the same industry."],"P/S i dividenda":["P/S = tržišna kapitalizacija / godišnji prihod. Dividend yield (%) = godišnja dividenda po akciji / cena akcije × 100.", "P/S = market capitalization / annual revenue. Dividend yield (%) = annual dividend per share / share price × 100.", "Primer: kompanija vredi 50 milijardi uz prihod od 10 milijardi - P/S je 5. Dividenda od 2 $ uz cenu od 50 $ daje prinos od 4%. Ako je prinos skočio jer je cena pala, proveri da li je isplata održiva.", "Compare P/S with similar companies and their margins. A high dividend yield may result from a falling share price, so check whether the payment is sustainable. These measures are not part of the opportunity score."],"Prinosi po periodima":["Prinos (%) = (cena na kraju perioda / cena na početku perioda - 1) × 100", "Return (%) = (price at end of period / price at start of period - 1) × 100", "Primer: +2% za mesec, ali -15% za godinu - akcija se možda oporavlja, ali je dugoročno i dalje slaba. Za poređenje dve akcije uvek gledaj isti period.", "Use the same period when comparing stocks. Past return describes price movement, but does not predict future performance."],"Potencijal do ciljne cene analitičara":["Potencijal (%) = (prosečna ciljna cena / trenutna cena - 1) × 100","Upside (%) = (average analyst target / current price - 1) × 100","Primer: cilj je 110 €, a cena 100 €. Potencijal je 10%. To je procena analitičara, ne obećanje da će cena dostići cilj.","Example: the target is €110 and the current price is €100. Upside is 10%. This is an analyst estimate, not a promise that price will reach the target."],"Ocena analitičara":["Prosek preporuka koje prijavljuje izvor podataka. Skala je obično 1 = snažna kupovina, 5 = prodaja.", "Average recommendation reported by the data provider. The scale is usually 1 = strong buy and 5 = sell.", "Primer: ocena 1,8 od 25 analitičara je jak konsenzus za kupovinu. Ista ocena od samo 3 analitičara je mnogo slabiji signal - jedan novi glas je može pomeriti.", "A lower rating means a more positive consensus. Check the analyst count and estimate date because a small or outdated sample can mislead."],"Sentiment vesti o kompaniji":["Nema jednostavne formule. Pozitivni i negativni izrazi iz vesti se sabiraju, pa se rezultat pretvara u komponentu od 0 do 1.", "No single simple formula. Positive and negative words in recent news are scored and converted to a 0-1 component.", "Primer: naslov „Nvidia beats estimates, shares rally“ se računa kao pozitivan. Ali „No warning signs despite rally“ može da se pogrešno pročita - zato otvori naslove pre odluke.", "The algorithm spots words, but does not understand the full story. Open the headlines and check the context before relying on sentiment."],"Zamah teme i uticaj sektora":["Zamah teme poredi broj vesti poslednjih 7 dana sa četiri prethodna perioda od po 7 dana. Uticaj se ograničava na raspon od -1 do 1.", "Theme momentum compares news from the last 7 days with the four previous 7-day periods. Sector effect is bounded from -1 to 1.", "Primer: o AI čipovima je ove nedelje bilo 40 vesti, a prosečno 20 nedeljno pre toga - zamah je 2. To podiže ocenu poluprovodničkih akcija, ali sama pažnja medija nije garancija rasta.", "Use it to see whether coverage of a topic is rising or falling and how it relates to a sector. More headlines do not automatically mean prices will rise."],
  "MACD":["MACD = EMA(12) - EMA(26). Signal = EMA(9) MACD-a. Histogram = MACD - signal.", "MACD = EMA(12) - EMA(26). Signal = 9-period EMA of MACD. Histogram = MACD - signal.", "Primer: MACD je bio ispod signalne linije, a danas je prešao iznad nje uz rast obima trgovanja - zamah možda jača. Bez rasta obima signal je slabiji. Aplikacija ga ne računa.", "A MACD cross above its signal line may point to strengthening momentum. Look for confirmation in price and volume. Signals can lag, and this indicator is not used in the app's score."],
  "Bollingerovi opsezi":["Srednja linija = SMA(20). Gornja = SMA(20) + 2 × standardna devijacija. Donja = SMA(20) - 2 × standardna devijacija.", "Middle band = SMA(20). Upper band = SMA(20) + 2 × standard deviations. Lower band = SMA(20) - 2 × standard deviations.", "Primer: pojas je mesecima bio širok ±8%, a sada samo ±3% - tržište se smirilo i često sledi veće pomeranje, ali opsezi ne govore u kom smeru. Aplikacija ih ne računa.", "A squeeze shows lower recent volatility, but does not predict which way price will move. Touching a band is not a standalone signal. The app's data does not include them."],
  "Transakcije insajdera":["Nema jedne standardne formule. Neto kupovina = kupovine na otvorenom tržištu - prodaje na otvorenom tržištu u izabranom periodu.", "There is no single standard formula. Net purchases = open-market purchases - open-market sales over the selected period.", "Primer: tri direktora su u istoj nedelji kupila akcije svojim novcem - to je jači signal od jedne prodaje radi plaćanja poreza na nagradu. Aplikacija ne preuzima ove prijave.", "Form 4 filings distinguish transaction types. Awards, option exercises, and tax sales differ from voluntary open-market purchases. The app does not retrieve these filings."],
  "Ulaganja fondova (13F)":["Promena pozicije = prijavljen broj akcija u novom izveštaju - broj u prethodnom izveštaju.", "Position change = shares reported in the new filing - shares reported in the previous filing.", "Primer: fond je u junu prijavio 1 milion akcija, a u septembru 1,5 miliona - povećao je poziciju za 50%. Ali izveštaj stiže i do 45 dana kasnije, pa je fond do tada možda već prodao.", "Compare the same securities across filings. 13F can lag quarter-end by up to 45 days, does not show short positions, and does not reveal a fund's current activity."]
};

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
  },
  "MACD": { desc: "MACD compares two exponential moving averages to assess trend direction and momentum.", good: "A MACD cross above its signal line may point to strengthening momentum. Check price and volume for confirmation.", caution: "Signals can lag and often misfire in sideways markets. This app does not calculate it." },
  "Bollingerovi opsezi": { desc: "Bands show how far price moves from a moving average relative to recent volatility.", good: "A squeeze can point to a quieter period before a larger move, but direction needs confirmation.", caution: "Touching the upper or lower band alone is not a buy or sell signal. This app does not calculate the bands." },
  "Transakcije insajdera": { desc: "US Form 4 filings report certain share purchases and sales by company directors and other insiders.", good: "Open-market purchases can add context, especially when several insiders buy.", caution: "Awards, option exercises, and tax sales differ from voluntary purchases. These filings are not in the app's data." },
  "Ulaganja fondova (13F)": { desc: "US 13F filings show some positions reported by large institutional investors at quarter-end.", good: "A change in reported share count shows how a position changed between filings.", caution: "Filings can lag quarter-end by up to 45 days, omit short positions, and do not show a fund's current activity." }
};

const TAGS_EN = {
  "Ulazi u ocenu": "In score",
  "Relativna ocena": "Relative score",
  "Dodatni signal": "Additional signal",
  "U oceni kad postoji": "In score when available",
  "Provera rizika": "Risk check",
  "Samo za prikaz": "Displayed, not in opportunity score",
  "Ne ulazi u ocenu": "Outside score",
};

function IndicatorCard({ item, en, L }) {
  const [flipped, setFlipped] = useState(false);
  const key = item.name;
  const display = DISPLAY_NAMES[key] || [key, key];
  const title = display[en ? 1 : 0];
  const text = EN[key] || {};
  const detail = DETAILS[key] || ["Nema jednostavne formule za ovaj pokazatelj.", "There is no simple formula for this indicator.", "Proveri ga zajedno sa ostalim podacima o kompaniji.", "Read it alongside the company's other data."];
  return (
    <div className="indicator-card h-full cursor-pointer rounded-2xl" role="button" tabIndex={0} aria-expanded={flipped}
      aria-label={L("Klikni za objašnjenje formule i praktične primene", "Click to see the formula and practical use")}
      onClick={() => setFlipped((value) => !value)}
      onKeyDown={(event) => { if ((event.key === "Enter" || event.key === " ") && event.target === event.currentTarget) { event.preventDefault(); setFlipped((value) => !value); } }}>
      <motion.div className="h-full" style={{ transformPerspective: 1100 }} key={flipped ? "back" : "front"} initial={{ opacity: 0, rotateY: flipped ? -80 : 80 }} animate={{ opacity: 1, rotateY: 0 }} transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}>
        {!flipped ? (
          <Card hover={false} className="indicator-face flex h-full min-h-[390px] flex-col p-4 md:p-5">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <h3 className="min-w-0 flex-1 font-display text-lg font-semibold leading-snug text-cream-50"><span className="marker">{title}</span></h3>
              <span className="rounded-full border border-wine-400/60 bg-wine-700/40 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-wine-200">{en ? TAGS_EN[item.tag] || item.tag : item.tag}</span>
            </div>
            <p className="score-copy mt-3 text-sm leading-relaxed text-cream-100">{en ? text.desc || item.sr : item.sr}</p>
            <div className="mt-3 space-y-2 text-sm">
              <p><b className="marker marker-green text-up font-semibold">{L("Povoljnije:", "More favorable:")}</b> <span className="text-cream-300">{en ? text.good || item.good : item.good}</span></p>
              <p><b className="marker text-gold-400">{L("Oprez:", "Caution:")}</b> <span className="text-cream-300">{en ? text.caution || item.caution : item.caution}</span></p>
            </div>
            <button type="button" onClick={(event) => { event.stopPropagation(); setFlipped(true); }} aria-label={L("Otvori formulu i praktičnu primenu", "Show formula and practical use")}
              className="flip-btn mt-auto">
              <RotateCw size={15} className="transition-transform duration-500" />{L("Formula i praktična primena", "Formula and practical use")}
            </button>
          </Card>
        ) : (
          <Card hover={false} className="indicator-face indicator-back flex h-full min-h-[390px] flex-col border-gold-500/45 bg-ink-850 p-4 md:p-5">
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-display text-lg font-semibold leading-snug text-cream-50">{title}</h3>
              <span className="shrink-0 rounded-full border border-gold-500/70 bg-gold-500/15 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-gold-300">{L("Kako čitati", "How to use it")}</span>
            </div>
            <Paper title={L("Formula", "Formula")} f={FORMULAS[key]} fallback={detail[en ? 1 : 0]} en={en} />
            <div className="indicator-practical mt-3 flex-1 rounded-xl border p-4">
              <div className="stat-label">{L("Praktično", "In practice")}</div>
              <p className="mt-1.5 text-sm leading-relaxed text-cream-50">{detail[en ? 3 : 2]}</p>
            </div>
            <button type="button" onClick={(event) => { event.stopPropagation(); setFlipped(false); }} aria-label={L("Vrati se na objašnjenje indikatora", "Return to indicator overview")}
              className="flip-btn flip-btn-back">
              <RotateCw size={15} className="transition-transform duration-500" />{L("Nazad na objašnjenje", "Back to overview")}
            </button>
          </Card>
        )}
      </motion.div>
    </div>
  );
}

// formula na "papiru": svetla podloga, tamno mastilo, linije sveske
function Paper({ title, f, fallback, en }) {
  return (
    <div className="paper mt-3 rounded-xl p-4 sm:p-5">
      <div className="paper-label">{title}</div>
      {f ? (
        <>
          <div className="mt-1 space-y-1 overflow-x-auto">{f.lines.map((l) => <Tex key={l} tex={texFor(l, en ? "en" : "sr")} />)}</div>
          {f.where.length > 0 && (
            <div className="paper-where mt-2 space-y-1 pt-2 text-[13px] leading-snug">
              {f.where.map(([sym, sr, e]) => (
                <div key={sym + sr} className="flex items-baseline gap-2">
                  {sym ? <><Tex tex={texFor(sym, en ? "en" : "sr")} display={false} className="shrink-0 whitespace-nowrap" /><span>-</span></> : null}<span>{en ? e : sr}</span>
                </div>
              ))}
            </div>
          )}
        </>
      ) : <p className="mt-2 text-[15px] leading-relaxed">{fallback}</p>}
    </div>
  );
}

function ScoreBar({ L }) {
  const [act, setAct] = useState(null);
  const rows = [...SCORES].sort((x, y) => parseFloat(y.value) - parseFloat(x.value));
  const max = parseFloat(rows[0].value);
  return (
    <div className="mt-6">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <span className="stat-label">{L("Udeo svake oblasti", "Weight of each factor")} <Tex tex="w_i" display={false} /></span>
        <span className="text-xs text-cream-400">{L("zbir = 100%", "total = 100%")}</span>
      </div>
      <div className="weights space-y-1.5">
        {rows.map((x, i) => {
          const v = parseFloat(x.value), on = act === i;
          return (
            <button type="button" key={x.sr} onMouseEnter={() => setAct(i)} onMouseLeave={() => setAct(null)} onClick={() => setAct(on ? null : i)}
              className={"weight-row grid w-full grid-cols-[minmax(0,1fr)_3.2rem] items-center gap-x-3 gap-y-1.5 rounded-xl px-3 py-2.5 text-left sm:grid-cols-[11rem_minmax(0,1fr)_3.2rem]" + (on ? " is-on" : "")}>
              <span className="truncate text-sm font-medium text-cream-100">{L(x.sr, x.en)}</span>
              <span className="order-3 col-span-2 h-2.5 overflow-hidden rounded-full bg-white/[0.07] sm:order-none sm:col-span-1">
                <motion.span className="weight-fill block h-full rounded-full" initial={{ width: 0 }} whileInView={{ width: `${(v / max) * 100}%` }} viewport={{ once: true }}
                  transition={{ duration: 0.9, delay: i * 0.06, ease: [0.22, 1, 0.36, 1] }} />
              </span>
              <span className="text-right font-mono text-base font-semibold text-cream-50">{x.value}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function IndicatorsPage() {
  const { lang } = useLang();
  const t = useT();
  const en = lang === "en";
  const L = (sr, english) => en ? english : sr;
  return (
    <div className="max-w-6xl">
      <PageHead title={t("indicators")} sub={L("Šta pokazuje svaki indikator, kako ga koristimo i na šta da obratiš pažnju.", "What each indicator shows, how we use it, and what to look out for.")} />

      <section className="mb-8">
        <Card hover={false} className="score-panel p-5 md:p-6">
          <div className="flex items-start gap-3">
            <Info size={20} className="mt-0.5 hidden shrink-0 text-gold-400 sm:block" />
            <div className="min-w-0">
              <div className="kicker text-gold-300">{L("Kako računamo ocenu prilike (0-100)", "How we calculate the opportunity score (0-100)")}</div>
              <p className="score-copy mt-3 text-base leading-relaxed text-cream-50">{L("Ocena objedinjuje osam oblasti. Svakoj dodeljujemo ocenu od 0 do 1, množimo je njenim udelom i saberemo rezultate:", "The score brings together eight areas. Each gets a value from 0 to 1. We multiply it by its share and add the results:")}</p>
              <div className="paper paper-hero mt-4 rounded-2xl p-5 md:p-7">
                <div className="paper-label">{L("Formula ocene prilike", "Opportunity score formula")}</div>
                <div className="mt-2 overflow-x-auto text-[1.25rem] md:text-[1.6rem]">
                  <Tex tex={en ? "\\text{Score} = 100 \\times \\sum_{i=1}^{8} w_i \\cdot x_i" : "\\text{Ocena} = 100 \\times \\sum_{i=1}^{8} w_i \\cdot x_i"} />
                  <Tex tex={en ? "\\text{then} \\times 0{.}75 \\text{ (falling knife)}" : "\\text{zatim} \\times 0{,}75 \\text{ (pad se ubrzava)}"} />
                  <Tex tex={en ? "\\text{or} \\times 0{.}85 \\text{ (RSI} > 70)" : "\\text{ili} \\times 0{,}85 \\text{ (RSI} > 70)"} />
                </div>
                <div className="paper-where mt-3 grid gap-1 pt-3 text-sm sm:grid-cols-2">
                  <div className="flex items-baseline gap-2"><Tex tex="w_i" display={false} /><span>- {L("udeo oblasti (lista ispod)", "factor weight (list below)")}</span></div>
                  <div className="flex items-baseline gap-2"><Tex tex={"x_i \\in [0, 1]"} display={false} className="shrink-0 whitespace-nowrap" /><span>- {L("koliko akcija ispunjava tu oblast", "how well the stock scores on it")}</span></div>
                </div>
              </div>
              <div className="score-copy mt-4 grid gap-3 text-base leading-relaxed text-cream-100 md:grid-cols-2">
                <p className="rounded-xl border border-wine-400/40 bg-wine-950/60 p-4 transition duration-300 hover:border-white/25">{L("Kvalitet obuhvata ROE, profitnu maržu, rast prihoda i FCF yield. Vrednovanje se računa pomoću PEG-a ili forward P/E-a. FCF yield utiče dodatno kada je dostupan.", "Quality includes ROE, profit margin, revenue growth, and FCF yield. Valuation uses PEG or forward P/E. FCF yield adds an adjustment when available.")}</p>
                <p className="rounded-xl border border-wine-400/40 bg-wine-950/60 p-4 transition duration-300 hover:border-white/25">{L("Ocenu zatim umanjujemo za rizične signale: uporan pad ispod SMA 200 smanjuje je za 25%, a RSI iznad 70 za 15%.", "We then reduce the score for risk signals. A falling-knife setup lowers it by 25%, while RSI above 70 lowers it by 15%.")}</p>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-cream-300">{L("Oznaka „ispunjava uslove“ se računa posebno. Potrebni su pad od najmanje 8% i potencijal od 5% ili više, odnosno ocena analitičara do 2,3. Ako ocena postoji, ne sme biti viša od 3. Prvo prikazujemo kandidate koji prolaze ove uslove, a zatim ostale po oceni. Ocena služi za poređenje - nije prognoza ni preporuka.", "The “qualifies” label is separate from the score. It requires a drop of at least 8% and either analyst upside of 5% or more or a rating of 2.3 or better. If a rating is available, it must be 3 or lower. Qualifying candidates appear first, followed by the remaining stocks ranked by score. The score helps compare stocks. It is not a forecast or recommendation.")}</p>
              <ScoreBar L={L} />
            </div>
          </div>
        </Card>
      </section>

      <Card hover={false} className="mb-10 flex gap-3 border-ink-600 bg-ink-850/80 p-4 text-sm leading-relaxed text-cream-400">
        <Info size={18} className="mt-0.5 shrink-0 text-cream-500" />
        <p>{L("Ovo su pravila po kojima aplikacija rangira akcije, a ne univerzalne granice za dobre i loše akcije. Pragovi su okvirni i razlikuju se po industrijama. Nijedan indikator sam po sebi ne potvrđuje da je akcija za kupovinu. Podaci mogu da nedostaju ili kasne. Sadržaj služi za istraživanje, nije investicioni savet.", "These are the app's ranking rules, not universal cutoffs for good and bad stocks. Thresholds are approximate and vary by industry. No single indicator confirms that a stock is worth buying. Data may be missing or delayed. This is for research, not investment advice.")}</p>
      </Card>

      <section className="space-y-10">
        {GROUPS.map((group) => (
          <div key={group.sr}>
            <SectionTitle>{L(group.sr, group.en)}</SectionTitle>
            <div className="grid gap-3 md:grid-cols-2">
              {group.items.map((item) => <IndicatorCard key={item.name} item={item} en={en} L={L} />)}
            </div>
          </div>
        ))}
      </section>

      <section className="mt-10">
        <SectionTitle>{L("Pokazatelji van ocene prilike", "Indicators outside the opportunity score")}</SectionTitle>
        <p className="mb-4 max-w-4xl text-base leading-relaxed text-cream-200">{L("Ovi pokazatelji mogu pomoći u dodatnoj analizi, ali ih aplikacija ne koristi za rangiranje. Okreni karticu za formulu i primer tumačenja. P/S i dividendni prinos objašnjeni su u prethodnoj grupi.", "These indicators can add context to your research, but the app does not use them for ranking. Turn a card over for its formula and a practical reading. P/S and dividend yield are explained in the previous group.")}</p>
        <div className="grid auto-rows-fr gap-3 md:grid-cols-2">
          {EXCLUDED_INDICATORS.map((item) => <IndicatorCard key={item.name} item={item} en={en} L={L} />)}
        </div>
        <p className="mt-4 rounded-xl border border-white/15 bg-[#0a0809] p-4 text-sm leading-relaxed text-cream-200">{L("MACD, Bollingerovi opsezi i podaci o transakcijama insajdera i fondova nisu dostupni u izvoru podataka ove aplikacije. Formule su prikazane radi objašnjenja. Prijave 13F kasne i ne pokazuju kompletnu sliku ulaganja.", "MACD, Bollinger Bands, and insider or fund transaction data are not available in this app's data source. Their formulas are shown for context. 13F filings are delayed and do not show a complete picture of an investor's positions.")}</p>
      </section>

      <section className="mt-10">
        <SectionTitle>{L("Ocena za poređenje svih akcija", "Score for comparing all stocks")}</SectionTitle>
        <Card hover={false} className="p-4 text-sm leading-relaxed text-cream-300">
          {L("U tabu „Istraži sve“ postoji i faktorska ocena: momentum 25%, cilj analitičara 20%, P/E 15%, ROE 15%, rast prihoda 10% i niža volatilnost 15%. Faktori se porede sa drugim akcijama na listi. Dugoročni trend dodaje 10% konačnoj oceni. Zato se ova ocena razlikuje od ocene prilike iznad.", "The “Explore all” tab also has a factor score: momentum 25%, analyst target 20%, P/E 15%, ROE 15%, revenue growth 10%, and lower volatility 15%. Factors are ranked against other stocks on the list. Long-term trend adds 10% to the final score. This is different from the opportunity score above.")}
        </Card>
      </section>

      <div className="mt-10 flex items-center gap-2 text-xs text-cream-500">
        <BookOpen size={14} />
        <span>{L("Za definiciju P/E pogledaj", "For a definition of P/E, see")} <a className="text-cream-300 underline" href="https://www.investor.gov/introduction-investing/investing-basics/glossary/price-earnings-pe-ratio" target="_blank" rel="noreferrer">Investor.gov</a>.</span>
      </div>
    </div>
  );
}
