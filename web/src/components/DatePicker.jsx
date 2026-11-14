// Izbor datuma u stilu aplikacije: kalendar u padajućem panelu (na telefonu se otvara odozdo).
import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CalendarDays, ChevronLeft, ChevronRight, X } from "lucide-react";
import { useLang } from "../lib/i18n";
import { cls } from "../lib/fmt";
import { Popover } from "./ui";

const MONTHS = {
  sr: ["januar", "februar", "mart", "april", "maj", "jun", "jul", "avgust", "septembar", "oktobar", "novembar", "decembar"],
  en: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
};
const SHORT = {
  sr: ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "avg", "sep", "okt", "nov", "dec"],
  en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
};
const DAYS = { sr: ["Po", "Ut", "Sr", "Če", "Pe", "Su", "Ne"], en: ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"] };

const pad = (n) => String(n).padStart(2, "0");
const iso = (y, m, d) => `${y}-${pad(m + 1)}-${pad(d)}`;
const parse = (s) => (s && /^\d{4}-\d{2}-\d{2}$/.test(s) ? { y: +s.slice(0, 4), m: +s.slice(5, 7) - 1, d: +s.slice(8, 10) } : null);
const todayIso = () => { const t = new Date(); return iso(t.getFullYear(), t.getMonth(), t.getDate()); };
const addDays = (s, k) => { const p = parse(s); const t = new Date(Date.UTC(p.y, p.m, p.d + k)); return t.toISOString().slice(0, 10); };

export function formatDate(s, lang) {
  const p = parse(s);
  if (!p) return "";
  return lang === "en" ? `${SHORT.en[p.m]} ${p.d}, ${p.y}` : `${p.d}. ${SHORT.sr[p.m]} ${p.y}.`;
}

export default function DatePicker({ value, onChange, min, max, placeholder, label, clearable = false, size = "md", className = "", align = "left" }) {
  const { lang } = useLang();
  const L = (a, b) => (lang === "en" ? b : a);
  const ref = useRef(null);
  const [open, setOpen] = useState(false);
  const start = parse(value) || parse(max && todayIso() > max ? max : todayIso());
  const [view, setView] = useState({ y: start.y, m: start.m });
  const [mode, setMode] = useState("days");
  const [dir, setDir] = useState(0);
  const [focus, setFocus] = useState(value || todayIso());
  useEffect(() => {
    if (open) { const p = parse(value) || start; setView({ y: p.y, m: p.m }); setFocus(value || iso(p.y, p.m, p.d)); setMode("days"); }
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  const ok = (s) => (!min || s >= min) && (!max || s <= max);
  const go = (k) => { setDir(k); setView((v) => { const t = new Date(v.y, v.m + k, 1); return { y: t.getFullYear(), m: t.getMonth() }; }); };
  const pick = (s) => { if (!ok(s)) return; onChange(s); setOpen(false); };

  const cells = useMemo(() => {
    const first = new Date(view.y, view.m, 1);
    const lead = (first.getDay() + 6) % 7;
    const out = [];
    for (let i = 0; i < 42; i++) {
      const t = new Date(view.y, view.m, 1 - lead + i);
      out.push({ s: iso(t.getFullYear(), t.getMonth(), t.getDate()), d: t.getDate(), cur: t.getMonth() === view.m });
    }
    return out;
  }, [view]);

  const onKey = (e) => {
    const step = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }[e.key];
    if (step) {
      e.preventDefault();
      const n = addDays(focus, step), p = parse(n);
      if (p.m !== view.m || p.y !== view.y) { setDir(step > 0 ? 1 : -1); setView({ y: p.y, m: p.m }); }
      setFocus(n);
    } else if (e.key === "PageUp" || e.key === "PageDown") { e.preventDefault(); go(e.key === "PageUp" ? -1 : 1); }
    else if (e.key === "Enter") { e.preventDefault(); pick(focus); }
  };

  const today = todayIso();
  const shown = formatDate(value, lang);
  return (
    <>
      <button type="button" ref={ref} onClick={() => setOpen((x) => !x)} aria-haspopup="dialog" aria-expanded={open} aria-label={label}
        className={cls("dropdown-trigger date-trigger inline-flex items-center gap-2.5 rounded-xl border text-left", size === "sm" ? "min-h-9 px-3 py-1.5 text-sm" : "min-h-11 w-full px-3.5 py-2 text-[15px]", open && "is-open", className)}>
        <CalendarDays size={size === "sm" ? 15 : 16} className="date-ico shrink-0" />
        <span className={cls("min-w-0 flex-1 truncate", !shown && "text-cream-500")}>{shown || placeholder || L("Izaberi datum", "Pick a date")}</span>
        {clearable && value && <span role="button" tabIndex={-1} aria-label={L("Obriši datum", "Clear date")} onClick={(e) => { e.stopPropagation(); onChange(""); }}
          className="date-clear grid h-5 w-5 place-items-center rounded-full"><X size={12} /></span>}
      </button>
      <Popover open={open} onClose={() => setOpen(false)} anchor={ref} width={300} align={align}>
        <div className="date-panel p-2" onKeyDown={onKey}>
          <div className="mb-2 flex items-center justify-between gap-1">
            <button type="button" className="date-nav" onClick={() => (mode === "days" ? go(-1) : setView((v) => ({ ...v, y: v.y - 1 })))} aria-label={L("Prethodni", "Previous")}><ChevronLeft size={16} /></button>
            <button type="button" className="date-title" onClick={() => setMode((x) => (x === "days" ? "months" : "days"))}>
              {mode === "days" ? <>{MONTHS[lang === "en" ? "en" : "sr"][view.m]} <span className="text-cream-400">{view.y}</span></> : view.y}
            </button>
            <button type="button" className="date-nav" onClick={() => (mode === "days" ? go(1) : setView((v) => ({ ...v, y: v.y + 1 })))} aria-label={L("Sledeći", "Next")}><ChevronRight size={16} /></button>
          </div>
          {mode === "days" ? <>
            <div className="mb-1 grid grid-cols-7 text-center text-[11px] font-semibold uppercase tracking-wider text-cream-500">
              {DAYS[lang === "en" ? "en" : "sr"].map((d) => <span key={d} className="py-1">{d}</span>)}
            </div>
            <div className="relative overflow-hidden">
              <AnimatePresence mode="popLayout" initial={false} custom={dir}>
                <motion.div key={`${view.y}-${view.m}`} custom={dir} initial={{ x: dir * 40, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: dir * -40, opacity: 0 }}
                  transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }} className="grid grid-cols-7 gap-0.5" role="grid">
                  {cells.map((c) => {
                    const sel = c.s === value, dis = !ok(c.s);
                    return <button type="button" key={c.s} disabled={dis} onClick={() => pick(c.s)} onMouseEnter={() => setFocus(c.s)}
                      className={cls("date-cell", !c.cur && "is-out", sel && "is-sel", c.s === today && "is-today", c.s === focus && !sel && "is-focus", dis && "is-dis")}
                      aria-pressed={sel} aria-label={formatDate(c.s, lang)}>{c.d}</button>;
                  })}
                </motion.div>
              </AnimatePresence>
            </div>
          </> : (
            <div className="grid grid-cols-3 gap-1.5 py-1">
              {SHORT[lang === "en" ? "en" : "sr"].map((m, i) => {
                const on = view.m === i;
                const dis = (min && iso(view.y, i, 31) < min) || (max && iso(view.y, i, 1) > max);
                return <button type="button" key={m} disabled={!!dis} onClick={() => { setDir(0); setView((v) => ({ ...v, m: i })); setMode("days"); }}
                  className={cls("date-month", on && "is-sel", dis && "is-dis")}>{m}</button>;
              })}
            </div>
          )}
          <div className="mt-2 flex items-center justify-between border-t border-white/10 pt-2">
            <button type="button" className="date-foot" disabled={!ok(today)} onClick={() => pick(today)}>{L("Danas", "Today")}</button>
            {clearable && value ? <button type="button" className="date-foot" onClick={() => { onChange(""); setOpen(false); }}>{L("Obriši", "Clear")}</button>
              : <span className="hidden text-[11px] text-cream-500 sm:inline">{L("strelice za kretanje", "use arrow keys")}</span>}
          </div>
        </div>
      </Popover>
    </>
  );
}
