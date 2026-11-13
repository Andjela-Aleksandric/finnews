import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Activity, Archive, Briefcase, CalendarRange, FlaskConical, Home, LayoutGrid, Newspaper, Search, Settings, TrendingUp, ArrowRight, CornerDownLeft } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
import { cls, num, pct, timeAgo, itTitle } from "../lib/fmt";
import { getMeta, load } from "../lib/data";
import { Aurora, BackToTop, Fx, ScrollProgress, Sheet, SplitText, ease } from "./ui";

export const RouteCtx = createContext(null);
export const useRoute = () => useContext(RouteCtx);

export const NAV = [
  ["", "home", Home], ["vesti", "news", Newspaper], ["akcije", "stocks", TrendingUp], ["indikatori", "indicators", Activity], ["portfolio", "portfolio", Briefcase],
  ["pregled", "review", CalendarRange], ["istrazivanja", "research", FlaskConical], ["arhiva", "archive", Archive], ["podesavanja", "settings", Settings],
];

function Logo({ small }) {
  return (
    <div className="flex items-center gap-2.5">
      <img src="icons/favicon.png" alt="" className={cls("rounded-xl shadow-lift", small ? "h-8 w-8" : "h-9 w-9")} />
      <span className={cls("font-display font-semibold tracking-tight", small ? "text-xl" : "text-[1.45rem]")}>
        <span className="text-cream-100">Fin</span><span className="text-wine-400">News</span>
      </span>
    </div>
  );
}

export function LangSwitch() {
  const { lang, setLang } = useLang();
  return (
    <div className="flex rounded-full border border-white/10 bg-ink-850 p-0.5 text-xs font-semibold">
      {["sr", "en"].map((l) => (
        <button key={l} onClick={() => setLang(l)} className={cls("relative rounded-full px-3 py-1.5 transition-colors", lang === l ? "text-cream-50" : "text-cream-400 hover:text-gold-300")}>
          {lang === l && <motion.span layoutId="langpill" className="absolute inset-0 rounded-full bg-wine-600 shadow-wine" transition={{ type: "spring", stiffness: 420, damping: 32 }} />}
          <span className="relative">{l.toUpperCase()}</span>
        </button>
      ))}
    </div>
  );
}

function Ticker() {
  const meta = getMeta();
  const { lang } = useLang();
  const items = (meta && meta.markets) || [];
  if (!items.length) return null;
  const nameEn = { "Zlato $": "Gold $", "US 10g %": "US 10y %" };
  const row = items.map((m, i) => (
    <div key={i} className="flex shrink-0 items-baseline gap-2 border-r border-white/[0.07] px-5 py-2.5 transition-colors duration-300 hover:bg-wine-900/40">
      <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-cream-400">{lang === "en" ? nameEn[m.n] || m.n : m.n}</span>
      <b className="font-mono text-sm font-medium text-cream-100">{num(m.v, m.dec, lang)}</b>
      <span className={cls("font-mono text-xs", m.ch >= 0 ? "text-up" : "text-down")}>{m.ch >= 0 ? "▲" : "▼"} {num(Math.abs(m.ch) * 100, 2, lang)}%</span>
    </div>
  ));
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-white/[0.08] bg-ink-900/80 backdrop-blur">
      <div className="flex w-max animate-marquee group-hover:[animation-play-state:paused]">{row}{row}</div>
      <div className="pointer-events-none absolute inset-y-0 left-0 w-12 bg-gradient-to-r from-ink-900 to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 w-12 bg-gradient-to-l from-ink-900 to-transparent" />
    </div>
  );
}

