/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sovereign: {
          dark: '#0f172a',
          navy: '#1e293b',
          muted: '#64748b',
          border: '#e2e8f0',
          hover: '#f1f5f9',
          bg: '#f8fafc',
          card: '#ffffff',
          blue: {
            DEFAULT: '#1d4ed8',
            light: '#eff6ff',
            border: '#bfdbfe',
            dark: '#1e40af',
          },
          emerald: {
            DEFAULT: '#059669',
            light: '#ecfdf5',
            border: '#a7f3d0',
            dark: '#065f46',
          }
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        subtle: '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)',
        card: '0 2px 8px -2px rgba(15, 23, 42, 0.06), 0 1px 4px -1px rgba(15, 23, 42, 0.04)',
        hover: '0 4px 12px -2px rgba(15, 23, 42, 0.08), 0 2px 6px -1px rgba(15, 23, 42, 0.05)',
      }
    },
  },
  plugins: [],
}
