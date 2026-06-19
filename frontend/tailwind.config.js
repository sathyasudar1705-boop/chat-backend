/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'primary':        '#2563EB',   // Professional blue
        'primary-hover':  '#1D4ED8',   // Darker blue on hover
        'primary-soft':   '#EFF6FF',   // Soft blue background
        'accent':         '#10B981',   // Emerald accent
        'accent-bg':      '#ECFDF5',   // Soft green background
        'page-bg':        '#F8FAFC',   // Very light gray-blue
        'card-bg':        '#FFFFFF',   // White cards
        'border-light':   '#E5E7EB',   // Soft gray border
        'text-primary':   '#111827',   // Near-black
        'text-muted':     '#6B7280',   // Muted gray
        'error':          '#EF4444',
        'success':        '#10B981',
        'warning':        '#F59E0B',
        // Keep 'accent' pointing to text-primary for compat
        'text-accent':    '#111827',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in':    'fadeIn 0.25s ease-out',
        'slide-up':   'slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        'shimmer':    'shimmer 1.5s infinite linear',
        'dots':       'dots 1.4s infinite ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        dots: {
          '0%, 80%, 100%': { transform: 'scale(0)', opacity: '0.3' },
          '40%':            { transform: 'scale(1)',   opacity: '1' },
        },
      },
      boxShadow: {
        'saas-sm':  '0 1px 3px 0 rgba(0,0,0,0.05), 0 1px 2px 0 rgba(0,0,0,0.04)',
        'saas-md':  '0 4px 6px -1px rgba(0,0,0,0.06), 0 2px 4px -1px rgba(0,0,0,0.04)',
        'saas-lg':  '0 10px 15px -3px rgba(0,0,0,0.06), 0 4px 6px -2px rgba(0,0,0,0.04)',
        'saas-xl':  '0 20px 25px -5px rgba(0,0,0,0.07), 0 10px 10px -5px rgba(0,0,0,0.03)',
        'chat':     '0 2px 12px 0 rgba(37,99,235,0.08)',
      },
      maxWidth: {
        'chat': '900px',
      },
    },
  },
  plugins: [],
}
