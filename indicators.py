"""Finansijski pokazatelji kompanija: definicije, objašnjenja (SR/EN), računanje i ocena."""

GROUPS = [
    ("val", "Vrednovanje", "Valuation", "Koliko plaćaš za ono što kompanija zarađuje ili poseduje.",
     "How much you pay for what the company earns or owns."),
    ("prof", "Profitabilnost", "Profitability", "Koliko efikasno kompanija pretvara prihod i kapital u profit.",
     "How efficiently the company turns revenue and capital into profit."),
    ("growth", "Rast", "Growth", "Koliko brzo rastu prihodi i zarada.", "How fast revenue and earnings grow."),
    ("health", "Finansijsko zdravlje", "Financial health", "Koliko je kompanija zadužena i da li može da plati obaveze.",
     "How indebted the company is and whether it can pay its bills."),
    ("div", "Dividenda", "Dividend", "Koliko novca kompanija vraća akcionarima.", "How much cash the company returns to shareholders."),
    ("risk", "Rizik i kretanje cene", "Risk & price action", "Koliko se cena njiše i kako se kretala.",
     "How much the price swings and how it has moved."),
    ("analyst", "Analitičari", "Analysts", "Šta o akciji misle analitičari banaka i brokera.", "What bank and broker analysts think of the stock."),
]

