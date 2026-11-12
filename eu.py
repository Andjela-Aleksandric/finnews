"""Evropske akcije u evrima: lista, porezi na dividende za rezidente Srbije, ETF-ovi i indeksi.
Izvori (proveriti pre odluke - stope se menjaju):
- ugovorne stope Srbije: PwC Worldwide Tax Summaries, Serbia - Withholding taxes
- statutarne stope: GlobeTax, Dividend Withholding Tax Rates by Country (2026)
- porez u Srbiji (15% na dividende i kapitalni dobitak, poreski kredit): Zakon o porezu na dohodak građana;
  PwC Serbia - Foreign tax relief"""

EU_WATCHLIST = [
    # Nemačka (Xetra)
    ("SAP.DE", "SAP"), ("SIE.DE", "Siemens"), ("ALV.DE", "Allianz"), ("DTE.DE", "Deutsche Telekom"),
    ("MUV2.DE", "Munich Re"), ("IFX.DE", "Infineon"), ("RHM.DE", "Rheinmetall"), ("DB1.DE", "Deutsche Börse"),
    ("MBG.DE", "Mercedes-Benz"), ("BAS.DE", "BASF"),
    # Francuska (Euronext Pariz)
    ("MC.PA", "LVMH"), ("OR.PA", "L'Oréal"), ("RMS.PA", "Hermès"), ("TTE.PA", "TotalEnergies"),
    ("SU.PA", "Schneider Electric"), ("AI.PA", "Air Liquide"), ("SAN.PA", "Sanofi"), ("AIR.PA", "Airbus"),
    ("BNP.PA", "BNP Paribas"), ("EL.PA", "EssilorLuxottica"),
    # Holandija (Euronext Amsterdam)
    ("ASML.AS", "ASML"), ("INGA.AS", "ING"), ("ADYEN.AS", "Adyen"), ("WKL.AS", "Wolters Kluwer"), ("HEIA.AS", "Heineken"),
    # Italija, Španija, Belgija, Irska
    ("RACE.MI", "Ferrari"), ("ENEL.MI", "Enel"), ("ISP.MI", "Intesa Sanpaolo"), ("UCG.MI", "UniCredit"),
    ("IBE.MC", "Iberdrola"), ("ITX.MC", "Inditex"), ("SAN.MC", "Banco Santander"), ("ABI.BR", "AB InBev"),
    ("RYA.IR", "Ryanair"),
    # SAD - velike kompanije sa malom ili nikakvom dividendom (porez od 30% na dividendu malo utiče)
    ("NVDA", "Nvidia"), ("MSFT", "Microsoft"), ("AAPL", "Apple"), ("GOOGL", "Alphabet"), ("AMZN", "Amazon"),
    ("META", "Meta Platforms"), ("BRK-B", "Berkshire Hathaway"), ("V", "Visa"), ("MA", "Mastercard"),
    ("COST", "Costco"), ("NFLX", "Netflix"), ("LLY", "Eli Lilly"), ("TSLA", "Tesla"),
    # ETF-ovi u evrima (Xetra)
    ("VWCE.DE", "Vanguard FTSE All-World (Acc)"), ("EUNL.DE", "iShares Core MSCI World (Acc)"),
    ("SXR8.DE", "iShares Core S&P 500 (Acc)"), ("EXSA.DE", "iShares STOXX Europe 600 (DE)"),
]
EU_ETFS = {"VWCE.DE", "EUNL.DE", "SXR8.DE", "EXSA.DE", "IS3N.DE"}

SUFFIX_COUNTRY = {".DE": "DE", ".PA": "FR", ".AS": "NL", ".MI": "IT", ".MC": "ES", ".BR": "BE", ".IR": "IE",
                  ".VI": "AT", ".HE": "FI", ".LS": "PT", ".SW": "CH", ".L": "GB"}
COUNTRY_NAME = {"DE": ("Nemačka", "Germany"), "FR": ("Francuska", "France"), "NL": ("Holandija", "Netherlands"),
                "IT": ("Italija", "Italy"), "ES": ("Španija", "Spain"), "BE": ("Belgija", "Belgium"), "IE": ("Irska", "Ireland"),
                "AT": ("Austrija", "Austria"), "FI": ("Finska", "Finland"), "PT": ("Portugal", "Portugal"),
                "CH": ("Švajcarska", "Switzerland"), "GB": ("Velika Britanija", "United Kingdom"), "US": ("SAD", "United States")}
