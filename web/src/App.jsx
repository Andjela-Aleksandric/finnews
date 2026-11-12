import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { LangCtx } from "./lib/i18n";
import { loadMeta, store } from "./lib/data";
import { owner } from "./lib/github";
import Shell, { RouteCtx } from "./components/Shell";
import { AppCtx, Reader } from "./components/News";
import { Toaster, toast } from "./components/ui";
import Home from "./pages/Home";
import NewsPage from "./pages/News";
import StocksPage from "./pages/Stocks";
import PortfolioPage from "./pages/Portfolio";
import Review from "./pages/Review";
import ResearchPage from "./pages/Research";
import ArchivePage from "./pages/Archive";
import SettingsPage from "./pages/Settings";

function parseHash() {
  const h = decodeURI(location.hash.replace(/^#/, "")) || "/";
  const [path, qs] = h.split("?");
  const parts = path.split("/").filter(Boolean);
  const q = Object.fromEntries(new URLSearchParams(qs || ""));
  return { page: parts[0] || "", parts, q, path };
}

export default function App() {
  const [ready, setReady] = useState(false);
  const [err, setErr] = useState(null);
  const [route, setRoute] = useState(parseHash());
  const [lang, setLangS] = useState(store.get("lang", "sr"));
  const [orig, setOrigS] = useState(store.get("orig", false));
  const [starredItems, setStarred] = useState(store.get("starred", []));
  const [reading, setReading] = useState(null);
  useEffect(() => { loadMeta().then(() => setReady(true)).catch((e) => setErr(String(e))); }, []);
  useEffect(() => {
    const f = () => { setRoute(parseHash()); window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" }); };
    window.addEventListener("hashchange", f);
    return () => window.removeEventListener("hashchange", f);
  }, []);
  useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  const go = useCallback((p) => { location.hash = p.startsWith("/") ? p : "/" + p; }, []);
  const setQuery = useCallback((upd) => {
    const r = parseHash();
    const q = { ...r.q, ...upd };
    Object.keys(q).forEach((k) => (q[k] === undefined || q[k] === null || q[k] === "") && delete q[k]);
    const qs = new URLSearchParams(q).toString();
    history.replaceState(null, "", "#" + r.path + (qs ? "?" + qs : ""));
    setRoute(parseHash());
  }, []);
  const app = useMemo(() => ({
    orig, setOrig: (v) => { setOrigS(v); store.set("orig", v); },
    isOwner: !!owner.get(),
    starredItems, starred: starredItems.map((x) => x.id),
    toggleStar: (it) => setStarred((l) => {
      const has = l.some((x) => x.id === it.id);
      const n = has ? l.filter((x) => x.id !== it.id) : [{ ...it }, ...l].slice(0, 500);
      store.set("starred", n);
      toast(has ? (lang === "en" ? "Removed from saved" : "Uklonjeno iz sačuvanih") : (lang === "en" ? "Saved ★" : "Sačuvano ★"));
      return n;
    }),
    open: (it) => setReading(it),
  }), [orig, starredItems, lang]);
  const langCtx = useMemo(() => ({ lang, setLang: (l) => { setLangS(l); store.set("lang", l); } }), [lang]);
  const pages = { "": Home, vesti: NewsPage, akcije: StocksPage, portfolio: PortfolioPage, pregled: Review, istrazivanja: ResearchPage, arhiva: ArchivePage, podesavanja: SettingsPage };
  const Page = pages[route.page] || Home;
  if (err) return <div className="p-10 text-center text-cream-300">FinNews: {err}</div>;
  if (!ready) return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <motion.img src="icons/favicon.png" alt="" className="h-16 w-16 rounded-2xl shadow-glow"
        initial={{ scale: 0.6, rotate: -12, opacity: 0 }} animate={{ scale: [0.6, 1.08, 1], rotate: [-12, 4, 0], opacity: 1 }} transition={{ duration: 0.9 }} />
      <motion.div initial={{ opacity: 0, y: 10, letterSpacing: "0.3em" }} animate={{ opacity: 1, y: 0, letterSpacing: "0em" }} transition={{ duration: 0.8, delay: 0.2 }}
        className="font-display text-2xl"><span className="text-sheen">Fin</span><span className="italic text-wine-500">News</span></motion.div>
      <motion.div className="h-[2px] w-40 overflow-hidden rounded-full bg-ink-600"><motion.div className="h-full w-1/3 bg-gradient-to-r from-wine-500 to-gold-500"
        animate={{ x: ["-100%", "300%"] }} transition={{ duration: 1.1, repeat: Infinity, ease: "easeInOut" }} /></motion.div>
    </div>
  );
  return (
    <LangCtx.Provider value={langCtx}>
      <RouteCtx.Provider value={{ route, go, setQuery }}>
        <AppCtx.Provider value={app}>
          <Shell><Page /></Shell>
          <Reader it={reading} onClose={() => setReading(null)} />
          <Toaster />
        </AppCtx.Provider>
      </RouteCtx.Provider>
    </LangCtx.Provider>
  );
}
