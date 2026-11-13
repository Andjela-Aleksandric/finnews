import { createContext, useContext, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { BookOpen, Bookmark, BookmarkCheck, ExternalLink, FileText, Layers, Lock, Sparkles } from "lucide-react";
import { countOf, plural, useLang, useT } from "../lib/i18n";
import { cls, itSum, itTitle, srcColor, timeAgo } from "../lib/fmt";
import { loadTexts, owner } from "../lib/github";
import { Badge, Sheet, Skeleton } from "./ui";

export const AppCtx = createContext(null);
export const useApp = () => useContext(AppCtx);

const CAT = { "Vesti": ["Tržišta", "Markets"], "Centralne banke i makro": ["Centralne banke", "Central banks"], "Analize i blogovi": ["Analize", "Analysis"],
  "Srbija i region": ["Finansije Srbija", "Serbia finance"], "Kompanije": ["Kompanije", "Companies"], "Srbija": ["Srbija", "Serbia"], "Svet": ["Svet", "World"] };
export const catLabel = (c, lang) => (CAT[c] ? CAT[c][lang === "en" ? 1 : 0] : c);

export function Dots({ score }) {
  const n = Math.max(1, Math.min(5, Math.round((score || 0) / 4.5)));
  return (
    <span className="inline-flex gap-[3px]" title={`${(score || 0).toFixed(1)}`}>
      {[0, 1, 2, 3, 4].map((i) => <i key={i} className={cls("h-1.5 w-1.5 rounded-full", i < n ? "bg-gold-500" : "bg-ink-500")} />)}
    </span>
  );
}

export function NewsCard({ it, extra = 0, hero = false, i = 0, translateAlways = false }) {
  const { lang } = useLang();
  const t = useT();
  const app = useApp();
  const original = !translateAlways && app.orig;
  const title = itTitle(it, lang, original), sum = itSum(it, lang, original);
  const starred = app.starred.includes(it.id);
  const col = srcColor(it.s);
  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-30px" }} transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1], delay: Math.min(i, 6) * 0.06 }} whileTap={{ scale: 0.99 }}
      onClick={() => app.open(it)}
      className={cls("group relative flex cursor-pointer flex-col overflow-hidden rounded-2xl border p-5 transition-[border-color,box-shadow] duration-300",
        hero ? "border-white/15 bg-ink-850 md:p-8"
             : "border-white/[0.08] bg-ink-850 hover:border-white/25")}>
      
      <div className="relative flex flex-wrap items-center gap-2 text-xs text-cream-400">
        {hero && <span className="rounded-full bg-gold-500 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-widest text-black">{lang === "en" ? "Top story" : "Vest dana"}</span>}
        <Badge color={col}>{it.s}</Badge>
        <span>{catLabel(it.c, lang)}</span>
        <span className="text-cream-500">·</span>
        <span>{timeAgo(it.p, lang)}</span>
        <Dots score={it.k} />
        {it.f && app.isOwner && <span className="inline-flex items-center gap-1 text-up"><FileText size={12} />{lang === "en" ? "full text" : "ceo tekst"}</span>}
      </div>
      <h3 className={cls("relative mt-3 font-display font-semibold leading-snug text-cream-50 transition-colors group-hover:text-cream-50", hero ? "text-[1.55rem] md:text-[1.9rem]" : "text-[1.12rem]")}>
        <span className="link-u">{title}</span>
      </h3>
      {sum && <p className={cls("relative mt-2 text-cream-300", hero ? "line-clamp-3 text-[15px]" : "line-clamp-2 text-sm")}>{sum}</p>}
      <div className="relative mt-auto flex items-center gap-2 pt-4">
        <span className="btn-ghost -ml-3 text-cream-200 group-hover:text-cream-50"><BookOpen size={15} />{t("read")}</span>
        {extra > 0 && <span className="inline-flex items-center gap-1 text-xs text-gold-500"><Layers size={13} />+{extra} {t("moreSources")}</span>}
        <button onClick={(e) => { e.stopPropagation(); app.toggleStar(it); }}
          className={cls("ml-auto rounded-full p-2 transition hover:bg-ink-700", starred ? "text-gold-500" : "text-cream-400 hover:text-cream-100")}>
          {starred ? <BookmarkCheck size={17} /> : <Bookmark size={17} />}
        </button>
      </div>
    </motion.article>
  );
}

export function NewsGrid({ items, extra = {}, heroFirst = true }) {
  if (!items.length) return null;
  const [first, ...rest] = items;
  return (
    <div className="space-y-4">
      {heroFirst ? <NewsCard it={first} extra={extra[first.id]} hero /> : null}
      <div className="grid gap-4 md:grid-cols-2">
        {(heroFirst ? rest : items).map((it, i) => <NewsCard key={it.id} it={it} extra={extra[it.id]} i={i} />)}
      </div>
    </div>
  );
}

