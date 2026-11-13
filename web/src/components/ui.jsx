import { useEffect, useId, useRef, useState } from "react";
import { AnimatePresence, motion, useInView, useMotionValue, useScroll, useSpring, useTransform } from "framer-motion";
import { X } from "lucide-react";
import { cls } from "../lib/fmt";

export const ease = [0.16, 1, 0.3, 1];

const canHover = typeof window !== "undefined" && window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches;

export function Card({ className = "", children, hover = true, glow = false, tilt = true, delay = 0, onClick, as = "div", onKeyDown, ...rest }) {
  const activate = (event) => {
    if (!onClick) return;
    if (event.target !== event.currentTarget && event.target.closest?.("button,a,input,select,textarea,[role='checkbox']")) return;
    onClick(event);
  };
  const activateByKeyboard = (event) => {
    onKeyDown?.(event);
    if (event.defaultPrevented || !onClick || event.target !== event.currentTarget) return;
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onClick(event); }
  };
  const M = motion[as] || motion.div;
  const ref = useRef(null);
  const rx = useMotionValue(0), ry = useMotionValue(0);
  const srx = useSpring(rx, { stiffness: 220, damping: 20 }), sry = useSpring(ry, { stiffness: 220, damping: 20 });
  const move = (e) => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const x = e.clientX - r.left, y = e.clientY - r.top;
    el.style.setProperty("--mx", `${x}px`);
    el.style.setProperty("--my", `${y}px`);
    
  };
  const leave = () => { rx.set(0); ry.set(0); };
  return (
    <M
      ref={ref}
      onMouseMove={move}
      onMouseLeave={leave}
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-30px" }}
      transition={{ duration: 0.75, ease, delay }}
      whileHover={hover ? { y: -2, transition: { type: "spring", stiffness: 400, damping: 30 } } : undefined}
      whileTap={onClick ? { scale: 0.985 } : undefined}
      style={{ rotateX: srx, rotateY: sry, transformPerspective: 900 }}
      onClick={activate}
      onKeyDown={activateByKeyboard}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      className={cls(
        "spot relative rounded-2xl border shadow-card",
                glow && "glow-border",
        onClick && "cursor-pointer",
        className
      )}
      {...rest}
    >
      {children}
    </M>
  );
}

// pojavljivanje sekcije pri skrolovanju
export function Reveal({ children, delay = 0, y = 26, className = "" }) {
  return (
    <motion.div className={className} initial={{ opacity: 0, y }} whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }} transition={{ duration: 0.8, ease, delay }}>
      {children}
    </motion.div>
  );
}

// naslov koji se pojavljuje reč po reč
export function SplitText({ text, className = "", delay = 0 }) {
  const words = String(text || "").split(" ");
  return (
    <span className={className} aria-label={text}>
      {words.map((w, i) => (
        <span key={i} className="inline-block overflow-hidden align-bottom">
          <motion.span className="inline-block" initial={{ y: "110%", opacity: 0 }} animate={{ y: "0%", opacity: 1 }}
            transition={{ duration: 0.6, ease, delay: delay + i * 0.07 }}>{w}{i < words.length - 1 ? "\u00a0" : ""}</motion.span>
        </span>
      ))}
    </span>
  );
}

// sadržaj kartice (taba) sa prelazom
export function TabPanel({ k, children }) {
  return (
    <AnimatePresence mode="wait">
      <motion.div key={k} initial={{ opacity: 0, x: 18 }} animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -14 }} transition={{ duration: 0.4, ease }}>
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

export function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const x = useSpring(scrollYProgress, { stiffness: 120, damping: 24 });
  return <motion.div style={{ scaleX: x }} className="fixed inset-x-0 top-0 z-[95] h-[2px] origin-left bg-gold-500" />;
}

