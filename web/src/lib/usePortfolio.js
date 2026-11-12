import { useCallback, useEffect, useState } from "react";
import { loadPortfolio, owner } from "./github";

const LOCAL_KEY = "fn_portfolio_local_v1";
const emptyPortfolio = () => ({ version: 1, changed: "", txns: [], assets: [], watchlist: [] });

function readLocal() {
  try {
    const raw = localStorage.getItem(LOCAL_KEY);
    if (!raw) return null;
    const state = JSON.parse(raw);
    if (!state || !Array.isArray(state.txns) || !Array.isArray(state.assets)) return null;
    return state;
  } catch {
    return null;
  }
}

function writeLocal(state) {
  const saved = { ...emptyPortfolio(), ...state, changed: new Date().toISOString() };
  localStorage.setItem(LOCAL_KEY, JSON.stringify(saved));
  return saved;
}

export function usePortfolio() {
  const [st, setSt] = useState({ loading: true, state: null, error: null, migrationWarning: null });
  const reload = useCallback(async () => {
    const local = readLocal();
    if (local) {
      setSt({ loading: false, state: local, error: null, migrationWarning: null });
      return;
    }

    // One-time migration for existing users who previously connected GitHub.
    if (owner.get()) {
      setSt((s) => ({ ...s, loading: true }));
      try {
        const remote = await loadPortfolio();
        const state = remote && remote.state ? remote.state : emptyPortfolio();
        const saved = writeLocal(state);
        setSt({ loading: false, state: saved, error: null, migrationWarning: null });
        return;
      } catch {
        const state = emptyPortfolio();
        setSt({ loading: false, state, error: null,
          migrationWarning: "Stari GitHub portfolio nije mogao da se uveze. Novi portfolio možeš da nastaviš lokalno." });
        return;
      }
    }

    const state = emptyPortfolio();
    setSt({ loading: false, state, error: null, migrationWarning: null });
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const save = useCallback(async (state) => {
    try {
      const saved = writeLocal(state);
      setSt({ loading: false, state: saved, error: null, migrationWarning: null });
    } catch {
      throw new Error("Portfolio nije mogao da se sačuva u ovom pregledaču. Proveri slobodan prostor ili privatni režim.");
    }
  }, []);

  return { ...st, reload, save, isOwner: true };
}
