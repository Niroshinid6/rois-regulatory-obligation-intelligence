/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#0a0f1d',
          900: '#0f172a',
          800: '#1e293b',
          700: '#334155',
        },
        teal: {
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
        rois: {
          surface: '#f8fafc',
          border: '#e2e8f0',
          accent: '#0d9488',
          accentLight: '#f0fdfa',
          accentDark: '#0f766e',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}
