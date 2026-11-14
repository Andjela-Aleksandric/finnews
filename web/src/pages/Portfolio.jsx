import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CloudDownload, CloudUpload, Coins, Pencil, Plus, RefreshCw, Trash2, Wallet } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
import { cls, eur, num, pct, upDown } from "../lib/fmt";
import { useData } from "../lib/data";
import { usePortfolio } from "../lib/usePortfolio";
import { loadCloudPortfolio, portfolioCloudConfigured, saveCloudPortfolio } from "../lib/portfolioCloud";
import { KIND, assetValues, goldEur, history, valuation } from "../lib/portfolio";
import { PageHead, useRoute } from "../components/Shell";
import { Card, CountUp, Donut, Empty, Segmented, SectionTitle, Select, Skeleton, Spark, toast } from "../components/ui";
import PriceChart from "../components/PriceChart";

const PORTFOLIO_SECURITIES = [
  { ticker: "1YD.DE", aliases: ["1YD.XETRA"], name: "Broadcom Inc.", isin: "US11135F1012" },
  { ticker: "ABEA.DE", aliases: ["ABEA.XETRA"], name: "Alphabet Inc. Class A", isin: "US02079K3059" },
  { ticker: "EUNK.DE", aliases: ["EUNK.XETRA"], name: "iShares Core MSCI Europe UCITS ETF EUR (Acc)", isin: "IE00B4K48X80" },
  { ticker: "EUNL.DE", aliases: ["EUNL.XETRA"], name: "iShares Core MSCI World UCITS ETF", isin: "IE00B4L5Y983" },
  { ticker: "IS3N.DE", aliases: ["IS3N.XETRA"], name: "iShares Core MSCI Emerging Markets ETF", isin: "IE00BKM4GZ66" },
  { ticker: "NVD.DE", aliases: ["NVD.XETRA"], name: "NVIDIA Corp.", isin: "US67066G1040" },
  { ticker: "SXR8.DE", aliases: ["SXR8.XETRA"], name: "iShares Core S&P 500 UCITS ETF", isin: "IE00B5BMR087" },
];

const COLORS = ["#C8285A", "#5FE39A", "#F6EDE4", "#FF4D63", "#D9AE5F", "#7A1A33", "#A99C93", "#2E9E5E"];

function Field({ label, children }) {
  return <label className="block"><span className="stat-label mb-1.5 block">{label}</span>{children}</label>;
}

