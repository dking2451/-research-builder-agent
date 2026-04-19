import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

export default {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0b1220",
          900: "#111b2e",
          800: "#1b2a45",
          700: "#2a3f63",
        },
        paper: {
          50: "#f7f8fb",
          100: "#eef1f7",
        },
        accent: { 600: "#2563eb", 700: "#1d4ed8" },
      },
    },
  },
  plugins: [typography],
} satisfies Config;
