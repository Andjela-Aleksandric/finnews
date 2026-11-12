import { useEffect, useRef } from "react";
import { createChart, CrosshairMode, LineStyle } from "lightweight-charts";

// profesionalni grafikon cene: prelaskom (ili prstom) vidiš datum i cenu
export default function PriceChart({ data, height = 340, sma = false, mini = false, valueFormat, days }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!ref.current || !data || data.length < 2) return;
    const cut = days ? new Date(Date.now() - days * 864e5).toISOString().slice(0, 10) : null;
    const vis = cut ? data.filter((d) => d.time >= cut) : data;
    const up = (vis[vis.length - 1] || data[data.length - 1]).value >= (vis[0] || data[0]).value;
    const col = up ? "#7FDB97" : "#FF7A90";
    const chart = createChart(ref.current, {
      height, autoSize: true,
      layout: { attributionLogo: false, background: { color: "transparent" }, textColor: "#A8979A", fontFamily: "Inter, system-ui, sans-serif", fontSize: 11 },
      grid: { vertLines: { visible: false }, horzLines: { color: mini ? "transparent" : "rgba(62,48,52,.45)" } },
      rightPriceScale: { visible: !mini, borderVisible: false, scaleMargins: { top: 0.12, bottom: 0.08 } },
      timeScale: { visible: !mini, borderVisible: false, fixLeftEdge: true, fixRightEdge: true },
      crosshair: { mode: CrosshairMode.Magnet, vertLine: { color: "rgba(214,176,114,.6)", style: LineStyle.Dashed, labelBackgroundColor: "#7A1A33" },
        horzLine: { color: "rgba(214,176,114,.4)", style: LineStyle.Dashed, labelBackgroundColor: "#7A1A33" } },
      handleScroll: !mini, handleScale: !mini,
      localization: valueFormat ? { priceFormatter: valueFormat } : undefined,
    });
    const area = chart.addAreaSeries({ lineColor: col, lineWidth: 2, topColor: up ? "rgba(127,219,151,.35)" : "rgba(255,122,144,.35)",
      bottomColor: "rgba(0,0,0,0)", priceLineVisible: !mini, lastValueVisible: !mini, crosshairMarkerRadius: 5,
      crosshairMarkerBorderColor: "#0B0909", crosshairMarkerBackgroundColor: col });
    area.setData(data);
    if (sma && data.length > 60) {
      for (const [n, c] of [[50, "#E6BC74"], [200, "#C99A7A"]]) {
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
    return () => chart.remove();
  }, [data, height, sma, mini, valueFormat, days]);
  return <div ref={ref} style={{ height }} className="w-full" />;
}
