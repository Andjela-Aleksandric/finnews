"""Popravke mašinskog prevoda finansijskih vesti na srpski.

1) simplify_en: pre prevoda žargon i idiome zamenjuje običnim engleskim ("hot inflation" -> "high inflation"),
   jer ih Google inače prevodi doslovno ("vruća inflacija").
2) polish_sr: posle prevoda ispravlja česte greške - ijekavicu, hrvatske reči, "zalihe" umesto "akcije" i slično.
"""
import os
import re

TR_VERSION = "12"

_EN = [
    # inflacija i kamate
    (r"\bhotter[- ]than[- ]expected\b", "higher-than-expected"), (r"\bcooler[- ]than[- ]expected\b", "lower-than-expected"),
    (r"\bhot (CPI|PCE|inflation (?:data|reading|report|print|figures?)|jobs (?:data|report|number)|payrolls?|prints?|readings?|wage growth|data)\b", r"higher-than-expected \1"),
    (r"\b(inflation|prices|the economy|economy|labou?r market|job market|wage growth|demand)( is| are| was| were| remains| remained| stays| stayed)?( still)? running (?:too )?hot\b", r"\1\2\3 rising fast"),
    (r"\bruns? (?:too )?hot\b", "rises fast"), (r"\b(?:too|very|still) hot\b", "too strong"), (r"\bhotter\b", "higher"), (r"\bhottest\b", "highest"),
    (r"\b(CPI|PCE|inflation|jobs|payrolls?) prints?\b", r"\1 data"), (r"\brattl(e|es|ed)\b", r"unsettl\1"), (r"\bsizzling\b", "very strong"), (r"\bon fire\b", "very strong"), (r"\blukewarm\b", "weak"), (r"\btepid\b", "weak"),
    (r"\bskyrocket(s|ed|ing)?\b", r"rise\1 sharply"), (r"\bcrater(s|ed)?\b", r"fall\1 sharply"), (r"\bcrush(?:es|ed)? (estimates|expectations|forecasts)\b", r"far exceed \1"),
    (r"\bbuoyed\b", "supported"), (r"\bdented\b", "hurt"), (r"\bbruised\b", "hurt"), (r"\b(?:battered|hammered|pummell?ed)\b", "hit hard"),
    (r"\broil(s|ed)\b", r"shake\1"), (r"\bbellwether\b", "leading indicator"), (r"\bsafe[- ]havens?\b", "safe investment"), (r"\brisk appetite\b", "willingness to take risk"),
    (r"\bhot inflation\b", "high inflation"), (r"\binflation (runs|running|ran) hot\b", r"inflation \1 high"),
    (r"\b(?:sticky|stubborn|persistent) inflation\b", "inflation that is slow to fall"), (r"\binflation cools\b", "inflation slows"), (r"\bcooling inflation\b", "slowing inflation"),
    (r"\bhawkish\b", "in favor of higher interest rates"), (r"\bdovish\b", "in favor of lower interest rates"),
    (r"^World Economy Latest:\s*", "World economy news: "), (r"\bclash(es|ed)? over\b", r"disagree over"),
    (r"\bfloat(s|ed)?\b(?=\s+(?:the |a |an )?(?:idea|possibility|plan|proposal|[A-Z]\w*\s+(?:merger|deal|bid|tie-up|sale)))", r"propose\1"),
    (r"\bcurbs\b", "restrictions"), (r"\bground stops?\b", "suspension of all flights"), (r"\ba post-((?-i:[A-Z])[\w.-]*(?: (?-i:[A-Z])[\w.-]*)*) era\b", r"the era after \1"),
    (r"\bfailed (?=(?-i:[A-Z]))", "let down "), (r"(?<!on )(?<!on the )\bboard\b(?! of)(?!ing)", "board of directors"),
    (r"\brate hikes?\b", "interest rate increase"), (r"\bsoft landing\b", "slowdown without a recession"), (r"\bhard landing\b", "recession"),
    # kretanje cena
    (r"\bweighs? on\b", "puts pressure on"), (r"\bweighed on\b", "put pressure on"),
    (r"\brall(?:y|ies) to\b", "rises to"), (r"\brallied\b", "rose strongly"), (r"\brallies\b", "rises strongly"), (r"\brallying\b", "rising strongly"),
    (r"\b(?:a|the) rally\b", "the rise"), (r"\brally\b", "rise"),
    (r"\b(?:surges|soars|skyrockets|spikes|jumps)\b", "rises sharply"), (r"\b(?:surge|soar|skyrocket|spike|jump)\b", "rise sharply"), (r"\b(?:surged|soared|skyrocketed|spiked|jumped)\b", "rose sharply"),
    (r"\b(?:plunges|plummets|tumbles|slumps|tanks|craters|nosedives|sinks)\b", "falls sharply"),
    (r"\b(?:plunge|plummet|tumble|slump|tank|crater|nosedive|sink)\b", "fall sharply"),
    (r"\b(?:plunged|plummeted|tumbled|slumped|tanked|cratered|nosedived|sank)\b", "fell sharply"),
    (r"\bslides\b", "falls"), (r"\bslide\b", "fall"), (r"\bslid\b", "fell"), (r"\bdips\b", "falls slightly"), (r"\bdip\b", "fall slightly"), (r"\bdipped\b", "fell slightly"),
    (r"\bedges? (?:up|higher)\b", "rises slightly"), (r"\bedges? (?:down|lower)\b", "falls slightly"),
    (r"\bsell-?offs?\b", "wave of selling"), (r"\bjitters\b", "worries"), (r"\brisk-off\b", "moving away from risky assets"),
    (r"\brisk-on\b", "appetite for risky assets"), (r"\bbull market\b", "rising market"), (r"\bbear market\b", "falling market"),
    (r"\bbulls\b", "optimistic investors"), (r"\bbears\b", "pessimistic investors"),
    # rezultati
    (r"\b(?:beats?|tops?|crushes?) (?:estimates|expectations|forecasts)\b", "exceeds expectations"),
    (r"\b(?:beat|topped|crushed) (?:estimates|expectations|forecasts)\b", "exceeded expectations"),
    (r"\bmiss(?:es)? (?:estimates|expectations|forecasts)\b", "falls short of expectations"), (r"\bmissed (?:estimates|expectations|forecasts)\b", "fell short of expectations"),
    (r"\bblowout (?:quarter|results|earnings)\b", "very strong results"), (r"\bguidance\b", "outlook"),
    (r"\bheadwinds\b", "obstacles"), (r"\btailwinds\b", "support"),
    # idiomi koji se doslovno prevode besmisleno
    (r"\b(?:red|white)-hot\b", "very strong"), (r"\bhot stocks?\b", "popular stocks"), (r"\bheats? up\b", "intensifies"), (r"\bheated up\b", "intensified"),
    (r"\b(?:cools?|cooled|cooling) (?:off|down)\b", "slows down"), (r"\blabou?r market cools\b", "labor market slows"), (r"\bcooling (?:labou?r|jobs|job) market\b", "slowing labor market"),
    (r"\boverheat(?:ed|ing)? econom(?:y|ies)\b", "economy growing too fast"), (r"\boverheating\b", "growing too fast"), (r"\boverheated\b", "overbought"),
    (r"\b(?:a )?tailwind\b", "support"), (r"\b(?:a )?headwind\b", "an obstacle"),
    (r"\bdead[- ]cat bounce\b", "short-lived recovery"), (r"\bfalling knife\b", "stock that keeps falling"),
    (r"\bgolden cross\b", "upward trend signal"), (r"\bdeath cross\b", "downward trend signal"),
    (r"\bmelt-?up\b", "sharp rise"), (r"\brout\b", "sharp drop"), (r"\bbloodbath\b", "heavy losses"), (r"\bwhipsaw(?:s|ed)?\b", "swing sharply"),
    (r"\bpivot\b", "change of course"), (r"\bGoldilocks\b", "balanced"), (r"\bin the red\b", "at a loss"), (r"\bin the black\b", "in profit"),
    (r"\bshake-?up\b", "reorganization"), (r"\beyes\b(?= (?:a |an |the )?(?:interest|rate|cut|hike|deal|stake|bid|acquisition|IPO|listing|expansion))", "is considering"), (r"\beye\b(?= (?:a |an |the )?(?:interest|rate|cut|hike|deal|stake|bid|acquisition|IPO|listing|expansion))", "are considering"),
    (r"\btaps\b(?= \w+ (?:as|to) )", "appoints"), (r"\binks\b", "signs"), (r"\bnabs\b", "wins"), (r"\baxes\b", "cuts"),
    (r"\bslashes\b", "sharply cuts"), (r"\bslashed\b", "sharply cut"), (r"\btrims\b", "reduces"), (r"\bspooks\b", "worries"), (r"\bspooked\b", "worried"),
    (r"\bshrugs off\b", "ignores"), (r"\bshrugged off\b", "ignored"), (r"\bbrace for\b", "prepare for"), (r"\blofty valuations?\b", "high valuations"),
    (r"\bfrothy\b", "overvalued"), (r"\bcash cow\b", "steady source of profit"), (r"\b(?:economic )?moat\b", "competitive advantage"),
    (r"\bwar chest\b", "cash reserves"), (r"\bdry powder\b", "available cash"), (r"\bdeep pockets\b", "plenty of money"),
    (r"\bblue[- ]chips?\b", "large established companies"), (r"\bmeme stocks?\b", "stocks popular with small investors"),
    (r"\bshort squeeze\b", "sharp rise as short sellers buy back"), (r"\b(?:Fed |ECB )?hawks\b", "supporters of higher interest rates"),
    (r"\b(?:Fed |ECB )?doves\b", "supporters of lower interest rates"), (r"\bwobbles?\b", "instability"), (r"\bsoft patch\b", "temporary slowdown"),
    (r"\bgame[- ]changer\b", "major change"), (r"\bhot potato\b", "sensitive issue"), (r"\bkicks the can down the road\b", "postpones the decision"),
    # glagoli koji se prevode doslovno
    (r"\braces? to\b", "hurries to"), (r"\braced to\b", "hurried to"), (r"\bAI race\b", "AI competition"), (r"\brace for\b", "competition for"),
    (r"\bmulls\b", "is considering"), (r"\bslams\b", "sharply criticizes"), (r"\bslammed\b", "sharply criticized"),
    (r"\bgreenback\b", "US dollar"), (r"\bthe Street\b", "analysts"), (r"\bMagnificent Seven\b", "seven largest US tech companies"),
    (r"\bdoubles down on\b", "increases its commitment to"), (r"\bbets big on\b", "invests heavily in"), (r"\bbets on\b", "counts on"),
]
_EN = [(re.compile(p, re.I), r) for p, r in _EN]