function Palette({ open, onClose }) {
  const t = useT();
  const { lang } = useLang();
  const { go } = useRoute();
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(0);
  const [data, setData] = useState({ stocks: [], news: [] });
  const inp = useRef(null);
  useEffect(() => {
    if (!open) return;
    setQ(""); setSel(0);
    setTimeout(() => inp.current && inp.current.focus(), 50);
    Promise.all([load("stocks.json"), load("news/recent.json")]).then(([s, n]) => setData({ stocks: (s && s.stocks) || [], news: n || [] }));
  }, [open]);
  const res = useMemo(() => {
    const s = q.trim().toLowerCase();
    const pages = NAV.filter(([, k]) => !s || t(k).toLowerCase().includes(s)).map(([p, k, I]) => ({ kind: "page", label: t(k), icon: I, path: "/" + p }));
    if (!s) return pages.slice(0, 8);
    const st = data.stocks.filter((x) => (x.name + " " + x.ticker).toLowerCase().includes(s)).slice(0, 7)
      .map((x) => ({ kind: "stock", label: x.name, sub: x.ticker, path: "/akcije/" + encodeURIComponent(x.ticker), ch: x.r1d }));
    const nw = data.news.filter((x) => (x.t + " " + itTitle(x, lang)).toLowerCase().includes(s)).slice(0, 6)
      .map((x) => ({ kind: "news", label: itTitle(x, lang), sub: x.s + " · " + timeAgo(x.p, lang), path: "/vesti?open=" + x.id }));
    return [...st, ...pages.slice(0, 3), ...nw];
  }, [q, data, lang, t]);
  const pick = (r) => { onClose(); go(r.path); };
  const key = (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setSel((x) => Math.min(res.length - 1, x + 1)); }
    if (e.key === "ArrowUp") { e.preventDefault(); setSel((x) => Math.max(0, x - 1)); }
    if (e.key === "Enter" && res[sel]) pick(res[sel]);
  };
  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[85] flex items-start justify-center px-3 pt-[10vh]">
          <motion.div className="absolute inset-0 bg-black/60 backdrop-blur-sm" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} />
          <motion.div initial={{ opacity: 0, y: -12, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }}
            className="relative w-full max-w-xl overflow-hidden rounded-2xl border border-ink-500 bg-ink-850 shadow-2xl">
            <div className="flex items-center gap-3 border-b border-ink-600 px-4">
              <Search size={18} className="text-cream-400" />
              <input ref={inp} value={q} onChange={(e) => { setQ(e.target.value); setSel(0); }} onKeyDown={key} placeholder={t("searchAll")}
                className="w-full bg-transparent py-4 text-base text-cream-50 outline-none placeholder:text-cream-500" />
              <kbd className="hidden rounded-md border border-ink-500 px-1.5 py-0.5 text-[10px] text-cream-400 md:block">ESC</kbd>
            </div>
            <div className="max-h-[60vh] overflow-y-auto p-2">
              {res.map((r, i) => {
                const I = r.icon || (r.kind === "stock" ? TrendingUp : Newspaper);
                return (
                  <button key={r.kind + r.path} onMouseEnter={() => setSel(i)} onClick={() => pick(r)}
                    className={cls("flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors", i === sel ? "bg-wine-700/40" : "hover:bg-wine-900/50")}>
                    <span className={cls("grid h-8 w-8 shrink-0 place-items-center rounded-lg", i === sel ? "bg-wine-600 text-cream-50" : "bg-wine-900/60 text-cream-300")}><I size={16} /></span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm text-cream-100">{r.label}</span>
                      {r.sub && <span className="block truncate text-xs text-cream-400">{r.sub}</span>}
                    </span>
                    {r.ch !== undefined && <span className={cls("font-mono text-xs", r.ch >= 0 ? "text-up" : "text-down")}>{pct(r.ch, 2, lang)}</span>}
                    {i === sel && <CornerDownLeft size={14} className="text-cream-400" />}
                  </button>
                );
              })}
              {!res.length && <div className="px-4 py-8 text-center text-sm text-cream-400">{t("nothing")}</div>}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