function TxForm({ tx, onSave, onDelete, onClose, lang, stocks = [] }) {
  const [f, setF] = useState(() => ({ ticker: "", name: "", isin: "", side: "buy", status: "filled", qty: 1, price: "", fee: 0, d: new Date().toISOString().slice(0, 10), limit_price: "", ...tx }));
  const [stockQuery, setStockQuery] = useState(() => tx?.ticker ? `${tx.ticker} · ${tx.name || tx.ticker}` : "");
  const [pickerOpen, setPickerOpen] = useState(false);
  const up = (k) => (e) => setF((x) => ({ ...x, [k]: e.target.value }));
  const chooseStock = (stock) => {
    setF((x) => ({ ...x, ticker: stock?.ticker || "", name: stock?.name || "", isin: stock?.isin || "" }));
    setStockQuery(stock ? `${stock.ticker} · ${stock.name}` : "");
    setPickerOpen(false);
  };
  const query = stockQuery.trim().toLocaleLowerCase();
  const stockMatches = stocks.filter((stock) => !query || `${stock.ticker} ${stock.name} ${stock.isin || ""}`.toLocaleLowerCase().includes(query)).slice(0, 20);
  const L = (a, b) => (lang === "en" ? b : a);
  const supportedTicker = stocks.some((stock) => stock.ticker === f.ticker);
  const ok = supportedTicker && +f.qty > 0 && (f.status === "pending" ? +f.limit_price > 0 : +f.price > 0);
  return (
    <div className="space-y-4">
      <h3 className="font-display text-xl font-bold">{tx && tx._i !== undefined ? L("Izmena transakcije", "Edit transaction") : L("Nova transakcija", "New transaction")}</h3>
      <div className="grid grid-cols-2 gap-3">
        <Field label={L("Kupovina / prodaja", "Buy / sell")}>
          <Segmented size="sm" value={f.side} onChange={(v) => setF((x) => ({ ...x, side: v }))} options={[["buy", L("Kupovina", "Buy")], ["sell", L("Prodaja", "Sell")]]} />
        </Field>
        <Field label="Status">
          <Segmented size="sm" value={f.status} onChange={(v) => setF((x) => ({ ...x, status: v }))} options={[["filled", L("Izvršeno", "Filled")], ["pending", L("Nalog", "Order")]]} />
        </Field>
      </div>
      <Field label={L("Akcija ili ETF - pretraži po tickeru ili nazivu", "Stock or ETF - search by ticker or name")}>
        <div className="relative">
          <input className="field" role="combobox" aria-autocomplete="list" aria-expanded={pickerOpen} value={stockQuery}
            onFocus={() => setPickerOpen(true)}
            onChange={(e) => {
              const value = e.target.value;
              setStockQuery(value);
              setPickerOpen(true);
              setF((x) => ({ ...x, ticker: "", name: "", isin: "" }));
            }}
            placeholder={L("Počni da kucaš npr. Alphabet ili GOOGL…", "Type e.g. Alphabet or GOOGL…")} />
          {pickerOpen && <div role="listbox" className="absolute z-30 mt-1 max-h-60 w-full overflow-y-auto rounded-xl border border-ink-500 bg-ink-850 p-1 shadow-2xl">
            {stockMatches.length ? stockMatches.map((stock) => <button type="button" role="option" aria-selected={stock.ticker === f.ticker} key={stock.ticker}
              onClick={() => chooseStock(stock)} className="flex w-full items-start gap-3 rounded-lg px-3 py-2 text-left hover:bg-white/[0.03] focus:bg-wine-900/50">
              <span className="min-w-16 font-mono text-xs text-gold-300">{stock.ticker}</span>
              <span className="text-sm text-cream-100">{stock.name}</span>
            </button>) : <div className="px-3 py-3 text-sm text-cream-400">{L("Nema praćenog instrumenta za ovu pretragu.", "No tracked instrument matches this search.")}</div>}
          </div>}
        </div>
        {supportedTicker
          ? <span className="mt-1 block text-xs text-cream-500">{f.name} · {f.ticker} · {L("cena je dostupna u aplikaciji", "price data available")}</span>
          : <span className="mt-1 block text-xs text-gold-400">{L("Pretražuj po nazivu ili tickeru. Rezultati imaju istoriju cena u aplikaciji.", "Search by company name or ticker. Results have price history in the app.")}</span>}
      </Field>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Field label={L("Količina", "Quantity")}><input className="field" type="number" step="any" value={f.qty} onChange={up("qty")} /></Field>
        {f.status === "filled"
          ? <Field label={L("Cena (€)", "Price (€)")}><input className="field" type="number" step="any" value={f.price ?? ""} onChange={up("price")} /></Field>
          : <Field label={L("Limit (€)", "Limit (€)")}><input className="field" type="number" step="any" value={f.limit_price ?? ""} onChange={up("limit_price")} /></Field>}
      </div>
      <details className="rounded-xl border border-ink-600 bg-ink-850/60 px-3 py-2">
        <summary className="cursor-pointer text-xs font-medium text-cream-300">{L("Dodatni detalji - datum, provizija i ISIN", "More details - date, fee and ISIN")}</summary>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <Field label={L("Datum", "Date")}><input className="field" type="date" value={f.d || ""} onChange={up("d")} /></Field>
          <Field label={L("Provizija (€)", "Fee (€)")}><input className="field" type="number" step="any" value={f.fee ?? 0} onChange={up("fee")} /></Field>
          <Field label="ISIN"><input className="field" value={f.isin || ""} onChange={up("isin")} /></Field>
        </div>
      </details>
      <div className="flex flex-wrap gap-2 pt-2">
        <button disabled={!ok} onClick={() => onSave({ ...f, ticker: f.ticker.trim().toUpperCase(), name: f.name || f.ticker.trim().toUpperCase(), qty: +f.qty,
          price: f.status === "filled" ? +f.price : null, limit_price: f.status === "pending" ? +f.limit_price : null, fee: +f.fee || 0 })}
          className={cls("btn btn-primary", !ok && "pointer-events-none opacity-40")}>{L("Sačuvaj", "Save")}</button>
        {onDelete && <button onClick={onDelete} className="btn text-down"><Trash2 size={15} />{L("Obriši", "Delete")}</button>}
        <button onClick={onClose} className="btn-ghost">{L("Otkaži", "Cancel")}</button>
      </div>
    </div>
  );
}

function AssetForm({ a, onSave, onDelete, onClose, lang, gNow }) {
  const [f, setF] = useState(() => ({ kind: "gold", name: "", amount: "", currency: "EUR", start: new Date().toISOString().slice(0, 10), maturity: "", ...a,
    rate: a && a.rate ? +(a.rate * 100).toFixed(3) : "" }));
  const up = (k) => (e) => setF((x) => ({ ...x, [k]: e.target.value }));
  const L = (x, y) => (lang === "en" ? y : x);
  return (
    <div className="space-y-4">
      <h3 className="font-display text-2xl font-bold">{a && a._i !== undefined ? L("Izmena", "Edit") : L("Nova stavka", "New item")}</h3>
      <Field label={L("Vrsta", "Type")}>
        <Segmented size="sm" value={f.kind} onChange={(v) => setF((x) => ({ ...x, kind: v }))} options={Object.entries(KIND).map(([k, v]) => [k, v[lang === "en" ? 1 : 0]])} />
      </Field>
      <Field label={L("Naziv", "Name")}><input className="field" value={f.name} onChange={up("name")} placeholder={L("npr. Obveznice RS 2030", "e.g. Bonds 2030")} /></Field>
      <div className="grid grid-cols-[2fr_1fr] gap-3">
        <Field label={L("Iznos", "Amount")}><input className="field" type="number" step="any" value={f.amount} onChange={up("amount")} /></Field>
        <Field label={L("Valuta", "Currency")}>
          <Select className="w-full" width={160} value={f.currency} onChange={(v) => up("currency")({ target: { value: v } })} options={["EUR", "RSD", "USD"].map((c) => [c, c])} />
        </Field>
      </div>
      {f.kind !== "gold" && f.kind !== "cash" && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <Field label={L("Prinos (%)", "Yield (%)")}><input className="field" type="number" step="any" value={f.rate} onChange={up("rate")} /></Field>
          <Field label={L("Od", "From")}><input className="field" type="date" value={f.start || ""} onChange={up("start")} /></Field>
          <Field label={L("Dospeće", "Maturity")}><input className="field" type="date" value={f.maturity || ""} onChange={up("maturity")} /></Field>
        </div>
      )}
      {f.kind === "gold" && <p className="text-xs text-cream-400">{L("Vrednost zlata prati indeks cene zlata u evrima od trenutka unosa (ili poslednje izmene iznosa).", "Gold value tracks the gold price index in EUR from entry (or the last change of the amount).")}</p>}
      <div className="flex flex-wrap gap-2 pt-2">
        <button disabled={!f.name || !(+f.amount > 0)} className={cls("btn btn-primary", (!f.name || !(+f.amount > 0)) && "pointer-events-none opacity-40")}
          onClick={() => {
            const out = { ...f, amount: +f.amount, rate: f.rate ? +f.rate / 100 : null, maturity: f.maturity || null };
            if (out.kind === "gold" && (!a || +a.amount !== out.amount || !a.gold_base)) out.gold_base = gNow;
            delete out._i;
            onSave(out);
          }}>{L("Sačuvaj", "Save")}</button>
        {onDelete && <button onClick={onDelete} className="btn text-down"><Trash2 size={15} />{L("Obriši", "Delete")}</button>}
        <button onClick={onClose} className="btn-ghost">{L("Otkaži", "Cancel")}</button>
      </div>
    </div>
  );
}