# (statutarna stopa za nerezidente, stopa iz ugovora sa Srbijom ili None ako ugovora nema)
# Francuska: 12,8% za fizička lica nerezidente (25% ako broker ne primeni stopu za fizička lica)
WHT = {"DE": (0.26375, 0.15), "FR": (0.128, 0.15), "NL": (0.15, 0.15), "IT": (0.26, 0.10), "ES": (0.19, 0.10),
       "BE": (0.30, 0.15), "IE": (0.25, 0.10), "AT": (0.275, 0.15), "CH": (0.35, 0.15), "GB": (0.0, 0.15),
       "US": (0.30, None)}
SERBIA_RATE = 0.15
# Porez na finansijske transakcije pri kupovini (Francuska: 0,4% za kompanije sa sedištem u Francuskoj i
# tržišnom vrednošću iznad 1 mlrd. € - od 1.4.2025.; izvor: legifiscal.fr)
FTT = {"FR": 0.004}

# ETF-ovi: karakteristike (približno, proveriti na justETF ili sajtu fonda)
ETF_INFO = {
    "VWCE.DE": {"index": "FTSE All-World", "ter": 0.0019, "dom": "IE", "policy": "acc", "repl": ("uzorkovanje", "sampling"),
                "holdings": "~4.000", "isin": "IE00BK5BQT80"},
    "EUNL.DE": {"index": "MSCI World", "ter": 0.0020, "dom": "IE", "policy": "acc", "repl": ("fizička", "physical"),
                "holdings": "~1.400", "isin": "IE00B4L5Y983"},
    "SXR8.DE": {"index": "S&P 500", "ter": 0.0007, "dom": "IE", "policy": "acc", "repl": ("fizička", "physical"),
                "holdings": "~500", "isin": "IE00B5BMR087"},
    "IS3N.DE": {"index": "MSCI Emerging Markets IMI", "ter": 0.0018, "dom": "IE", "policy": "acc", "repl": ("uzorkovanje", "sampling"),
                "holdings": "~3.000", "isin": "IE00BKM4GZ66"},
    "EXSA.DE": {"index": "STOXX Europe 600", "ter": 0.0020, "dom": "DE", "policy": "dist", "repl": ("fizička", "physical"),
                "holdings": "~600", "isin": "DE0002635307"},
}
INDEX_INFO = {
    "MSCI Emerging Markets IMI": ("Oko 3.000 velikih, srednjih i malih kompanija sa tržišta u razvoju (Kina, Indija, Tajvan, "
                                  "Južna Koreja, Brazil...). Ponderisan tržišnom vrednošću; veća volatilnost i valutni rizik.",
                                  "About 3,000 large, mid and small caps from emerging markets (China, India, Taiwan, South Korea, "
                                  "Brazil...). Market-cap weighted; higher volatility and currency risk."),
    "FTSE All-World": ("Oko 4.000 velikih i srednjih kompanija iz razvijenih i tržišta u razvoju. Ponderisan tržišnom vrednošću "
                       "(slobodno prenosive akcije); SAD čine oko 60%. Najšira diverzifikacija jednim fondom.",
                       "About 4,000 large and mid caps from developed and emerging markets. Free-float market-cap weighted; "
                       "the US is about 60%. The broadest diversification in a single fund."),
    "MSCI World": ("Oko 1.400 velikih i srednjih kompanija iz 23 razvijena tržišta, bez tržišta u razvoju. Ponderisan tržišnom "
                   "vrednošću; SAD čine oko 70%, a najveće tehnološke firme imaju veliki udeo.",
                   "About 1,400 large and mid caps from 23 developed markets, no emerging markets. Market-cap weighted; "
                   "the US is about 70% and the largest tech firms carry a big weight."),
    "S&P 500": ("500 velikih američkih kompanija koje bira komisija S&P Dow Jones Indices prema veličini, likvidnosti i "
                "profitabilnosti. Ponderisan tržišnom vrednošću; visoka koncentracija u tehnologiji.",
                "500 large US companies selected by an S&P Dow Jones Indices committee on size, liquidity and profitability. "
                "Market-cap weighted; heavily concentrated in technology."),
    "STOXX Europe 600": ("600 velikih, srednjih i malih kompanija iz 17 evropskih zemalja (uključujući Veliku Britaniju i "
                         "Švajcarsku). Ponderisan tržišnom vrednošću, revizija sastava kvartalno.",
                         "600 large, mid and small companies from 17 European countries (including the UK and Switzerland). "
                         "Market-cap weighted, reviewed quarterly."),
}


INFO_COUNTRY = {"United States": "US", "Germany": "DE", "France": "FR", "Netherlands": "NL", "Italy": "IT", "Spain": "ES",
                "Belgium": "BE", "Ireland": "IE", "Austria": "AT", "Finland": "FI", "Switzerland": "CH", "United Kingdom": "GB",
                "Portugal": "PT"}