export default function Shell({ children }) {
  const t = useT();
  const { lang } = useLang();
  const { route, go } = useRoute();
  const [pal, setPal] = useState(false);
  const [more, setMore] = useState(false);
  const meta = getMeta();
  useEffect(() => {
    const k = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setPal((x) => !x); }
      if (e.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) { e.preventDefault(); setPal(true); }
    };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, []);
  const cur = route.page;
  const mobileMain = NAV.slice(0, 4);
  return (
    <div className="min-h-screen">
      <Aurora />
      <Fx />
      <ScrollProgress />
      <BackToTop />
      {/* bočni meni - računar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[248px] flex-col border-r border-white/[0.06] bg-ink-900/80 px-4 py-6 backdrop-blur-xl lg:flex">
        <button onClick={() => go("/")} className="mb-8 px-2 text-left"><Logo /></button>
        <button onClick={() => setPal(true)} className="mb-5 flex items-center gap-2.5 rounded-xl border border-white/10 bg-ink-850 px-3 py-2.5 text-sm text-cream-400 transition duration-300 hover:border-gold-500/50 hover:text-gold-300 hover:shadow-lift">
          <Search size={16} /> <span className="flex-1 text-left">{t("search")}</span>
          <kbd className="rounded-md border border-ink-500 px-1.5 text-[10px]">⌘K</kbd>
        </button>
        <nav className="flex flex-col gap-1">
          {NAV.map(([p, k, I]) => {
            const on = cur === p;
            return (
              <button key={p} onClick={() => go("/" + p)}
                className={cls("group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors", on ? "text-cream-50" : "text-cream-400 hover:bg-wine-900/50 hover:text-gold-300")}>
                {on && <motion.span layoutId="sidenav" className="absolute inset-0 rounded-xl bg-wine-700/40" transition={{ type: "spring", stiffness: 400, damping: 34 }} />}
                <I size={18} className={cls("nav-ico relative", on ? "text-gold-500" : "")} />
                <span className="relative">{t(k)}</span>
              </button>
            );
          })}
        </nav>
        <div className="mt-auto space-y-3 px-1">
          <LangSwitch />
          {meta && <div className="flex items-center gap-2 text-[11px] text-cream-400"><span className="h-1.5 w-1.5 animate-pulseDot rounded-full bg-up" />{t("updated")} {timeAgo(meta.generated, lang)}</div>}
        </div>
      </aside>

      {/* gornja traka - telefon i tablet */}
      <header className="sticky top-0 z-40 flex items-center justify-between border-b border-white/[0.07] bg-ink-900/85 px-4 transition-[box-shadow,border-color] duration-300 pb-2.5 pt-[max(10px,env(safe-area-inset-top))] backdrop-blur-xl lg:hidden">
        <button onClick={() => go("/")}><Logo small /></button>
        <div className="flex items-center gap-2">
          <button onClick={() => setPal(true)} className="grid h-9 w-9 place-items-center rounded-full border border-white/10 bg-ink-850 text-cream-300 transition hover:border-gold-500/50 hover:text-gold-300"><Search size={17} /></button>
          <LangSwitch />
        </div>
      </header>

      <main className="lg:pl-[248px]">
        <div className="mx-auto max-w-6xl px-3 pb-28 pt-3 sm:px-4 md:px-8 md:pb-32 md:pt-7 lg:pb-16">
          <div className="mb-6"><Ticker /></div>
          <AnimatePresence mode="wait">
            <motion.div key={cur} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.5, ease }}>
              {children}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      {/* donja traka - telefon */}
      <nav className="fixed inset-x-0 bottom-0 z-50 border-t border-white/[0.08] bg-ink-900/90 pb-[max(6px,env(safe-area-inset-bottom))] backdrop-blur-xl lg:hidden">
        <div className="mx-auto grid max-w-md grid-cols-5 px-1">
          {[...mobileMain, ["__more", "more", LayoutGrid]].map(([p, k, I]) => {
            const on = p === "__more" ? NAV.slice(4).some(([x]) => x === cur) : cur === p;
            return (
              <button key={p} onClick={() => (p === "__more" ? setMore(true) : go("/" + p))} className="relative flex flex-col items-center gap-1 pb-1 pt-2.5">
                {on && <motion.span layoutId="botnav" className="absolute top-0 h-[2px] w-8 rounded-full bg-gradient-to-r from-wine-400 to-gold-500" />}
                <motion.span whileTap={{ scale: 0.8 }} animate={on ? { y: [0, -5, 0], scale: [1, 1.15, 1] } : { y: 0, scale: 1 }} transition={{ duration: 0.45 }}>
                  <I size={21} className={on ? "text-gold-400" : "text-cream-500"} />
                </motion.span>
                <span className={cls("whitespace-nowrap text-[9px] font-semibold tracking-wide sm:text-[10px]", on ? "text-cream-50" : "text-cream-400")}>{p === "__more" ? (lang === "en" ? "More" : "Više") : t(k)}</span>
              </button>
            );
          })}
        </div>
      </nav>
      <Sheet open={more} onClose={() => setMore(false)} title={lang === "en" ? "More" : "Više"}>
        <div className="grid grid-cols-2 gap-3 pb-4">
          {NAV.slice(4).map(([p, k, I], i) => (
            <motion.button key={p} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
              onClick={() => { setMore(false); go("/" + p); }}
              className="flex flex-col items-start gap-3 rounded-2xl border border-white/10 bg-ink-800 p-4 text-left transition duration-300 hover:-translate-y-0.5 hover:border-gold-500/50 hover:shadow-lift">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-wine-800/70 text-gold-400"><I size={20} /></span>
              <span className="flex w-full items-center justify-between text-sm font-semibold">{t(k)} <ArrowRight size={14} className="text-cream-400" /></span>
            </motion.button>
          ))}
        </div>
      </Sheet>
      <Palette open={pal} onClose={() => setPal(false)} />
    </div>
  );
}

export function PageHead({ title, sub, right }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="font-display text-[2.1rem] font-semibold leading-[1.05] tracking-tight text-cream-50 md:text-[3rem]"><SplitText text={title} /></h1>
        {sub && <motion.p initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25, duration: 0.5 }} className="mt-2 max-w-2xl text-[15px] leading-relaxed text-cream-300">{sub}</motion.p>}
      </div>
      {right}
    </div>
  );
}
