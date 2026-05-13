/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        sw: {
          primary: '#1677ff',
          'primary-strong': '#0f63df',
          sidebar: '#06245a',
          'sidebar-deep': '#041a43',
          bg: '#f3f7fc',
          card: '#ffffff',
          line: '#e5edf6',
          'line-strong': '#d5e0ec',
          text: '#1e293b',
          muted: '#6b7a90',
          faint: '#9aa8ba',
          success: '#16b26b',
          warning: '#f59f00',
          danger: '#f04438',
          info: '#1677ff',
        },
      },
      boxShadow: {
        'sw-card': '0 14px 38px rgba(15, 35, 70, 0.08)',
        'sw-soft': '0 8px 24px rgba(15, 35, 70, 0.06)',
        'sw-primary': '0 10px 22px rgba(22, 119, 255, 0.24)',
        'sw-primary-hover': '0 13px 28px rgba(22, 119, 255, 0.3)',
      },
      borderRadius: {
        sw: '12px',
      },
      fontFamily: {
        sans: ['Noto Sans SC', 'Microsoft YaHei', 'PingFang SC', 'sans-serif'],
        mono: ['SFMono-Regular', 'Consolas', 'monospace'],
      },
      keyframes: {
        'sw-spin': {
          to: { transform: 'rotate(360deg)' },
        },
        'sw-fade-up': {
          from: {
            opacity: '0',
            transform: 'translateY(10px)',
          },
          to: {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
      },
      animation: {
        'sw-spin': 'sw-spin 0.8s linear infinite',
        'sw-fade-up': 'sw-fade-up 0.28s ease-out both',
      },
    },
  },
  plugins: [],
}
