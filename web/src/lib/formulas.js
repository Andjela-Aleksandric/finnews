// Formule indikatora zapisane matematički (KaTeX), sa legendom oznaka.
// lines: redovi formule; where: [oznaka (TeX), objašnjenje sr, objašnjenje en]
export const FORMULAS = {
  "SMA 50 / SMA 200": {
    lines: ["\\mathrm{SMA}_n = \\dfrac{1}{n}\\sum_{i=1}^{n} P_{t-i+1}"],
    where: [["P_t", "zaključna cena dana t", "closing price on day t"], ["n", "broj dana (50 ili 200)", "number of days (50 or 200)"]],
  },
  "RSI (14)": {
    lines: ["\\mathrm{RSI} = 100 - \\dfrac{100}{1 + \\mathrm{RS}}", "\\mathrm{RS} = \\dfrac{\\overline{\\text{rast}}_{14}}{\\overline{\\text{pad}}_{14}}"],
    where: [["\\overline{\\text{rast}}_{14}", "prosečan dnevni rast u 14 dana", "average daily gain over 14 days"], ["\\overline{\\text{pad}}_{14}", "prosečan dnevni pad u 14 dana", "average daily loss over 14 days"]],
  },
  "Odmak od maksimuma za 52 nedelje": {
    lines: ["\\text{Odmak} = \\dfrac{P_{\\text{danas}}}{P_{\\max,\\,52\\text{n}}} - 1"],
    where: [["P_{\\max,\\,52\\text{n}}", "najviša cena u poslednjih 52 nedelje", "highest price in the last 52 weeks"]],
  },
  "Momentum za 12-1 mesec": {
    lines: ["M_{12-1} = \\dfrac{P_{t-1\\text{m}}}{P_{t-12\\text{m}}} - 1"],
    where: [["P_{t-1\\text{m}}", "cena pre mesec dana", "price one month ago"], ["P_{t-12\\text{m}}", "cena pre 12 meseci", "price 12 months ago"]],
  },
  "Godišnja volatilnost": {
    lines: ["\\sigma_{\\text{god}} = \\sigma_{\\text{dan}} \\cdot \\sqrt{252}", "r_t = \\ln\\dfrac{P_t}{P_{t-1}}"],
    where: [["\\sigma_{\\text{dan}}", "standardna devijacija dnevnih prinosa r_t", "standard deviation of daily returns r_t"], ["252", "broj trgovačkih dana u godini", "trading days in a year"]],
  },
  "Ukrštanje proseka 50 i 200 dana": {
    lines: ["\\text{naviše: } \\mathrm{SMA}_{50} \\uparrow \\mathrm{SMA}_{200}", "\\text{naniže: } \\mathrm{SMA}_{50} \\downarrow \\mathrm{SMA}_{200}"],
    where: [["\\uparrow", "prelazak odozdo naviše", "crosses from below to above"], ["\\downarrow", "prelazak odozgo naniže", "crosses from above to below"]],
  },
  "Rast prihoda": {
    lines: ["g = \\dfrac{\\text{Prihod}_{t}}{\\text{Prihod}_{t-1\\,\\text{god}}} - 1"],
    where: [["t", "poslednji izveštajni period", "latest reporting period"]],
  },
  "ROE - prinos na kapital": {
    lines: ["\\mathrm{ROE} = \\dfrac{\\text{Neto dobit}}{\\text{Kapital akcionara}}"],
    where: [],
  },
  "Profitna marža": {
    lines: ["\\text{Marža} = \\dfrac{\\text{Neto dobit}}{\\text{Prihod}}"],
    where: [],
  },
  "Slobodan novčani tok / tržišna vrednost": {
    lines: ["\\text{FCF prinos} = \\dfrac{\\text{OCF} - \\text{CapEx}}{\\text{Tržišna kapitalizacija}}"],
    where: [["\\text{OCF}", "novčani tok iz poslovanja", "operating cash flow"], ["\\text{CapEx}", "ulaganja u opremu i objekte", "capital expenditure"]],
  },
  "PEG": {
    lines: ["\\mathrm{PEG} = \\dfrac{P/E}{g_{\\text{dobit}} \\times 100}"],
    where: [["g_{\\text{dobit}}", "očekivana godišnja stopa rasta dobiti", "expected annual earnings growth"]],
  },
  "Forward P/E i P/E": {
    lines: ["P/E = \\dfrac{\\text{Cena akcije}}{\\mathrm{EPS}_{12\\text{m}}}", "\\text{Forward } P/E = \\dfrac{\\text{Cena akcije}}{\\mathrm{EPS}_{\\text{očekivan}}}"],
    where: [["\\mathrm{EPS}", "dobit po akciji", "earnings per share"]],
  },
  "Dug / kapital (D/E)": {
    lines: ["D/E = \\dfrac{\\text{Ukupan dug}}{\\text{Kapital akcionara}} \\times 100\\%"],
    where: [],
  },
  "P/S i dividenda": {
    lines: ["P/S = \\dfrac{\\text{Tržišna kapitalizacija}}{\\text{Godišnji prihod}}", "\\text{Prinos od dividende} = \\dfrac{\\text{Dividenda po akciji (god.)}}{\\text{Cena akcije}}"],
    where: [],
  },
  "Prinosi po periodima": {
    lines: ["R_{T} = \\dfrac{P_{\\text{danas}}}{P_{\\text{pre } T}} - 1"],
    where: [["T", "period: 1 dan, 1 nedelja, 1 mesec, 6 meseci, 1 godina", "period: 1 day, 1 week, 1 month, 6 months, 1 year"]],
  },
  "Potencijal do ciljne cene analitičara": {
    lines: ["\\text{Potencijal} = \\dfrac{\\overline{C}_{\\text{cilj}}}{P_{\\text{danas}}} - 1"],
    where: [["\\overline{C}_{\\text{cilj}}", "prosečna ciljna cena analitičara", "average analyst price target"]],
  },
  "Ocena analitičara": {
    lines: ["\\bar{r} = \\dfrac{1}{N}\\sum_{i=1}^{N} r_i, \\quad r_i \\in \\{1, \\dots, 5\\}"],
    where: [["r_i", "preporuka analitičara: 1 = kupi, 5 = prodaj", "analyst rating: 1 = buy, 5 = sell"], ["N", "broj analitičara", "number of analysts"]],
  },
  "Sentiment vesti o kompaniji": {
    lines: ["S = \\dfrac{1}{N}\\sum_{i=1}^{N} s_i, \\quad s_i \\in [-1, 1]"],
    where: [["s_i", "ton jedne vesti (-1 negativan, +1 pozitivan)", "tone of one story (-1 negative, +1 positive)"], ["N", "broj vesti o kompaniji", "number of company stories"]],
  },
  "Aktuelnost teme i uticaj na sektor": {
    lines: ["Z = \\dfrac{n_{7\\text{d}}}{n_{28\\text{d}} / 4}"],
    where: [["n_{7\\text{d}}", "broj vesti o temi u poslednjih 7 dana", "stories on the theme in the last 7 days"], ["n_{28\\text{d}}", "broj vesti u prethodne 4 nedelje", "stories in the previous 4 weeks"]],
  },
  "MACD": {
    lines: ["\\mathrm{MACD} = \\mathrm{EMA}_{12} - \\mathrm{EMA}_{26}", "\\text{Signal} = \\mathrm{EMA}_{9}(\\mathrm{MACD})", "\\text{Histogram} = \\mathrm{MACD} - \\text{Signal}"],
    where: [["\\mathrm{EMA}_n", "eksponencijalni prosek cene za n dana", "exponential moving average over n days"]],
  },
  "Bollingerovi opsezi": {
    lines: ["\\text{Sredina} = \\mathrm{SMA}_{20}", "\\text{Gornji / donji} = \\mathrm{SMA}_{20} \\pm 2\\sigma_{20}"],
    where: [["\\sigma_{20}", "standardna devijacija cene za 20 dana", "20-day standard deviation of price"]],
  },
  "Transakcije insajdera": {
    lines: ["\\text{Neto kupovina} = \\sum \\text{kupovine} - \\sum \\text{prodaje}"],
    where: [["", "samo transakcije na otvorenom tržištu u izabranom periodu", "open-market transactions only, over the chosen period"]],
  },
  "Ulaganja fondova (13F)": {
    lines: ["\\Delta Q = Q_{\\text{novi izveštaj}} - Q_{\\text{prethodni}}"],
    where: [["Q", "broj akcija koje fond prijavljuje", "shares the fund reports holding"]],
  },
};

