import { useState } from "react";
import { CheckCircle2, ExternalLink, Eye, EyeOff, KeyRound, LogOut, Smartphone } from "lucide-react";
import { useLang, useT } from "../lib/i18n";
import { cls, timeAgo } from "../lib/fmt";
import { getMeta } from "../lib/data";
import { owner, testOwner } from "../lib/github";
import { LangSwitch, PageHead } from "../components/Shell";
import { useApp } from "../components/News";
import { Card, SectionTitle, toast } from "../components/ui";

export default function SettingsPage() {
  const { lang } = useLang();
  const t = useT();
  const app = useApp();
  const meta = getMeta() || {};
  const cur = owner.get();
  const [repo, setRepo] = useState((cur && cur.repo) || meta.data_repo || "");
  const [token, setToken] = useState((cur && cur.token) || "");
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const L = (a, b) => (lang === "en" ? b : a);
  const connect = async () => {
    setBusy(true);
    try { await testOwner({ repo: repo.trim(), token: token.trim() }); owner.set({ repo: repo.trim(), token: token.trim() }); toast(L("Povezano ✓ - portfolio i celi tekstovi su dostupni", "Connected ✓ - portfolio and full texts are available")); setTimeout(() => location.reload(), 900); }
    catch (e) { toast(e.message, "err"); }
    setBusy(false);
  };
  return (
    <div className="max-w-3xl">
      <PageHead title={t("settings")} />
      <SectionTitle>{L("Prikaz", "Display")}</SectionTitle>
      <Card hover={false} className="divide-y divide-ink-600/70">
        <div className="flex items-center justify-between gap-4 p-4"><span>{t("language")}</span><LangSwitch /></div>
        <label className="flex cursor-pointer items-center justify-between gap-4 p-4">
          <span>{L("Prikazuj vesti na originalnom jeziku (bez prevoda)", "Show stories in their original language")}</span>
          <button onClick={() => app.setOrig(!app.orig)} className={cls("relative h-6 w-11 rounded-full transition-colors", app.orig ? "bg-wine-600" : "bg-ink-600")}>
            <span className={cls("absolute top-0.5 h-5 w-5 rounded-full bg-cream-50 shadow transition-all", app.orig ? "left-[22px]" : "left-0.5")} />
          </button>
        </label>
      </Card>

      <div className="mt-10"><SectionTitle>{L("Tvoj portfolio i celi tekstovi", "Your portfolio and full texts")}</SectionTitle></div>
      <Card hover={false} className="p-5">
        {cur ? (
          <div className="flex flex-wrap items-center gap-3">
            <CheckCircle2 className="text-up" size={20} />
            <div className="flex-1"><div className="font-semibold">{L("Povezano na ovom uređaju", "Connected on this device")}</div><div className="font-mono text-xs text-cream-400">{cur.repo}</div></div>
            <button onClick={() => { owner.clear(); location.reload(); }} className="btn"><LogOut size={15} />{L("Odjavi", "Disconnect")}</button>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-cream-300">{L("Portfolio i celi tekstovi vesti čuvaju se u tvom privatnom GitHub repozitorijumu i vidiš ih samo ti. Poveži ih jednom na svakom uređaju - ključ ostaje samo u ovom pregledaču.",
              "Your portfolio and full article texts live in your private GitHub repository and only you can see them. Connect once per device - the key stays only in this browser.")}</p>
            <label className="block"><span className="stat-label mb-1.5 block">{L("Privatni repozitorijum", "Private repository")}</span>
              <input className="field font-mono" value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="korisnik/finnews-data" /></label>
            <label className="block"><span className="stat-label mb-1.5 block">{L("Ključ (GitHub token)", "Key (GitHub token)")}</span>
              <div className="relative"><input className="field pr-10 font-mono" type={show ? "text" : "password"} value={token} onChange={(e) => setToken(e.target.value)} placeholder="github_pat_..." />
                <button onClick={() => setShow((x) => !x)} className="absolute right-3 top-1/2 -translate-y-1/2 text-cream-400">{show ? <EyeOff size={16} /> : <Eye size={16} />}</button></div></label>
            <button disabled={busy || !repo || !token} onClick={connect} className={cls("btn btn-primary", (busy || !repo || !token) && "pointer-events-none opacity-40")}><KeyRound size={15} />{busy ? "..." : L("Poveži", "Connect")}</button>
            <div className="rounded-xl border border-ink-600 bg-ink-850/60 p-4 text-sm text-cream-300">
              <div className="mb-2 font-semibold text-cream-100">{L("Kako dobiti ključ (jednom, 1 minut)", "How to get a key (once, 1 minute)")}</div>
              <ol className="list-decimal space-y-1 pl-5">
                <li>{L("Otvori", "Open")} <a className="text-wine-400 underline" href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noreferrer">github.com → Fine-grained token <ExternalLink size={11} className="inline" /></a></li>
                <li>{L("Ime: FinNews · Rok: 1 godina · Repository access: Only select → ", "Name: FinNews · Expiration: 1 year · Repository access: Only select → ")}<b>{repo || "finnews-data"}</b></li>
                <li>{L("Permissions → Repository → Contents: ", "Permissions → Repository → Contents: ")}<b>Read and write</b></li>
                <li>{L("Generate token, kopiraj ga i nalepi ovde.", "Generate token, copy it and paste it here.")}</li>
              </ol>
            </div>
          </div>
        )}
      </Card>

      <div className="mt-10"><SectionTitle>{t("install")}</SectionTitle></div>
      <Card hover={false} className="flex gap-4 p-5 text-sm text-cream-300">
        <Smartphone className="shrink-0 text-wine-400" />
        <div>
          <b className="text-cream-100">iPhone:</b> {L("otvori sajt u Safari-ju → Share → Add to Home Screen.", "open the site in Safari → Share → Add to Home Screen.")}<br />
          <b className="text-cream-100">Android:</b> {L("Chrome → meni ⋮ → Install app.", "Chrome → ⋮ menu → Install app.")}<br />
          <span className="text-cream-400">{L("Otvara se preko celog ekrana, kao prava aplikacija.", "It opens full-screen, like a real app.")}</span>
        </div>
      </Card>

      <div className="mt-10 text-xs text-cream-500">
        {L("Podaci se osvežavaju automatski na svakih 30 minuta.", "Data refreshes automatically every 30 minutes.")} {t("updated")} {timeAgo(meta.generated, lang)} · {(meta.sources || []).length} {t("sources")}. {L("Grafikoni:", "Charts:")} <a className="underline" href="https://www.tradingview.com/" target="_blank" rel="noreferrer">TradingView Lightweight Charts</a>.
        {" "}{L("Sadržaj služi za informisanje i istraživanje, a ne kao investicioni savet.", "Content is for information and research, not investment advice.")}
      </div>
    </div>
  );
}