function AllocationRing({ classes, tv, lang, t }) {
  const [hov, setHov] = useState(null);
  const [sel, setSel] = useState(null);
  const act = hov !== null ? hov : sel;
  const pick = (i) => setSel((x) => (x === i ? null : i));
  const cur = act !== null ? classes[act] : null;
  return (
    <>
      <Donut parts={classes.map(([l, v], i) => ({ value: v, color: COLORS[i % COLORS.length] }))} size={200} thick={18}
        active={act} onActive={setHov} onSelect={pick}
        center={
          <AnimatePresence mode="wait">
            <motion.div key={cur ? cur[0] : "total"} initial={{ opacity: 0, y: 6, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -6, scale: 0.96 }} transition={{ duration: 0.25 }} className="flex flex-col items-center">
              <span className="stat-label" style={cur ? { color: COLORS[act % COLORS.length] } : undefined}>{cur ? cur[0] : t("totalValue")}</span>
              <b className="font-display text-xl text-cream-50">{eur(cur ? cur[1] : tv, 0, lang)}</b>
              {cur && <span className="font-mono text-xs text-cream-300">{num((cur[1] / tv) * 100, 1, lang)}%</span>}
            </motion.div>
          </AnimatePresence>
        } />
      <div className="mt-5 w-full space-y-1.5">
        {classes.map(([l, v], i) => {
          const on = act === i, col = COLORS[i % COLORS.length], share = (v / tv) * 100;
          return (
            <motion.button type="button" key={l} onMouseEnter={() => setHov(i)} onMouseLeave={() => setHov(null)} onFocus={() => setHov(i)} onBlur={() => setHov(null)} onClick={() => pick(i)}
              whileTap={{ scale: 0.99 }} aria-pressed={sel === i}
              className={cls("relative w-full overflow-hidden rounded-xl border px-3 py-2.5 text-left text-sm transition-colors duration-300",
                on ? "border-cream-100/30 bg-white/[0.04]" : "border-white/[0.08] bg-transparent")}>
              <span className="pointer-events-none absolute inset-y-0 left-0 transition-[width,opacity] duration-500" style={{ width: on ? `${share}%` : "0%", opacity: 0.08, background: col }} />
              <span className="relative flex items-center gap-2.5">
                <motion.i className="h-2.5 w-2.5 rounded-full" style={{ background: col }} animate={{ scale: on ? 1.2 : 1 }} />
                <span className={cls("flex-1 transition-colors", on ? "text-cream-50" : "text-cream-200")}>{l}</span>
                <span className={cls("font-mono transition-colors", on ? "text-cream-100" : "text-cream-400")}>{eur(v, 0, lang)}</span>
                <span className={cls("w-12 text-right font-mono transition-colors", on ? "text-cream-50" : "text-cream-400")}>{num(share, 0, lang)}%</span>
              </span>
            </motion.button>
          );
        })}
      </div>
    </>
  );
}