// engleske verzije tekstova u formulama
const EN_WORDS = [["Odmak", "Drawdown"], ["danas", "today"], ["52\\text{n}", "52\\text{w}"], ["\\text{rast}", "\\text{gain}"], ["\\text{pad}", "\\text{loss}"], ["\\text{god}", "\\text{yr}"], ["\\text{dan}", "\\text{day}"],
  ["naviše: ", "golden: "], ["naniže: ", "death: "], ["Prihod", "Revenue"], ["Neto dobit", "Net income"], ["Kapital akcionara", "Shareholders' equity"], ["Marža", "Margin"], ["FCF prinos", "FCF yield"],
  ["Tržišna kapitalizacija", "Market cap"], ["dobit", "earnings"], ["Cena akcije", "Share price"], ["očekivan", "forecast"], ["Ukupan dug", "Total debt"], ["Godišnji prihod", "Annual revenue"],
  ["Prinos od dividende", "Dividend yield"], ["Dividenda po akciji (god.)", "Annual dividend per share"], ["pre ", "ago "], ["Potencijal", "Upside"], ["cilj", "target"], ["Sredina", "Middle"],
  ["Gornji / donji", "Upper / lower"], ["Neto kupovina", "Net buying"], ["kupovine", "buys"], ["prodaje", "sells"], ["novi izveštaj", "new filing"], ["prethodni", "previous"]];
export function texFor(line, lang) {
  if (lang !== "en") return line;
  let out = line;
  for (const [sr, en] of EN_WORDS) out = out.split(sr).join(en);
  return out;
}
