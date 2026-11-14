import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, CloudDownload, CloudUpload, Coins, Pencil, Plus, RefreshCw, Trash2, Wallet } from "lucide-react";
import { plural, useLang, useT } from "../lib/i18n";
import { cls, eur, num, pct, upDown } from "../lib/fmt";
import { useData } from "../lib/data";
import { usePortfolio } from "../lib/usePortfolio";
import { backupCloudPortfolio, backupName, itemCount, loadCloudPortfolio, peekCloudPortfolio, portfolioCloudConfigured, saveCloudPortfolio } from "../lib/portfolioCloud";
import { KIND, assetValues, goldEur, history, valuation } from "../lib/portfolio";
import { PageHead, useRoute } from "../components/Shell";
import { Card, CountUp, Donut, Empty, Layer, Segmented, SectionTitle, Select, Skeleton, Spark, toast } from "../components/ui";
import PriceChart from "../components/PriceChart";
import DatePicker from "../components/DatePicker";

const PORTFOLIO_SECURITIES = [
  { ticker: "1YD.DE", aliases: ["1YD.XETRA"], name: "Broadcom Inc.", isin: "US11135F1012" },
  { ticker: "ABEA.DE", aliases: ["ABEA.XETRA"], name: "Alphabet Inc. Class A", isin: "US02079K3059" },
  { ticker: "EUNK.DE", aliases: ["EUNK.XETRA"], name: "iShares Core MSCI Europe UCITS ETF EUR (Acc)", isin: "IE00B4K48X80" },
  { ticker: "EUNL.DE", aliases: ["EUNL.XETRA"], name: "iShares Core MSCI World UCITS ETF", isin: "IE00B4L5Y983" },
  { ticker: "IS3N.DE", aliases: ["IS3N.XETRA"], name: "iShares Core MSCI Emerging Markets ETF", isin: "IE00BKM4GZ66" },
  { ticker: "NVD.DE", aliases: ["NVD.XETRA"], name: "NVIDIA Corp.", isin: "US67066G1040" },
  { ticker: "SXR8.DE", aliases: ["SXR8.XETRA"], name: "iShares Core S&P 500 UCITS ETF", isin: "IE00B5BMR087" },
];

const EXTRA_SECTORS = { "Bonds": ["Obveznice", "Bonds"], "Precious Metals": ["Plemeniti metali", "Precious metals"] };

