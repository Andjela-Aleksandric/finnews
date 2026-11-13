import { createContext, useContext } from "react";

export const LangCtx = createContext({ lang: "sr", setLang: () => {} });
export const useLang = () => useContext(LangCtx);

const D = {
  home: ["Početna", "Home"], news: ["Vesti", "News"], stocks: ["Akcije", "Stocks"], indicators: ["Indikatori", "Indicators"], portfolio: ["Portfolio", "Portfolio"],
  review: ["Pregled", "Review"], research: ["Istraživanja", "Research"], archive: ["Arhiva", "Archive"], settings: ["Podešavanja", "Settings"],
  search: ["Pretraži", "Search"], searchAll: ["Pretraži akcije, vesti, stranice...", "Search stocks, news, pages..."],
  goodMorning: ["Dobro jutro", "Good morning"], goodDay: ["Dobar dan", "Good afternoon"], goodEvening: ["Dobro veče", "Good evening"],
  todayMatters: ["Evo šta je danas važno.", "Here is what matters today."],
  todayBrief: ["Danas ukratko", "Today in brief"], opportunities: ["Prilike na tržištu", "Market opportunities"],
  risingThemes: ["Teme u usponu", "Rising themes"], fromResearch: ["Iz istraživanja", "From research"],
  allNews: ["Sve vesti", "All news"], seeAll: ["Pogledaj sve", "See all"], read: ["Čitaj", "Read"], save: ["Sačuvaj", "Save"], saved: ["Sačuvano", "Saved"],
  openOriginal: ["Otvori original", "Open original"], keyPoints: ["Suština i ključni nalazi", "Essence and key findings"], fullText: ["Ceo tekst", "Full text"],
  original: ["Original", "Original"], updated: ["Osveženo", "Updated"], sources: ["izvora", "sources"], stories: ["vesti", "stories"],
  moreSources: ["izvora piše o ovome", "outlets cover this"], themesTrend: ["Teme i trend", "Themes & trend"], new: ["novo", "new"],
  summary: ["Sažetak", "Summary"], period: ["Period", "Period"], d1: ["1 dan", "1 day"], d7: ["7 dana", "7 days"], d30: ["30 dana", "30 days"],
  d60: ["60 dana", "60 days"], d90: ["90 dana", "90 days"], d180: ["180 dana", "180 days"],
  fin: ["Finansije", "Finance"], comp: ["Kompanije", "Companies"], srb: ["Srbija", "Serbia"], svet: ["Svet", "World"],
  sortRel: ["Relevantnost", "Relevance"], sortNew: ["Najnovije", "Newest"], sortImp: ["Važnost", "Importance"], sortSrc: ["Najviše izvora", "Most covered"],
  filters: ["Filteri", "Filters"], onlyFull: ["Samo sa celim tekstom", "Full text only"], onlyMulti: ["Prenosi više izvora", "Covered by several outlets"],
  loadMore: ["Prikaži još", "Show more"], nothing: ["Ništa ne odgovara filterima.", "Nothing matches these filters."],
  showing: ["Prikazano", "Showing"], of: ["od", "of"],
  oppNow: ["Prilike sada", "Opportunities"], explore: ["Istraži sve", "Explore all"], markets: ["Tržišta", "Markets"], themes: ["Teme", "Themes"],
  chartDetails: ["Grafikon i detalji", "Chart & details"], whyNow: ["Zašto sada", "Why now"], watchOut: ["Na šta paziti", "Watch out for"],
  fromHigh: ["od maksimuma", "from high"], target: ["cilj analitičara", "analyst target"], score: ["ocena", "score"], oneYear: ["1 godina", "1 year"],
  sector: ["Sektor", "Sector"], allSectors: ["Svi sektori", "All sectors"], sortBy: ["Poređaj po", "Sort by"], onlyFallen: ["Samo u padu", "Only fallen"],
  noEtf: ["Bez ETF-ova", "Hide ETFs"], newsMove: ["Vesti koje mogu da pokrenu cenu", "News that may move the price"],
  disclaimer: ["Alat za istraživanje, a ne investicioni savet. Pad može i da se nastavi.", "A research tool, not investment advice. The decline may continue."],
  aboutCompany: ["O kompaniji", "About the company"], latestNews: ["Najnovije vesti", "Latest news"], back: ["Nazad", "Back"],
  gainers: ["Najveći rast", "Top gainers"], losers: ["Najveći pad", "Top losers"],
  totalValue: ["Ukupna vrednost", "Total value"], invested: ["Uloženo", "Invested"], profit: ["Dobit / gubitak", "Profit / loss"],
  ret: ["Prinos", "Return"], today: ["Danas", "Today"], holdings: ["Pozicije", "Holdings"], allocation: ["Raspodela", "Allocation"],
  valueOverTime: ["Kretanje vrednosti", "Value over time"], transactions: ["Transakcije", "Transactions"], assets: ["Zlato, obveznice i gotovina", "Gold, bonds & cash"],
  addTx: ["Nova transakcija", "New transaction"], edit: ["Izmeni", "Edit"], del: ["Obriši", "Delete"], cancel: ["Otkaži", "Cancel"], saveCh: ["Sačuvaj", "Save"],
  pending: ["Nalozi na čekanju", "Pending orders"], ownerOnly: ["Portfolio vidi samo vlasnik", "Only the owner can see the portfolio"],
  connect: ["Poveži portfolio", "Connect portfolio"], keyFindings: ["Najvažniji nalazi", "Key findings"], papers: ["Radovi", "Papers"],
  classics: ["Klasici", "Classics"], phd: ["Popularnost tema", "Topic popularity"], savedItems: ["Sačuvane vesti", "Saved stories"],
  noNews: ["Još nema vesti za ovaj period.", "No news for this period yet."], language: ["Jezik", "Language"],
  install: ["Instaliraj na telefon", "Install on your phone"], loading: ["Učitavam...", "Loading..."],
};
export function tr(key, lang) {
  const v = D[key];
  return v ? v[lang === "en" ? 1 : 0] : key;
}
export const useT = () => {
  const { lang } = useLang();
  return (k) => tr(k, lang);
};
