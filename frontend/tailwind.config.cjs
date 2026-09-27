/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'fin-navy': '#001529',
        'fin-blue': '#1890ff',
      },
    },
  },
  plugins: [],
}
