/** @type {import('tailwindcss').Config} */
// FinNews paleta: skoro crna osnova, jarka narandžasta, živa burgundy i mint zelena.
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#000000", 900: "#040404", 850: "#09090A", 800: "#0F0E0F", 750: "#151315", 700: "#1D191B", 600: "#2B2427", 500: "#463C40" },
        wine: { 950: "#1C0410", 900: "#33061A", 800: "#560B2A", 700: "#850F3C", 600: "#B3154E", 500: "#E5245F", 400: "#FF4F82", 300: "#FF94B2" },
        // "gold" je u kodu istorijsko ime - sada je to jarka narandžasta
        gold: { 500: "#FF7A1A", 400: "#FF9A3D", 300: "#FFBE7D", 200: "#FFD9B0", 100: "#FFEBD6" },
        orange: { 300: "#FFBE7D", 400: "#FF9A3D", 500: "#FF7A1A" },
        mint: { 300: "#A8FFD8", 400: "#4DF5A8", 500: "#1FD98A", 600: "#12A86A" },
        cream: { 50: "#FFFFFF", 100: "#FFF8F3", 200: "#F2EAE5", 300: "#E0D6D1", 400: "#C2B7B2", 500: "#968C88" },
        up: "#4DF5A8", down: "#FF5577", copper: "#FF8A2B",
      },
      fontFamily: {
        display: ["'Playfair Display'", "Georgia", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 16px 44px -18px rgba(255,122,26,.55)",
        wine: "0 16px 44px -18px rgba(229,36,95,.6)",
        mint: "0 14px 40px -18px rgba(77,245,168,.45)",
        card: "0 1px 0 rgba(255,255,255,.05) inset, 0 24px 48px -32px rgba(0,0,0,1)",
      },
      keyframes: {
        sheen: { "0%": { backgroundPosition: "200% 0" }, "100%": { backgroundPosition: "-200% 0" } },
        marquee: { "0%": { transform: "translateX(0)" }, "100%": { transform: "translateX(-50%)" } },
        pulseDot: { "0%": { boxShadow: "0 0 0 0 rgba(77,245,168,.65)" }, "70%": { boxShadow: "0 0 0 8px rgba(77,245,168,0)" }, "100%": { boxShadow: "0 0 0 0 rgba(77,245,168,0)" } },
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
