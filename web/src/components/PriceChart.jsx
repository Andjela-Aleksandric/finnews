import { useEffect, useRef, useState } from "react";
import { createChart, CrosshairMode, LineStyle, TrackingModeExitMode } from "lightweight-charts";
import { useLang } from "../lib/i18n";

// profesionalni grafikon cene: prelaskom (ili prstom) vidiš datum i cenu
const fmtDate = (t, lang) => {
  const d = typeof t === "string" ? new Date(t + "T00:00:00") : new Date((t.year ? Date.UTC(t.year, t.month - 1, t.day) : t * 1000));
  return d.toLocaleDateString(lang === "en" ? "en-GB" : "sr-Latn-RS", { day: "numeric", month: "short", year: "numeric" });
};

export default function PriceChart({ data, height = 340, sma = false, mini = false, valueFormat, days }) {
  const ref = useRef(null);
  const { lang } = useLang();
  const [hover, setHover] = useState(null);
  const [pin, setPin] = useState(null);
  const pinRef = useRef(null);
  pinRef.current = pin;
  useEffect(() => { setPin(null); setHover(null); }, [data, days]);
  useEffect(() => {
    if (!ref.current || !data || data.length < 2) return;
    const cut = days ? new Date(Date.now() - days * 864e5).toISOString().slice(0, 10) : null;
    const vis = cut ? data.filter((d) => d.time >= cut) : data;
    const up = (vis[vis.length - 1] || data[data.length - 1]).value >= (vis[0] || data[0]).value;
    const col = up ? "#5FE39A" : "#FF4D63";
    const chart = createChart(ref.current, {
      height, autoSize: true,
      layout: { attributionLogo: false, background: { color: "transparent" }, textColor: "#A99C93", fontFamily: "Inter, system-ui, sans-serif", fontSize: 11 },
      grid: { vertLines: { visible: false }, horzLines: { color: mini ? "transparent" : "rgba(255,255,255,.06)" } },
      rightPriceScale: { visible: !mini, borderVisible: false, scaleMargins: { top: 0.12, bottom: 0.08 } },
      timeScale: { visible: !mini, borderVisible: false, fixLeftEdge: true, fixRightEdge: true },
      crosshair: { mode: CrosshairMode.Magnet, vertLine: { color: "rgba(255,255,255,.35)", style: LineStyle.Dashed, labelBackgroundColor: "#5A1226" },
        horzLine: { color: "rgba(255,255,255,.2)", style: LineStyle.Dashed, labelBackgroundColor: "#5A1226" } },
      handleScroll: mini ? false : { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: false, vertTouchDrag: false },
      handleScale: mini ? false : { axisPressedMouseMove: true, mouseWheel: true, pinch: true },
      trackingMode: { exitMode: TrackingModeExitMode.OnNextTap },
      localization: valueFormat ? { priceFormatter: valueFormat } : undefined,
    });
    const area = chart.addAreaSeries({ lineColor: col, lineWidth: 1.5, topColor: up ? "rgba(61,220,151,.18)" : "rgba(255,77,94,.18)",
      bottomColor: "rgba(0,0,0,0)", priceLineVisible: !mini, lastValueVisible: !mini, crosshairMarkerRadius: 5,
      crosshairMarkerBorderColor: "#0B0909", crosshairMarkerBackgroundColor: col });
    area.setData(data);
    if (sma && data.length > 60) {
      for (const [n, c] of [[50, "#E8475F"], [200, "#A99C93"]]) {
        const s = [];
        let sum = 0;
        for (let i = 0; i < data.length; i++) {
          sum += data[i].value;
          if (i >= n) sum -= data[i - n].value;
          if (i >= n - 1) s.push({ time: data[i].time, value: sum / n });
        }
        const l = chart.addLineSeries({ color: c, lineWidth: 1, lineStyle: LineStyle.Dashed, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
        l.setData(s);
      }
    }
    if (cut && vis.length > 1) chart.timeScale().setVisibleRange({ from: vis[0].time, to: vis[vis.length - 1].time });
    else chart.timeScale().fitContent();
    if (!mini) {
      const pick = (param) => {
        const v = param && param.time && param.seriesData && param.seriesData.get(area);
        return v ? { time: param.time, value: v.value } : null;
      };
      chart.subscribeCrosshairMove((param) => setHover(pick(param)));
      chart.subscribeClick((param) => {
        const pt = pick(param);
        if (!pt) return;
        setPin(pt);
      });
    }
    return () => chart.remove();
  }, [data, height, sma, mini, valueFormat, days]);
  if (mini) return <div ref={ref} style={{ height }} className="w-full" />;
  const en = lang === "en";
  const fmtV = (v) => (valueFormat ? valueFormat(v) : v.toFixed(2));
  const lastPt = data && data.length ? data[data.length - 1] : null;
  const cur = hover || lastPt;
  const from = pin;
  const chg = from && cur && from.value ? cur.value / from.value - 1 : null;
  return (
    <div className="relative">
      <div className="chart-readout mb-2 flex min-h-[44px] flex-wrap items-baseline gap-x-3 gap-y-1 rounded-xl px-3 py-2 text-sm">
        {cur && <span className="text-cream-400">{fmtDate(cur.time, lang)}</span>}
        {cur && <b className="font-mono text-base text-cream-50">{fmtV(cur.value)}</b>}
        {from && chg !== null && (
          <span className={"font-mono font-semibold " + (chg >= 0 ? "text-up" : "text-down")}>
            {chg >= 0 ? "+" : ""}{(chg * 100).toFixed(1).replace(".", en ? "." : ",")}% <span className="font-sans font-normal text-cream-400">{en ? "since" : "od"} {fmtDate(from.time, lang)}</span>
          </span>
        )}
        <span className="ml-auto text-xs text-cream-500">
          {from ? <button type="button" onClick={() => setPin(null)} className="underline decoration-dotted underline-offset-4 hover:text-cream-100">{en ? "Clear start point" : "Poništi početnu tačku"}</button>
            : (en ? "Tap a point to measure the change from it" : "Dodirni tačku da izmeriš promenu od nje")}
        </span>
      </div>
      <div ref={ref} style={{ height }} className="w-full touch-pan-y" />
    </div>
  );
}
