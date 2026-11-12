import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Coins, Pencil, Plus, RefreshCw, Trash2, Wallet } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
import { cls, eur, num, pct, upDown } from "../lib/fmt";
import { useData } from "../lib/data";
import { usePortfolio } from "../lib/usePortfolio";
import { KIND, assetValues, goldEur, history, valuation } from "../lib/portfolio";
import { PageHead, useRoute } from "../components/Shell";
import { Card, CountUp, Donut, Empty, Segmented, SectionTitle, Sheet, Skeleton, Spark, toast } from "../components/ui";
import PriceChart from "../components/PriceChart";

const COLORS = ["#DE4A6E", "#E6BC74", "#C99A7A", "#7FDB97", "#B9A0C9", "#8FB8B0", "#FF7A90", "#D99A80"];

function Field({ label, children }) {
  return <label className="block"><span className="stat-label mb-1.5 block">{label}</span>{children}</label>;
}

function TxForm({ tx, onSave, onDelete, onClose, lang, stocks = [] }) {
  const [f, setF] = useState(() => ({ ticker: "", name: "", isin: "", side: "buy", status: "filled", qty: 1, price: "", fee: 0, d: new Date().toISOString().slice(0, 10), limit_price: "", ...tx }));
  const [stockSearch, setStockSearch] = useState(() => (tx && tx.ticker && tx.name && tx.name !== tx.ticker ? tx.name : (tx && tx.ticker) || ""));
  const up = (k) => (e) => setF((x) => ({ ...x, [k]: e.target.value }));
  const chooseStock = (value) => {
    setStockSearch(value);
    const q = value.trim().toLowerCase();
    const match = stocks.find((x) => x.ticker.toLowerCase() === q || x.name.toLowerCase() === q);
    if (match) setF((x) => ({ ...x, ticker: match.ticker, name: match.name, isin: match.isin || x.isin }));
    else if (/^[a-z0-9.^=-]+$/i.test(value.trim())) setF((x) => ({ ...x, ticker: value.trim().toUpperCase(), name: value.trim().toUpperCase() }));
    else setF((x) => ({ ...x, ticker: "", name: "" }));
  };
  const L = (a, b) => (lang === "en" ? b : a);
  const ok = f.ticker.trim() && +f.qty > 0 && (f.status === "pending" ? +f.limit_price > 0 : +f.price > 0);
  return (
    <div className="space-y-4">
      <h3 className="font-display text-2xl font-bold">{tx && tx._i !== undefined ? L("Izmena transakcije", "Edit transaction") : L("Nova transakcija", "New transaction")}</h3>
      <div className="grid grid-cols-2 gap-3">
        <Field label={L("Kupovina / prodaja", "Buy / sell")}>
          <Segmented size="sm" value={f.side} onChange={(v) => setF((x) => ({ ...x, side: v }))} options={[["buy", L("Kupovina", "Buy")], ["sell", L("Prodaja", "Sell")]]} />
        </Field>
        <Field label="Status">
          <Segmented size="sm" value={f.status} onChange={(v) => setF((x) => ({ ...x, status: v }))} options={[["filled", L("Izvršeno", "Filled")], ["pending", L("Nalog", "Order")]]} />
        </Field>
      </div>
      <Field label={L("Akcija (ticker ili naziv)", "Stock (ticker or name)")}>
        <input className="field" list="portfolio-stock-list" value={stockSearch} onChange={(e) => chooseStock(e.target.value)}
          placeholder={L("npr. NVDA ili Nvidia", "e.g. NVDA or Nvidia")} />
        <datalist id="portfolio-stock-list">{stocks.map((x) => <option key={x.ticker} value={x.ticker} label={x.name} />)}</datalist>
        {f.ticker && <span className="mt-1 block text-xs text-cream-500">{f.name} · {f.ticker}</span>}
      </Field>
      <div className="grid grid-cols-3 gap-3">
        <Field label={L("Količina", "Quantity")}><input className="field" type="number" step="any" value={f.qty} onChange={up("qty")} /></Field>
        {f.status === "filled"
          ? <Field label={L("Cena (€)", "Price (€)")}><input className="field" type="number" step="any" value={f.price ?? ""} onChange={up("price")} /></Field>
          : <Field label={L("Limit (€)", "Limit (€)")}><input className="field" type="number" step="any" value={f.limit_price ?? ""} onChange={up("limit_price")} /></Field>}
        <Field label={L("Provizija (€)", "Fee (€)")}><input className="field" type="number" step="any" value={f.fee ?? 0} onChange={up("fee")} /></Field>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Field label={L("Datum", "Date")}><input className="field" type="date" value={f.d || ""} onChange={up("d")} /></Field>
        <Field label="ISIN"><input className="field" value={f.isin || ""} onChange={up("isin")} /></Field>
      </div>
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
          <select className="field" value={f.currency} onChange={up("currency")}>{["EUR", "RSD", "USD"].map((c) => <option key={c}>{c}</option>)}</select>
        </Field>
      </div>
      {f.kind !== "gold" && f.kind !== "cash" && (
        <div className="grid grid-cols-3 gap-3">
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

export default function PortfolioPage() {
  const { lang } = useLang();
  const t = useT();
  const { go } = useRoute();
  const pf = usePortfolio();
  const { data: [stocksD, prices] } = useData(["stocks.json", "prices_all.json"]);
  const [rng, setRng] = useState(366);
  const [edit, setEdit] = useState(null); // {type:'tx'|'asset', item}
  const [busy, setBusy] = useState(false);
  const smap = useMemo(() => Object.fromEntries(((stocksD && stocksD.stocks) || []).map((s) => [s.ticker, s])), [stocksD]);
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
      <PageHead title={L("Tvoj portfolio", "Your portfolio")} sub={L("Dodaj akciju po tickeru ili nazivu. Portfolio se čuva lokalno u ovom pregledaču i nije potreban GitHub nalog.", "Add a stock by ticker or name. Your portfolio is stored locally in this browser; no GitHub account is needed.")}
        right={<button onClick={() => setEdit({ type: "tx", item: null })} className="btn btn-primary"><Plus size={16} />{t("addTx")}</button>} />
      {pf.migrationWarning && <div role="status" className="mb-5 rounded-xl border border-gold-500/30 bg-gold-500/5 p-4 text-sm text-cream-300">{pf.migrationWarning}</div>}
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
          <Donut parts={classes.map(([l, v], i) => ({ value: v, color: COLORS[i] }))} size={180}
            center={<><span className="stat-label">{t("totalValue")}</span><b className="font-display text-xl">{eur(tv, 0, lang)}</b></>} />
          <div className="mt-5 w-full space-y-2">
            {classes.map(([l, v], i) => (
              <div key={l} className="flex items-center gap-2.5 text-sm">
                <i className="h-2.5 w-2.5 rounded-full" style={{ background: COLORS[i] }} />
                <span className="flex-1 text-cream-200">{l}</span>
                <span className="font-mono text-cream-400">{num((v / tv) * 100, 0, lang)}%</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <section className="mt-10">
        <SectionTitle>{t("holdings")}</SectionTitle>
        <div className="grid gap-3 md:grid-cols-2">
          {vals.map((r, i) => (
            <Card key={r.ticker} delay={i * 0.04} onClick={() => go("/akcije/" + encodeURIComponent(r.ticker))} className="group p-4">
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
              <div className="mt-2 flex gap-1 opacity-100 transition md:opacity-0 md:group-hover:opacity-100">
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
              <span className={cls("grid h-11 w-11 shrink-0 place-items-center rounded-xl", a.kind === "gold" ? "bg-gold-500/15 text-gold-400" : "bg-wine-900/60 text-wine-300")}>
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
              <Pencil size={15} className="text-cream-500 transition group-hover:text-wine-400" />
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
              className="grid w-full grid-cols-[84px_1fr_auto] items-center gap-3 border-b border-ink-600/70 px-4 py-3 text-left text-sm transition-colors last:border-0 hover:bg-wine-950/40 md:grid-cols-[100px_90px_1fr_auto_24px]">
              <span className="font-mono text-xs text-cream-400">{x.d || "-"}</span>
              <span className={cls("hidden text-xs font-semibold md:block", x.side === "buy" ? "text-up" : "text-down")}>{x.side === "buy" ? L("kupovina", "buy") : L("prodaja", "sell")}{x.status === "pending" ? ` · ${L("nalog", "order")}` : ""}</span>
              <span className="truncate text-cream-100">{x.ticker} <span className="text-cream-400">· {x.name}</span></span>
              <span className="font-mono text-cream-300">{x.qty} × {num(x.price || x.limit_price, 2, lang)}</span>
              <Pencil size={14} className="hidden text-cream-500 md:block" />
            </motion.button>
          ))}
        </Card>
      </section>

      <Sheet open={!!edit} onClose={() => !busy && setEdit(null)} title={L("Portfolio", "Portfolio")}>
        {edit && edit.type === "tx" && (
          <TxForm tx={edit.item} stocks={(stocksD && stocksD.stocks) || []} lang={lang} onClose={() => setEdit(null)} onSave={saveTx}
            onDelete={edit.item && edit.item._i !== undefined ? () => delTx(edit.item._i) : null} />
        )}
        {edit && edit.type === "asset" && (
          <AssetForm a={edit.item} lang={lang} gNow={gNow} onClose={() => setEdit(null)} onSave={(a) => saveAsset(a, edit.item ? edit.item._i : undefined)}
            onDelete={edit.item && edit.item._i !== undefined ? () => delAsset(edit.item._i) : null} />
        )}
        {busy && <div className="mt-4 text-sm text-cream-400">{L("Čuvam...", "Saving...")}</div>}
      </Sheet>
    </div>
  );
}
