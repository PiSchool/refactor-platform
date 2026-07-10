import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas:       { DEFAULT: 'rgb(var(--color-canvas-default) / <alpha-value>)', overlay: 'rgb(var(--color-canvas-overlay) / <alpha-value>)', inset: 'rgb(var(--color-canvas-inset) / <alpha-value>)', subtle: 'rgb(var(--color-canvas-subtle) / <alpha-value>)' },
        fg:           { DEFAULT: 'rgb(var(--color-fg-default) / <alpha-value>)', muted: 'rgb(var(--color-fg-muted) / <alpha-value>)', subtle: 'rgb(var(--color-fg-subtle) / <alpha-value>)', onEmphasis: 'rgb(var(--color-fg-on-emphasis) / <alpha-value>)' },
        border:       { DEFAULT: 'rgb(var(--color-border-default) / <alpha-value>)', muted: 'rgb(var(--color-border-muted) / <alpha-value>)', subtle: 'rgb(var(--color-border-subtle) / <alpha-value>)' },
        neutral:      { emphasisPlus: 'rgb(var(--color-neutral-emphasis-plus) / <alpha-value>)', emphasis: 'rgb(var(--color-neutral-emphasis) / <alpha-value>)', muted: 'rgb(var(--color-neutral-muted) / <alpha-value>)', subtle: 'rgb(var(--color-neutral-subtle) / <alpha-value>)' },
        accent:       { fg: 'rgb(var(--color-accent-fg) / <alpha-value>)', emphasis: 'rgb(var(--color-accent-emphasis) / <alpha-value>)', muted: 'rgb(var(--color-accent-muted) / <alpha-value>)', subtle: 'rgb(var(--color-accent-subtle) / <alpha-value>)' },
        success:      { fg: 'rgb(var(--color-success-fg) / <alpha-value>)', emphasis: 'rgb(var(--color-success-emphasis) / <alpha-value>)', muted: 'rgb(var(--color-success-muted) / <alpha-value>)', subtle: 'rgb(var(--color-success-subtle) / <alpha-value>)' },
        attention:    { fg: 'rgb(var(--color-attention-fg) / <alpha-value>)', emphasis: 'rgb(var(--color-attention-emphasis) / <alpha-value>)', muted: 'rgb(var(--color-attention-muted) / <alpha-value>)', subtle: 'rgb(var(--color-attention-subtle) / <alpha-value>)' },
        danger:       { fg: 'rgb(var(--color-danger-fg) / <alpha-value>)', emphasis: 'rgb(var(--color-danger-emphasis) / <alpha-value>)', muted: 'rgb(var(--color-danger-muted) / <alpha-value>)', subtle: 'rgb(var(--color-danger-subtle) / <alpha-value>)' },
        done:         { fg: 'rgb(var(--color-done-fg) / <alpha-value>)', emphasis: 'rgb(var(--color-done-emphasis) / <alpha-value>)' },
        btn:          { bg: 'rgb(var(--color-btn-bg) / <alpha-value>)', border: 'rgb(var(--color-btn-border) / <alpha-value>)', hover: 'rgb(var(--color-btn-hover-bg) / <alpha-value>)', primaryBg: 'rgb(var(--color-btn-primary-bg) / <alpha-value>)', primaryHover: 'rgb(var(--color-btn-primary-hover-bg) / <alpha-value>)', dangerBg: 'rgb(var(--color-btn-danger-bg) / <alpha-value>)' },
        header:       { bg: 'rgb(var(--color-header-bg) / <alpha-value>)' },
        sidenav:      { selected: 'rgb(var(--color-sidenav-selected) / <alpha-value>)' },
        timelineBadge: 'rgb(var(--color-timeline-badge-bg) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Noto Sans', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'SF Mono', 'Menlo', 'Consolas', 'Liberation Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;