ISIN_OVERRIDE = {"NVD.DE": "US"}  # američke akcije koje se trguju na Xetri u evrima


def country(ticker, info=None):
    """Zemlja izdavaoca: ETF -> domicil fonda; akcija -> sedište kompanije (ne berza!)."""
    if ticker in ETF_INFO:
        return ETF_INFO[ticker]["dom"]
    if ticker in ISIN_OVERRIDE:
        return ISIN_OVERRIDE[ticker]
    if info and info.get("country") in INFO_COUNTRY and not info.get("fundFamily"):
        return INFO_COUNTRY[info["country"]]
    for suf, c in SUFFIX_COUNTRY.items():
        if ticker.upper().endswith(suf):
            if ticker in ETF_INFO:
                return ETF_INFO[ticker]["dom"]
            return c
    return "US"


def is_eur(ticker, info=None):
    cur = (info or {}).get("currency")
    if cur:
        return cur == "EUR"
    return any(ticker.upper().endswith(s) for s in (".DE", ".PA", ".AS", ".MI", ".MC", ".BR", ".IR", ".VI", ".HE", ".LS"))


def dividend_tax(c):
    """Efektivni porez na dividendu za rezidenta Srbije: (zadržano u inostranstvu, doplata u Srbiji,
    ukupno bez povraćaja, ukupno uz povraćaj, iznos za povraćaj)."""
    stat, treaty = WHT.get(c, (None, None))
    if stat is None:
        return None
    serbia_extra = max(0.0, SERBIA_RATE - min(stat, SERBIA_RATE))
    total_no_reclaim = stat + serbia_extra
    if treaty is None:
        return stat, serbia_extra, total_no_reclaim, total_no_reclaim, 0.0
    total_reclaim = treaty + max(0.0, SERBIA_RATE - treaty)
    return stat, serbia_extra, total_no_reclaim, total_reclaim, max(0.0, stat - treaty)


def costs(amount, years, exp_return, div_yield, c, commission_pct, commission_min, fx_pct, ter=0.0, accumulating=False,
          reclaim=False):
    """Pojednostavljen račun troškova i poreza za jednu poziciju (u evrima)."""
    buy_fee = max(amount * commission_pct, commission_min) if amount else 0
    fx = amount * fx_pct
    ftt = amount * FTT.get(c, 0.0)
    invested = amount - buy_fee - fx - ftt
    value, ter_cost, divs_net, div_tax = invested, 0.0, 0.0, 0.0
    t = dividend_tax(c) or (0.0, 0.0, 0.15, 0.15, 0.0)
    rate = t[3] if reclaim else t[2]
    for _ in range(int(years)):
        growth = value * exp_return
        tc = value * ter
        value += growth - tc
        ter_cost += tc
        if div_yield and not accumulating:
            d = value * div_yield
            div_tax += d * rate
            divs_net += d * (1 - rate)
    sell_fee = max(value * commission_pct, commission_min)
    gain = value - sell_fee - amount
    cg_tax = 0.0 if years > 10 else max(0.0, gain) * SERBIA_RATE
    return {"buy_fee": buy_fee, "fx": fx, "ftt": ftt, "ter": ter_cost, "div_tax": div_tax, "divs_net": divs_net, "sell_fee": sell_fee,
            "cg_tax": cg_tax, "end_value": value - sell_fee - cg_tax, "div_rate": rate}


