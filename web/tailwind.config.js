/** @type {import('tailwindcss').Config} */
// FinNews paleta: crna i bela osnova, narandžasta kao jedini akcent, mint/crvena samo za rast i pad.
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // neutralna crna i bela - bez toplog tona
        ink: { 950: "#000000", 900: "#030303", 850: "#0A0A0A", 800: "#0F0F0F", 750: "#141414", 700: "#1A1A1A", 600: "#262626", 500: "#3A3A3A" },
        // burgundy - samo kao duboki ton
        wine: { 950: "#12040A", 900: "#1E0610", 800: "#33091A", 700: "#4F0D27", 600: "#7A1238", 500: "#A3194B", 400: "#C9325F", 300: "#E07A96" },
        // "gold" je istorijsko ime - jedini akcent je narandžasta
        gold: { 500: "#FF6A13", 400: "#FF8A3D", 300: "#FFB27A", 200: "#FFD3B0", 100: "#FFE9D9" },
        orange: { 300: "#FFB27A", 400: "#FF8A3D", 500: "#FF6A13" },
        mint: { 300: "#9CF0C8", 400: "#3DDC97", 500: "#22C47F", 600: "#15965F" },
        cream: { 50: "#FFFFFF", 100: "#F5F5F5", 200: "#E5E5E5", 300: "#C7C7C7", 400: "#A3A3A3", 500: "#7A7A7A" },
        up: "#3DDC97", down: "#FF4D5E", copper: "#FF8A3D",
      },
      fontFamily: {
        display: ["'Inter Tight'", "Inter", "system-ui", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        lift: "0 1px 0 rgba(255,255,255,.06) inset, 0 20px 40px -24px rgba(0,0,0,1)",
        glow: "0 1px 0 rgba(255,255,255,.06) inset, 0 20px 40px -24px rgba(0,0,0,1)",
        card: "0 1px 0 rgba(255,255,255,.04) inset",
      },
      keyframes: {
        sheen: { "0%": { backgroundPosition: "200% 0" }, "100%": { backgroundPosition: "-200% 0" } },
        marquee: { "0%": { transform: "translateX(0)" }, "100%": { transform: "translateX(-50%)" } },
        pulseDot: { "0%": { boxShadow: "0 0 0 0 rgba(61,220,151,.6)" }, "70%": { boxShadow: "0 0 0 8px rgba(61,220,151,0)" }, "100%": { boxShadow: "0 0 0 0 rgba(61,220,151,0)" } },
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
