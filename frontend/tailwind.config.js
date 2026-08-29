/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ─── Dark theme core ───
        background: '#0A0E1A',
        'background-elevated': '#0F1629',
        'background-card': '#141B2E',
        surface: '#FFFFFF',
        'surface-elevated': '#FFFFFF',
        'surface-dark': '#1A2235',
        ink: '#0A0E1A',
        panel: '#121A2E',
        border: '#1E293B',
        'border-light': '#2D3B54',
        'border-strong': '#3B4B68',
        'border-glow': 'rgba(76, 141, 255, 0.3)',

        // ─── Typography ───
        'text-primary': '#FFFFFF',
        'text-secondary': '#94A3B8',
        'text-muted': '#64748B',
        'text-accent': '#4C8DFF',
        text: '#E8ECF7',
        muted: '#6B7592',

        // Light theme fallbacks for dashboard
        'text-primary-light': '#0F172A',
        'text-secondary-light': '#64748B',
        'text-muted-light': '#94A3B8',
        primary: '#0F172A',
        secondary: '#64748B',
        'muted-foreground': '#64748B',

        // ─── Brand accent ───
        sentinel: '#4C8DFF',
        'sentinel-bright': '#6BA3FF',
        'sentinel-deep': '#3B7AE5',
        'sentinel-dark': '#2563EB',
        'sentinel-glow': 'rgba(76, 141, 255, 0.15)',
        signal: '#4C8DFF',

        // ─── Semantic decision states ───
        allow: '#10B981',
        'allow-bg': 'rgba(16, 185, 129, 0.1)',
        escalate: '#F5A623',
        'escalate-bg': 'rgba(245, 166, 35, 0.1)',
        drift: '#F5A623',
        contain: '#E5484D',
        'contain-bg': 'rgba(229, 72, 77, 0.1)',
        unknown: '#6B7280',

        // ─── Semantic UI states ───
        info: '#4C8DFF',
        success: '#10B981',
        warning: '#F5A623',
        danger: '#E5484D',

        // ─── Sidebar ───
        'sidebar-bg': '#0A0E1A',
        'sidebar-text': '#CBD5E1',
        'sidebar-muted': '#64748B',
        'sidebar-active': '#4C8DFF',
        'sidebar-hover': '#141B2E',
        'sidebar-border': '#1E293B',

        // ─── Atmospheric & Effects ───
        'field-glow': 'rgba(76, 141, 255, 0.12)',
        'shield-glow': 'rgba(76, 141, 255, 0.25)',
        'risk-warning': 'rgba(229, 72, 77, 0.08)',
        'risk-critical': 'rgba(229, 72, 77, 0.15)',
        'success-glow': 'rgba(16, 185, 129, 0.08)',
        'flow-line': 'rgba(76, 141, 255, 0.4)',
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        body: ['"Inter"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      fontSize: {
        'display-xl': ['4.5rem', { lineHeight: '1', fontWeight: '700' }],
        'display-lg': ['3.5rem', { lineHeight: '1.1', fontWeight: '700' }],
        'display': ['3rem', { lineHeight: '1.1', fontWeight: '700' }],
        'page-title': ['1.75rem', { lineHeight: '1.3', fontWeight: '600' }],
        'section-title': ['1.125rem', { lineHeight: '1.4', fontWeight: '600' }],
        'body': ['0.875rem', { lineHeight: '1.5', fontWeight: '400' }],
        'secondary': ['0.8125rem', { lineHeight: '1.4', fontWeight: '400' }],
        'metadata': ['0.6875rem', { lineHeight: '1.3', fontWeight: '500' }],
      },
      spacing: {
        '4.5': '1.125rem',
        '13': '3.25rem',
        '15': '3.75rem',
        '18': '4.5rem',
        '72': '18rem',
        '84': '21rem',
        '96': '24rem',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'flow': 'flow 3s ease-in-out infinite',
      },
      keyframes: {
        glow: {
          '0%': { opacity: '0.5' },
          '100%': { opacity: '1' },
        },
        flow: {
          '0%, 100%': { opacity: '0.3' },
          '50%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