# key, grupa, naziv SR, naziv EN, format, smer ('up' = više je bolje, 'down' = niže je bolje, None = bez ocene),
# (granica za "dobro", granica za "slabo"), kratko SR, kratko EN, detaljno SR, detaljno EN
DEFS = [
    ("pe_t", "val", "P/E (prošlih 12 meseci)", "P/E (trailing 12 months)", "x", "down", (15, 35),
     "Cena akcije podeljena zaradom po akciji u poslednjih 12 meseci.",
     "Share price divided by earnings per share over the last 12 months.",
     "**Šta meri:** koliko dinara (dolara) investitori plaćaju za 1 dinar godišnje dobiti. P/E od 20 znači da bi, uz istu dobit, "
     "trebalo 20 godina da kompanija „zaradi“ svoju tržišnu vrednost.\n\n**Formula:** cena akcije / zarada po akciji (EPS) za poslednjih 12 meseci.\n\n"
     "**Kako čitati:** niži P/E znači jeftiniju akciju u odnosu na dobit, ali može značiti i da tržište očekuje pad zarade. "
     "Visok P/E obično znači da investitori očekuju brz rast. Dugoročni prosek za S&P 500 je oko 15-20.\n\n"
     "**Pazi:** poredi samo kompanije iz istog sektora - tehnološke firme po pravilu imaju viši P/E od banaka. "
     "Negativan P/E (gubitak) se ne tumači kao „jeftino“.",
     "**What it measures:** how many dollars investors pay for one dollar of annual profit. A P/E of 20 means that, with flat profits, "
     "it would take 20 years for the company to 'earn' its market value.\n\n**Formula:** share price / earnings per share (EPS) over the last 12 months.\n\n"
     "**How to read it:** a lower P/E means a cheaper stock relative to profit, but can also signal that the market expects earnings to fall. "
     "A high P/E usually means investors expect fast growth. The long-run average for the S&P 500 is around 15-20.\n\n"
     "**Watch out:** compare only within a sector - tech firms typically trade at higher P/E than banks. A negative P/E (a loss) does not mean 'cheap'."),
    ("pe_f", "val", "P/E (očekivani)", "Forward P/E", "x", "down", (15, 30),
     "Cena podeljena očekivanom zaradom po akciji za narednih 12 meseci.",
     "Price divided by expected earnings per share for the next 12 months.",
     "**Šta meri:** isto što i P/E, ali na osnovu procene analitičara za buduću dobit, a ne ostvarene.\n\n"
     "**Formula:** cena akcije / očekivani EPS za narednih 12 meseci.\n\n"
     "**Kako čitati:** ako je očekivani P/E znatno niži od prošlog, analitičari očekuju rast dobiti. Ako je viši, očekuje se pad.\n\n"
     "**Pazi:** zasniva se na prognozama, koje su često preoptimistične, naročito pred recesiju.",
     "**What it measures:** the same as P/E, but using analysts' estimate of future profit rather than reported profit.\n\n"
     "**Formula:** share price / expected EPS for the next 12 months.\n\n"
     "**How to read it:** if forward P/E is well below trailing P/E, analysts expect earnings to grow. If higher, they expect a decline.\n\n"
     "**Watch out:** it relies on forecasts, which are often too optimistic, especially ahead of recessions."),
    ("peg", "val", "PEG", "PEG ratio", "num", "down", (1.0, 2.5),
     "P/E podeljen očekivanom stopom rasta zarade.", "P/E divided by the expected earnings growth rate.",
     "**Šta meri:** da li je visok P/E opravdan brzim rastom. Povezuje cenu i rast u jedan broj.\n\n"
     "**Formula:** P/E / očekivani godišnji rast zarade u procentima (npr. P/E 30 i rast 30% daju PEG 1).\n\n"
     "**Kako čitati:** PEG oko 1 smatra se „fer“ cenom za taj rast, ispod 1 potencijalno povoljno, iznad 2 skupo u odnosu na rast.\n\n"
     "**Pazi:** veoma zavisi od procene rasta, koja može biti netačna. Za kompanije sa malim ili negativnim rastom nema smisla.",
     "**What it measures:** whether a high P/E is justified by fast growth. It combines price and growth into one number.\n\n"
     "**Formula:** P/E / expected annual earnings growth in percent (e.g. P/E 30 with 30% growth gives a PEG of 1).\n\n"
     "**How to read it:** a PEG around 1 is often seen as a 'fair' price for that growth, below 1 potentially cheap, above 2 expensive relative to growth.\n\n"
     "**Watch out:** it depends heavily on the growth estimate, which may be wrong. It is meaningless for firms with little or negative growth."),
    ("ps", "val", "P/S (cena / prihod)", "P/S (price to sales)", "x", "down", (3, 10),
     "Tržišna vrednost podeljena godišnjim prihodom.", "Market value divided by annual revenue.",
     "**Šta meri:** koliko investitori plaćaju za 1 dinar prihoda. Korisno za kompanije koje još nemaju dobit.\n\n"
     "**Formula:** tržišna kapitalizacija / prihod za poslednjih 12 meseci.\n\n"
     "**Kako čitati:** niži P/S je jeftiniji. Firme sa visokim maržama (softver) opravdano imaju viši P/S od firmi sa niskim maržama (trgovina).\n\n"
     "**Pazi:** prihod nije profit - kompanija može imati veliki prihod i gubitak.",
     "**What it measures:** how much investors pay for one dollar of revenue. Useful for companies that are not yet profitable.\n\n"
     "**Formula:** market capitalisation / revenue over the last 12 months.\n\n"
     "**How to read it:** lower is cheaper. High-margin firms (software) justifiably trade at a higher P/S than low-margin ones (retail).\n\n"
     "**Watch out:** revenue is not profit - a company can have large revenue and still lose money."),
    ("pb", "val", "P/B (cena / knjigovodstvena vrednost)", "P/B (price to book)", "x", "down", (2, 8),
     "Cena podeljena knjigovodstvenom vrednošću kapitala po akciji.", "Price divided by book value of equity per share.",
     "**Šta meri:** odnos tržišne cene i neto imovine iz bilansa (imovina minus obaveze).\n\n"
     "**Formula:** cena akcije / knjigovodstvena vrednost kapitala po akciji.\n\n"
     "**Kako čitati:** P/B ispod 1 znači da se akcija prodaje ispod vrednosti neto imovine - čest signal kod „value“ investiranja. "
     "Najkorisniji je za banke i osiguravajuće kuće.\n\n"
     "**Pazi:** kod tehnoloških firmi najveća vrednost (softver, brend, patenti) često nije u bilansu, pa je P/B prirodno visok.",
     "**What it measures:** market price relative to net assets on the balance sheet (assets minus liabilities).\n\n"
     "**Formula:** share price / book value of equity per share.\n\n"
     "**How to read it:** a P/B below 1 means the stock trades below its net asset value - a classic value-investing signal. It is most useful for banks and insurers.\n\n"
     "**Watch out:** for tech firms most value (software, brand, patents) is not on the balance sheet, so P/B is naturally high."),
    ("ev_ebitda", "val", "EV/EBITDA", "EV/EBITDA", "x", "down", (10, 22),
     "Vrednost cele firme (sa dugom) podeljena operativnom zaradom pre amortizacije.",
     "Whole-firm value (including debt) divided by operating earnings before depreciation.",
     "**Šta meri:** cenu cele kompanije - i akcija i duga - u odnosu na njenu operativnu zaradu. Omiljen pokazatelj kod preuzimanja firmi.\n\n"
     "**Formula:** (tržišna vrednost + dug - gotovina) / EBITDA (zarada pre kamata, poreza i amortizacije).\n\n"
     "**Kako čitati:** niži broj znači jeftiniju firmu. Bolji je od P/E za poređenje firmi sa različitim zaduženjem i poreskim tretmanom.\n\n"
     "**Pazi:** EBITDA ignoriše investicije u opremu, pa kod kapitalno intenzivnih firmi (telekomi, industrija) može ulepšati sliku.",
     "**What it measures:** the price of the whole company - both equity and debt - relative to its operating earnings. A favourite in takeovers.\n\n"
     "**Formula:** (market value + debt - cash) / EBITDA (earnings before interest, taxes, depreciation and amortisation).\n\n"
     "**How to read it:** lower means cheaper. Better than P/E for comparing firms with different debt levels and tax treatment.\n\n"
     "**Watch out:** EBITDA ignores capital spending, so it can flatter capital-intensive firms (telecoms, industrials)."),
    ("fcf_yield", "val", "Prinos slobodnog novčanog toka", "Free cash flow yield", "pct", "up", (0.05, 0.02),
     "Slobodan novčani tok kao procenat tržišne vrednosti.", "Free cash flow as a percentage of market value.",
     "**Šta meri:** koliko stvarnog novca (posle investicija) kompanija generiše u odnosu na to koliko košta. Teže ga je „ulepšati“ računovodstvom nego dobit.\n\n"
     "**Formula:** slobodni novčani tok (operativni novčani tok - kapitalne investicije) / tržišna kapitalizacija.\n\n"
     "**Kako čitati:** iznad 5% je atraktivno, 2-5% umereno, ispod 2% znači da plaćaš visoku cenu za novac koji firma pravi.\n\n"
     "**Pazi:** jedna godina velikih investicija može privremeno da ga smanji, iako je to dobro za budući rast.",
     "**What it measures:** how much real cash (after investment) the company generates relative to what it costs. Harder to 'dress up' with accounting than profit.\n\n"
     "**Formula:** free cash flow (operating cash flow - capital expenditure) / market capitalisation.\n\n"
     "**How to read it:** above 5% is attractive, 2-5% moderate, below 2% means you pay a high price for the cash the firm produces.\n\n"
     "**Watch out:** a year of heavy investment can temporarily depress it, even though that is good for future growth."),
    ("gross", "prof", "Bruto marža", "Gross margin", "pct", "up", (0.50, 0.25),
     "Procenat prihoda koji ostaje posle direktnih troškova proizvodnje.", "Share of revenue left after direct production costs.",
     "**Šta meri:** koliko kompanija zarađuje na samom proizvodu, pre troškova poslovanja (plate, marketing, razvoj).\n\n"
     "**Formula:** (prihod - trošak prodate robe) / prihod.\n\n"
     "**Kako čitati:** visoka bruto marža (softver 70-90%) znači snažnu poziciju i moć određivanja cena. Niska (trgovina 20-30%) znači oštru konkurenciju.\n\n"
     "**Pazi:** poredi u okviru industrije. Prati trend - pad marže je često rani znak problema.",
     "**What it measures:** how much the company earns on the product itself, before operating expenses (salaries, marketing, R&D).\n\n"
     "**Formula:** (revenue - cost of goods sold) / revenue.\n\n"
     "**How to read it:** a high gross margin (software 70-90%) signals a strong position and pricing power. A low one (retail 20-30%) signals fierce competition.\n\n"
     "**Watch out:** compare within an industry and watch the trend - a falling margin is often an early warning."),
    ("op", "prof", "Operativna marža", "Operating margin", "pct", "up", (0.20, 0.08),
     "Procenat prihoda koji ostaje posle svih troškova poslovanja.", "Share of revenue left after all operating costs.",
     "**Šta meri:** profitabilnost osnovnog poslovanja, pre kamata i poreza.\n\n**Formula:** operativna dobit (EBIT) / prihod.\n\n"
     "**Kako čitati:** iznad 20% je odlično, 8-20% solidno, ispod 8% tanko. Pokazuje koliko je poslovanje efikasno vođeno.\n\n"
     "**Pazi:** jednokratni troškovi (restrukturiranje) mogu privremeno da je spuste.",
     "**What it measures:** profitability of the core business, before interest and taxes.\n\n**Formula:** operating profit (EBIT) / revenue.\n\n"
     "**How to read it:** above 20% is excellent, 8-20% solid, below 8% thin. It shows how efficiently the business is run.\n\n"
     "**Watch out:** one-off costs (restructuring) can temporarily lower it."),
    ("net", "prof", "Neto marža", "Net profit margin", "pct", "up", (0.15, 0.05),
     "Procenat prihoda koji postaje čista dobit.", "Share of revenue that becomes net profit.",
     "**Šta meri:** koliko od svakog dinara prihoda ostane akcionarima posle svih troškova, kamata i poreza.\n\n"
     "**Formula:** neto dobit / prihod.\n\n**Kako čitati:** iznad 15% je visoko, 5-15% uobičajeno, ispod 5% nisko. Negativna znači gubitak.\n\n"
     "**Pazi:** može je iskriviti jednokratni prihod ili trošak (prodaja imovine, sudski spor).",
     "**What it measures:** how much of each dollar of revenue is left for shareholders after all costs, interest and taxes.\n\n"
     "**Formula:** net profit / revenue.\n\n**How to read it:** above 15% is high, 5-15% typical, below 5% low. Negative means a loss.\n\n"
     "**Watch out:** one-off gains or charges (asset sales, lawsuits) can distort it."),
    ("roe", "prof", "ROE - prinos na kapital", "ROE - return on equity", "pct", "up", (0.15, 0.08),
     "Dobit u odnosu na kapital akcionara.", "Profit relative to shareholders' equity.",
     "**Šta meri:** koliko dobiti kompanija napravi na novac koji su uložili akcionari. Jedan od omiljenih pokazatelja Vorena Bafeta.\n\n"
     "**Formula:** neto dobit / kapital akcionara.\n\n**Kako čitati:** iznad 15% je odlično, 8-15% prosečno, ispod 8% slabo. "
     "Stabilan visok ROE kroz više godina ukazuje na trajnu konkurentsku prednost.\n\n"
     "**Pazi:** veliki dug ili otkup sopstvenih akcija smanjuju kapital i veštački podižu ROE - zato ga gledaj zajedno sa zaduženošću.",
     "**What it measures:** how much profit the company makes on the money shareholders invested. One of Warren Buffett's favourite measures.\n\n"
     "**Formula:** net profit / shareholders' equity.\n\n**How to read it:** above 15% is excellent, 8-15% average, below 8% weak. "
     "A consistently high ROE over years points to a durable competitive advantage.\n\n"
     "**Watch out:** heavy debt or share buybacks shrink equity and inflate ROE artificially - read it together with leverage."),
    ("roa", "prof", "ROA - prinos na imovinu", "ROA - return on assets", "pct", "up", (0.08, 0.03),
     "Dobit u odnosu na ukupnu imovinu.", "Profit relative to total assets.",
     "**Šta meri:** koliko efikasno kompanija koristi svu svoju imovinu (fabrike, zalihe, gotovinu) da napravi dobit, nezavisno od toga kako je finansirana.\n\n"
     "**Formula:** neto dobit / ukupna imovina.\n\n**Kako čitati:** iznad 8% je odlično, 3-8% solidno. Kod banaka je normalan ROA oko 1%.\n\n"
     "**Pazi:** prirodno je niži u kapitalno intenzivnim granama.",
     "**What it measures:** how efficiently the company uses all its assets (plants, inventory, cash) to make profit, regardless of how it is financed.\n\n"
     "**Formula:** net profit / total assets.\n\n**How to read it:** above 8% is excellent, 3-8% solid. For banks about 1% is normal.\n\n"
     "**Watch out:** it is naturally lower in capital-intensive industries."),
    ("rev_g", "growth", "Rast prihoda (godišnji)", "Revenue growth (year over year)", "pct", "up", (0.10, 0.0),
     "Promena prihoda u odnosu na isti period prošle godine.", "Change in revenue versus the same period last year.",
     "**Šta meri:** da li kompanija prodaje sve više. Rast prihoda je osnova dugoročnog rasta dobiti.\n\n"
     "**Formula:** (prihod u poslednjem kvartalu / prihod u istom kvartalu prošle godine) - 1.\n\n"
     "**Kako čitati:** iznad 10% je snažan rast, 0-10% umeren, negativan znači pad poslovanja.\n\n"
     "**Pazi:** preuzimanja drugih firmi mogu veštački da ga podignu. Kod zrelih firmi i 3-5% je dobro.",
     "**What it measures:** whether the company is selling more and more. Revenue growth is the basis of long-term profit growth.\n\n"
     "**Formula:** (revenue in the latest quarter / revenue in the same quarter last year) - 1.\n\n"
     "**How to read it:** above 10% is strong, 0-10% moderate, negative means the business is shrinking.\n\n"
     "**Watch out:** acquisitions can inflate it. For mature firms 3-5% is fine."),
    ("eps_g", "growth", "Rast zarade (godišnji)", "Earnings growth (year over year)", "pct", "up", (0.10, 0.0),
     "Promena dobiti u odnosu na isti period prošle godine.", "Change in earnings versus the same period last year.",
     "**Šta meri:** da li dobit raste. Na dugi rok cena akcije prati rast zarade.\n\n"
     "**Formula:** (zarada po akciji u poslednjem kvartalu / u istom kvartalu prošle godine) - 1.\n\n"
     "**Kako čitati:** brži rast dobiti od prihoda znači da se marže šire - odličan znak.\n\n"
     "**Pazi:** ume da bude vrlo nestabilan zbog jednokratnih stavki. Gledaj ga uz rast prihoda.",
     "**What it measures:** whether profit is growing. Over the long run, share prices follow earnings growth.\n\n"
     "**Formula:** (EPS in the latest quarter / EPS in the same quarter last year) - 1.\n\n"
     "**How to read it:** profit growing faster than revenue means margins are expanding - a very good sign.\n\n"
     "**Watch out:** it can be very volatile because of one-off items. Read it alongside revenue growth."),
    ("de", "health", "Dug / kapital", "Debt to equity", "x", "down", (0.5, 2.0),
     "Ukupan dug podeljen kapitalom akcionara.", "Total debt divided by shareholders' equity.",
     "**Šta meri:** koliko se kompanija finansira dugom u odnosu na sopstveni kapital - mera finansijskog rizika.\n\n"
     "**Formula:** ukupan dug / kapital akcionara (1,0 znači da je duga koliko i kapitala).\n\n"
     "**Kako čitati:** ispod 0,5 je konzervativno, 0,5-2 umereno, iznad 2 visoko zaduženje. Veći dug pojačava i dobitke i gubitke, "
     "a u periodima visokih kamatnih stopa postaje skuplji.\n\n"
     "**Pazi:** banke i komunalna preduzeća normalno imaju visok odnos. Kod firmi koje otkupljuju akcije kapital može biti mali ili negativan.",
     "**What it measures:** how much the company relies on debt versus its own equity - a measure of financial risk.\n\n"
     "**Formula:** total debt / shareholders' equity (1.0 means as much debt as equity).\n\n"
     "**How to read it:** below 0.5 is conservative, 0.5-2 moderate, above 2 highly leveraged. More debt amplifies both gains and losses and gets more expensive when interest rates are high.\n\n"
     "**Watch out:** banks and utilities normally run high ratios. Firms that buy back shares can have small or even negative equity."),
    ("current", "health", "Tekući racio", "Current ratio", "num", "up", (1.5, 1.0),
     "Kratkoročna imovina podeljena kratkoročnim obavezama.", "Current assets divided by current liabilities.",
     "**Šta meri:** da li kompanija može da plati obaveze koje dospevaju u narednih 12 meseci.\n\n"
     "**Formula:** obrtna imovina (gotovina, potraživanja, zalihe) / kratkoročne obaveze.\n\n"
     "**Kako čitati:** iznad 1,5 je komforno, 1-1,5 prihvatljivo, ispod 1 znači da kratkoročne obaveze premašuju kratkoročnu imovinu.\n\n"
     "**Pazi:** velike firme sa stabilnim novčanim tokom (Apple, Walmart) često rade ispod 1 bez problema.",
     "**What it measures:** whether the company can pay obligations due in the next 12 months.\n\n"
     "**Formula:** current assets (cash, receivables, inventory) / current liabilities.\n\n"
     "**How to read it:** above 1.5 is comfortable, 1-1.5 acceptable, below 1 means short-term liabilities exceed short-term assets.\n\n"
     "**Watch out:** large firms with steady cash flow (Apple, Walmart) often run below 1 without trouble."),
    ("quick", "health", "Brzi racio", "Quick ratio", "num", "up", (1.0, 0.6),
     "Kao tekući racio, ali bez zaliha.", "Like the current ratio, but excluding inventory.",
     "**Šta meri:** strožu likvidnost - može li firma da plati kratkoročne obaveze bez prodaje zaliha.\n\n"
     "**Formula:** (obrtna imovina - zalihe) / kratkoročne obaveze.\n\n**Kako čitati:** iznad 1 je dobro, ispod 0,6 može biti rizično.\n\n"
     "**Pazi:** kod trgovaca je prirodno nizak jer im je veliki deo imovine u zalihama.",
     "**What it measures:** stricter liquidity - can the firm pay short-term obligations without selling inventory.\n\n"
     "**Formula:** (current assets - inventory) / current liabilities.\n\n**How to read it:** above 1 is good, below 0.6 can be risky.\n\n"
     "**Watch out:** it is naturally low for retailers, whose assets are largely inventory."),
    ("net_cash", "health", "Neto gotovina", "Net cash", "money", "up", (0, None),
     "Gotovina minus ukupan dug.", "Cash minus total debt.",
     "**Šta meri:** da li bi kompanija mogla da otplati sav dug iz gotovine koju ima.\n\n**Formula:** gotovina i kratkoročne investicije - ukupan dug.\n\n"
     "**Kako čitati:** pozitivna vrednost (neto gotovina) znači finansijsku snagu i fleksibilnost u krizi. Negativna (neto dug) je normalna, ali treba da bude u razmeri sa zaradom.\n\n"
     "**Pazi:** poredi je sa veličinom firme - 10 milijardi duga nije isto za Apple i za malu firmu.",
     "**What it measures:** whether the company could pay off all its debt from the cash it holds.\n\n**Formula:** cash and short-term investments - total debt.\n\n"
     "**How to read it:** a positive value (net cash) means financial strength and flexibility in a crisis. A negative value (net debt) is normal but should be in proportion to earnings.\n\n"
     "**Watch out:** compare it with the firm's size - 10 billion of debt means something different for Apple than for a small firm."),
    ("div_y", "div", "Dividendni prinos", "Dividend yield", "pct", None, None,
     "Godišnja dividenda kao procenat cene akcije.", "Annual dividend as a percentage of the share price.",
     "**Šta meri:** koliko gotovine godišnje dobijaš kao dividendu za svaki uloženi dinar, bez prodaje akcija.\n\n"
     "**Formula:** godišnja dividenda po akciji / cena akcije.\n\n"
     "**Kako čitati:** 2-4% je uobičajeno za stabilne firme. Mnoge tehnološke firme ne isplaćuju dividendu jer zaradu ulažu u rast - to nije loše.\n\n"
     "**Pazi:** neobično visok prinos (iznad 7-8%) često znači da je cena pala zbog problema i da je dividenda ugrožena.",
     "**What it measures:** how much cash you receive each year as a dividend per dollar invested, without selling shares.\n\n"
     "**Formula:** annual dividend per share / share price.\n\n"
     "**How to read it:** 2-4% is typical for stable firms. Many tech firms pay no dividend because they reinvest in growth - that is not bad.\n\n"
     "**Watch out:** an unusually high yield (above 7-8%) often means the price has fallen on trouble and the dividend is at risk."),
    ("payout", "div", "Racio isplate", "Payout ratio", "pct", "down", (0.6, 0.9),
     "Deo dobiti koji se isplaćuje kao dividenda.", "Share of profit paid out as dividends.",
     "**Šta meri:** koliko je dividenda „pokrivena“ dobiti.\n\n**Formula:** isplaćene dividende / neto dobit.\n\n"
     "**Kako čitati:** ispod 60% je održivo i ostavlja prostor za rast dividende, 60-90% je napeto, iznad 100% znači da firma isplaćuje više nego što zarađuje.\n\n"
     "**Pazi:** kod nekretninskih fondova (REIT) visoka isplata je pravilo, pa se meri drugačije.",
     "**What it measures:** how well the dividend is 'covered' by profit.\n\n**Formula:** dividends paid / net profit.\n\n"
     "**How to read it:** below 60% is sustainable and leaves room to raise the dividend, 60-90% is stretched, above 100% means the firm pays out more than it earns.\n\n"
     "**Watch out:** real-estate trusts (REITs) are required to pay out most profit, so they are measured differently."),
    ("beta", "risk", "Beta", "Beta", "num", None, None,
     "Koliko se akcija pomera u odnosu na celo tržište.", "How much the stock moves relative to the overall market.",
     "**Šta meri:** osetljivost akcije na kretanje tržišta (S&P 500). Ključni parametar u CAPM modelu.\n\n"
     "**Formula:** kovarijansa prinosa akcije i tržišta / varijansa prinosa tržišta (obično na 5 godina mesečnih podataka).\n\n"
     "**Kako čitati:** beta 1 znači da se akcija kreće kao tržište, beta 1,5 da u proseku raste ili pada 50% više, a 0,6 da je mirnija od tržišta. "
     "Konzervativni investitori biraju nižu betu.\n\n**Pazi:** meri samo vezu sa tržištem, ne i rizik specifičan za firmu.",
     "**What it measures:** the stock's sensitivity to market moves (S&P 500). A key parameter in the CAPM model.\n\n"
     "**Formula:** covariance of stock and market returns / variance of market returns (usually 5 years of monthly data).\n\n"
     "**How to read it:** a beta of 1 means the stock moves with the market, 1.5 means it rises/falls about 50% more, and 0.6 means it is calmer. "
     "Conservative investors prefer lower beta.\n\n**Watch out:** it captures only the link to the market, not company-specific risk."),
    ("vol", "risk", "Volatilnost (godišnja)", "Volatility (annualised)", "pct", "down", (0.20, 0.40),
     "Koliko se cena njiše - standardna devijacija prinosa za poslednja 3 meseca.",
     "How much the price swings - standard deviation of returns over the last 3 months.",
     "**Šta meri:** prosečan raspon kretanja cene. Volatilnost 25% znači da se u tipičnoj godini cena kreće oko ±25% od očekivane.\n\n"
     "**Formula:** standardna devijacija dnevnih prinosa × √252 (broj trgovačkih dana).\n\n"
     "**Kako čitati:** ispod 20% je mirna akcija (kao indeks), 20-40% umerena, iznad 40% vrlo nestabilna. Viša volatilnost znači veći rizik i potrebu za dužim horizontom.\n\n"
     "**Pazi:** računa se iz skorašnjih podataka, pa u mirnim periodima potcenjuje rizik od krize.",
     "**What it measures:** the typical range of price moves. 25% volatility means that in a typical year the price moves around ±25% from its expected path.\n\n"
     "**Formula:** standard deviation of daily returns × √252 (trading days).\n\n"
     "**How to read it:** below 20% is calm (index-like), 20-40% moderate, above 40% very unstable. Higher volatility means more risk and the need for a longer horizon.\n\n"
     "**Watch out:** it uses recent data, so in calm periods it understates crisis risk."),
    ("mdd", "risk", "Najveći pad (1 godina)", "Max drawdown (1 year)", "pct", "up", (-0.15, -0.35),
     "Najveći pad cene od prethodnog vrha u poslednjih godinu dana.", "Largest fall from a previous peak over the past year.",
     "**Šta meri:** najgori gubitak koji bi doživeo investitor koji je kupio na vrhu u poslednjoj godini. Psihološki najvažnija mera rizika.\n\n"
     "**Formula:** najmanja vrednost (cena / prethodni maksimum - 1) u periodu.\n\n"
     "**Kako čitati:** -10% do -15% je blago, -15% do -35% značajno, preko -35% veliki pad. Pitaj se: da li bih izdržao(la) takav pad bez prodaje?\n\n"
     "**Pazi:** prošli pad ne predviđa budući. U krizama padovi budu i dublji.",
     "**What it measures:** the worst loss an investor who bought at the top in the past year would have suffered. The most psychologically important risk measure.\n\n"
     "**Formula:** minimum of (price / previous peak - 1) over the period.\n\n"
     "**How to read it:** -10% to -15% is mild, -15% to -35% significant, beyond -35% a large fall. Ask yourself: could I sit through such a fall without selling?\n\n"
     "**Watch out:** past drawdowns do not predict future ones. In crises they get deeper."),
    ("mom", "risk", "Momentum (12-1 mesec)", "Momentum (12-1 month)", "pct", "up", (0.15, 0.0),
     "Promena cene za 12 meseci, bez poslednjeg meseca.", "Price change over 12 months, excluding the last month.",
     "**Šta meri:** dugoročni trend cene. Jedna od najpostojanijih anomalija u finansijama (Jegadeesh i Titman, 1993): akcije koje su rasle 3-12 meseci često nastavljaju da rastu.\n\n"
     "**Formula:** cena pre 1 mesec / cena pre 12 meseci - 1 (poslednji mesec se izostavlja jer se kratkoročno cene često vraćaju).\n\n"
     "**Kako čitati:** pozitivan i visok momentum je signal snage. Negativan znači da tržište gubi poverenje.\n\n"
     "**Pazi:** momentum se naglo okreće u preokretima tržišta.",
     "**What it measures:** the long-term price trend. One of the most persistent anomalies in finance (Jegadeesh and Titman, 1993): stocks that rose over 3-12 months often keep rising.\n\n"
     "**Formula:** price 1 month ago / price 12 months ago - 1 (the last month is skipped because short-term moves tend to reverse).\n\n"
     "**How to read it:** strong positive momentum signals strength. Negative means the market is losing confidence.\n\n"
     "**Watch out:** momentum reverses sharply at market turning points."),
    ("pos52", "risk", "Položaj u 52-nedeljnom rasponu", "Position in 52-week range", "pct", None, None,
     "Gde je današnja cena između najniže i najviše cene u poslednjih godinu dana.", "Where today's price sits between the past year's low and high.",
     "**Šta meri:** 0% znači da je cena na godišnjem minimumu, 100% na godišnjem maksimumu.\n\n"
     "**Formula:** (cena - 52-nedeljni minimum) / (52-nedeljni maksimum - minimum).\n\n"
     "**Kako čitati:** blizu 100% - akcija je u snažnom trendu ali je možda „skupa“. Blizu 0% - akcija je pod pritiskom, što može biti prilika ili upozorenje.\n\n"
     "**Pazi:** sam po sebi nije signal za kupovinu ili prodaju.",
     "**What it measures:** 0% means the price is at its one-year low, 100% at its one-year high.\n\n"
     "**Formula:** (price - 52-week low) / (52-week high - low).\n\n"
     "**How to read it:** near 100% - the stock is in a strong trend but may be 'expensive'. Near 0% - it is under pressure, which may be an opportunity or a warning.\n\n"
     "**Watch out:** on its own it is not a buy or sell signal."),
    ("mcap", "risk", "Tržišna kapitalizacija", "Market capitalisation", "money", None, None,
     "Ukupna tržišna vrednost svih akcija kompanije.", "Total market value of all the company's shares.",
     "**Šta meri:** veličinu kompanije na berzi.\n\n**Formula:** cena akcije × broj akcija.\n\n"
     "**Kako čitati:** preko 200 mlrd. $ - mega firme, 10-200 mlrd. - velike, 2-10 mlrd. - srednje, ispod 2 mlrd. - male. Manje firme imaju veći potencijal rasta, ali i veći rizik.\n\n"
     "**Pazi:** veličina nije kvalitet - i velike firme mogu da propadnu.",
     "**What it measures:** the company's size on the stock market.\n\n**Formula:** share price × number of shares.\n\n"
     "**How to read it:** above $200bn - mega caps, $10-200bn - large, $2-10bn - mid, below $2bn - small. Smaller firms have more growth potential but also more risk.\n\n"
     "**Watch out:** size is not quality - large firms can fail too."),
    ("upside", "analyst", "Potencijal do cilja analitičara", "Upside to analyst target", "pct", "up", (0.10, 0.0),
     "Razlika između prosečne ciljne cene analitičara i trenutne cene.", "Gap between the average analyst price target and today's price.",
     "**Šta meri:** koliko bi akcija trebalo da poraste (ili padne) za oko 12 meseci prema proseku procena analitičara.\n\n"
     "**Formula:** prosečna ciljna cena / trenutna cena - 1.\n\n"
     "**Kako čitati:** iznad 10% analitičari vide prostor za rast. Negativna vrednost znači da je cena već iznad njihovih procena.\n\n"
     "**Pazi:** analitičari su sistematski optimistični i sporo menjaju ciljeve. Koristi kao jedan od signala, ne kao prognozu.",
     "**What it measures:** how much the stock should rise (or fall) over about 12 months according to the average analyst estimate.\n\n"
     "**Formula:** average target price / current price - 1.\n\n"
     "**How to read it:** above 10% analysts see room to rise. A negative value means the price is already above their estimates.\n\n"
     "**Watch out:** analysts are systematically optimistic and slow to change targets. Use it as one signal, not a forecast."),
    ("rec", "analyst", "Preporuka analitičara", "Analyst recommendation", "num", "down", (2.0, 3.0),
     "Prosečna ocena na skali 1 (jaka kupovina) do 5 (prodaja).", "Average rating on a scale of 1 (strong buy) to 5 (sell).",
     "**Šta meri:** prosečnu preporuku svih analitičara koji prate akciju.\n\n"
     "**Skala:** 1 = jaka kupovina, 2 = kupovina, 3 = držanje, 4 = smanjenje, 5 = prodaja.\n\n"
     "**Kako čitati:** ispod 2 je konsenzus „kupuj“, 2-3 između kupovine i držanja, iznad 3 skeptičan stav. Gledaj i broj analitičara - ocena 10+ analitičara je pouzdanija.\n\n"
     "**Pazi:** preporuke „prodaj“ su retke jer banke često imaju poslovne odnose sa kompanijama.",
     "**What it measures:** the average recommendation of all analysts covering the stock.\n\n"
     "**Scale:** 1 = strong buy, 2 = buy, 3 = hold, 4 = underperform, 5 = sell.\n\n"
     "**How to read it:** below 2 is a 'buy' consensus, 2-3 between buy and hold, above 3 sceptical. Check the number of analysts too - a rating from 10+ analysts is more reliable.\n\n"
     "**Watch out:** 'sell' ratings are rare because banks often have business ties with the companies."),
]
BY_KEY = {d[0]: d for d in DEFS}