export function BackToTop() {
  const { scrollY } = useScroll();
  const [show, setShow] = useState(false);
  useEffect(() => scrollY.on("change", (v) => setShow(v > 900)), [scrollY]);
  return (
    <AnimatePresence>
      {show && (
        <motion.button initial={{ opacity: 0, scale: 0.6, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.6, y: 20 }}
          whileHover={{ y: -3 }} whileTap={{ scale: 0.9 }} onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          className="fixed bottom-24 right-4 z-[60] grid h-11 w-11 place-items-center rounded-full border border-white/15 bg-ink-850/90 text-white shadow-lift hover:border-white/40 backdrop-blur lg:bottom-8 lg:right-8">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 15l-6-6-6 6" /></svg>
        </motion.button>
      )}
    </AnimatePresence>
  );
}

// pozadina: spore "aurora" mrlje boja koje se pomeraju
export function Aurora() {
  const { scrollYProgress } = useScroll();
  const o = useTransform(scrollYProgress, [0, 0.4], [1, 0.35]);
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <motion.div style={{ opacity: o }} className="absolute left-1/2 top-[-30vh] h-[60vh] w-[90vw] -translate-x-1/2 rounded-full bg-[radial-gradient(closest-side,rgba(255,255,255,.07),transparent)]" />
      <motion.div style={{ opacity: o }} className="absolute right-[-10vw] top-[-20vh] h-[50vh] w-[50vw] rounded-full bg-[radial-gradient(closest-side,rgba(163,25,75,.16),transparent)]" />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.025)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.025)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_70%_50%_at_50%_0%,#000,transparent)]" />
    </div>
  );
}

export function SectionTitle({ children, action, kicker }) {
  return (
    <div className="group/section-heading mb-5 mt-2 flex min-w-0 flex-row items-end justify-between gap-3">
      <div>
        {kicker && <motion.div initial={{ opacity: 0, x: -10 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} className="kicker mb-1">{kicker}</motion.div>}
        <motion.h2 initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
          transition={{ duration: 0.7, ease }} className="break-words font-display text-[1.45rem] font-semibold leading-tight tracking-tight text-white">{children}</motion.h2>
        <motion.div initial={{ width: 0 }} whileInView={{ width: 40 }} viewport={{ once: true }} transition={{ duration: 0.7, ease, delay: 0.2 }}
          className="mt-3 h-px w-10 bg-gold-500 transition-all duration-700 group-hover/section-heading:w-20" />
      </div>
      {action && <motion.div className="shrink-0" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ delay: 0.3 }}>{action}</motion.div>}
    </div>
  );
}

// segmentirani izbor sa animiranom "pilulom"
export function Segmented({ options, value, onChange, size = "md", className = "" }) {
  const id = useId();
  return (
    <div className={cls("no-scrollbar flex max-w-full gap-1 overflow-x-auto rounded-full border border-white/10 bg-ink-850/90 p-1", className)}>
      {options.map(([k, label, icon]) => {
        const on = k === value;
        return (
          <motion.button
            key={k}
            whileTap={{ scale: 0.92 }}
            onClick={() => onChange(k)}
            className={cls(
              "relative shrink-0 whitespace-nowrap rounded-full font-medium transition-colors duration-200",
              size === "sm" ? "px-3.5 py-2 text-sm" : "px-4 py-2.5 text-base",
              on ? "text-black" : "text-cream-400 hover:text-white"
            )}
          >
            {on && (
              <motion.span layoutId={`seg-${id}`} className="absolute inset-0 rounded-full bg-white"
                transition={{ type: "spring", stiffness: 420, damping: 34 }} />
            )}
            <span className="relative z-10 flex items-center gap-1.5">{icon}{label}</span>
          </motion.button>
        );
      })}
    </div>
  );
}

