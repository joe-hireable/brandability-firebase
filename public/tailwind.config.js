/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    // Ensure brand color classes are always included
    'bg-brand-primary',
    'bg-brand-secondary',
    'bg-brand-accent',
    'bg-brand-success',
    'bg-brand-warning',
    'bg-brand-error',
    'bg-brand-text-primary',
    'bg-brand-text-secondary',
    'bg-brand-neutral-gray',
    'text-brand-primary',
    'text-brand-secondary',
    'text-brand-accent',
    'text-white',
  ],
  theme: {
    fontFamily: {
      sans: ['"Open Sans"', 'sans-serif'],
      serif: ['"Merriweather"', 'serif'],
      heading: ['"Merriweather"', 'serif'],
      body: ['"Open Sans"', 'sans-serif'],
    },
    extend: {
      colors: {
        // Brand colors
        'brand-primary': '#0A2A4D',
        'brand-secondary': '#F0F4F8',
        'brand-accent': '#D4AF37',
        'brand-success': '#10B981',
        'brand-warning': '#F59E0B',
        'brand-error': '#EF4444',
        'brand-text-primary': '#111827',
        'brand-text-secondary': '#6B7280',
        'brand-neutral-gray': '#F9FAFB',
      },
      borderRadius: {
        DEFAULT: '0.625rem',
        'lg': '0.625rem',
        'md': '0.375rem',
        'sm': '0.25rem',
      }
    },
  },
  plugins: [],
}