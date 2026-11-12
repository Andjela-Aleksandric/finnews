/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#060404", 900: "#090707", 850: "#100B0C", 800: "#150F11", 750: "#1C1418", 700: "#251B1F", 600: "#3A2B30", 500: "#4E3A40" },
        wine: { 950: "#2E0814", 900: "#521023", 800: "#741936", 700: "#8F1F3F", 600: "#B42F51", 500: "#DE4A6E", 400: "#EC7391", 300: "#F5A9BC" },
        gold: { 500: "#E6BC74", 400: "#F0CF93", 300: "#F7E2BC" },
        cream: { 50: "#FFFBF7", 100: "#FAF2EA", 200: "#EEE2D9", 300: "#DACBC4", 400: "#BCA9AC", 500: "#94817F" },
        up: "#7FDB97", down: "#FF7A90", copper: "#D9A47F",
      },
      fontFamily: {
        display: ["'Playfair Display'", "Georgia", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 18px 50px -20px rgba(222,74,110,.7)",
        card: "0 1px 0 rgba(255,255,255,.04) inset, 0 20px 40px -30px rgba(0,0,0,.9)",
      },
      keyframes: {
        sheen: { "0%": { backgroundPosition: "200% 0" }, "100%": { backgroundPosition: "-200% 0" } },
        marquee: { "0%": { transform: "translateX(0)" }, "100%": { transform: "translateX(-50%)" } },
        pulseDot: { "0%": { boxShadow: "0 0 0 0 rgba(143,203,155,.6)" }, "70%": { boxShadow: "0 0 0 8px rgba(143,203,155,0)" }, "100%": { boxShadow: "0 0 0 0 rgba(143,203,155,0)" } },
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
