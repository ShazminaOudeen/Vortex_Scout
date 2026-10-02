import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        scout: {
          bg: "#FAFAFA", // canvas
          surface: "#FFFFFF", // cards
          border: "#E4E4E7",
          foreground: "#09090B",
          muted: "#71717A",
          // semantic
          alert: "#E11D48", // critical phantom voids
          alertBg: "#FFE4E6",
          success: "#10B981", // restocked
          successBg: "#D1FAE5",
          warning: "#F59E0B", // damaged / write-off
          ai: "#7C3AED", // Gemini agent cards
          aiBg: "#F5F3FF",
          // dark mode for /simulate
          night: "#09090B",
          violet: "#8B5CF6",
          neon: "#F43F5E",
          cyan: "#06B6D4",
        },
      },
    },
  },
  plugins: [],
};
export default config;
