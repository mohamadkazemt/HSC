/** Tailwind config for build tools; for CDN we also set window.tailwind.config in base.html */
module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './static/js/**/*.js'
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#5850EC',
          700: '#4C51E0',
          800: '#4338CA',
          900: '#3730A3'
        },
        accent: {
          50: '#ecfeff',
          100: '#cffafe',
          200: '#a5f3fc',
          300: '#67e8f9',
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
          700: '#0e7490',
          800: '#155e75',
          900: '#164e63'
        },
        success: {
          50: '#ecfdf5', 100: '#d1fae5', 200: '#a7f3d0', 300: '#6ee7b7', 400: '#34d399', 500: '#10b981', 600: '#059669', 700: '#047857', 800: '#065f46', 900: '#064e3b'
        },
        warning: {
          50: '#fff7ed', 100: '#ffedd5', 200: '#fed7aa', 300: '#fdba74', 400: '#fb923c', 500: '#f97316', 600: '#ea580c', 700: '#c2410c', 800: '#9a3412', 900: '#7c2d12'
        },
        danger: {
          50: '#fef2f2', 100: '#fee2e2', 200: '#fecaca', 300: '#fca5a5', 400: '#f87171', 500: '#ef4444', 600: '#dc2626', 700: '#b91c1c', 800: '#991b1b', 900: '#7f1d1d'
        },
        neutral: {
          50: '#f9fafb', 100: '#f3f4f6', 200: '#e5e7eb', 300: '#d1d5db', 400: '#9ca3af', 500: '#6b7280', 600: '#4b5563', 700: '#374151', 800: '#1f2937', 900: '#111827'
        }
      },
      boxShadow: {
        soft: '0 2px 6px rgba(0,0,0,0.06), 0 8px 24px rgba(0,0,0,0.08)',
        glow: '0 0 0 2px rgba(99,102,241,0.15), 0 8px 24px rgba(99,102,241,0.35)'
      },
      borderRadius: { xl: '0.9rem' }
    }
  },
  plugins: []
};