export function Tabs({ options, value, onChange }) {
  const id = useId();
  return (
    <div className="no-scrollbar mb-5 flex gap-6 overflow-x-auto border-b border-white/10">
      {options.map(([k, label, icon]) => (
        <button key={k} onClick={() => onChange(k)}
          className={cls("relative flex shrink-0 items-center gap-2 pb-3 pt-1 text-base font-semibold tracking-wide transition-colors",
            k === value ? "text-white" : "text-cream-500 hover:text-cream-200")}>
          {icon}{label}
          {k === value && <motion.span layoutId={`tab-${id}`} className="absolute inset-x-0 -bottom-px h-[2px] rounded-full bg-gold-500" />}
        </button>
      ))}
    </div>
  );
}

export function Chip({ children, active, onClick, className = "" }) {
  return (
    <motion.button onClick={onClick} whileTap={{ scale: 0.92 }} whileHover={{ y: -2, transition: { type: "spring", stiffness: 400, damping: 18 } }}
      className={cls("inline-flex min-h-10 items-center gap-2 whitespace-nowrap rounded-full border px-4 py-2 text-sm font-medium transition-colors duration-200 hover:shadow-lift",
        active ? "border-white bg-white text-black" : "border-white/10 bg-transparent text-cream-300 hover:border-white/30 hover:text-white",
        className)}>
      {children}
    </motion.button>
  );
}

export function Badge({ children, color = "#A3A3A3", className = "" }) {
  return (
    <span className={cls("inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold", className)}
      style={{ color, borderColor: color + "40", background: "transparent" }}>
      {children}
    </span>
  );
}

// mali grafikon koji se iscrtava animirano
export function Spark({ data, height = 56, className = "" }) {
  const id = useId().replace(/:/g, "");
  const vals = (data || []).map((d) => (typeof d === "number" ? d : d.value)).filter((v) => v);
  if (vals.length < 2) return <div style={{ height }} />;
  const w = 300, h = height;
  const lo = Math.min(...vals), hi = Math.max(...vals), rg = hi - lo || 1;
  const pts = vals.map((v, i) => [(i * w) / (vals.length - 1), h - 4 - ((v - lo) / rg) * (h - 10)]);
  const d = "M" + pts.map((p) => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" L");
  const col = vals[vals.length - 1] >= vals[0] ? "#3DDC97" : "#FF4D5E";
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className={cls("block w-full overflow-visible", className)} style={{ height }}>
      <defs>
        <linearGradient id={`g${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={col} stopOpacity=".35" /><stop offset="1" stopColor={col} stopOpacity="0" />
        </linearGradient>
      </defs>
      <motion.path d={`${d} L${w},${h} L0,${h} Z`} fill={`url(#g${id})`} initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ duration: 0.8, delay: 0.4 }} />
      <motion.path d={d} fill="none" stroke={col} strokeWidth="2" vectorEffect="non-scaling-stroke"
        initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }} viewport={{ once: true }} transition={{ duration: 1.2, ease }} />
    </svg>
  );
}

