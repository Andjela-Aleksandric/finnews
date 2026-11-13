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
        wine: { 950: "#1A0509", 900: "#2B0811", 800: "#420E1C", 700: "#5A1226", 600: "#7A1A33", 500: "#9E2443", 400: "#C4405F", 300: "#E58AA0" },
        // šampanj zlatna sa loga (ime "gold" ostaje u kodu)
        gold: { 500: "#D9B474", 400: "#E4C690", 300: "#EED8AE", 200: "#F4E6CA", 100: "#FAF2E4" },
        orange: { 300: "#EED8AE", 400: "#E4C690", 500: "#D9B474" },
        // rast i pad - prigušeni tonovi koji se slažu sa paletom
        mint: { 300: "#B5E6C8", 400: "#7FD1A0", 500: "#5DBB84", 600: "#3F9466" },
        // krem sa slova F na logu
        cream: { 50: "#FFFBF6", 100: "#F6EDE4", 200: "#E6DBD1", 300: "#CDC1B7", 400: "#A99C93", 500: "#7E726B" },
        up: "#7FD1A0", down: "#F0607A", copper: "#E4C690",
      },
      fontFamily: {
        display: ["'Inter Tight'", "Inter", "system-ui", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        lift: "0 1px 0 rgba(246,237,228,.06) inset, 0 22px 44px -26px rgba(0,0,0,1)",
        glow: "0 18px 44px -20px rgba(158,36,67,.55)",
        wine: "0 10px 30px -12px rgba(158,36,67,.75)",
        gold: "0 10px 30px -14px rgba(217,180,116,.5)",
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