def simplify_en(text):
    if not text:
        return text
    out = sentence_case(text)
    for p, r in _EN:
        out = p.sub(lambda m, r=r: _keep_case(m.group(0), m.expand(r)), out)
    return out


def _keep_case(src, rep):
    return rep[:1].upper() + rep[1:] if src[:1].isupper() else rep


_SR = [
    # hrvatske reči i ijekavica
    (r"\bdionic(a|e|i|om|ama|u)\b", r"akcij\1"), (r"\btvrtk(a|e|i|om|u)\b", r"kompanij\1"), (r"\btvrtkama\b", "kompanijama"),
    (r"\bprošl(i|og) tjedan\b", "prošle nedelje"), (r"\bov(aj|og) tjedan\b", "ove nedelje"), (r"\bsljedeći tjedan\b", "sledeće nedelje"),
    (r"\btjedan\b", "nedelja"), (r"\btjedna\b", "nedelje"), (r"\btjednu\b", "nedelji"), (r"\btjedno\b", "nedeljno"), (r"\bsljedeć", "sledeć"), (r"\bmilijun(a|i|e)?\b", r"milion\1"), (r"\btakođer\b", "takođe"),
    (r"\bvjerojatno\b", "verovatno"), (r"\buslijed\b", "usled"), (r"\bpostot(ak|ka|ku)\b", r"procen\1"),
    (r"cijen", "cen"), (r"vrijed", "vred"), (r"mjesec", "mesec"), (r"\bprije\b", "pre"), (r"\bposlije\b", "posle"),
    (r"smjer", "smer"), (r"\bdjelat", "delat"), (r"\bsvijet", "svet"), (r"\bvrijeme\b", "vreme"), (r"\bnovac\b", "novac"),
    (r"\buvjet", "uslov"), (r"\bizvješ", "izveš"), (r"\bgospodarstv", "privred"),
    # doslovno prevedeni idiomi
    (r"\bima(ju)? vetar u leđa\b", r"ima\1 podršku"), (r"\bvetar u leđa\b", "podrška"), (r"\bvetra u leđa\b", "podrške"), (r"\bvetrom u leđa\b", "podrškom"), (r"\bvetru u leđa\b", "podršci"), (r"\b(?:čeon\w* vet\w*|protivvet\w*)", "otežavajuće okolnosti"),
    (r"\bpregrevanj\w* privred\w*", "prebrz rast privrede"), (r"\bpregrejan\w* privred\w*", "privreda koja raste prebrzo"),
    (r"\bpregrejan(a|o|e|i|u|ih|om)?\b", lambda m: "prekupljen" + (m.group(1) or "")),
    (r"\b(?:uporn|tvrdoglav|lepljiv)(?:a|e|u|om|oj) inflacij\w*", "inflacija koja sporo opada"),
    (r"\bmrtv\w* mačk\w*", "kratkotrajni oporavak"), (r"\bnož\w* koji pada\b", "akcija koja i dalje pada"),
    (r"\bzlatn\w* krst\w*", "signal rasta"), (r"\b(?:mrtvačk\w* krst\w*|krst\w* smrti)", "signal pada"),
    (r"\bjastreb(?:ovi|ova|ovima)\b", "zagovornici viših kamata"), (r"\bgolub(?:ovi|ova|ovima)\b", "zagovornici nižih kamata"),
    (r"\bjastrebov\w*", "sklon višim kamatama"), (r"\bgolub(?:ij|ov)\w*", "sklon nižim kamatama"),
    (r"\bmeko sletanje\b", "usporavanje bez recesije"), (r"\bmekog sletanja\b", "usporavanja bez recesije"),
    (r"\btvrdo sletanje\b", "recesija"), (r"\btvrdog sletanja\b", "recesije"), (r"\bu reliju\b", "u snažnom rastu"), (r"\breli(?:ja|ju|jem)?\b", "snažan rast"), (r"\brali(?:ja|ju|jem)?\b", "rast"),
    (r"\bzamah(?:a|u|om)?\b", "rast"), (r"\bzlatokos\w*", "uravnotežene okolnosti"),
    # pogrešan izbor reči u finansijama
    (r"\bzalih(e|a|ama)\b", lambda m: {"e": "akcije", "a": "akcija", "ama": "akcijama"}[m.group(1)]),
    (r"\b(\w+) se utrkuje\b", r"\1 žuri"), (r"\butrkuj(e|u) se\b", r"žur\1"), (r"\butkriva\b", "žuri"),
    (r"\b(?:vruć|pregrejan)\w*\s+(tržišt\w* rada)", r"snažno \1"),
    (r"\b(?:vruć|pregrejan)\w*\s+(privred\w*|ekonomij\w*)", r"\1 koja raste prebrzo"),
    (r"\bvruć(i|ih|im|ima|e|a|u|om|oj|eg|em|og)?\b(?=(?:\s+\S+){0,3}?\s+(?:inflacij|cen|CPI|PCE|podat|podac|izveštaj|brojk|plat|zarad|očitavanj))",
     lambda m: "visok" + {"em": "om", None: ""}.get(m.group(1), m.group(1) or "")),
    (r"\b(inflacij\w*|cene)(\s+(?:je|su|bila je|bile su|ostaje|ostaju|ostala je|i dalje je|i dalje su)(?:\s+i dalje)?)\s+vruć(a|e|om)\b", r"\1\2 visok\3"),
    (r"\b(inflacij\w*) se zagreva\b", r"\1 se ubrzava"), (r"\bzagrevanj(e|a|u) inflacij", r"ubrzavanj\1 inflacij"),
    (r"\btoplij(i|a|e|ih|im|u|om|oj)? od očekivan", lambda m: "viš" + (m.group(1) or "i") + " od očekivan"),
    (r"\bhladnij(i|a|e|ih|im|u|om|oj)? od očekivan", lambda m: "niž" + (m.group(1) or "i") + " od očekivan"),
    (r"\bvruć(a|e|u|om|oj) inflacij", r"visok\1 inflacij"), (r"\bVol Strit\b", "Wall Street"), (r"\bVolstrit\b", "Wall Street"),
    (r"\bbikov(i|a)\b", "optimisti"), (r"\bmedved(i|a)\b", "pesimisti"),
]
_SR = [(re.compile(p, re.I) if not isinstance(p, re.Pattern) else p, r) for p, r in _SR]


