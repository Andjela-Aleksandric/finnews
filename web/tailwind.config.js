/** @type {import('tailwindcss').Config} */
// FinNews paleta: topla crna, burgundy, crvena i zelena; zlatna (sand) samo za sitne detalje.
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // topla crna - kao pozadina loga
        ink: { 950: "#000000", 900: "#050304", 850: "#0B0809", 800: "#110C0E", 750: "#171113", 700: "#20171A", 600: "#2E2125", 500: "#4A3A3F" },
        // burgundy sa loga - glavni akcenat
        wine: { 950: "#1C050B", 900: "#300813", 800: "#4D0D20", 700: "#6E1230", 600: "#87183C", 500: "#A8204C", 400: "#E5487A", 300: "#FF8FB0", 200: "#FFC2D3" },
        // šampanj zlatna sa loga (ime "gold" ostaje u kodu)
        gold: { 500: "#E8475F", 400: "#F06A7E", 300: "#F5A3AE", 200: "#FAD0D5", 100: "#FDE8EA" },
        sand: { 400: "#E8C27A", 500: "#D9AE5F" },
        orange: { 300: "#F5A3AE", 400: "#F06A7E", 500: "#E8475F" },
        // rast i pad - prigušeni tonovi koji se slažu sa paletom
        mint: { 300: "#9EF0C0", 400: "#5FE39A", 500: "#38C97B", 600: "#22995A" },
        // krem sa slova F na logu
        cream: { 50: "#FFFBF6", 100: "#F6EDE4", 200: "#E6DBD1", 300: "#CDC1B7", 400: "#A99C93", 500: "#7E726B" },
        up: "#5FE39A", down: "#FF4D63", copper: "#F06A7E",
      },
      fontFamily: {
        display: ["'Inter Tight'", "Inter", "system-ui", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        lift: "0 1px 0 rgba(246,237,228,.05) inset",
        glow: "0 1px 0 rgba(246,237,228,.05) inset",
        wine: "none",
        gold: "none",
        mint: "none",
        card: "0 1px 0 rgba(246,237,228,.04) inset",
      },
      keyframes: {
        sheen: { "0%": { backgroundPosition: "200% 0" }, "100%": { backgroundPosition: "-200% 0" } },
        marquee: { "0%": { transform: "translateX(0)" }, "100%": { transform: "translateX(-50%)" } },
        pulseDot: { "0%": { boxShadow: "0 0 0 0 rgba(127,209,160,.6)" }, "70%": { boxShadow: "0 0 0 8px rgba(127,209,160,0)" }, "100%": { boxShadow: "0 0 0 0 rgba(127,209,160,0)" } },
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