export function CountUp({ value, format, duration = 900 }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });
  const [v, setV] = useState(0);
  useEffect(() => {
    if (!inView || value === null || value === undefined || Number.isNaN(value)) return;
    let raf, start;
    const step = (t) => {
      start ??= t;
      const k = Math.min(1, (t - start) / duration);
      setV(value * (1 - Math.pow(1 - k, 3)));
      if (k < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [inView, value, duration]);
  return <span ref={ref}>{value === null || value === undefined ? "-" : format(v)}</span>;
}

export function Skeleton({ className = "" }) {
  return <div className={cls("shimmer rounded-xl", className)} />;
}
export function SkeletonList({ n = 4 }) {
  return <div className="space-y-3">{Array.from({ length: n }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>;
}

export function Empty({ children, icon }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-white/10 px-6 py-10 text-center text-sm text-cream-400">
      {icon}<div className="max-w-md">{children}</div>
    </div>
  );
}

// panel koji izlazi sa desne strane (računar) ili odozdo (telefon)
export function Sheet({ open, onClose, children, wide = false, title }) {
  useEffect(() => {
    if (!open) return;
    const k = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", k); document.body.style.overflow = ""; };
  }, [open, onClose]);
  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[80]">
          <motion.div className="absolute inset-0 bg-black/60 backdrop-blur-sm" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} />
          <motion.div
            className={cls("absolute bottom-0 right-0 flex max-h-[94vh] w-full flex-col overflow-hidden rounded-t-3xl border border-ink-600 bg-ink-850 shadow-2xl",
              "md:top-0 md:max-h-none md:rounded-l-3xl md:rounded-tr-none", wide ? "md:w-[760px]" : "md:w-[560px]")}
            initial={{ y: 40, x: 0, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 40, opacity: 0 }}
            transition={{ duration: 0.35, ease }}
          >
            <div className="flex items-center justify-between border-b border-ink-600 px-5 py-3.5">
              <div className="mx-auto h-1 w-10 rounded-full bg-ink-500 md:hidden" />
              <div className="hidden text-sm font-semibold text-cream-300 md:block">{title}</div>
              <button onClick={onClose} className="absolute right-4 top-2.5 rounded-full p-2 text-cream-400 transition hover:rotate-90 hover:bg-ink-700 hover:text-cream-50"><X size={18} /></button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 pb-10 pt-4 md:px-7">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

let toastFn = null;
export const toast = (msg, kind = "ok") => toastFn && toastFn({ msg, kind, id: Date.now() });
export function Toaster() {
  const [list, setList] = useState([]);
  useEffect(() => {
    toastFn = (t) => { setList((l) => [...l, t]); setTimeout(() => setList((l) => l.filter((x) => x.id !== t.id)), 3500); };
    return () => { toastFn = null; };
  }, []);
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-24 z-[90] flex flex-col items-center gap-2 md:bottom-8">
      <AnimatePresence>
        {list.map((t) => (
          <motion.div key={t.id} initial={{ opacity: 0, y: 20, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 10 }}
            className={cls("rounded-full border px-5 py-2.5 text-sm shadow-lift backdrop-blur", t.kind === "err" ? "border-down/50 bg-ink-800/95 text-down" : "border-white/15 bg-ink-800/95 text-cream-100")}>
            {t.msg}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

export function Donut({ parts, size = 170, thick = 18, center }) {
  const total = parts.reduce((a, p) => a + p.value, 0) || 1;
  const r = (size - thick) / 2, c = 2 * Math.PI * r;
  let acc = 0;
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1A1A1A" strokeWidth={thick} />
        {parts.map((p, i) => {
          const len = (p.value / total) * c;
          const el = (
            <motion.circle key={i} cx={size / 2} cy={size / 2} r={r} fill="none" stroke={p.color} strokeWidth={thick} strokeLinecap="butt"
              strokeDasharray={`${len} ${c}`} initial={{ strokeDashoffset: len }} whileInView={{ strokeDashoffset: 0 }} viewport={{ once: true }}
              transition={{ duration: 0.9, delay: 0.1 * i, ease }} style={{ strokeDashoffset: 0 }} transform={`rotate(${(acc / total) * 360} ${size / 2} ${size / 2})`} />
          );
          acc += p.value;
          return el;
        })}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">{center}</div>
    </div>
  );
}

export function Gauge({ value, label, size = 72 }) {
  const r = (size - 10) / 2, c = 2 * Math.PI * r;
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1F1F1F" strokeWidth="4" />
        <motion.circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="url(#gaugeg)" strokeWidth="4" strokeLinecap="round"
          strokeDasharray={c} initial={{ strokeDashoffset: c }} whileInView={{ strokeDashoffset: c * (1 - value / 100) }} viewport={{ once: true }} transition={{ duration: 1.1, ease }} />
        <defs><linearGradient id="gaugeg"><stop offset="0" stopColor="#FF6A13" /><stop offset="1" stopColor="#FF6A13" /></linearGradient></defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <b className="font-mono text-lg leading-none text-cream-50">{value}</b>
        {label && <span className="mt-0.5 text-[9px] uppercase tracking-widest text-cream-400">{label}</span>}
      </div>
    </div>
  );
}