def polish_sr(text):
    if not text:
        return text
    out = text
    for p, r in _SR:
        out = p.sub(lambda m, r=r: _keep_case(m.group(0), r(m) if callable(r) else m.expand(r)), out)
    out = re.sub(r"\bNev Iork\b", "Njujork", out)
    out = re.sub(r"\b(AP|Fox|CBS|NBC|ABC|Sky|BBC|Yahoo) Nevs\b", r"\1 News", out)
    out = re.sub(r"\bvisoku inflacij", "visoku inflacij", out)
    # tačka-zarez se ne koristi u srpskim rečenicama: novu misao počinje tačka
    out = re.sub(r"\s*;\s+(\S)", lambda m: ". " + m.group(1)[:1].upper() + m.group(1)[1:], out)
    out = re.sub(r"\s*;\s*$", ".", out, flags=re.M)
    return out


# ---------- vlastite imenice ostaju u izvornom obliku ----------
# Google imena ljudi, kompanija, medija i časopisa prevodi ili prepisuje fonetski ("Džerom Pauel", "SpaceKs", "Akios").
# Pre prevoda ih menjamo oznakom, a posle vraćamo original - u srpskom sa padežnim nastavkom ("Powella", "Teslom", "SpaceX-a").
KNOWN_NAMES = {
    "Powell", "Lagarde", "Trump", "Biden", "Harris", "Musk", "Bessent", "Yellen", "Waller", "Bowman", "Jefferson", "Goolsbee",
    "Kashkari", "Daly", "Hammack", "Logan", "Schmid", "Musalem", "Bostic", "Barkin", "Miran", "Warsh", "Hassett", "Lutnick",
    "Navarro", "Greer", "Huang", "Altman", "Buffett", "Dimon", "Zuckerberg", "Nadella", "Pichai", "Bezos", "Jassy", "Cook",
    "Su", "Gelsinger", "Tan", "Fraser", "Solomon", "Moynihan", "Fink", "Dalio", "Ackman", "Griffin", "Icahn", "Wood",
    "Xi", "Putin", "Zelensky", "Zelenskiy", "Macron", "Merz", "Scholz", "Meloni", "Starmer", "Reeves", "Bailey", "Ueda",
    "Kuroda", "Takaichi", "Jinping", "Ishiba", "Modi", "Erdogan", "Netanyahu", "Vucic", "Vučić", "Orban", "Lula", "Milei",
    "Sheinbaum", "Carney", "Albanese", "Nagel", "Villeroy", "Lane", "Schnabel", "Kazaks", "Holzmann", "Knot", "Rehn",
    "Dombrovskis", "Gentiloni", "Leyen", "Georgieva", "Banga", "Okonjo-Iweala", "Collins", "Cleveland",
}
KNOWN_ORGS = {
    "SpaceX", "Tesla", "Google Cloud", "Fannie Mae", "Freddie Mac", "Target", "Walmart", "Costco", "Oracle", "Visa", "Mastercard", "Block", "Snap", "Shell", "Unilever", "Nvidia", "NVIDIA", "Apple", "Microsoft", "Alphabet", "Google", "Amazon", "Meta", "OpenAI", "Anthropic",
    "Netflix", "Intel", "AMD", "Broadcom", "Oracle", "Salesforce", "Palantir", "Berkshire", "Hathaway", "JPMorgan", "Goldman",
    "Sachs", "Morgan", "Stanley", "BlackRock", "Citigroup", "Citi", "Wells", "Fargo", "Boeing", "Airbus", "Pfizer", "Moderna",
    "Novo", "Nordisk", "Lilly", "Merck", "Walmart", "Costco", "Disney", "Uber", "Airbnb", "Shopify", "Samsung", "TSMC", "ASML",
    "SAP", "Siemens", "Volkswagen", "BMW", "Mercedes", "Porsche", "Toyota", "Honda", "Sony", "Alibaba", "Tencent", "Baidu",
    "BYD", "Xiaomi", "Huawei", "Aramco", "Shell", "Exxon", "ExxonMobil", "Chevron", "TotalEnergies", "LVMH", "Nestle",
    "Nestlé", "Unilever", "Visa", "Mastercard", "PayPal", "Coinbase", "Robinhood", "Reuters", "Bloomberg", "CNBC", "Axios",
    "Politico", "Barron's", "MarketWatch", "Forbes", "Fortune", "Yahoo", "Morningstar", "Moody's", "Fitch", "Nasdaq", "NYSE",
    "Vanguard", "Fidelity", "Schwab", "Megaspeed", "Starlink", "xAI", "MicroStrategy", "Telekom", "Erste", "Raiffeisen",
    "Intesa", "UniCredit", "Deutsche", "Commerzbank", "HSBC", "Barclays", "UBS", "Nomura", "SoftBank", "Arm", "Qualcomm",
    "Micron", "Dell", "IBM", "Cisco", "Adobe", "Snowflake", "CoreWeave", "Supermicro", "Vertiv", "Caterpillar", "Deere",
    "Ford", "Stellantis", "Rivian", "Lucid", "Nike", "Starbucks", "McDonald's", "Coca-Cola", "PepsiCo", "Wolt", "Glovo",
    "Infineon", "Rheinmetall", "Allianz", "Ferrari", "Renault", "Kering", "Hermès", "L'Oréal", "AstraZeneca", "Novartis",
    "Roche", "Bayer", "BASF", "Equinor", "Gazprom", "Rosneft", "Sberbank", "NIS", "Bitcoin", "Ethereum", "ChatGPT", "Gemini",
    "Claude", "Copilot", "Blackwell", "Hopper", "iPhone", "Windows", "Azure", "AWS", "YouTube", "Instagram", "WhatsApp",
    "TikTok", "ByteDance", "Temu", "Shein", "Pinduoduo", "JD", "Nio", "Spotify", "Zoom", "Slack", "Stripe", "Klarna",
    "Revolut", "Ozempic", "Wegovy", "Mounjaro", "Zepbound", "Elsevier", "Springer", "Wiley", "SSRN", "arXiv", "OpenAlex",
}
JOURNALS = ["The Guardian", "The New Yorker", "Washington Post", "The Washington Post", "New York Post", "The Independent", "Associated Press", "AP News", "Yahoo Finance", "The Economist", "Fox News", "Sky News", "Business Insider", "Journal of Finance", "Journal of Financial Economics", "Review of Financial Studies", "Journal of Financial and Quantitative Analysis",
            "Review of Finance", "Journal of Banking & Finance", "Journal of Banking and Finance", "Financial Analysts Journal",
            "Journal of Portfolio Management", "Quantitative Finance", "Expert Systems with Applications", "Applied Soft Computing",
            "Management Science", "Journal of Econometrics", "Wall Street Journal", "Financial Times", "New York Times",
            "Washington Post", "The Economist", "Business Insider", "Seeking Alpha", "Associated Press", "Dow Jones",
            "Morgan Stanley", "Goldman Sachs", "Bank of America", "Wells Fargo", "Charles Schwab", "Berkshire Hathaway",
            "Novo Nordisk", "Eli Lilly", "Deutsche Bank", "Banca Intesa", "S&P Global"]
