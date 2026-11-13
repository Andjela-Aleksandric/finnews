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
    const col = up ? "#3DDC97" : "#FF4D5E";
    const chart = createChart(ref.current, {
      height, autoSize: true,
      layout: { attributionLogo: false, background: { color: "transparent" }, textColor: "#8C8C8C", fontFamily: "Inter, system-ui, sans-serif", fontSize: 11 },
      grid: { vertLines: { visible: false }, horzLines: { color: mini ? "transparent" : "rgba(255,255,255,.06)" } },
      rightPriceScale: { visible: !mini, borderVisible: false, scaleMargins: { top: 0.12, bottom: 0.08 } },
      timeScale: { visible: !mini, borderVisible: false, fixLeftEdge: true, fixRightEdge: true },
      crosshair: { mode: CrosshairMode.Magnet, vertLine: { color: "rgba(255,255,255,.35)", style: LineStyle.Dashed, labelBackgroundColor: "#262626" },
        horzLine: { color: "rgba(255,255,255,.2)", style: LineStyle.Dashed, labelBackgroundColor: "#262626" } },
      handleScroll: !mini, handleScale: !mini,
      localization: valueFormat ? { priceFormatter: valueFormat } : undefined,
    });
    const area = chart.addAreaSeries({ lineColor: col, lineWidth: 1.5, topColor: up ? "rgba(61,220,151,.18)" : "rgba(255,77,94,.18)",
      bottomColor: "rgba(0,0,0,0)", priceLineVisible: !mini, lastValueVisible: !mini, crosshairMarkerRadius: 5,
      crosshairMarkerBorderColor: "#0B0909", crosshairMarkerBackgroundColor: col });
    area.setData(data);
    if (sma && data.length > 60) {
      for (const [n, c] of [[50, "#FF6A13"], [200, "#A3A3A3"]]) {
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
