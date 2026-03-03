/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Deep editorial palette
        ink: {
          50:  '#f5f3f0',
          100: '#e8e4de',
          200: '#d0c9be',
          300: '#b5aa9a',
          400: '#9a8d7a',
          500: '#7d7062',
          600: '#635a4e',
          700: '#4a433b',
          800: '#312d27',
          900: '#1a1713',
          950: '#0e0c09',
        },
        cream: '#f7f3ed',
        parchment: '#ede7db',
        dust:  '#c9bfb0',
        terracotta: {
          400: '#e8849a',
          500: '#d6637e',
          600: '#c04d6a',
        },
        sage: {
          400: '#8a9e88',
          500: '#728f6f',
        }
      },
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        body:    ['"DM Sans"', 'system-ui', 'sans-serif'],
        mono:    ['"DM Mono"', 'monospace'],
      },
      animation: {
        'fade-up':    'fadeUp 0.5s ease forwards',
        'fade-in':    'fadeIn 0.3s ease forwards',
        'slide-in':   'slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'shimmer':    'shimmer 1.8s infinite',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%':   { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.5' },
        }
      }
    },
  },
  plugins: [],
}