# reči koje počinju velikim slovom, a nisu imena koja treba sačuvati (institucije, mesta, meseci, nacionalnosti...)
_INSTITUTION = {"England", "Scotland", "Wales", "Ireland", 
    "Islamic", "Christian", "Muslim", "Jewish", "Catholic", "Orthodox", "European", "Asian", "Western", "Eastern", "Gulf", "Arctic", "Atlantic", "Pacific",
    "Federal", "Reserve", "Bank", "Banks", "Central", "European", "Union", "Department", "Treasury", "Ministry", "Commission",
    "Market", "Markets", "Stock", "Stocks", "Exchange", "States", "United", "Kingdom", "House", "White", "Senate", "Congress",
    "Court", "Supreme", "Inc", "Corp", "Group", "Holdings", "Fund", "Funds", "Index", "Street", "Wall", "Securities",
    "National", "International", "Monetary", "World", "Trade", "Organization", "Office", "Council", "Parliament", "Republic",
    "Asia", "Europe", "America", "American", "Chinese", "China", "Japan", "Japanese", "German", "Germany", "British", "Britain",
    "Serbia", "Serbian", "Russia", "Russian", "Ukraine", "Ukrainian", "India", "Indian", "Canada", "Canadian", "Mexico", "Mexican",
    "France", "French", "Italy", "Italian", "Spain", "Spanish", "Middle", "East", "West", "North", "South", "New", "York",
    "Silicon", "Valley", "Street's", "Fed", "ECB", "AI", "IMF", "OPEC", "EU", "UN", "NATO", "WTO", "GDP", "CPI", "PCE", "ETF", "IPO",
    "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Q1", "Q2", "Q3", "Q4", "CEO", "CFO",
    "President", "Chair", "Chairman", "Governor", "Minister", "Prime", "Secretary", "Director", "Chief", "Executive",
    "Capital", "Partners", "Management", "Research", "Energy", "Motors", "Airlines", "Systems", "Technologies", "Pharma",
    "Korea", "Korean", "Taiwan", "Taiwanese", "Iran", "Iranian", "Israel", "Israeli", "Gaza", "Saudi", "Arabia", "Turkey",
    "Turkish", "Brazil", "Brazilian", "Argentina", "Australia", "Australian", "Switzerland", "Swiss", "Netherlands", "Dutch",
    "Poland", "Polish", "Greece", "Greek", "Egypt", "Africa", "African", "Asian", "Vietnam", "Indonesia", "Singapore", "Dubai",
    "Qatar", "Venezuela", "Greenland", "Panama", "Hungary", "Hungarian", "Croatia", "Croatian", "Bosnia", "Montenegro", "Kosovo",
    "Romania", "Bulgaria", "Austria", "Belgium", "Sweden", "Norway", "Denmark", "Finland", "Ireland", "Portugal", "Czech",
    "Beijing", "Washington", "London", "Paris", "Berlin", "Tokyo", "Moscow", "Kyiv", "Kiev", "Brussels", "Frankfurt", "Belgrade",
    "Shanghai", "Hong", "Kong", "Davos", "Geneva", "Zurich", "Milan", "Rome", "Madrid", "Vienna", "Seoul", "Delhi", "Mumbai",
    "Texas", "California", "Florida", "Ohio", "Michigan", "Illinois", "Georgia", "Arizona", "Nevada", "Virginia", "Carolina",
    "Pennsylvania", "Massachusetts", "Chicago", "Boston", "Atlanta", "Houston", "Dallas", "Detroit", "Seattle", "San", "Francisco",
    "Los", "Angeles", "Western", "Eastern", "Northern", "Southern", "Latin", "Arab", "Democrats", "Republicans", "Democratic",
    "Republican", "Senator", "Representative", "Pentagon", "Commerce", "Justice", "Labor", "Administration", "Government",
    "Board", "Committee", "Institute", "University", "Christmas", "Easter", "Thanksgiving", "Black", "Cyber", "Halloween",
    "Olympics", "Mr", "Mrs", "Ms", "Dr", "Inc.", "Ltd", "PLC", "LLC", "SA", "AG", "NV", "Co", "Corp.", "The",
}
_STARTERS = {"The", "A", "An", "In", "On", "At", "After", "Before", "As", "But", "And", "Or", "If", "When", "While", "With",
             "For", "From", "To", "Why", "How", "What", "Who", "This", "That", "These", "Those", "It", "Its", "US", "U.S.", "UK",
             "I", "We", "They", "He", "She", "Our", "Their", "His", "Her", "Some", "Many", "Most", "All", "Both", "Each", "Also",
             "Here", "There", "Now", "Today", "Yesterday", "Still", "Even", "Only", "More", "Less", "One", "Two", "Three", "Its",
             "Is", "Are", "Was", "Were", "Will", "Would", "Could", "Should", "Can", "May", "Might", "Do", "Does", "Did", "Not", "No",
             "Yes", "Shares", "Stocks", "Investors", "Analysts", "Markets", "Prices", "Oil", "Gold", "Rates", "Inflation", "Sales",
             "Revenue", "Profit", "Earnings", "Data", "Report", "Reports", "Study", "Results", "Researchers", "Experts", "Officials"}
