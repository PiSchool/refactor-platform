/**
 * @module theme
 * @description Theme management: dark/light/dimmed mode with localStorage persistence.
 */
'use client';

import { useCallback, useEffect, useState } from 'react';

export type Theme = 'dark' | 'light' | 'dimmed';
const STORAGE_KEY = 'gh-theme';
const THEMES: Theme[] = ['dark', 'light', 'dimmed'];

function getInitial(): Theme {
  if (typeof window === 'undefined') return 'dark';
  const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
  if (stored && THEMES.includes(stored)) return stored;
  return 'dark';
}

function apply(theme: Theme) {
  document.documentElement.setAttribute('data-theme', theme);
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>('dark');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
    if (stored && THEMES.includes(stored)) setThemeState(stored);
    setMounted(true);
  }, []);

  useEffect(() => { if (mounted) apply(theme); }, [theme, mounted]);

  const setTheme = useCallback((t: Theme) => {
    localStorage.setItem(STORAGE_KEY, t);
    setThemeState(t);
  }, []);

  const cycle = useCallback(() => {
    setTheme(THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length]);
  }, [theme, setTheme]);

  return { theme, setTheme, cycle, themes: THEMES };
}