export function NewsRow({ it, extra, n }) {
  const { lang } = useLang();
  const app = useApp();
  return (
    <motion.li initial={{ opacity: 0, x: -8 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ delay: Math.min(n || 0, 8) * 0.04 }}
      onClick={() => app.open(it)}
     
      className="row-accent group flex min-w-0 cursor-pointer gap-3 rounded-xl px-3 py-3 transition-colors hover:bg-white/[0.03] sm:gap-4">
      {n !== undefined && <span className="w-6 shrink-0 pt-0.5 font-display text-xl font-bold italic text-gold-500/80 transition group-hover:text-cream-50">{n + 1}</span>}
      <div className="min-w-0">
        <div className="text-[15px] font-medium leading-snug text-cream-100 transition-colors group-hover:text-cream-50"><span className="link-u">{itTitle(it, lang, app.orig)}</span></div>
        <div className="mt-1 flex flex-wrap items-center gap-x-2 text-xs text-cream-400">
          <span style={{ color: srcColor(it.s) }}>{it.s}</span>· {timeAgo(it.p, lang)}
          {extra > 0 && <span className="text-gold-500">· +{extra} {plural(extra, "outlets", lang)}</span>}
        </div>
      </div>
    </motion.li>
  );
}

const paras = (txt) => (txt || "").split(/\n+/).map((p) => p.trim()).filter((p) => p.length > 1);

export function Reader({ it, onClose }) {
  const { lang } = useLang();
  const t = useT();
  const app = useApp();
  const [txt, setTxt] = useState(undefined);
  const [showOrig, setShowOrig] = useState(false);
  const isOwner = !!owner.get();
  useEffect(() => {
    setTxt(undefined); setShowOrig(false);
    if (!it) return;
    if (!isOwner) { setTxt(null); return; }
    loadTexts(it.p.slice(0, 10)).then((d) => setTxt((d && d[it.id]) || null));
  }, [it, isOwner]);
  if (!it) return <Sheet open={false} onClose={onClose} />;
  const title = itTitle(it, lang, app.orig);
  const quick = txt && txt.q && (txt.q[lang] || txt.q.sr || txt.q.en);
  const body = txt ? (lang === "sr" && txt.sr && !showOrig ? txt.sr : txt.x) : null;
  const starred = app.starred.includes(it.id);
  return (
    <Sheet open={!!it} onClose={onClose} wide title={it.s}>
      <div className="flex flex-wrap items-center gap-2 text-xs text-cream-400">
        <Badge color={srcColor(it.s)}>{it.s}</Badge><span>{catLabel(it.c, lang)}</span><span>· {timeAgo(it.p, lang)}</span><Dots score={it.k} />
      </div>
      <h2 className="mt-4 font-display text-[1.7rem] font-bold leading-tight text-cream-50 md:text-[2.1rem]">{title}</h2>
      {app.orig === false && it.l !== lang && it.t !== title && <p className="mt-2 text-sm italic text-cream-400">{it.t}</p>}
      <div className="mt-5 flex flex-wrap gap-2">
        <a href={(txt && txt.u) || it.u} target="_blank" rel="noreferrer" className="btn"><ExternalLink size={15} />{t("openOriginal")}</a>
        <button onClick={() => app.toggleStar(it)} className={cls("btn", starred && "border-gold-500/60 text-gold-400")}>
          {starred ? <BookmarkCheck size={15} /> : <Bookmark size={15} />}{starred ? t("saved") : t("save")}
        </button>
        {txt && txt.sr && lang === "sr" && <button onClick={() => setShowOrig((x) => !x)} className="btn">{showOrig ? "Prevod" : "Original (EN)"}</button>}
      </div>
      {txt === undefined ? (
        <div className="mt-6 space-y-3"><Skeleton className="h-28" /><Skeleton className="h-5 w-4/5" /><Skeleton className="h-5 w-3/5" /></div>
      ) : (
        <>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="mt-6 rounded-2xl border border-white/10 bg-white/[0.02] p-5">
            <div className="kicker mb-2 flex items-center gap-1.5"><Sparkles size={13} />{t("keyPoints")}</div>
            {quick ? (
              <ul className="space-y-2">
                {quick.split("\n").map((l) => l.replace(/^-\s*/, "")).filter(Boolean).map((l, i) => (
                  <motion.li key={i} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.05 * i }} className="flex gap-2.5 text-[15px] leading-relaxed text-cream-100">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rotate-45 bg-gold-500" />{l}
                  </motion.li>
                ))}
              </ul>
            ) : <p className="text-[15px] leading-relaxed text-cream-100">{itSum(it, lang, app.orig) || "-"}</p>}
          </motion.div>
          {body ? (
            <div className="mt-7">
              <div className="kicker mb-3">{t("fullText")}{txt.a ? ` · ${lang === "en" ? "via" : "preuzeto od"} ${txt.a}` : ""}</div>
              <div className="article">{paras(body).map((p, i) => <p key={i}>{p}</p>)}</div>
            </div>
          ) : (
            <div className="mt-6 flex items-start gap-3 rounded-xl border border-ink-600 bg-ink-800/60 p-4 text-sm text-cream-400">
              <Lock size={16} className="mt-0.5 shrink-0 text-cream-500" />
              {isOwner
                ? (lang === "en" ? "The full text of this story was not found at the source or at other free outlets. Open it on the site." : "Ceo tekst ove vesti nije pronađen ni na izvoru ni kod drugih besplatnih redakcija. Otvori je na sajtu.")
                : (lang === "en" ? "Read the full story on the publisher's website." : "Ceo tekst pročitaj na sajtu izvora.")}
            </div>
          )}
        </>
      )}
    </Sheet>
  );
}