_TOKEN = "ZM{}MZ"
_TOKEN_RX = re.compile(r"Z\s?M\s?(\d+)\s?M\s?Z(-?[a-zčćšžđ]{1,4})?\b", re.I)
_CAP = r"[A-Z][a-zà-öø-ÿčćšžđ]+(?:-[A-Z][a-zà-öø-ÿčćšžđ]+)?"
_MULTI = re.compile(rf"\b{_CAP}(?:\s+[A-Z]\.)?(?:\s+{_CAP}){{1,5}}\b")
_WORD = re.compile(r"(?<![\w-])([A-Za-z][\w'’&.-]*[\w])(?![\w-])")
_SENT_START = re.compile(r"(^|[.!?:]\s+|[\"“(]\s*)$")


def _title_case(text):
    words = re.findall(r"[A-Za-z][\w'-]*", text)
    return sum(1 for w in words[1:] if w in _TITLE_WORDS) >= 2


_TITLE_WORDS = {"Says", "Is", "Are", "To", "Of", "In", "On", "For", "As", "After", "With", "Its", "At", "By", "From", "Up",
                "Down", "Over", "And", "The", "Will", "May", "Could", "Rises", "Falls", "Rise", "Fall", "Than", "Into", "Amid",
                "Be", "Has", "Have", "New", "More", "Less", "Higher", "Lower", "Gains", "Drops", "Hits", "Sees", "Gets"}


def _odd_case(w):
    """SpaceX, xAI, iPhone, AMD, TSMC - neobična velika slova odaju ime, a ne običnu reč."""
    core = w.strip(".'’")
    return (len(core) >= 2 and (any(c.isupper() for c in core[1:]) or any(c.isdigit() for c in core))
            and not core.isupper() or (core.isupper() and len(core) >= 3 and core not in _INSTITUTION and core not in _STARTERS))


