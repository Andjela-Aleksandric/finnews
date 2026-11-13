import { useEffect, useRef } from "react";
import { createChart, CrosshairMode, LineStyle } from "lightweight-charts";

const COLORS = ["#D9B474", "#C4405F", "#F6EDE4", "#7FD1A0"];

export default function CompareChart({ items, height = 300, lang = "sr" }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!ref.current || !items || !items.length) return;
    const chart = createChart(ref.current, {
      height, autoSize: true,
      layout: { attributionLogo: false, background: { color: "transparent" }, textColor: "#A99C93", fontFamily: "Inter, system-ui, sans-serif", fontSize: 11 },
      grid: { vertLines: { visible: false }, horzLines: { color: "rgba(255,255,255,.06)" } },
      rightPriceScale: { borderVisible: false, scaleMargins: { top: 0.12, bottom: 0.08 } },
      timeScale: { borderVisible: false, fixLeftEdge: true, fixRightEdge: true },
      crosshair: { mode: CrosshairMode.Magnet },
      handleScroll: true, handleScale: true,
      localization: { priceFormatter: (v) => `${v >= 0 ? "+" : ""}${v.toFixed(1)}%` },
    });
    for (const [i, item] of items.entries()) {
      const first = item.data.find((p) => p.value > 0)?.value;
      if (!first) continue;
      const line = chart.addLineSeries({ color: COLORS[i % COLORS.length], lineWidth: 2, title: item.ticker, priceLineVisible: false, lastValueVisible: true, crosshairMarkerRadius: 4 });
      line.setData(item.data.filter((p) => p.value > 0).map((p) => ({ time: p.time, value: (p.value / first - 1) * 100 })));
    }
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [items, height, lang]);
  return <div ref={ref} style={{ height }} className="w-full" />;
}
