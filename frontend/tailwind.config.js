/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12151C",       // app shell background
        paper: "#F7F5F0",     // content surface
        graphite: "#3A3F4B",  // body text on paper
        mist: "#9AA0AC",      // muted/secondary text
        signal: "#4F7CFF",    // primary interactive accent
        line: "#E4E1D8",      // hairline dividers on paper
        // Model "channel" colors — assigned consistently to a model across
        // every visualization (leaderboard, heatmap, diversity map) so its
        // identity is trackable at a glance without re-reading labels.
        channel: {
          1: "#E8734A", // amber-orange
          2: "#4F7CFF", // signal blue
          3: "#33A373", // green
          4: "#B072D9", // violet
          5: "#D9B23C", // gold
          6: "#4AAFC7", // teal
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