EXPLAIN = {
    "sr": """**Zašto evropske kompanije - i šta tačno izbegava dvostruko oporezivanje**

Porez na dividendu zadržava **država u kojoj je kompanija registrovana**, bez obzira na berzu i valutu. Kupovina u evrima ti štedi trošak konverzije valute, ali ne menja porez. Ono što pomaže je **ugovor o izbegavanju dvostrukog oporezivanja**: Srbija ga ima sa većinom zemalja EU, a sa SAD nema.

**Kako se oporezuje dividenda (rezident Srbije):**
1. Država kompanije zadrži porez po svojoj stopi (npr. Nemačka 26,375%, Holandija 15%, Francuska 12,8% za fizička lica).
2. Ugovor sa Srbijom ograničava taj porez (najčešće na 15% ili 10%). Razliku iznad ugovorne stope možeš da tražiš nazad od te države - postupak je spor i papirološki zahtevan, a za male iznose se često ne isplati.
3. U Srbiji je porez na dividendu 15%. Porez plaćen u inostranstvu se priznaje kao poreski kredit, najviše do iznosa srpskog poreza. Ako je u inostranstvu zadržano 15% ili više, u Srbiji uglavnom ne doplaćuješ; ako je zadržano 10% (Italija, Španija, Irska uz ugovor), doplaćuješ 5%.
4. Prijava: obrazac PP OPO u roku od 30 dana od isplate svake dividende.

**Kapitalni dobitak (prodaja sa zaradom):** 15% u Srbiji, prijava PPDG-3R. Prema dostupnim tumačenjima, hartije koje držiš duže od 10 godina oslobođene su ovog poreza - proveri sa poreskim savetnikom.

**ETF-ovi koji akumuliraju dividende (Acc, irski):** ne isplaćuju ti dividende, pa nema mesečnih prijava ni poreza na dividende na tvom nivou; porez od 15% plaćaš tek na kapitalni dobitak pri prodaji. Zato su često najjednostavnija opcija za dugoročno ulaganje.

**Troškovi koje treba uračunati:** provizija brokera (pri kupovini i prodaji, često sa minimalnim iznosom), francuski porez na transakcije 0,4% pri kupovini akcija velikih francuskih kompanija, konverzija valute ako račun nije u evrima, godišnji trošak fonda (TER) za ETF-ove, eventualna naknada za čuvanje hartija, i gubitak na porezu na dividende ako ne tražiš povraćaj.

*Ovo je opšti pregled, a ne poreski savet. Stope se menjaju, a primena zavisi od brokera i tvoje situacije - pre ulaganja proveri sa poreskim savetnikom ili Poreskom upravom.*""",
    "en": """**Why European companies - and what actually avoids double taxation**

Dividend tax is withheld by **the country where the company is incorporated**, regardless of the exchange or currency. Buying in euros saves currency-conversion costs but does not change the tax. What helps is a **double taxation treaty**: Serbia has one with most EU countries, but not with the United States.

**How a dividend is taxed (Serbian resident):**
1. The company's country withholds tax at its own rate (e.g. Germany 26.375%, Netherlands 15%, France 12.8% for individuals).
2. The treaty with Serbia caps that tax (usually at 15% or 10%). You can reclaim the excess above the treaty rate from that country - the process is slow and paperwork-heavy, and often not worth it for small amounts.
3. Serbia taxes dividends at 15%. Tax paid abroad is credited, up to the Serbian tax. If 15% or more was withheld abroad you generally pay nothing more in Serbia; if 10% was withheld (Italy, Spain, Ireland under the treaty) you top up 5%.
4. Filing: form PP OPO within 30 days of each dividend payment.

**Capital gains (selling at a profit):** 15% in Serbia, form PPDG-3R. According to available interpretations, securities held longer than 10 years are exempt - check with a tax adviser.

**Accumulating (Acc, Irish) ETFs:** they pay you no dividends, so there are no per-dividend filings or dividend tax at your level; you pay 15% capital gains tax only when you sell. That is why they are often the simplest option for long-term investing.

**Costs to include:** broker commission (on buy and sell, often with a minimum), French financial transaction tax of 0.4% when buying shares of large French companies, currency conversion if the account is not in euros, the fund's annual cost (TER) for ETFs, any custody fee, and dividend tax leakage if you do not reclaim.

*This is a general overview, not tax advice. Rates change and the treatment depends on your broker and situation - check with a tax adviser or the Serbian Tax Administration before investing.*""",
}
SOURCES = [("PwC - Serbia: Withholding taxes (ugovorne stope)", "https://taxsummaries.pwc.com/Serbia/Corporate/Withholding-taxes"),
           ("PwC - Serbia: Foreign tax relief", "https://taxsummaries.pwc.com/serbia/individual/foreign-tax-relief-and-tax-treaties"),
           ("GlobeTax - Dividend withholding tax rates (2026)", "https://www.globetax.com/dividend-withholding-tax-rates-database/")]


DRAG_OK = 0.0015  # do 0,15% godišnje poreskog gubitka smatramo prihvatljivim (npr. dividenda 1% x 15 p.p. viška)


def drag(div_yield, c, reclaim=False, accumulating=False):
    """Godišnji gubitak prinosa zbog poreza na dividendu iznad srpskih 15% (u odnosu na vrednost ulaganja)."""
    if accumulating or not div_yield:
        return 0.0
    t = dividend_tax(c)
    if not t:
        return 0.0
    return div_yield * max(0.0, (t[3] if reclaim else t[2]) - SERBIA_RATE)


def region(ticker, info=None):
    c = country(ticker, info)
    if c == "US":
        return "us"
    return "eu" if WHT.get(c, (None, None))[1] is not None else "other"