def _f(info, *keys):
    for k in keys:
        v = info.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def values(info, m):
    """info: rečnik iz Yahoo Finance, m: izračunati pokazatelji iz cena (stocks.metrics)."""
    price = m.get("price")
    mcap = _f(info, "marketCap")
    fcf = _f(info, "freeCashflow")
    de = _f(info, "debtToEquity")
    dy = _f(info, "trailingAnnualDividendYield")
    if dy is None:
        dy = _f(info, "dividendYield")
        if dy is not None and dy > 0.2:  # novije verzije daju procenat (0.45 = 0,45%)
            dy = dy / 100
    lo, hi = _f(info, "fiftyTwoWeekLow"), _f(info, "fiftyTwoWeekHigh")
    cash, debt = _f(info, "totalCash"), _f(info, "totalDebt")
    tgt = _f(info, "targetMeanPrice")
    return {
        "pe_t": _f(info, "trailingPE"), "pe_f": _f(info, "forwardPE"), "peg": _f(info, "trailingPegRatio", "pegRatio"),
        "ps": _f(info, "priceToSalesTrailing12Months"), "pb": _f(info, "priceToBook"), "ev_ebitda": _f(info, "enterpriseToEbitda"),
        "fcf_yield": fcf / mcap if fcf is not None and mcap else None,
        "gross": _f(info, "grossMargins"), "op": _f(info, "operatingMargins"), "net": _f(info, "profitMargins"),
        "roe": _f(info, "returnOnEquity"), "roa": _f(info, "returnOnAssets"),
        "rev_g": _f(info, "revenueGrowth"), "eps_g": _f(info, "earningsQuarterlyGrowth", "earningsGrowth"),
        "de": de / 100 if de is not None else None, "current": _f(info, "currentRatio"), "quick": _f(info, "quickRatio"),
        "net_cash": cash - debt if cash is not None and debt is not None else None,
        "div_y": dy, "payout": _f(info, "payoutRatio"),
        "beta": _f(info, "beta"), "vol": m.get("vol"), "mdd": m.get("mdd"), "mom": m.get("mom"),
        "pos52": (price - lo) / (hi - lo) if price and lo is not None and hi and hi > lo else None, "mcap": mcap,
        "upside": tgt / price - 1 if tgt and price else m.get("upside"), "rec": _f(info, "recommendationMean"),
    }