export default function PortfolioPage() {
  const { lang } = useLang();
  const t = useT();
  const { go } = useRoute();
  const pf = usePortfolio();
  const { data: [stocksD, prices] } = useData(["stocks.json", "prices_all.json"]);
  const [rng, setRng] = useState(366);
  const [edit, setEdit] = useState(null); // {type:'tx'|'asset', item}
  const [busy, setBusy] = useState(false);
  const [cloudBusy, setCloudBusy] = useState(false);
  const [cloudName, setCloudName] = useState("");
  const [cloudPassword, setCloudPassword] = useState("");
  const smap = useMemo(() => Object.fromEntries(((stocksD && stocksD.stocks) || []).map((s) => [s.ticker, s])), [stocksD]);
  const portfolioStockOptions = useMemo(() => {
    const all = [...PORTFOLIO_SECURITIES, ...((stocksD && stocksD.stocks) || [])];
    const seen = new Set();
    return all.filter((stock) => {
      if (!stock.ticker || seen.has(stock.ticker) || !prices?.[stock.ticker]?.c?.length) return false;
      seen.add(stock.ticker);
      return true;
    }).sort((a, b) => a.ticker.localeCompare(b.ticker));
  }, [stocksD, prices]);
  const L = (a, b) => (lang === "en" ? b : a);
  if (pf.loading || !prices) return <div><PageHead title={t("portfolio")} /><div className="grid gap-4 md:grid-cols-3"><Skeleton className="h-28" /><Skeleton className="h-28" /><Skeleton className="h-28" /></div><Skeleton className="mt-6 h-80" /></div>;
  if (pf.error) return <div><PageHead title={t("portfolio")} /><Empty>{pf.error} <button className="btn mt-3" onClick={pf.reload}><RefreshCw size={14} />{L("Pokušaj ponovo", "Retry")}</button></Empty></div>;
  const state = pf.state;
  const vals = valuation(state, prices, smap);
  const av = assetValues(state, prices);
  const gold = goldEur(prices) || [];
  const gNow = gold.length ? gold[gold.length - 1].value : null;
  const tv = vals.reduce((x, r) => x + (r.value || 0), 0) + av.reduce((x, r) => x + (r.value || 0), 0);
  const tc = vals.reduce((x, r) => x + r.cost, 0) + av.reduce((x, r) => x + r.base, 0);
  const td = vals.reduce((x, r) => x + (r.dayEur || 0), 0) + av.reduce((x, r) => x + (r.dayEur || 0), 0);
  const hist = history(state, prices, smap, rng);
  const classes = [[L("ETF-ovi i akcije", "ETFs & stocks"), vals.reduce((x, r) => x + (r.value || 0), 0)],
    ...Object.keys(KIND).map((k) => [KIND[k][lang === "en" ? 1 : 0], av.filter((a) => a.kind === k).reduce((x, a) => x + (a.value || 0), 0)])].filter(([, v]) => v > 0);
  const equityValue = vals.reduce((sum, row) => sum + (row.value || 0), 0);
  const directStockRows = vals.filter((row) => !smap[row.ticker]?.etf);
  const directStockValue = directStockRows.reduce((sum, row) => sum + (row.value || 0), 0);
  const etfValue = vals.filter((row) => smap[row.ticker]?.etf).reduce((sum, row) => sum + (row.value || 0), 0);
  const sectorExposure = Object.values(directStockRows.reduce((groups, row) => {
    const sector = smap[row.ticker]?.sector || "other";
    groups[sector] = groups[sector] || { sector, value: 0, positions: 0 };
    groups[sector].value += row.value || 0;
    groups[sector].positions += 1;
    return groups;
  }, {})).sort((a, b) => b.value - a.value);
  const sectorIdeas = Object.values(((stocksD && stocksD.stocks) || []).filter((stock) => !stock.etf && stock.sector && Number.isFinite(+stock.opp))
    .reduce((groups, stock) => {
      const key = stock.sector;
      groups[key] = groups[key] || { sector: key, scoreTotal: 0, count: 0 };
      groups[key].scoreTotal += +stock.opp;
      groups[key].count += 1;
      return groups;
    }, {}))
    .map((group) => ({ ...group, score: group.scoreTotal / group.count, exposure: sectorExposure.find((item) => item.sector === group.sector)?.value || 0 }))
    .filter((group) => group.exposure / (directStockValue || 1) < 0.2)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);
  const pending = (state.txns || []).map((x, i) => ({ ...x, _i: i })).filter((x) => x.status === "pending");

  const persist = async (next, msg) => {
    setBusy(true);
    try { await pf.save(next); toast(msg || L("Sačuvano ✓", "Saved ✓")); setEdit(null); }
    catch (e) { toast(e.message, "err"); }
    setBusy(false);
  };
  const saveTx = (tx) => {
    const txns = [...(state.txns || [])];
    const { _i, ...clean } = tx;
    if (_i !== undefined) txns[_i] = { ...txns[_i], ...clean };
    else txns.push({ ...clean, created: new Date().toISOString() });
    persist({ ...state, txns });
  };
  const delTx = (i) => persist({ ...state, txns: state.txns.filter((_, k) => k !== i) }, L("Obrisano", "Deleted"));
  const saveAsset = (a, i) => {
    const assets = [...(state.assets || [])];
    if (i !== undefined) assets[i] = { ...assets[i], ...a };
    else assets.push({ ...a, created: new Date().toISOString() });
    persist({ ...state, assets });
  };
  const delAsset = (i) => persist({ ...state, assets: state.assets.filter((_, k) => k !== i) }, L("Obrisano", "Deleted"));

  return (
    <div>
      <PageHead title={L("Tvoj portfolio", "Your portfolio")} sub={L("Pretraži ticker ili naziv kompanije da dodaš akciju. Sačuvaj portfolio pod imenom i lozinkom da bi mu pristupila i na drugom uređaju.", "Search by ticker or company name to add a stock. Save it with a name and password to access it on another device.")}
        right={<button onClick={() => setEdit({ type: "tx", item: null })} className="btn btn-primary"><Plus size={16} />{t("addTx")}</button>} />
      {pf.migrationWarning && <div role="status" className="mb-5 rounded-xl border border-gold-500/30 bg-gold-500/5 p-4 text-sm text-cream-300">{pf.migrationWarning}</div>}
      <Card hover={false} className="mb-6 p-4 md:p-5">
        <div className="flex items-start gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white/[0.04] text-gold-500"><CloudUpload size={19} /></span>
          <div className="min-w-0 flex-1">
            <div className="font-semibold text-cream-50">{L("Tvoj portfolio na svakom uređaju", "Your portfolio on every device")}</div>
            <p className="mt-1 text-sm leading-relaxed text-cream-400">{L("Izmene ostaju u ovoj sesiji dok ne izabereš „Sačuvaj“. Istim imenom i lozinkom možeš da otvoriš šifrovanu kopiju na drugom uređaju. Portfolio se ne čuva u ovom pregledaču.", "Portfolio changes stay in this session until you choose Save. Use the same name and password to open the encrypted cloud copy on another device. Nothing is saved in this browser.")}</p>
          </div>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <Field label={L("Jedinstveno ime portfolija", "Unique portfolio name")}><input className="field" value={cloudName} onChange={(e) => setCloudName(e.target.value)} placeholder={L("npr. Moj dugoročni portfolio", "e.g. My long-term portfolio")} /></Field>
          <Field label={L("Lozinka (najmanje 10 znakova)", "Password (at least 10 characters)")}><input className="field" type="password" autoComplete="current-password" value={cloudPassword} onChange={(e) => setCloudPassword(e.target.value)} /></Field>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <button disabled={!portfolioCloudConfigured() || cloudBusy || !cloudName.trim() || cloudPassword.length < 10} onClick={async () => {
            setCloudBusy(true);
            try { await saveCloudPortfolio(cloudName, cloudPassword, state); pf.markCloudSaved(); toast(L("Portfolio je šifrovano sačuvan u cloud-u ✓", "Portfolio saved encrypted in the cloud ✓")); }
            catch (e) { toast(e.message, "err"); }
            setCloudBusy(false);
          }} className={cls("btn btn-primary", (!portfolioCloudConfigured() || cloudBusy || !cloudName.trim() || cloudPassword.length < 10) && "pointer-events-none opacity-40")}><CloudUpload size={15} />{L("Sačuvaj portfolio", "Save portfolio")}</button>
          <button disabled={!portfolioCloudConfigured() || cloudBusy || !cloudName.trim() || cloudPassword.length < 10} onClick={async () => {
            setCloudBusy(true);
            try { const remote = await loadCloudPortfolio(cloudName, cloudPassword); await pf.save(remote); pf.markCloudSaved(); toast(L("Portfolio je učitan na ovom uređaju ✓", "Portfolio loaded on this device ✓")); }
            catch (e) { toast(e.message, "err"); }
            setCloudBusy(false);
          }} className={cls("btn", (!portfolioCloudConfigured() || cloudBusy || !cloudName.trim() || cloudPassword.length < 10) && "pointer-events-none opacity-40")}><CloudDownload size={15} />{L("Otvori portfolio", "Open portfolio")}</button>
          {cloudBusy && <span className="self-center text-sm text-cream-400">{L("Čuvam portfolio…", "Saving portfolio…")}</span>}
        </div>
        <p className="mt-3 text-[11px] text-cream-500">{portfolioCloudConfigured()
          ? L("Lozinka se ne šalje cloud servisu i ne može da se vrati ako je zaboraviš. Za otvaranje na drugom uređaju treba ti samo isto ime i lozinka.", "Your password is never sent to the cloud service and cannot be recovered if forgotten. To open it on another device, you only need the same name and password.")
          : L("Cloud čuvanje još nije podešeno. Lokalni portfolio možeš da koristiš kao i do sada. Cloud opcije će se pojaviti kada povežemo bazu.", "Cloud storage is not set up yet. You can keep using your local portfolio. Cloud options will appear once the database is connected.")}</p>
      </Card>
      <div className="grid grid-cols-2 gap-3 md:gap-4 lg:grid-cols-4">
        {[[t("totalValue"), tv, (x) => eur(x, 0, lang), null], [t("invested"), tc, (x) => eur(x, 0, lang), null],
          [t("profit"), tv - tc, (x) => (x >= 0 ? "+" : "") + eur(x, 0, lang), tv - tc], [t("today"), td, (x) => (x >= 0 ? "+" : "") + eur(x, 0, lang), td]].map(([l, v, f, c], i) => (
          <Card key={l} delay={i * 0.05} className="p-4 md:p-5">
            <div className="stat-label">{l}</div>
            <div className={cls("mt-2 font-display text-[1.45rem] font-bold md:text-[1.8rem]", c === null ? "text-cream-50" : upDown(c))}><CountUp value={v} format={f} /></div>
            {i === 2 && <div className={cls("mt-0.5 font-mono text-xs", upDown(tv - tc))}>{pct(tc ? tv / tc - 1 : 0, 2, lang)}</div>}
          </Card>
        ))}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <Card hover={false} className="p-4 md:p-5">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <div className="kicker">{t("valueOverTime")}</div>
            <Segmented size="sm" value={rng} onChange={setRng} options={[[31, "1M"], [183, "6M"], [366, lang === "en" ? "1Y" : "1G"], [732, lang === "en" ? "2Y" : "2G"]]} />
          </div>
          {hist.length > 1 ? <PriceChart data={hist.map((h) => ({ time: h.time, value: h.value }))} height={290} valueFormat={(v) => eur(v, 0, lang)} />
            : <Empty>{L("Nema dovoljno podataka o cenama.", "Not enough price data.")}</Empty>}
          <p className="mt-2 text-[11px] text-cream-500">{L("Kako bi se kretala vrednost sadašnjeg portfolija u izabranom periodu (zlato po indeksu cene zlata, obveznice sa prirastom prinosa).", "How today's portfolio would have moved over the period (gold by the gold price index, bonds with accrued yield).")}</p>
        </Card>
        <Card hover={false} className="flex flex-col items-center p-5">
          <div className="kicker mb-4 self-start">{t("allocation")}</div>
          <AllocationRing classes={classes} tv={tv} lang={lang} t={t} />
        </Card>
      </div>

      <section className="mt-10">
        <SectionTitle>{L("Sektorska raspodela i ideje za diverzifikaciju", "Sector allocation and diversification ideas")}</SectionTitle>
        <Card hover={false} className="p-4 md:p-5">
          <p className="mb-4 max-w-3xl text-sm leading-relaxed text-cream-300">
            {L("Raspodela se računa iz trenutne tržišne vrednosti tvojih akcija i ETF-ova. Ideje ispod izdvajaju sektore koji su slabije zastupljeni i imaju višu prosečnu FinNews ocenu među praćenim kompanijama. To je polazna tačka za istraživanje, ne prognoza niti preporuka za kupovinu.", "Allocation uses the current market value of your directly held stocks. Ideas below highlight sectors with lower portfolio exposure and a higher average FinNews score among tracked companies. Use them as a research starting point, not as a forecast or buy recommendation.")}
          </p>
          <div className="mb-4 rounded-xl border border-gold-500/25 bg-ink-950/70 p-3 text-sm leading-relaxed text-cream-300">
            {L("Udeo sektora računa se u odnosu na direktno držane akcije. ETF-ove prikazujemo odvojeno jer nemamo pouzdane podatke o svim njihovim ulaganjima.", "Sector percentages use the value of directly held stocks as the base. ETFs are shown separately because reliable holdings data is not available for every fund.")}
            {etfValue > 0 && <span className="mt-1 block font-medium text-gold-300">{L("Vrednost ETF-ova u portfoliju", "ETF value in portfolio")}: {eur(etfValue, 0, lang)} · {num(equityValue ? etfValue / equityValue * 100 : 0, 1, lang)}%</span>}
          </div>
          {sectorExposure.length ? <div className="mb-5 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
            {sectorExposure.map((item) => <div key={item.sector} className="rounded-xl border border-ink-600 bg-ink-850/80 p-3">
              <div className="flex items-center justify-between gap-2">
                <span className="truncate text-sm font-semibold text-cream-100">{item.sector === "other" ? L("Sektor nije naveden", "Sector not listed") : (lang === "sr" ? stocksD?.sectors_sr?.[item.sector] || item.sector : item.sector)}</span>
                <span className="font-mono text-sm text-gold-300">{num(directStockValue ? item.value / directStockValue * 100 : 0, 1, lang)}%</span>
              </div>
              <div className="mt-1 text-xs text-cream-400">{eur(item.value, 0, lang)} · {item.positions} {L("pozicija", "positions")}</div>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-ink-700"><div className="h-full rounded-full bg-gold-500" style={{ width: `${Math.min(100, directStockValue ? item.value / directStockValue * 100 : 0)}%` }} /></div>
            </div>)}
          </div> : <Empty>{L("Dodaj akciju ili ETF da bi se prikazala sektorska raspodela.", "Add a stock or ETF to see sector allocation.")}</Empty>}
          <div className="border-t border-ink-600 pt-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h3 className="font-display text-lg font-semibold text-cream-50">{L("Sektori za dalju analizu", "Sectors to research")}</h3>
              <span className="text-xs text-cream-500">{L("prema oceni praćenih kompanija", "based on tracked-company scores")}</span>
            </div>
            {sectorIdeas.length ? <div className="grid gap-3 md:grid-cols-3">
              {sectorIdeas.map((idea, index) => <button key={idea.sector} type="button" onClick={() => go(`/akcije?tab=all&q=${encodeURIComponent(idea.sector)}`)}
                className="group rounded-xl border border-ink-600 bg-ink-850/70 p-4 text-left transition hover:border-white/25 hover:bg-white/[0.03] focus:outline-none focus:ring-2 focus:ring-gold-400/60">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-cream-50">{lang === "sr" ? stocksD?.sectors_sr?.[idea.sector] || idea.sector : idea.sector}</span>
                  <span className="rounded-full border border-gold-500/30 px-2 py-0.5 text-xs font-mono text-gold-300">{L("ocena", "score")} {num(idea.score, 0, lang)}</span>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-cream-400">
                  {idea.exposure > 0
                    ? L(`Trenutno čini ${num(idea.exposure / (directStockValue || 1) * 100, 1, lang)}% vrednosti direktno držanih akcija. Pregledaj kompanije iz sektora i uporedi rizik i vrednovanje.`, `Currently ${num(idea.exposure / (directStockValue || 1) * 100, 1, lang)}% of your stocks and ETFs. Review companies in the sector and compare risk and valuation.`)
                    : L("Nemaš direktnu poziciju u ovom sektoru. Pogledaj praćene kompanije i proveri da li odgovaraju tvom planu.", "You have no direct position in this sector. Review tracked companies and decide whether they fit your plan.")}
                </p>
                <span className="mt-3 inline-flex text-xs font-medium text-gold-500 group-hover:text-cream-50">{L("Prikaži kompanije", "View companies")} →</span>
              </button>)}
            </div> : <p className="text-sm text-cream-400">{L("Trenutno nema dovoljno sektorskih podataka za poređenje.", "There is not enough sector data to compare right now.")}</p>}
          </div>
        </Card>
      </section>

      <section className="mt-10">
        <SectionTitle>{t("holdings")}</SectionTitle>
        <div className="grid gap-3 md:grid-cols-2">
          {vals.map((r, i) => (
            <Card key={r.ticker} delay={i * 0.04} onClick={() => go("/akcije/" + encodeURIComponent(r.ticker) + "?name=" + encodeURIComponent(r.name || "") + "&isin=" + encodeURIComponent(r.isin || ""))} className="group p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="font-mono text-[11px] text-cream-400">{r.ticker}</div>
                  <div className="truncate font-display text-[1.05rem] font-semibold text-cream-50">{r.name}</div>
                  <div className="mt-1 text-xs text-cream-400">{num(r.qty, 4, lang).replace(/[,.]?0+$/, "")} × {num(r.price, 2, lang)} · {L("prosek", "avg")} {num(r.avg, 2, lang)}</div>
                </div>
                <div className="shrink-0 text-right">
                  <div className="font-mono text-lg text-cream-50">{eur(r.value, 0, lang)}</div>
                  <div className={cls("font-mono text-xs", upDown(r.plPct))}>{pct(r.plPct, 1, lang)} · {(r.pl >= 0 ? "+" : "") + eur(r.pl, 0, lang)}</div>
                  <div className={cls("font-mono text-[11px]", upDown(r.day))}>{t("today").toLowerCase()} {pct(r.day, 2, lang)}</div>
                </div>
              </div>
              <Spark data={r.series.slice(-120)} height={44} className="mt-3" />
              <div className="mt-2 flex gap-1 opacity-100 transition">
                <button onClick={(e) => { e.stopPropagation(); const index = (state.txns || []).reduce((found, tx, j) => tx.ticker === r.ticker ? j : found, -1); if (index >= 0) setEdit({ type: "tx", item: { ...state.txns[index], _i: index } }); }} className="btn-ghost text-xs"><Pencil size={13} />{L("Izmeni", "Edit")}</button>
                <button onClick={(e) => { e.stopPropagation(); setEdit({ type: "tx", item: { ticker: r.ticker, name: r.name, isin: r.isin, side: "buy", price: r.price ? +r.price.toFixed(2) : "" } }); }} className="btn-ghost text-xs"><Plus size={13} />{L("Dokupi", "Buy more")}</button>
                <button onClick={(e) => { e.stopPropagation(); setEdit({ type: "tx", item: { ticker: r.ticker, name: r.name, isin: r.isin, side: "sell", qty: r.qty, price: r.price ? +r.price.toFixed(2) : "" } }); }} className="btn-ghost text-xs">− {L("Prodaj", "Sell")}</button>
              </div>
            </Card>
          ))}
          {!vals.length && <Empty>{L("Još nema pozicija. Dodaj prvu transakciju.", "No positions yet. Add your first transaction.")}</Empty>}
        </div>
      </section>

      <section className="mt-10">
        <SectionTitle action={<button onClick={() => setEdit({ type: "asset", item: null })} className="btn-ghost"><Plus size={14} />{L("Dodaj", "Add")}</button>}>{t("assets")}</SectionTitle>
        <div className="grid gap-3 md:grid-cols-2">
          {av.map((a, i) => (
            <Card key={i} delay={i * 0.05} onClick={() => setEdit({ type: "asset", item: { ...state.assets[i], _i: i } })} className="group flex items-center gap-4 p-4">
              <span className={cls("grid h-11 w-11 shrink-0 place-items-center rounded-xl", a.kind === "gold" ? "bg-gold-500/15 text-gold-400" : "bg-white/[0.04] text-gold-500")}>
                {a.kind === "gold" ? <Coins size={20} /> : <Wallet size={20} />}
              </span>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-semibold text-cream-100">{a.name}</div>
                <div className="text-xs text-cream-400">
                  {KIND[a.kind] ? KIND[a.kind][lang === "en" ? 1 : 0] : a.kind}
                  {a.kind === "gold" && a.extra !== null ? ` · ${pct(a.extra, 1, lang)} ${L("od unosa", "since entry")}` : ""}
                  {(a.kind === "bond" || a.kind === "savings") && a.rate ? ` · ${num(a.rate * 100, 2, lang)}% · ${num(a.amount, 0, lang)} ${a.currency}` : ""}
                </div>
              </div>
              <div className="text-right"><div className="font-mono text-lg text-cream-50">{eur(a.value, 0, lang)}</div>
                <div className="text-[11px] text-cream-500">{num(((a.value || 0) / tv) * 100, 0, lang)}%</div></div>
              <Pencil size={15} className="text-cream-500 transition group-hover:text-cream-50" />
            </Card>
          ))}
        </div>
      </section>

      {pending.length > 0 && (
        <section className="mt-10">
          <SectionTitle>{t("pending")}</SectionTitle>
          <div className="space-y-2">
            {pending.map((o) => {
              const s = (prices[o.ticker] && prices[o.ticker].c) || [];
              const lastPx = s[s.length - 1];
              return (
                <Card key={o._i} onClick={() => setEdit({ type: "tx", item: o })} className="flex flex-wrap items-center gap-3 p-4">
                  <span className="rounded-full bg-gold-500/15 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-gold-400">{L("nalog", "order")}</span>
                  <span className="font-semibold">{o.name}</span>
                  <span className="font-mono text-sm text-cream-400">{o.qty} × LIMIT {num(o.limit_price, 2, lang)} €</span>
                  {lastPx && <span className="text-xs text-cream-400">{L("poslednja cena", "last price")} {num(lastPx, 2, lang)} {lastPx <= o.limit_price ? (lang === "en" ? "- should fill" : "- trebalo bi da se izvrši") : `(${pct(lastPx / o.limit_price - 1, 1, lang)} ${L("iznad limita", "above limit")})`}</span>}
                  <button onClick={(e) => { e.stopPropagation(); saveTx({ ...o, status: "filled", price: o.limit_price, d: new Date().toISOString().slice(0, 10) }); }} className="btn ml-auto text-xs">✓ {L("Izvršen", "Filled")}</button>
                </Card>
              );
            })}
          </div>
        </section>
      )}

      <section className="mt-10">
        <SectionTitle>{t("transactions")}</SectionTitle>
        <Card hover={false} className="overflow-hidden">
          {(state.txns || []).map((x, i) => ({ ...x, _i: i })).sort((a, b) => (b.d || "").localeCompare(a.d || "")).map((x) => (
            <motion.button key={x._i} layout onClick={() => setEdit({ type: "tx", item: x })}
              className="grid w-full grid-cols-[84px_1fr_auto] items-center gap-3 border-b border-ink-600/70 px-4 py-3 text-left text-sm transition-colors last:border-0 hover:bg-white/[0.03] md:grid-cols-[100px_90px_1fr_auto_24px]">
              <span className="font-mono text-xs text-cream-400">{x.d || "-"}</span>
              <span className={cls("hidden text-xs font-semibold md:block", x.side === "buy" ? "text-up" : "text-down")}>{x.side === "buy" ? L("kupovina", "buy") : L("prodaja", "sell")}{x.status === "pending" ? ` · ${L("nalog", "order")}` : ""}</span>
              <span className="truncate text-cream-100">{x.ticker} <span className="text-cream-400">· {x.name}</span></span>
              <span className="font-mono text-cream-300">{x.qty} × {num(x.price || x.limit_price, 2, lang)}</span>
              <Pencil size={14} className="hidden text-cream-500 md:block" />
            </motion.button>
          ))}
        </Card>
      </section>

      <AnimatePresence>
        {edit && (
          <div className="fixed inset-0 z-[80] flex items-center justify-center p-3 sm:p-6">
            <motion.button type="button" aria-label={L("Zatvori prozor", "Close dialog")} onClick={() => !busy && setEdit(null)}
              className="absolute inset-0 cursor-default bg-black/70 backdrop-blur-sm" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />
            <motion.div role="dialog" aria-modal="true" aria-labelledby="portfolio-edit-title"
              initial={{ opacity: 0, y: 14, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 8, scale: 0.98 }}
              transition={{ duration: 0.2 }} className="relative z-[1] max-h-[88dvh] w-full max-w-xl overflow-y-auto rounded-2xl border border-ink-600 bg-ink-850 p-4 shadow-2xl sm:p-6">
              <div className="mb-4 flex items-center justify-between border-b border-ink-600 pb-3">
                <div id="portfolio-edit-title" className="text-sm font-semibold text-cream-300">{L("Portfolio", "Portfolio")}</div>
                <button type="button" onClick={() => !busy && setEdit(null)} className="btn-ghost text-xs">{L("Zatvori", "Close")} ×</button>
              </div>
              {edit.type === "tx" && (
                <TxForm tx={edit.item} stocks={portfolioStockOptions} lang={lang} onClose={() => setEdit(null)} onSave={saveTx}
                  onDelete={edit.item && edit.item._i !== undefined ? () => delTx(edit.item._i) : null} />
              )}
              {edit.type === "asset" && (
                <AssetForm a={edit.item} lang={lang} gNow={gNow} onClose={() => setEdit(null)} onSave={(a) => saveAsset(a, edit.item ? edit.item._i : undefined)}
                  onDelete={edit.item && edit.item._i !== undefined ? () => delAsset(edit.item._i) : null} />
              )}
              {busy && <div className="mt-3 text-sm text-cream-400">{L("Čuvam...", "Saving...")}</div>}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
