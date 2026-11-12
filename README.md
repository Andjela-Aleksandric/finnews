# FinNews - lični terminal za finansijske vesti

Prati ~25 izvora (Reuters, Bloomberg, FT, WSJ, Economist, CNBC, Fed, ECB, BIS, arXiv q-fin, NBER...), rangira vesti po važnosti, prevodi na srpski/engleski, pravi dnevni brief i čuva celu arhivu.

## Instalacija (jednom)
1. Raspakuj folder gde želiš da stoji (npr. `~/FinNews`) - nemoj ga posle pomerati.
2. Terminal: `cd ~/FinNews && bash install.sh`
3. Otvori **FinNews** iz Spotlight-a (Cmd+Space) ili `~/Applications`. Otvara se u pregledaču na `localhost:8765`.
   - Za izgled prave aplikacije: u Safariju `File → Add to Dock`.

Treba ti Python 3 (`python3 --version`; ako ga nema: `brew install python`).

## Šta radi
- **Najvažnije** - vesti iz poslednjih 24h/3/7 dana sortirane po važnosti (težina izvora + ključne reči kao Fed, CPI, yields + koliko izvora piše o istoj temi).
- **Dnevni brief** - sažetak dana po temama, sa linkovima na izvore; svaki brief se čuva po datumu.
- **Pregled 6 meseci** - najvažnije vesti velikih medija za svaki mesec i nedelju unazad 6 meseci (učitava se automatski prvi put), plus AI pregled meseca i celih 6 meseci.
- **Istraživanja** - pet pogleda: najnovije (arXiv q-fin, NBER, BIS, rangirano po tvojim temama), novo u top časopisima (JF, JFE, RFS, JFQA, Quantitative Finance, ESWA, Applied Soft Computing...), najcitiranije u 6 meseci i 2 godine, i klasici (22 odabrana temeljna rada sa objašnjenjem + najcitiraniji radovi po temama). Podaci o radovima dolaze iz OpenAlex-a, osvežavaju se nedeljno.
- **Srpski / English** - prekidač u bočnom meniju menja i interfejs i prevod sadržaja; „Prikaži original“ gasi prevod.
- **Arhiva** - sve što je ikad preuzeto, pretraga po datumu i tekstu, izvoz u CSV.
- **Sačuvano** - vesti označene zvezdicom.
- **Podešavanja** - API ključ, latinica/ćirilica, teme istraživanja, dodavanje/isključivanje RSS izvora, status izvora.

Vesti se preuzimaju same na svaka 2 sata (i kad je app zatvoren) i pri otvaranju aplikacije.

## AI režim
Bez ključa: besplatan Google prevod + izdvajanje najbitnijih rečenica.
Sa Anthropic API ključem (console.anthropic.com → Podešavanja u app-u): Claude prevodi, pravi pravi dnevni brief i dugme „🧠 Objasni“ kod svake vesti. Trošak je mali (prevod Haiku, brief Sonnet).

Napomena: FT, WSJ i Bloomberg u RSS-u daju samo naslov i kratak opis - pun tekst je iza paywall-a, pa se sažeci prave iz toga.

## Podaci
`~/Library/Application Support/FinNews/` - baza (news.db), izvori (feeds.json), podešavanja.
Logovi: `~/Library/Logs/finnews*.log`. Uklanjanje: `bash uninstall.sh` (arhiva ostaje).

## Telefon i deljenje sa drugima (v17)

- `bash ~/finnews/share.sh` ispiše https link. Otvori ga na telefonu ili ga pošalji drugima. Link radi dok je Terminal otvoren i Mac uključen.
- Preko linka su Portfolio i Podešavanja zaključani PIN-om. PIN se postavlja u aplikaciji: ⚙ → Deljenje i telefon.
- Na telefonu: Share → Add to Home Screen, pa se otvara kao aplikacija.
- Trajni link (radi i kad je Mac ugašen): `Dockerfile` je spreman za Fly.io, Render, Railway ili sopstveni server.
- Napomena: celi tekstovi vesti pripadaju redakcijama. Za javno deljenje koristi aplikaciju kao demonstraciju, uz navođenje izvora (koji je uvek prikazan).

## Šta je novo u v17

- Samo vesti sa celim tekstom: ako original nije dostupan, ista vest se traži kod drugih besplatnih izvora; delimični tekstovi se ne prikazuju.
- Relevantnost = važnost x svežina; napredni filteri (period, sortiranje, teme, izvori, jezik, važnost, više izvora).
- Trenutni sažetak svake vesti i pregled perioda (danas, juče, 7 dana, 30 dana).
- Sve akcije se rangiraju ravnopravno (bez poreskih bodova).
- Portfolio: zlato kao ulaganje u indeks cene zlata, dinarski deo kao obveznice sa fiksnim prinosom.
- Stranica „O aplikaciji“ sa metodologijom.

## Šta je novo u v18

- Novi izgled: crna i burgundy, nova ikonica, animacije.
- Novi meni: Početna, Vesti, Pregled perioda, Akcije, Portfolio, Istraživanja, Arhiva, O aplikaciji, ⚙.
- Periodi 1, 7, 30, 60, 90 i 180 dana u Vestima, Pregledu perioda i Istraživanjima: sažetak vesti, trend tema i najvažniji naučni nalazi za isti period.
- Akcije → Prilike sada: akcije u padu sa potencijalom rasta, povezane sa vestima i temama koje se zahuktavaju.
- Portfolio: izmena, brisanje i dodavanje svih transakcija i imovine, dokupljivanje i prodaja dela pozicije.
- Telefon i kad je Mac ugašen: `bash ~/finnews/deploy_cloud.sh` (Streamlit Community Cloud, besplatno; portfolio se sinhronizuje preko privatnog GitHub repozitorijuma).
- Menu bar sa portfoliom: `bash ~/finnews/swiftbar.sh`.
- Pouzdaniji i brži prevod (ponovni pokušaji, više tekstova u jednom zahtevu, paralelno), keširanje i brža baza.

## Nova veb aplikacija (v20) - GitHub Pages

- `bash ~/finnews/deploy_web.sh` - objavi sajt na `https://<korisnik>.github.io/finnews/` (besplatno, radi i kad je Mac ugašen).
- GitHub Action (`.github/workflows/site.yml`) na svakih 30 minuta pokreće `site_build.py`: vesti, prevodi, akcije, prilike, radovi -> JSON za sajt.
- Sajt: `web/` (React + Vite + Tailwind + Framer Motion + TradingView Lightweight Charts), instalira se na telefon kao aplikacija.
- Portfolio i celi tekstovi su samo u privatnom repozitorijumu `finnews-data`; na sajtu ih vidi samo vlasnik posle povezivanja ključa (Podešavanja).
- `personal_seed.json` (početni portfolio) se nikad ne objavljuje.
- Lokalna Mac aplikacija (Streamlit, localhost:8765) i SwiftBar i dalje rade kao do sada i dele isti portfolio.

## v21
- Lista praćenja proširena na ~160 akcija (teme: AI, čipovi, memorija, fotonika, energija, nuklearna, odbrana, svemir, robotika, kvantni, materijali) - `universe.py`.
- Za svaku akciju: oznaka i cena na matičnoj berzi i na Xetri (`stocks.refresh_listings`, Yahoo pretraga, keširano), ISIN, kratak opis kompanije i industrija.
- 20 predloga po pravilima: kvalitet na popustu, trend (200-dnevni prosek), RSI ulaz 30-50, forward P/E i PEG u odnosu na rast, sektor sa vetrom u leđa, veličina pozicije po nivou rizika.
