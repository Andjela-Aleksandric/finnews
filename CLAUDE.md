# FinNews - stalna pravila

Ova pravila važe za svaku izmenu aplikacije, za sve tekstove na sajtu i za svaki prevod.
Primenjuju se automatski u kodu (`translate_fix.py`, `site_build._polish_all`) i ne smeju se uklanjati.

## Jezik i stil (srpski)
- Latinica, nikad ćirilica na sajtu.
- Nigde tačka-zarez (;). Rečenica se završava tačkom.
- Kratka crta "-", nikad em-crtica.
- Profesionalna zvanja u muškom rodu (analitičar, direktor, trener), i za žene.
- Engleski idiomi se prevode po smislu, nikad doslovno: "hot inflation" -> visoka inflacija, "tailwind" -> podrška,
  "overheated" -> prebrz rast ili prekupljen, "soft landing" -> usporavanje bez recesije, "rally" -> snažan rast.
  Nova pravila se dodaju u `_EN` (pre prevoda, engleski žargon u običan engleski) i `_SR` (posle prevoda, ispravke srpskog).

## Vlastite imenice
- Imena ljudi, kompanija, proizvoda, medija i časopisa ostaju u izvornom obliku (Musk, SpaceX, Jensen Huang, The Guardian).
- U srpskom se menjaju po padežima, ali pravopis ostaje izvorni: Powella, sa Teslom, SpaceX-a, Apple-a, Nvidije.
- Prevodi se samo vlastita imenica koja ima veran srpski oblik: države, gradovi, narodi (Njujork, Prag, Česi, Banka Engleske).
- Sve ostalo se prevodi verno i prirodno, tako da rečenica ima smisla na srpskom.

## Prevod u praksi
- Svaka vest iz arhive (6 meseci) mora imati srpski prevod. Najnovije idu prve.
- Prevod koji je ostao na engleskom se ne čuva i ponavlja se u sledećem osvežavanju.
- Kad se promene pravila, povećaj `TR_VERSION` u `translate_fix.py` - cela poslednja nedelja se tada prevodi ponovo.
- Svaki JSON za sajt prolazi kroz `_polish_all` pre objave.

## Ostalo
- Nema plaćenih API-ja. Prevod je besplatan Google, AI je lokalni Ollama model u GitHub Actions.
- `personal_seed.json` (portfolio) se nikad ne objavljuje. Tokeni i ključevi se ne dele.
- Gde je relevantno, napomena da aplikacija nije finansijski savet.