def protect_names(text):
    """Vraća (tekst sa oznakama, lista imena). Štiti vlastite imenice: ljude, kompanije, medije, časopise, proizvode."""
    if not text:
        return text, []
    names = []

    def tok(name):
        if name not in names:
            names.append(name)
        return _TOKEN.format(names.index(name))

    text = sentence_case(text)
    out = text
    # 1) poznati višečlani nazivi (časopisi, mediji, banke)
    for j in sorted(JOURNALS, key=len, reverse=True):
        if j in out:
            out = re.sub(r"(?<![\w])" + re.escape(j) + r"(?![\w])", lambda m: tok(m.group(0)), out)
    title = _title_case(text)
    # 2) imena od dve i više reči velikim slovom (ljudi i kompanije), bez institucija i mesta
    def multi(m):
        words = m.group(0).split()
        stop = lambda w: w.strip(".") in _INSTITUTION or w in _STARTERS or w in _TITLE_WORDS
        res, run = [], []
        def flush():
            plain_words = all((_common(w) or re.sub(r"['’]s$", "", w) in PLACES) and re.sub(r"['’]s$", "", w) not in KNOWN_NAMES | KNOWN_ORGS for w in run) \
                or re.sub(r"['’]s$", "", " ".join(run)) in PLACES
            if len(run) >= 2 and not plain_words and (not title or run[-1] in KNOWN_NAMES or run[-1] in KNOWN_ORGS or run[0] in KNOWN_ORGS):
                res.append(tok(" ".join(run)))
            else:
                res.extend(run)
            run.clear()
        for w in words:
            if stop(w):
                flush(); res.append(w)
            elif run and re.sub(r"['’]s$", "", w) in KNOWN_ORGS and " ".join(run + [w]) not in KNOWN_ORGS:
                flush(); run.append(w)  # "Jensen Huang Nvidia" -> "Jensen Huang" + "Nvidia"
            else:
                run.append(w)
        flush()
        return " ".join(res)
    out = _MULTI.sub(multi, out)
    # 3) pojedinačne reči: poznata imena i kompanije, neobična velika slova i (u običnim rečenicama) reči velikim slovom usred rečenice
    surnames = {n.split()[-1] for n in names}
    def single(m):
        w = m.group(1)
        if re.search(r"ZM\d+MZ", w):
            return w
        base = re.sub(r"['’]s$", "", w)
        if base in _INSTITUTION or base in _STARTERS or len(base) < 2:
            return w
        known = base in KNOWN_NAMES or base in KNOWN_ORGS or base in surnames
        if not known and not _odd_case(base) and (_common(base) or base in PLACES):  # obična reč velikim slovom ("Home", "Aviation") se prevodi
            return w
        mid = not _SENT_START.search(out[:m.start()]) and base[0].isupper() and not title
        if known or _odd_case(base) or (mid and base not in _TITLE_WORDS and not base.isupper()):
            if len(base) <= 2 and base not in ("Xi", "Li", "Su", "JD", "HP", "GM", "BP"):
                return w
            return tok(base) + w[len(base):]
        return w
    out = _WORD.sub(single, out)
    return out, names


# ---------- padeži u srpskom (pravopis imena ostaje izvorni: "Powella", "sa Teslom", "SpaceX-a") ----------
FEMALE_FIRST = {"Christine", "Janet", "Kristalina", "Ursula", "Giorgia", "Kamala", "Hillary", "Claudia", "Gita", "Ngozi", "Lisa",
                "Mary", "Isabel", "Isabelle", "Elizabeth", "Margrethe", "Michelle", "Sarah", "Susan", "Ruth", "Ann", "Anne", "Karen",
                "Lael", "Lorie", "Beth", "Sanae", "Rachel", "Gina", "Nancy", "Catherine", "Cathie", "Abigail", "Jane", "Julie",
                "Linda", "Emma", "Olivia", "Sophie", "Angela", "Marine", "Ana", "Maria", "Marie", "Alexandria", "Jennifer", "Jessica",
                "Laura", "Andrea", "Ellen", "Helen", "Carol", "Diane", "Melinda", "Indra", "Safra", "Whitney", "Lina", "Gita"}
FEMALE_SURNAMES = {"Lagarde", "Yellen", "Meloni", "Georgieva", "Sheinbaum", "Reeves", "Schnabel", "Daly", "Hammack", "Logan",
                   "Bowman", "Su", "Leyen", "Takaichi", "Okonjo-Iweala", "Harris", "Wood", "Raimondo", "Pelosi", "Clinton", "Collins"}
_VOWELS = set("aeiouyAEIOUY")
_CASE_BY_PREP = {}
for _w in ("od", "iz", "do", "bez", "kod", "oko", "umesto", "posle", "pre", "nakon", "tokom", "preko", "sem", "osim", "blizu",
           "pored", "ispred", "iza", "zbog", "radi", "povodom", "putem", "strane", "protiv", "duž", "usled", "prilikom"):
    _CASE_BY_PREP[_w] = "a"
for _w in ("prema", "ka", "k", "zahvaljujući", "uprkos", "nasuprot"):
    _CASE_BY_PREP[_w] = "u"
for _w in ("o", "pri", "po"):
    _CASE_BY_PREP[_w] = "u"
for _w in ("sa", "s", "pod", "nad", "pred", "među", "između"):
    _CASE_BY_PREP[_w] = "om"
# imenice posle kojih ime stoji u genitivu ("akcije Nvidije", "administracije Trumpa", "osnivač Tesle")
_GEN_NOUNS = re.compile(r"^(akcij|deonic|administracij|vlad|kabinet|izjav|odluk|predlog|plan|prihod|dobit|rezultat|direktor|šef|"
                        r"osnivač|vlasni|portparol|strategij|ponud|preuzimanj|spajanj|kupovin|vrednost|cen|tržišn|izveštaj|"
                        r"zarad|poslovanj|proizvod|čip|model|tim|analitičar|ekonomist|investitor|akcionar|deo|udeo|pad|rast|"
                        r"sedišt|fabri|servis|platform|uprav|odbor|predsednik|ministar|guverner|tim|rukovodstv|vest|tvrdnj)\w*$", re.I)
_OK_SUFFIX = {"a", "u", "om", "em", "e", "i", "ov", "ova", "ovu", "ove", "ovo", "ovog", "ovom", "ovim", "ovih", "ovi"}


def _female(name):
    words = name.split()
    return bool(words) and (words[0] in FEMALE_FIRST or words[-1] in FEMALE_SURNAMES)


