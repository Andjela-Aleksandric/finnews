import { useCallback, useEffect, useState } from "react";
import { loadPortfolio, owner, savePortfolio } from "./github";

export function usePortfolio() {
  const [st, setSt] = useState({ loading: !!owner.get(), state: null, sha: null, error: null });
  const reload = useCallback(() => {
    if (!owner.get()) { setSt({ loading: false, state: null, sha: null, error: null }); return; }
    setSt((s) => ({ ...s, loading: true }));
    loadPortfolio().then((r) => setSt({ loading: false, state: r.state, sha: r.sha, error: null }))
      .catch((e) => setSt({ loading: false, state: null, sha: null, error: e.message }));
  }, []);
  useEffect(() => { reload(); }, [reload]);
  const save = useCallback(async (state) => {
    const sha = await savePortfolio(state, st.sha);
    setSt((s) => ({ ...s, state: { ...state }, sha }));
  }, [st.sha]);
  return { ...st, reload, save, isOwner: !!owner.get() };
}
