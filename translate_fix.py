"""Popravke mašinskog prevoda finansijskih vesti na srpski.

1) simplify_en: pre prevoda žargon i idiome zamenjuje običnim engleskim ("hot inflation" -> "high inflation"),
   jer ih Google inače prevodi doslovno ("vruća inflacija").
2) polish_sr: posle prevoda ispravlja česte greške - ijekavicu, hrvatske reči, "zalihe" umesto "akcije" i slično.
"""
import re

TR_VERSION = "3"

_EN = [
    # inflacija i kamate
    (r"\bhotter[- ]than[- ]expected\b", "higher-than-expected"), (r"\bcooler[- ]than[- ]expected\b", "lower-than-expected"),
    (r"\bhot inflation\b", "high inflation"), (r"\binflation (runs|running|ran) hot\b", r"inflation \1 high"),
    (r"\b(?:sticky|stubborn|persistent) inflation\b", "inflation that is slow to fall"), (r"\binflation cools\b", "inflation slows"), (r"\bcooling inflation\b", "slowing inflation"),
    (r"\bhawkish\b", "in favor of higher interest rates"), (r"\bdovish\b", "in favor of lower interest rates"),
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
    out = text
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
    out = re.sub(r"\bvisoku inflacij", "visoku inflacij", out)
    # tačka-zarez se ne koristi u srpskim rečenicama: novu misao počinje tačka
    out = re.sub(r"\s*;\s+(\S)", lambda m: ". " + m.group(1)[:1].upper() + m.group(1)[1:], out)
    out = re.sub(r"\s*;\s*$", ".", out, flags=re.M)
    return out
