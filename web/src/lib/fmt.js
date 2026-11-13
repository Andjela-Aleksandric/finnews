export const PALETTE = ["#FF6A13", "#F5F5F5", "#3DDC97", "#8C8C8C", "#C9325F", "#FFB27A", "#5E5E5E", "#BFBFBF"];
// izvori i sektori su neutralni - boja je rezervisana za akcenat i rast/pad
const SOURCE_TONES = ["#E5E5E5", "#C7C7C7", "#A3A3A3"];
export function srcColor(name = "") {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return SOURCE_TONES[h % SOURCE_TONES.length];
}
export function num(v, d = 2, lang = "sr") {
  if (v === null || v === undefined || Number.isNaN(v)) return "-";
  return new Intl.NumberFormat(lang === "en" ? "en-US" : "de-DE", { minimumFractionDigits: d, maximumFractionDigits: d }).format(v);
}
export const pct = (v, d = 1, lang = "sr", signed = true) =>
  v === null || v === undefined || Number.isNaN(v) ? "-" : (signed && v > 0 ? "+" : "") + num(v * 100, d, lang) + "%";
export const eur = (v, d = 0, lang = "sr") => (v === null || v === undefined ? "-" : lang === "en" ? "€" + num(v, d, lang) : num(v, d, lang) + " €");
export function big(v, lang = "sr") {
  if (!v) return "-";
  const u = lang === "en" ? [[1e12, "T"], [1e9, "B"], [1e6, "M"]] : [[1e12, " bil."], [1e9, " mlrd."], [1e6, " mil."]];
  for (const [d, s] of u) if (v >= d) return num(v / d, 1, lang) + s;
  return num(v, 0, lang);
}
export function timeAgo(iso, lang = "sr") {
  if (!iso) return "";
  const dt = new Date(iso);
  const m = (Date.now() - dt.getTime()) / 60000;
  if (m < 60) return lang === "en" ? `${Math.max(1, Math.round(m))} min ago` : `pre ${Math.max(1, Math.round(m))} min`;
  if (m < 60 * 24) return lang === "en" ? `${Math.round(m / 60)} h ago` : `pre ${Math.round(m / 60)} h`;
  const sameYear = dt.getFullYear() === new Date().getFullYear();
  return dt.toLocaleDateString(lang === "en" ? "en-GB" : "sr-Latn-RS", { day: "numeric", month: "short", ...(sameYear ? {} : { year: "numeric" }) });
}
export const dateLong = (d, lang = "sr") =>
  d.toLocaleDateString(lang === "en" ? "en-GB" : "sr-Latn-RS", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
export const cls = (...a) => a.filter(Boolean).join(" ");
export const upDown = (v) => (v === null || v === undefined ? "text-cream-400" : v >= 0 ? "text-up" : "text-down");

// tekst vesti na izabranom jeziku (original ako je vest već na tom jeziku ili ako je uključen prikaz originala)
export function itTitle(it, lang, orig = false) {
  if (!it) return "";
  if (orig || it.l === lang) return it.t;
  return (it.tr && it.tr[lang] && it.tr[lang][0]) || it.t;
}
export function itSum(it, lang, orig = false) {
  if (!it) return "";
  if (orig || it.l === lang) return it.d || "";
  return (it.tr && it.tr[lang] && it.tr[lang][1]) || it.d || "";
}