def grade(key, v):
    """'good' | 'mid' | 'bad' | None."""
    d = BY_KEY[key]
    if v is None or d[5] is None or d[6] is None:
        return None
    good, bad = d[6]
    if key in ("pe_t", "pe_f", "peg", "ps", "pb", "ev_ebitda") and v <= 0:
        return "bad"
    if bad is None:
        return "good" if v >= good else "bad"
    if d[5] == "up":
        return "good" if v >= good else "bad" if v <= bad else "mid"
    return "good" if v <= good else "bad" if v >= bad else "mid"


def fmt(key, v, ui="sr"):
    if v is None:
        return "-"
    kind = BY_KEY[key][4]
    dec = (lambda x: x.replace(".", ",")) if ui == "sr" else (lambda x: x)
    if kind == "pct":
        return dec(f"{v * 100:.1f}") + "%"
    if kind == "x":
        return dec(f"{v:.1f}") + "x"
    if kind == "money":
        for d, u_sr, u_en in ((1e12, " bil.", "T"), (1e9, " mlrd.", "B"), (1e6, " mil.", "M")):
            if abs(v) >= d:
                return dec(f"{v / d:.1f}") + (u_sr if ui == "sr" else u_en)
        return f"{v:,.0f}"
    return dec(f"{v:.2f}")
