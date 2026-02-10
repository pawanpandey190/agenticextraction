/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-950': '#f8fafc', // Lightest slate
        'brand-900': '#f1f5f9', // Light slate
        'brand-800': '#e2e8f0', // Medium light slate
        'brand-primary': '#2563eb', // Dynamic Blue (slightly darker for contrast)
        'brand-secondary': '#059669', // Emerald (slightly darker for contrast)
        'brand-accent': '#7c3aed', // Purple (slightly darker for contrast)
        'slate-950': '#0f172a', // Dark text color
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(59, 130, 246, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(59, 130, 246, 0.6)' },
        }
      }
    },
  },
  plugins: [],
}
