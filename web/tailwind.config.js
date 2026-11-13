/** @type {import('tailwindcss').Config} */
// FinNews paleta sa loga: burgundy, šampanj zlatna i krem na toploj crnoj; zelena i ružičasta samo za rast i pad.
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // topla crna - kao pozadina loga
        ink: { 950: "#000000", 900: "#050304", 850: "#0B0809", 800: "#110C0E", 750: "#171113", 700: "#20171A", 600: "#2E2125", 500: "#4A3A3F" },
        // burgundy sa loga - glavni akcenat
        wine: { 950: "#1C050B", 900: "#300813", 800: "#4D0D20", 700: "#6E1230", 600: "#A11D45", 500: "#C8285A", 400: "#E5487A", 300: "#FF8FB0", 200: "#FFC2D3" },
        // šampanj zlatna sa loga (ime "gold" ostaje u kodu)
        gold: { 500: "#F2C46B", 400: "#F7D38A", 300: "#FBE3B0", 200: "#FDEFD2", 100: "#FFF8EA" },
        orange: { 300: "#FBE3B0", 400: "#F7D38A", 500: "#F2C46B" },
        // rast i pad - prigušeni tonovi koji se slažu sa paletom
        mint: { 300: "#A8F0C6", 400: "#6FE3A0", 500: "#45CC80", 600: "#2E9E5E" },
        // krem sa slova F na logu
        cream: { 50: "#FFFBF6", 100: "#F6EDE4", 200: "#E6DBD1", 300: "#CDC1B7", 400: "#A99C93", 500: "#7E726B" },
        up: "#6FE3A0", down: "#FF5C7A", copper: "#F7D38A",
      },
      fontFamily: {
        display: ["'Inter Tight'", "Inter", "system-ui", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        lift: "0 1px 0 rgba(246,237,228,.06) inset, 0 22px 44px -26px rgba(0,0,0,1)",
        glow: "0 18px 44px -18px rgba(200,40,90,.6)",
        wine: "0 10px 30px -10px rgba(200,40,90,.75)",
        gold: "0 8px 26px -12px rgba(242,196,107,.55)",
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
