import { useCallback, useEffect, useState } from "react";

const LOCAL_KEY = "fn_portfolio_local_v1";
const emptyPortfolio = () => ({ version: 1, changed: "", txns: [], assets: [], watchlist: [] });

export function usePortfolio() {
  const [st, setSt] = useState({ loading: true, state: null, error: null, migrationWarning: null });
  const reload = useCallback(async () => {
    let legacy = null;
    try {
      const raw = localStorage.getItem(LOCAL_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && Array.isArray(parsed.txns) && Array.isArray(parsed.assets)) legacy = parsed;
      }
      localStorage.removeItem(LOCAL_KEY);
    } catch {
      // Private browsing may block storage. The portfolio still works in memory.
    }
    const state = legacy ? { ...emptyPortfolio(), ...legacy } : emptyPortfolio();
    setSt({
      loading: false,
      state,
      error: null,
      migrationWarning: legacy
        ? "Postojeći portfolio je prenet u trenutnu sesiju i uklonjen iz pregledača. Sačuvaj ga imenom i lozinkom u cloud-u da ga ne izgubiš."
        : null,
    });
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const save = useCallback(async (state) => {
    const saved = { ...emptyPortfolio(), ...state, changed: new Date().toISOString() };
    setSt((current) => ({ ...current, loading: false, state: saved, error: null }));
    return saved;
  }, []);

  const markCloudSaved = useCallback(() => {
    setSt((current) => ({ ...current, migrationWarning: null }));
  }, []);

  return { ...st, reload, save, markCloudSaved, isOwner: false };
}
