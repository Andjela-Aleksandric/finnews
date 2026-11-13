/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#030303", 900: "#070607", 850: "#0D0B0C", 800: "#121011", 750: "#191416", 700: "#21191C", 600: "#382A2F", 500: "#514047" },
        wine: { 950: "#260711", 900: "#430B1D", 800: "#66132D", 700: "#8D1738", 600: "#B51F45", 500: "#D93659", 400: "#F05A79", 300: "#FF9DB0" },
        gold: { 500: "#FF8A24", 400: "#FFAA45", 300: "#FFD08A" },
        cream: { 50: "#FFFDF9", 100: "#FFF4E8", 200: "#F3E2D5", 300: "#DEC9BB", 400: "#C5AEA4", 500: "#97847D" },
        up: "#8EF0A7", down: "#FF7384", copper: "#FF9B52", mint: { 300: "#B3F4C1", 400: "#8EF0A7", 500: "#51D982" }, orange: { 300: "#FFD08A", 400: "#FFAA45", 500: "#FF8A24" },
      },
      fontFamily: {
        display: ["'Playfair Display'", "Georgia", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 18px 50px -20px rgba(255,138,36,.55)",
        card: "0 1px 0 rgba(255,255,255,.04) inset, 0 20px 40px -30px rgba(0,0,0,.9)",
      },
      keyframes: {
        sheen: { "0%": { backgroundPosition: "200% 0" }, "100%": { backgroundPosition: "-200% 0" } },
        marquee: { "0%": { transform: "translateX(0)" }, "100%": { transform: "translateX(-50%)" } },
        pulseDot: { "0%": { boxShadow: "0 0 0 0 rgba(142,240,167,.6)" }, "70%": { boxShadow: "0 0 0 8px rgba(142,240,167,0)" }, "100%": { boxShadow: "0 0 0 0 rgba(143,203,155,0)" } },
        draw: { to: { strokeDashoffset: "0" } },
      },
      animation: {
        sheen: "sheen 8s linear infinite",
        marquee: "marquee 60s linear infinite",
        pulseDot: "pulseDot 2.2s infinite",
      },
    },
  },
  plugins: [],
};
