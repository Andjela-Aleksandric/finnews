export const SECTIONS = {
  fin: ["Vesti", "Centralne banke i makro", "Analize i blogovi", "Srbija i region"],
  comp: ["Kompanije"], srb: ["Srbija", "Srbija i region"], svet: ["Svet"],
};
export const PERIODS = [1, 7, 30, 60, 90, 180];
export const periodOpts = (t) => PERIODS.map((p) => [p, t("d" + p)]);
export function themeTrend(cnt, prev, lang) {
  if (!prev) return { txt: lang === "en" ? "new" : "novo", up: true };
  const ch = cnt / prev - 1;
  return { txt: `${ch >= 0 ? "▲" : "▼"}${Math.abs(Math.round(ch * 100))}%`, up: ch >= 0 };
}