const stavki = (n, lang) => {
  if (lang === "en") return `${n} ${n === 1 ? "item" : "items"}`;
  const d = n % 10, h = n % 100;
  return `${n} ${d === 1 && h !== 11 ? "stavku" : d >= 2 && d <= 4 && (h < 12 || h > 14) ? "stavke" : "stavki"}`;
};

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
            onClick={() => setPickerOpen(true)}
            onKeyDown={(e) => { if (e.key === "Escape") { e.stopPropagation(); setPickerOpen(false); } }}
            onBlur={() => setTimeout(() => setPickerOpen(false), 160)}
            onChange={(e) => {
              const value = e.target.value;
              setStockQuery(value);
              setPickerOpen(true);
              setF((x) => ({ ...x, ticker: "", name: "", isin: "" }));
            }}
            placeholder={L("Počni da kucaš npr. Alphabet ili GOOGL…", "Type e.g. Alphabet or GOOGL…")} />
          {pickerOpen && <div role="listbox" className="absolute z-30 mt-1 max-h-60 w-full overflow-y-auto rounded-xl border border-ink-500 bg-ink-850 p-1 shadow-2xl">
            {stockMatches.length ? stockMatches.map((stock) => <button type="button" role="option" aria-selected={stock.ticker === f.ticker} key={stock.ticker}
              onMouseDown={(e) => e.preventDefault()} onClick={() => chooseStock(stock)} className="flex w-full items-start gap-3 rounded-lg px-3 py-2 text-left hover:bg-white/[0.03] focus:bg-wine-900/50">
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
          <Field label={L("Datum", "Date")}><DatePicker value={f.d || ""} onChange={(v) => setF((x) => ({ ...x, d: v }))} max={new Date().toISOString().slice(0, 10)} label={L("Datum transakcije", "Transaction date")} /></Field>
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
          <Field label={L("Od", "From")}><DatePicker value={f.start || ""} onChange={(v) => setF((x) => ({ ...x, start: v }))} max={f.maturity || undefined} clearable label={L("Početak", "Start")} /></Field>
          <Field label={L("Dospeće", "Maturity")}><DatePicker value={f.maturity || ""} onChange={(v) => setF((x) => ({ ...x, maturity: v }))} min={f.start || undefined} clearable presets={false} align="right" label={L("Dospeće", "Maturity")} /></Field>
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

const SECTOR_COLORS = ["#C8285A", "#5FE39A", "#F6EDE4", "#E8C27A", "#FF8FB0", "#7FB7FF", "#A99C93", "#2E9E5E", "#B98CFF", "#FF4D63", "#6E1230"];

function SectorPanel({ sectorExposure, equityValue, etfRows, etfValue, etfWeights, etfPrimary, secName, sectorIdeas, vals, infoOf, isEtf, sectorOf, go, lang, L, onBuy }) {
  const [hov, setHov] = useState(null);
  const [sel, setSel] = useState(sectorExposure.length ? 0 : null);
  const [openEtf, setOpenEtf] = useState(null);
  const act = hov !== null ? hov : sel;
  const cur = act !== null ? sectorExposure[act] : null;
  const colorOf = (i) => SECTOR_COLORS[i % SECTOR_COLORS.length];
  const pageOf = (tk) => "/akcije/" + encodeURIComponent(infoOf(tk)?.ticker || tk);
  const selItem = sel !== null ? sectorExposure[sel] : null;
  const positions = selItem ? vals.filter((r) => r.value > 0 && sectorOf(r.ticker) === selItem.sector).sort((a, b) => b.value - a.value) : [];
  const pickSector = (i) => setSel((x) => (x === i ? null : i));
  if (!sectorExposure.length) return <Empty>{L("Dodaj akciju ili ETF da bi se prikazala sektorska raspodela.", "Add a stock or ETF to see sector allocation.")}</Empty>;
  return (
    <div className="sector-panel">
      <div className="grid items-start gap-6 lg:grid-cols-[230px_1fr]">
        <div className="flex flex-col items-center">
          <Donut parts={sectorExposure.map((s, i) => ({ value: s.value, color: colorOf(i) }))} size={220} thick={20}
            active={act} onActive={setHov} onSelect={pickSector}
            center={
              <AnimatePresence mode="wait">
                <motion.div key={cur ? cur.sector : "all"} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.22 }} className="flex flex-col items-center">
                  <span className="stat-label" style={cur ? { color: colorOf(act) } : undefined}>{cur ? secName(cur.sector) : L("Sektori", "Sectors")}</span>
                  <b className="font-display text-2xl text-cream-50">{cur ? `${num(cur.value / (equityValue || 1) * 100, 1, lang)}%` : sectorExposure.length}</b>
                  <span className="text-xs text-cream-400">{cur ? eur(cur.value, 0, lang) : L("klikni na deo kruga", "click a slice")}</span>
                </motion.div>
              </AnimatePresence>
            } />
          <p className="mt-3 text-center text-xs text-cream-500">{L("Pređi mišem ili klikni na sektor da vidiš šta je u njemu.", "Hover or click a sector to see what is inside.")}</p>
        </div>
        <div className="space-y-1.5" onMouseLeave={() => setHov(null)}>
          {sectorExposure.map((item, i) => {
            const share = equityValue ? item.value / equityValue * 100 : 0;
            const on = act === i;
            return (
              <button type="button" key={item.sector} onMouseEnter={() => setHov(i)} onFocus={() => setHov(i)} onClick={() => pickSector(i)} aria-pressed={sel === i}
                className={cls("sector-row w-full text-left", on && "is-on", sel === i && "is-sel")}>
                <span className="flex items-center gap-3">
                  <i className="h-2.5 w-2.5 shrink-0 rounded-full transition-transform duration-300" style={{ background: colorOf(i), transform: on ? "scale(1.35)" : "none" }} />
                  <span className="min-w-0 flex-1 truncate font-semibold text-cream-100">{secName(item.sector)}</span>
                  <span className="hidden text-xs text-cream-400 sm:inline">{item.stocks ? plural(item.stocks, "stocks", lang) : ""}{item.stocks && item.etfs.length ? " · " : ""}{item.etfs.length ? `${item.etfs.length} ETF` : ""}</span>
                  <span className="w-14 text-right font-mono text-sm text-cream-50">{num(share, 1, lang)}%</span>
                </span>
                <span className="mt-2 flex h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                  <motion.span className="h-full" style={{ background: colorOf(i) }} initial={{ width: 0 }} whileInView={{ width: `${Math.min(100, item.stockValue / (equityValue || 1) * 100)}%` }} viewport={{ once: true }} transition={{ duration: 0.8, delay: i * 0.04 }} />
                  <motion.span className="h-full opacity-50" style={{ background: colorOf(i) }} initial={{ width: 0 }} whileInView={{ width: `${Math.min(100, item.etfValue / (equityValue || 1) * 100)}%` }} viewport={{ once: true }} transition={{ duration: 0.8, delay: 0.2 + i * 0.04 }} />
                </span>
              </button>
            );
          })}
          {sectorExposure.some((x) => x.etfs.length) && <div className="flex gap-4 pt-1 text-[11px] text-cream-500">
            <span className="inline-flex items-center gap-1.5"><i className="h-1.5 w-3 rounded-full bg-cream-200" />{L("akcije", "stocks")}</span>
            <span className="inline-flex items-center gap-1.5"><i className="h-1.5 w-3 rounded-full bg-cream-200/50" />ETF</span>
          </div>}
        </div>
      </div>

      <AnimatePresence mode="wait">
        {selItem && <motion.div key={selItem.sector} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.25 }}
          className="sector-detail mt-5">
          <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
            <h4 className="font-display text-base font-semibold text-cream-50"><i className="mr-2 inline-block h-2.5 w-2.5 rounded-full align-middle" style={{ background: colorOf(sel) }} />{L("U sektoru", "In")} {secName(selItem.sector)}</h4>
            <span className="text-xs text-cream-400">{eur(selItem.value, 0, lang)} · {num(selItem.value / (equityValue || 1) * 100, 1, lang)}% {L("akcija i ETF-ova", "of stocks and ETFs")}</span>
          </div>
          <ul className="grid gap-1.5 md:grid-cols-2">
            {positions.map((r) => {
              const etf = isEtf(r.ticker); const w = etf ? etfWeights(r.ticker) : null; const p = etf ? etfPrimary(r.ticker) : null;
              return <li key={r.ticker}>
                <button type="button" onClick={() => go(pageOf(r.ticker))} className="pos-row w-full text-left">
                  <span className="flex items-center gap-2">
                    <b className="text-cream-50">{r.ticker}</b>
                    {etf && <span className="rounded-full border border-white/15 px-1.5 text-[10px] font-semibold text-cream-300">ETF</span>}
                    <span className="min-w-0 flex-1 truncate text-sm text-cream-400">{r.name || infoOf(r.ticker)?.name}</span>
                    <span className="font-mono text-sm text-cream-100">{eur(r.value, 0, lang)}</span>
                  </span>
                  <span className="mt-1 flex items-center justify-between text-xs text-cream-400">
                    <span>{num(r.value / (selItem.value || 1) * 100, 0, lang)}% {L("sektora", "of sector")}{etf && w && p ? ` · ${num(w[p] * 100, 0, lang)}% ${L("fonda je u ovom sektoru", "of the fund is in this sector")}` : ""}</span>
                    {r.plPct !== null && r.plPct !== undefined && <span className={upDown(r.plPct)}>{pct(r.plPct, 1, lang)}</span>}
                  </span>
                  <span className="pos-go">{L("Otvori", "Open")} →</span>
                </button>
              </li>;
            })}
          </ul>
        </motion.div>}
      </AnimatePresence>

      {etfRows.length > 0 && <div className="mt-6">
        <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
          <h4 className="font-display text-base font-semibold text-cream-50">{L("Šta je zaista u tvojim ETF-ovima", "What is really inside your ETFs")}</h4>
          <span className="text-xs text-cream-400">{L("ETF-ovi čine", "ETFs make up")} {num(equityValue ? etfValue / equityValue * 100 : 0, 1, lang)}% ({eur(etfValue, 0, lang)})</span>
        </div>
        <p className="mb-2 text-sm text-cream-400">{L("Gore se svaki ETF računa u sektor u koji ulaže najviše. Klikni na fond da vidiš kako je stvarno raspoređen.", "Above, each ETF counts toward its largest sector. Click a fund to see how it is really spread.")}</p>
        <div className="space-y-1.5">
          {etfRows.map((row) => {
            const w = etfWeights(row.ticker); const p = etfPrimary(row.ticker); const open = openEtf === row.ticker;
            return <div key={row.ticker} className={cls("etf-row", open && "is-open")}>
              <button type="button" onClick={() => setOpenEtf(open ? null : row.ticker)} aria-expanded={open} className="flex w-full items-center gap-3 text-left">
                <b className="text-cream-50">{row.ticker}</b>
                <span className="min-w-0 flex-1 truncate text-sm text-cream-400">→ {secName(p || "other")}{w && p ? ` · ${num(w[p] * 100, 0, lang)}% ${L("fonda", "of fund")}` : ""}</span>
                <span className="font-mono text-sm text-cream-100">{eur(row.value, 0, lang)}</span>
                <ChevronDown size={15} className={cls("shrink-0 text-cream-400 transition-transform duration-300", open && "rotate-180")} />
              </button>
              <AnimatePresence initial={false}>
                {open && <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.28 }} className="overflow-hidden">
                  <div className="space-y-1.5 pt-3">
                    {w ? Object.entries(w).map(([sec, v], j) => <div key={sec} className="grid grid-cols-[minmax(0,9rem)_1fr_3rem] items-center gap-3 text-xs">
                      <span className="truncate text-cream-300">{secName(sec)}</span>
                      <span className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]"><motion.span className="block h-full rounded-full bg-wine-400" initial={{ width: 0 }} animate={{ width: `${Math.min(100, v * 100)}%` }} transition={{ duration: 0.6, delay: j * 0.05 }} /></span>
                      <span className="text-right font-mono text-cream-200">{num(v * 100, 0, lang)}%</span>
                    </div>) : <p className="text-xs text-cream-500">{L("Izvor još ne objavljuje udele sektora za ovaj fond.", "The data source does not publish sector weights for this fund yet.")}</p>}
                    <button type="button" onClick={() => go(pageOf(row.ticker))} className="mt-1 text-xs font-medium text-wine-400 transition hover:text-cream-50">{L("Otvori fond", "Open fund")} →</button>
                  </div>
                </motion.div>}
              </AnimatePresence>
            </div>;
          })}
        </div>
      </div>}

      <div className="mt-6 border-t border-white/10 pt-5">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h4 className="font-display text-lg font-semibold text-cream-50">{L("Sektori za dalju analizu i dodatna ulaganja", "Sectors to research and add")}</h4>
          <span className="text-xs text-cream-500">{L("prema oceni praćenih kompanija", "based on tracked-company scores")}</span>
        </div>
        {sectorIdeas.length ? <div className="grid gap-3 md:grid-cols-3">
          {sectorIdeas.map((idea, k) => <motion.div key={idea.sector} initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.4, delay: k * 0.06 }}
            className="idea-card flex flex-col">
            <button type="button" onClick={() => go(`/akcije?tab=all&q=${encodeURIComponent(idea.sector)}`)} className="idea-head flex items-center justify-between gap-2 text-left">
              <span className="font-semibold text-cream-50">{secName(idea.sector)}</span>
              <span className="font-mono text-sm text-cream-100">{num(idea.score, 0, lang)}</span>
            </button>
            <span className="mt-2 flex h-1.5 overflow-hidden rounded-full bg-white/[0.06]" title={L("prosečna FinNews ocena sektora", "average FinNews score")}>
              <motion.span className="h-full rounded-full bg-wine-400" initial={{ width: 0 }} whileInView={{ width: `${Math.min(100, idea.score)}%` }} viewport={{ once: true }} transition={{ duration: 0.8 }} />
            </span>
            <p className="mt-2 text-xs leading-relaxed text-cream-400">
              {idea.exposure > 0
                ? L(`Sada čini ${num(idea.exposure / (equityValue || 1) * 100, 1, lang)}% vrednosti tvojih akcija i ETF-ova. Prosečna ocena sektora je ${num(idea.score, 0, lang)}.`, `Currently ${num(idea.exposure / (equityValue || 1) * 100, 1, lang)}% of your stocks and ETFs. Average sector score ${num(idea.score, 0, lang)}.`)
                : L(`Nemaš nijednu poziciju u ovom sektoru, ni kroz ETF. Prosečna ocena sektora je ${num(idea.score, 0, lang)}.`, `You have no position here, not even through an ETF. Average sector score ${num(idea.score, 0, lang)}.`)}
            </p>
            {[[L("Akcije sa najvišom ocenom", "Highest-scoring stocks"), idea.picks, false], [L("ETF za ceo sektor", "Sector ETFs"), idea.funds, true]].map(([title, list, fund]) => list.length > 0 && <div key={title} className="mt-3">
              <div className="stat-label mb-1.5">{title}</div>
              <ul className="space-y-1">
                {list.map((st) => <li key={st.ticker} className="pick-row">
                  <button type="button" onClick={() => go(`/akcije/${st.ticker}`)} className="flex min-w-0 flex-1 items-center gap-2 text-left text-sm">
                    <b className="font-semibold text-cream-50">{st.ticker}</b>
                    <span className="min-w-0 flex-1 truncate text-cream-400">{st.name}</span>
                    <span className="shrink-0 font-mono text-xs text-cream-200">{fund ? (st.w !== null ? `${num(st.w * 100, 0, lang)}%` : "") : num(st.opp, 0, lang)}</span>
                  </button>
                  <button type="button" onClick={() => onBuy(st)} title={L("Dodaj u portfolio", "Add to portfolio")} aria-label={L(`Dodaj ${st.ticker} u portfolio`, `Add ${st.ticker} to portfolio`)} className="pick-add"><Plus size={14} /></button>
                </li>)}
              </ul>
            </div>)}
            <button type="button" onClick={() => go(`/akcije?tab=all&q=${encodeURIComponent(idea.sector)}`)}
              className="mt-auto inline-flex pt-3 text-xs font-medium text-wine-400 transition hover:text-cream-50">{L("Sve kompanije iz sektora", "All companies in the sector")} →</button>
          </motion.div>)}
        </div> : <p className="text-sm text-cream-400">{L("Trenutno nema dovoljno sektorskih podataka za poređenje.", "There is not enough sector data to compare right now.")}</p>}
        <p className="mt-3 text-xs text-cream-500">{L("Znak + otvara novu transakciju sa već upisanom hartijom. Ovo su polazne tačke za istraživanje, ne preporuke za kupovinu.", "The + button opens a new transaction with the security filled in. These are research starting points, not buy recommendations.")}</p>
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
  const [cloudConfirm, setCloudConfirm] = useState(null);
  const smap = useMemo(() => Object.fromEntries(((stocksD && stocksD.stocks) || []).map((s) => [s.ticker, s])), [stocksD]);
  // Xetra oznake (npr. NVD.DE) vode na istu kompaniju kao američki ticker, da bi se sektor prepoznao
  const xmap = useMemo(() => Object.fromEntries(((stocksD && stocksD.stocks) || []).filter((s) => s.xetra?.t).map((s) => [s.xetra.t, s])), [stocksD]);
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
  const etfMeta = stocksD?.etf_sectors || {};
  const infoOf = (tk) => smap[tk] || xmap[tk];
  const isEtf = (tk) => !!(infoOf(tk)?.etf || etfMeta[tk]);
  const etfPrimary = (tk) => infoOf(tk)?.etf_primary || etfMeta[tk]?.p || null;
  const etfWeights = (tk) => infoOf(tk)?.etf_weights || etfMeta[tk]?.w || null;
  const secName = (sec) => sec === "other" ? L("Sektor nije naveden", "Sector not listed")
    : EXTRA_SECTORS[sec] ? EXTRA_SECTORS[sec][lang === "en" ? 1 : 0]
    : (lang === "sr" ? stocksD?.sectors_sr?.[sec] || sec : sec);
  const sectorOf = (tk) => (isEtf(tk) ? etfPrimary(tk) : infoOf(tk)?.sector) || "other";
  const etfValue = vals.filter((row) => isEtf(row.ticker)).reduce((sum, row) => sum + (row.value || 0), 0);
  const etfRows = vals.filter((row) => isEtf(row.ticker) && row.value > 0);
  const sectorExposure = Object.values(vals.filter((row) => row.value > 0).reduce((groups, row) => {
    const sector = sectorOf(row.ticker);
    const g = groups[sector] = groups[sector] || { sector, value: 0, stockValue: 0, etfValue: 0, stocks: 0, etfs: [] };
    g.value += row.value || 0;
    if (isEtf(row.ticker)) { g.etfValue += row.value || 0; g.etfs.push(row.ticker); }
    else { g.stockValue += row.value || 0; g.stocks += 1; }
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
    .filter((group) => group.exposure / (equityValue || 1) < 0.2)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map((group) => {
      const all = (stocksD && stocksD.stocks) || [];
      const held = new Set(vals.map((row) => infoOf(row.ticker)?.ticker || row.ticker));
      const picks = all.filter((st) => !st.etf && st.sector === group.sector && Number.isFinite(+st.opp) && !held.has(st.ticker))
        .sort((a, b) => (b.qual ? 1 : 0) - (a.qual ? 1 : 0) || b.opp - a.opp).slice(0, 3);
      const funds = all.filter((st) => st.etf && !held.has(st.ticker) && (st.etf_primary || etfMeta[st.ticker]?.p) === group.sector)
        .map((st) => ({ ...st, w: (st.etf_weights || etfMeta[st.ticker]?.w || {})[group.sector] ?? null }))
        .filter((st) => st.w === null || st.w >= 0.25)
        .sort((a, b) => (b.w ?? 0.5) - (a.w ?? 0.5)).slice(0, 2);
      return { ...group, picks, funds };
    });
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
            <p className="mt-1 text-sm leading-relaxed text-cream-400">{L("Na drugom uređaju prvo klikni „Otvori sačuvani portfolio“. Izmene ostaju u ovoj sesiji dok ne izabereš „Sačuvaj izmene“. Istim imenom i lozinkom možeš da otvoriš šifrovanu kopiju na drugom uređaju. Portfolio se ne čuva u ovom pregledaču.", "Portfolio changes stay in this session until you choose Save. Use the same name and password to open the encrypted cloud copy on another device. Nothing is saved in this browser.")}</p>
          </div>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <Field label={L("Jedinstveno ime portfolija", "Unique portfolio name")}><input className="field" value={cloudName} onChange={(e) => setCloudName(e.target.value)} placeholder={L("npr. Moj dugoročni portfolio", "e.g. My long-term portfolio")} /></Field>
          <Field label={L("Lozinka (najmanje 10 znakova)", "Password (at least 10 characters)")}><input className="field" type="password" autoComplete="current-password" value={cloudPassword} onChange={(e) => setCloudPassword(e.target.value)} /></Field>
        </div>
        {(() => {
          const off = !portfolioCloudConfigured() || cloudBusy || !cloudName.trim() || cloudPassword.length < 10;
          const localCount = itemCount(state);
          const canSave = localCount > 0 && (pf.dirty || !!pf.migrationWarning);
          const openCloud = async (name, msg) => {
            setCloudBusy("open"); setCloudConfirm(null);
            try { const remote = await loadCloudPortfolio(name, cloudPassword); await pf.save(remote); pf.markCloudSaved(); toast(msg); }
            catch (e) { toast(e.message, "err"); }
            setCloudBusy(false);
          };
          const writeCloud = async (previous) => {
            setCloudBusy("save"); setCloudConfirm(null);
            try {
              const backed = await backupCloudPortfolio(cloudName, cloudPassword, previous);
              await saveCloudPortfolio(cloudName, cloudPassword, state); pf.markCloudSaved();
              toast(backed ? L("Sačuvano ✓ Prethodna verzija je sačuvana kao rezerva.", "Saved ✓ The previous version was kept as a backup.") : L("Portfolio je šifrovano sačuvan u cloud-u ✓", "Portfolio saved encrypted in the cloud ✓"));
            } catch (e) { toast(e.message, "err"); }
            setCloudBusy(false);
          };
          const trySave = async () => {
            setCloudBusy("check");
            let remote = null;
            try { remote = await peekCloudPortfolio(cloudName, cloudPassword); }
            catch (e) { toast(e.message, "err"); setCloudBusy(false); return; }
            setCloudBusy(false);
            const remoteCount = itemCount(remote);
            if (remote && localCount === 0) {
              setCloudConfirm({ blocked: true, remoteCount });
              return;
            }
            if (remote && localCount < remoteCount) { setCloudConfirm({ remote, remoteCount }); return; }
            writeCloud(remote);
          };
          return <>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="cloud-zone">
                <button disabled={off} onClick={() => openCloud(cloudName, L("Portfolio je učitan na ovom uređaju ✓", "Portfolio loaded on this device ✓"))}
                  className={cls("btn btn-primary w-full", off && "pointer-events-none opacity-40")}><CloudDownload size={16} />{L("Otvori sačuvani portfolio", "Open saved portfolio")}</button>
                <p className="mt-2 text-xs leading-relaxed text-cream-400">{L("Učitava sačuvanu verziju na ovaj uređaj. Ništa se ne briše.", "Loads the saved version on this device. Nothing is deleted.")}</p>
              </div>
              <div className="cloud-zone">
                <button disabled={off || !canSave} onClick={trySave}
                  className={cls("btn btn-save w-full", (off || !canSave) && "pointer-events-none opacity-40")}><CloudUpload size={16} />{L("Sačuvaj izmene", "Save changes")}</button>
                <p className="mt-2 flex items-center gap-1.5 text-xs leading-relaxed text-cream-400">
                  {localCount === 0 ? L("Portfolio je prazan - prvo ga otvori ili dodaj transakciju.", "The portfolio is empty - open it or add a transaction first.")
                    : canSave ? <><i className="h-1.5 w-1.5 shrink-0 rounded-full bg-sand-400" />{L("Imaš nesačuvane izmene. Čuvanje menja sačuvanu verziju.", "You have unsaved changes. Saving replaces the saved version.")}</>
                    : <><i className="h-1.5 w-1.5 shrink-0 rounded-full bg-mint-400" />{L("Sve izmene su sačuvane.", "All changes are saved.")}</>}
                </p>
              </div>
            </div>
            {cloudBusy && <p className="mt-2 text-sm text-cream-400">{cloudBusy === "open" ? L("Otvaram portfolio…", "Opening portfolio…") : cloudBusy === "check" ? L("Proveravam sačuvanu verziju…", "Checking the saved version…") : L("Čuvam portfolio…", "Saving portfolio…")}</p>}
            {cloudConfirm && <div role="alert" className="mt-3 rounded-xl border border-down/40 bg-down/[0.06] p-3 text-sm text-cream-200">
              {cloudConfirm.blocked
                ? <p>{L(`Sačuvani portfolio pod ovim imenom ima ${stavki(cloudConfirm.remoteCount, lang)}, a ovde nemaš nijednu. Čuvanje bi ga obrisalo, pa ništa nije sačuvano. Da li si htela da ga otvoriš?`, `A portfolio with ${stavki(cloudConfirm.remoteCount, 'en')} is saved under this name and this device has none. Saving would erase it, so nothing was saved. Did you mean to open it?`)}</p>
                : <p>{L(`Sačuvana verzija ima ${stavki(cloudConfirm.remoteCount, lang)}, a ova ${localCount}. Ako nastaviš, sačuvana verzija se zamenjuje ovom, a stara ostaje kao rezerva.`, `The saved version has ${stavki(cloudConfirm.remoteCount, 'en')} and this one has ${localCount}. If you continue, the saved version is replaced and the old one is kept as a backup.`)}</p>}
              <div className="mt-2 flex flex-wrap gap-2">
                {cloudConfirm.blocked
                  ? <button className="btn btn-primary" onClick={() => openCloud(cloudName, L("Portfolio je učitan na ovom uređaju ✓", "Portfolio loaded on this device ✓"))}><CloudDownload size={15} />{L("Otvori portfolio", "Open portfolio")}</button>
                  : <button className="btn" onClick={() => writeCloud(cloudConfirm.remote)}>{L("Da, zameni sačuvanu verziju", "Yes, replace saved version")}</button>}
                <button className="btn" onClick={() => setCloudConfirm(null)}>{L("Otkaži", "Cancel")}</button>
              </div>
            </div>}
            <button type="button" disabled={off} onClick={() => openCloud(backupName(cloudName), L("Vraćena je prethodna sačuvana verzija ✓ Klikni „Sačuvaj izmene“ ako želiš da je zadržiš.", "Previous saved version restored ✓ Click Save changes to keep it."))}
              className={cls("mt-3 text-xs font-medium text-wine-400 transition hover:text-cream-50", off && "pointer-events-none opacity-40")}>{L("Vrati prethodnu sačuvanu verziju", "Restore previous saved version")} ↺</button>
          </>;
        })()}
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
            {L("Raspodela se računa iz trenutne tržišne vrednosti svih tvojih akcija i ETF-ova. Ideje ispod izdvajaju sektore koji su slabije zastupljeni, a imaju višu prosečnu FinNews ocenu, uz konkretne akcije i ETF-ove koje još nemaš. To je polazna tačka za istraživanje, ne prognoza niti preporuka za kupovinu.", "Allocation uses the current market value of all your stocks and ETFs. Ideas below highlight sectors with lower exposure and a higher average FinNews score, with specific stocks and ETFs you do not own yet. Use them as a research starting point, not as a forecast or buy recommendation.")}
          </p>
          <SectorPanel sectorExposure={sectorExposure} equityValue={equityValue} etfRows={etfRows} etfValue={etfValue} etfWeights={etfWeights} etfPrimary={etfPrimary}
            secName={secName} sectorIdeas={sectorIdeas} vals={vals} infoOf={infoOf} isEtf={isEtf} sectorOf={sectorOf} go={go} lang={lang} L={L}
            onBuy={(st) => setEdit({ type: "tx", item: { ticker: st.ticker, name: st.name, isin: st.isin || "", side: "buy" } })} />
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
          <Layer key="edit-layer" className="fixed inset-0 z-[80] flex items-center justify-center p-3 sm:p-6">
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
          </Layer>
        )}
      </AnimatePresence>
    </div>
  );
}
