/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#020202", 900: "#050405", 850: "#0A0809", 800: "#110B0D", 750: "#1B0E12", 700: "#2A1219", 600: "#45202B", 500: "#68404A" },
        wine: { 950: "#22030D", 900: "#390516", 800: "#5A0922", 700: "#840D31", 600: "#B51443", 500: "#E02B57", 400: "#FF4F76", 300: "#FF9CB3" },
        gold: { 500: "#FF6A00", 400: "#FF861C", 300: "#FFB15C" },
        cream: { 50: "#FFFEFC", 100: "#FFF7F0", 200: "#F5E8DF", 300: "#E7D2C6", 400: "#D2BEB3", 500: "#A99690" },
        up: "#7CF59A", down: "#FF687F", copper: "#FF8A24", mint: { 300: "#B8FFC6", 400: "#7CF59A", 500: "#38D979" }, orange: { 300: "#FFB15C", 400: "#FF861C", 500: "#FF6A00" },
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
