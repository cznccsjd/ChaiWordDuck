import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // 主色调 - 黄色系
        yellow: {
          50: '#FFFBEA',
          100: '#FFF3C4',
          400: '#FFD93D',
          500: '#FFC107',
          600: '#FFA000',
        },
        // 辅助色 - 蓝紫色系
        purple: {
          50: '#F5F3FF',
          400: '#8B7FFF',
          500: '#6C63FF',
          600: '#5850EC',
        },
        // 辅助色 - 橙色系
        orange: {
          400: '#FF8A3D',
          500: '#FF6B35',
        },
        // 中性色
        gray: {
          50: '#F9FAFB',
          100: '#F3F4F6',
          200: '#E5E7EB',
          400: '#9CA3AF',
          600: '#4B5563',
          800: '#1F2937',
          900: '#111827',
        },
        // 语义色
        success: '#10B981',
        error: '#EF4444',
        warning: '#F59E0B',
        info: '#3B82F6',
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          '"PingFang SC"',
          '"Hiragino Sans GB"',
          '"Microsoft YaHei"',
          '"Helvetica Neue"',
          'Helvetica',
          'Arial',
          'sans-serif',
        ],
        english: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'sans-serif',
        ],
        mono: [
          '"JetBrains Mono"',
          '"Fira Code"',
          '"SF Mono"',
          'Consolas',
          'monospace',
        ],
      },
      spacing: {
        '0': '0px',
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '5': '20px',
        '6': '24px',
        '8': '32px',
        '10': '40px',
        '12': '48px',
        '16': '64px',
      },
      borderRadius: {
        'none': '0px',
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '24px',
        'full': '9999px',
      },
      boxShadow: {
        'sm': '0 1px 2px rgba(0, 0, 0, 0.05)',
        'md': '0 4px 6px rgba(0, 0, 0, 0.07)',
        'lg': '0 10px 15px rgba(0, 0, 0, 0.1)',
        'xl': '0 20px 25px rgba(0, 0, 0, 0.15)',
        'focus': '0 0 0 3px rgba(255, 217, 61, 0.3), 0 1px 2px rgba(0, 0, 0, 0.05)',
        'brand': '0 4px 12px rgba(255, 217, 61, 0.4), 0 2px 4px rgba(0, 0, 0, 0.1)',
      },
    },
  },
  plugins: [],
};
export default config;