def _decline(name, case):
    """case: 'a' (genitiv), 'u' (dativ/lokativ), 'om' (instrumental) ili prisvojni nastavak ('ova'...)."""
    if not case or _female(name):
        return name
    words = name.split()
    last = words[-1]
    if case.startswith("ov"):  # prisvojni pridev samo na poslednjoj reči: "Powellova izjava"
        if last[-1] in _VOWELS:
            return name
        return " ".join(words[:-1] + [last + ("-" if last[-1].isupper() or last[-1].isdigit() else "") + case])
    def one(w, is_last):
        if not w[-1].isalpha() and not w[-1].isdigit():
            return w
        if w[-1].isupper() or w[-1].isdigit() or (w.isupper() and len(w) > 1):  # SpaceX-a, AMD-om, BMW-u
            return w + "-" + case if is_last else w
        if w[-1] == "a" and w[-2:] != "ia" and len(w) > 2:  # Tesla -> Tesle, Tesli, Teslom
            return w[:-1] + {"a": "e", "u": "i", "om": "om", "e": "e", "i": "i"}.get(case, "a") if is_last else w
        if w.endswith("ia") and len(w) > 3:  # Nvidia -> Nvidije, Nvidiji, Nvidijom
            return w[:-1] + "j" + {"a": "e", "u": "i", "om": "om", "e": "e", "i": "i"}.get(case, "a") if is_last else w
        if w[-1] == "e" and w[-2] not in _VOWELS and (w in KNOWN_ORGS or name in KNOWN_ORGS):  # nemo e: Apple-a, Google-om
            return w + "-" + ("a" if case == "e" else "u" if case == "i" else case) if is_last else w
        if w[-1] in _VOWELS:
            return w
        suf = case
        if suf == "om" and w[-1] in "jčćđšž":
            suf = "em"
        if suf in ("e", "i"):
            suf = "a" if suf == "e" else "u"
        return w + suf
    return " ".join(one(w, i == len(words) - 1) for i, w in enumerate(words))


def restore_names(text, names, lang="sr"):
    """Vraća imena na mesto oznaka (sa padežom u srpskom). None ako je neka oznaka izgubljena u prevodu."""
    if not names:
        return text
    seen = set()
    src = text or ""
    def back(m):
        i = int(m.group(1))
        if i >= len(names):
            return m.group(0)
        seen.add(i)
        name = names[i]
        if lang != "sr":
            return name
        suf = (m.group(2) or "").lstrip("-").lower()
        if suf and suf in _OK_SUFFIX:
            return _decline(name, suf)
        if suf:  # nepoznat nastavak - ostavi ime bez njega
            return name
        before = re.findall(r"[A-Za-zčćšžđČĆŠŽĐ]+", src[max(0, m.start() - 30):m.start()])
        prev = before[-1] if before else ""
        if prev.lower() in _CASE_BY_PREP:
            return _decline(name, _CASE_BY_PREP[prev.lower()])
        if prev and _GEN_NOUNS.match(prev.lower()):
            return _decline(name, "a")
        return name
    out = _TOKEN_RX.sub(back, src)
    if len(seen) < len(names) or re.search(r"ZM\s?\d", out):
        return None
    return out


# ---------- naslovi u kojima je svaka reč velikim slovom ("Inflation Report Supports Fed Rate Hike") ----------
# Takav naslov se pre prevoda prepravlja u običnu rečenicu: obične reči dobijaju malo slovo, a vlastite imenice ostaju.
# Šta je "obična reč" uči se iz samih vesti: reč koja se u tekstovima javlja malim slovom (VOCAB).
VOCAB = set()
_SEED = """a about above after again against all also amid an and any are as at back bank be because been before being below
best between big bid billion board boost both but by can cash chief clash climb cut cuts curbs data deal debt decline decision
decisions demand down drop drops due during early economy end era expected face faces fail failed fall falls fear fears fight
first for from fund funds gain gains gets give global good growth half has have he her high higher hike hikes his how in into
investors is it its job jobs just key last latest lead leads less life likely loss low lower make maker market markets may more
most move new news next no not now of off offer oil on one only or out over own plan plans post prices profit push rate rates
record report reports return rise rises risk rules sales say says see sees sell set share shares should slow some stake steady
gradual appropriate still stock stocks strong supports talks than that the their them then there these they this those through
time to top trade under up us vote war was we week what when where which while who why will with world would year years yet
inflation interest determine preparing merger floats failed bid new life increase increases government administration committee board new pare pares slump slumps tumble tumbles soar soars plunge plunges""".split()


def load_vocab(texts):
    """Uči obične reči iz tekstova vesti: reč koja se javi malim slovom bar dva puta."""
    from collections import Counter
    c = Counter(w for t in texts for w in re.findall(r"(?<![A-Za-z])[a-z][a-z'-]{1,}", t or ""))
    VOCAB.update(w for w, n in c.items() if n >= 2)
    return len(VOCAB)


def _common(word):
    w = word.lower().strip(".,:;!?\"'’()")
    w = re.sub(r"['’]s$", "", w)
    if not w:
        return False
    if w in VOCAB or w in _SEED_SET:
        return True
    for pre in ("under", "over", "out", "re", "un"):  # undervalued, outperform, reprice
        if w.startswith(pre) and len(w) > len(pre) + 3 and _common(w[len(pre):]):
            return True
    for suf in ("s", "es", "ed", "ing", "ly"):  # rise -> rises, cut -> cuts, steady -> steadily
        if w.endswith(suf) and (w[:-len(suf)] in VOCAB or w[:-len(suf)] in _SEED_SET or w[:-len(suf)] + "e" in VOCAB):
            return True
    return False


_SEED_SET = set(_SEED)
_MULTI_KNOWN = sorted({n for n in KNOWN_NAMES | KNOWN_ORGS | set(JOURNALS) if " " in n}, key=len, reverse=True)
try:  # ~12.000 najčešćih engleskih reči (wordfreq), bez poznatih imena i kompanija
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocab_en.txt"), encoding="utf-8") as _f:
        _SEED_SET.update(w.strip() for w in _f if w.strip())
except OSError:
    pass
try:  # države, gradovi i nazivi naroda - imaju srpski prevod (Prag, Česi, Bahrein), pa se ne štite
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "places_en.txt"), encoding="utf-8") as _f:
        PLACES = {w.strip() for w in _f if w.strip()}
except OSError:
    PLACES = set()
try:  # lična imena koja su i obične reči (Mark, Bill, Rose) - ostaju velikim slovom kad iza njih ide prezime
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "first_names_common.txt"), encoding="utf-8") as _f:
        _FIRST_COMMON = {w.strip() for w in _f if w.strip()}
except OSError:
    _FIRST_COMMON = set()
