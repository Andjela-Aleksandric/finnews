import { useCallback, useEffect, useState } from "react";

const LOCAL_KEY = "fn_portfolio_local_v1";
const emptyPortfolio = () => ({ version: 1, changed: "", txns: [], assets: [], watchlist: [] });
let shared = { initialized: false, loading: true, state: null, error: null, migrationWarning: null };
const subscribers = new Set();

function publish(next) {
  shared = { ...shared, ...next };
  subscribers.forEach((notify) => notify(shared));
}

function initialize() {
  if (shared.initialized) return shared;
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
  publish({
    initialized: true,
    loading: false,
    state: legacy ? { ...emptyPortfolio(), ...legacy } : emptyPortfolio(),
    error: null,
    migrationWarning: legacy
      ? "Postojeći portfolio je prenet u trenutnu sesiju i uklonjen iz pregledača. Sačuvaj ga imenom i lozinkom u cloud-u da ga ne izgubiš."
      : null,
  });
  return shared;
}

export function usePortfolio() {
  const [st, setSt] = useState(() => shared);
  const reload = useCallback(async () => {
    const current = initialize();
    setSt(current);
  }, []);

  useEffect(() => {
    const notify = (current) => setSt(current);
    subscribers.add(notify);
    reload();
    return () => subscribers.delete(notify);
  }, [reload]);

  const save = useCallback(async (state) => {
    const saved = { ...emptyPortfolio(), ...state, changed: new Date().toISOString() };
    publish({ initialized: true, loading: false, state: saved, error: null });
    return saved;
  }, []);

  const markCloudSaved = useCallback(() => {
    publish({ migrationWarning: null });
  }, []);

  return { ...st, reload, save, markCloudSaved, isOwner: false };
}
