/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0b0f19',
        card: '#151d30',
        cyan: '#06b6d4',
        emerald: '#10b981',
        amber: '#f59e0b',
        crimson: '#e11d48'
      }
    },
  },
  plugins: [],
}