# opšte imenice iz _INSTITUTION koje u naslovu Svakom Reči Velikim Slovom treba spustiti (države, gradovi, meseci ostaju)
_GENERIC_INST = {"Board", "Government", "Committee", "Administration", "New", "Market", "Markets", "Stock", "Stocks", "Index",
                 "Exchange", "Trade", "Research", "Energy", "Management", "Office", "Fund", "Funds", "Group", "Capital", "Central",
                 "Chief", "Director", "Executive", "Black", "White", "World", "International", "National", "Union", "Bank", "Banks",
                 "Council", "Court", "Department", "Ministry", "Minister", "President", "Chair", "Chairman", "Secretary", "Governor",
                 "Senator", "Systems", "Technologies", "Partners", "Holdings", "Institute", "Organization", "Commission", "Labor",
                 "Justice", "Commerce", "Monetary", "Prime", "Representative", "Securities", "Supreme", "Cyber", "Pharma", "Motors",
                 "Airlines", "Republic", "Kingdom", "Middle", "East", "West", "North", "South", "Eastern", "Western", "Northern", "Southern"}


_TITLE_RUN = re.compile(r"(?:(?<=\s)|^)(?:[A-Z][\w'’&.-]*\s+){2,}[A-Z][\w'’&.-]*")


def sentence_case(text):
    """Naslov sa svim velikim slovima -> obična rečenica, uz čuvanje vlastitih imenica."""
    if not text:
        return text
    words = re.findall(r"[A-Za-z][\w'’-]*", text)
    long_ = [w for w in words if len(w) > 3]
    whole = len(long_) >= 3 and sum(w[0].isupper() for w in long_) / len(long_) >= 0.7
    if not whole and not _TITLE_RUN.search(text):
        return text
    parts = re.split(r"(\s+)", re.sub(r"\b(Post|Pre|Ex|Anti)-(?=[A-Z])", lambda m: m.group(1).lower() + "-", text))
    words_i = [i for i, p in enumerate(parts) if p.strip()]
    joined = "".join(parts)
    fixed = set()  # reči koje su deo poznatog višečlanog naziva ("Google Cloud", "Wall Street Journal")
    for nm in _MULTI_KNOWN:
        for m in re.finditer(r"(?<![\w])" + re.escape(nm) + r"(?![\w])", joined):
            fixed.update(range(m.start(), m.end()))
    pos, starts = 0, {}
    for i, p in enumerate(parts):
        starts[i] = pos
        pos += len(p)
    allowed = None  # bez celog naslova velikim slovima: samo nizovi od 3+ reči velikim slovom (spojeni naslovi iz Google News opisa)
    if not whole:
        allowed = set()
        for m in _TITLE_RUN.finditer(joined):
            if sum(1 for w in m.group(0).split() if _common(w)) >= 2:
                allowed.update(range(m.start(), m.end()))
    out, first = list(parts), True
    for k, i in enumerate(words_i):
        tok_ = parts[i]
        if allowed is not None and starts[i] not in allowed:
            first = bool(re.search(r"[:.!?]$", tok_.strip()))
            continue
        core = re.sub(r"^[\"“'(\[]+|[\"”'),.:;!?\]]+$", "", tok_)
        base = re.sub(r"['’]s$", "", core)
        nxt = parts[words_i[k + 1]] if k + 1 < len(words_i) else ""
        nxt_core = re.sub(r"^[\"“'(\[]+|[\"”'),.:;!?\]]+$", "", nxt)
        def _proper(w):  # susedna reč koja je deo imena ("John Smith", "New York")
            b = re.sub(r"['’]s$", "", w)
            return bool(w[:1].isupper()) and (not _common(w) or (b in _INSTITUTION and b not in _GENERIC_INST) or b in KNOWN_NAMES or b in KNOWN_ORGS)
        nxt_cap = _proper(nxt_core) and not re.search(r"[:.!?,]$", tok_)
        inst_common = base in _GENERIC_INST and _common(core) and not nxt_cap
        first_name = base in _FIRST_COMMON and bool(nxt[:1].isupper()) and not _common(nxt_core) and nxt_core not in KNOWN_ORGS
        keep = (first or first_name or starts[i] in fixed or not core or not core[0].isupper() or core.isupper() or _odd_case(base) or base in KNOWN_NAMES
                or base in KNOWN_ORGS or (base in _INSTITUTION and not inst_common) or not _common(core)
                )
        if not keep:
            out[i] = tok_.replace(core, core[:1].lower() + core[1:], 1)
        first = bool(re.search(r"[:.!?]$", tok_.strip()))
    return "".join(out)


# ---------- provera da li je "prevod" ostao na engleskom ----------
_EN_MARK = {"the", "and", "of", "for", "with", "is", "are", "says", "said", "will", "from", "after", "as", "its", "their", "this",
            "that", "has", "have", "was", "were", "by", "into", "over", "amid", "against", "about", "than", "could", "would",
            "should", "be", "been", "it", "they", "he", "she", "which", "what", "how", "why", "while", "rises", "falls", "gets"}


def looks_english(text, names=()):
    """Tačno kad srpski prevod i dalje sadrži engleske rečenice (imena i nazivi se ne računaju)."""
    if not text:
        return False
    t = text
    for n in sorted(names or (), key=len, reverse=True):
        t = t.replace(n, " ")
    words = re.findall(r"[A-Za-zčćšžđČĆŠŽĐ']+", t)
    if len(words) < 3:
        return False
    # samo reči malim slovom - nazivi izvora ("The Guardian", "The New Yorker") ostaju na engleskom i nisu greška
    low = [w for w in words if w[:1].islower()]
    marks = sum(1 for w in low if w in _EN_MARK)
    common = sum(1 for w in low if w in _SEED_SET and len(w) > 3 and w not in _SR_OK and not re.search(r"[čćšžđ]", w))
    return marks >= 2 or (marks >= 1 and len(words) <= 8) or common / len(words) > 0.45


def english_words(text):
    """Engleske reči koje su ostale u srpskom tekstu (bez imena, skraćenica i reči sa velikim slovom)."""
    out = []
    for w in re.findall(r"(?<![\w-])[a-z][a-z']{3,}(?![\w-])", text or ""):
        if w in _SEED_SET and w not in _SR_OK:
            out.append(w)
    return out


# reči koje postoje i u engleskom i u srpskom (ili su uobičajene pozajmice) - nisu greška u prevodu
_SR_OK = set("""dona sale more pare data rate kola noga ruke dana mala malo male sada tako koja koje koji samo nego tada pala pali
pada rast lista plan plana planu cena cene kada kao nove novi nova neka nema mesto mere meru sve svet sveta online start
startup hedge fond fonda fondu fondovi bank banka banke trend trenda trendu lider lidera marketing menadžment status tim tima
analiza analize ideja ideje ponuda ponude prema posle pred preko zato more mora moraju""".split())
