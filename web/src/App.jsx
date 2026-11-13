import { Component, useCallback, useEffect, useMemo, useState } from "react";
import { LangCtx } from "./lib/i18n";
import { loadMeta, store } from "./lib/data";
import { owner } from "./lib/github";
import Shell, { RouteCtx } from "./components/Shell";
import { AppCtx, Reader } from "./components/News";
import { Toaster, toast } from "./components/ui";
import Home from "./pages/Home";
import NewsPage from "./pages/News";
import StocksPage from "./pages/Stocks";
import IndicatorsPage from "./pages/Indicators";
import PortfolioPage from "./pages/Portfolio";
import Review from "./pages/Review";
import ResearchPage from "./pages/Research";
import ArchivePage from "./pages/Archive";
import SettingsPage from "./pages/Settings";

class PageErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(error) {
    console.error("FinNews page render failed:", error);
  }
  render() {
    if (this.state.failed) {
      return <div role="alert" className="mx-auto my-8 max-w-xl rounded-2xl border border-wine-500/50 bg-ink-950 p-6 text-cream-100">
        <h2 className="font-display text-xl font-semibold">Ovaj prikaz nije mogao da se učita</h2>
        <p className="mt-2 text-sm leading-relaxed text-cream-300">Osveži stranicu. Ako se problem ponovi, pošalji nam snimak konzole pregledača.</p>
        <button className="btn btn-primary mt-4" onClick={() => window.location.reload()}>Osveži stranicu</button>
      </div>;
    }
    return this.props.children;
  }
}

function parseHash() {
  const h = decodeURI(location.hash.replace(/^#/, "")) || "/";
  const [path, qs] = h.split("?");
  const parts = path.split("/").filter(Boolean);
  const q = Object.fromEntries(new URLSearchParams(qs || ""));
  return { page: parts[0] || "", parts, q, path };
}

export default function App() {
  const [, setReady] = useState(false);
  const [err, setErr] = useState(null);
  const [route, setRoute] = useState(parseHash());
  const [lang, setLangS] = useState(store.get("lang", "sr"));
  const [orig, setOrigS] = useState(store.get("orig", false));
  const [starredItems, setStarred] = useState(store.get("starred", []));
  const [reading, setReading] = useState(null);
  useEffect(() => { loadMeta().then(() => setReady(true)).catch((e) => { setErr(String(e)); setReady(true); }); }, []);
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
  const pages = { "": Home, vesti: NewsPage, akcije: StocksPage, indikatori: IndicatorsPage, portfolio: PortfolioPage, pregled: Review, istrazivanja: ResearchPage, arhiva: ArchivePage, podesavanja: SettingsPage };
  const Page = pages[route.page] || Home;

  return (
    <LangCtx.Provider value={langCtx}>
      <RouteCtx.Provider value={{ route, go, setQuery }}>
        <AppCtx.Provider value={app}>
          {err && <div role="status" className="mx-auto max-w-7xl px-4 pt-4">
            <div className="rounded-xl border border-gold-500/30 bg-ink-850 px-4 py-3 text-sm text-cream-200">
              FinNews je pokrenut, ali dodatni podaci nisu učitani. Proveri vezu i osveži stranicu.
            </div>
          </div>}
          <Shell><PageErrorBoundary key={route.page}><Page /></PageErrorBoundary></Shell>
          <Reader it={reading} onClose={() => setReading(null)} />
          <Toaster />
        </AppCtx.Provider>
      </RouteCtx.Provider>
    </LangCtx.Provider>
  );
}
