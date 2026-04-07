/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '0.125rem',
        sm: '0.125rem',
        md: '0.25rem',
        lg: '0.25rem',
        xl: '0.5rem',
        '2xl': '0.75rem',
<<<<<<< HEAD
        '3xl': '1rem',
        full: '9999px',
      },
      boxShadow: {
        shell: '0 1px 2px rgba(32, 33, 36, 0.06), 0 1px 3px rgba(32, 33, 36, 0.04)',
        lift: '0 2px 8px rgba(32, 33, 36, 0.08), 0 1px 2px rgba(32, 33, 36, 0.06)',
      },
=======
        full: '9999px',
      },
>>>>>>> 32629c1c2d2595ea4edddeb2b46ff4d551f18285
      colors: {
        primary: {
          DEFAULT: '#1a73e8',
          50: '#e8f0fe',
          100: '#d2e3fc',
          200: '#aecbfa',
          300: '#7baaf7',
          400: '#4285f4',
          500: '#1a73e8',
          600: '#1765cc',
          700: '#185abc',
          800: '#174ea6',
          900: '#0d47a1',
        },
        surface: {
          DEFAULT: '#ffffff',
          dim: '#f8f9fa',
          container: '#f1f3f4',
          variant: '#e8eaed',
        },
        on: {
          surface: '#202124',
          'surface-variant': '#5f6368',
          primary: '#ffffff',
        },
        error: {
          DEFAULT: '#d93025',
          container: '#fce8e6',
        },
        success: {
          DEFAULT: '#137333',
          container: '#e6f4ea',
        },
        warning: {
          DEFAULT: '#f29900',
          container: '#fef7e0',
        },
        outline: {
          DEFAULT: '#dadce0',
          variant: '#e8eaed',
        },
      },
    },
  },
  plugins: [],
}
