/**
 * @module lock-screen
 * @description Windows 11-style intro splash shown over the app on first load.
 *
 * A single screen: the Pi School mark and the "refactor-platform" identity, with
 * a swipe-up hint. Any scroll-up / key / click slides the whole screen away to
 * reveal the dashboard — the opening animation for the demonstration video.
 * No passkey; it is purely presentational. It re-shows once per browser session.
 */
'use client';

import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { ChevronUp } from 'lucide-react';

const SESSION_KEY = 'rp-unlocked';

export function LockGate({ children }: { children: ReactNode }) {
  // Covered by default so the splash is present in the initial (SSR) HTML until
  // we confirm this session already entered.
  const [locked, setLocked] = useState(true);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (sessionStorage.getItem(SESSION_KEY) === '1') setLocked(false);
    setReady(true);
  }, []);

  const enter = useCallback(() => {
    sessionStorage.setItem(SESSION_KEY, '1');
    setLocked(false);
  }, []);

  return (
    <>
      {children}
      {locked && <Splash onEnter={enter} animate={ready} />}
    </>
  );
}

function Splash({ onEnter, animate }: { onEnter: () => void; animate: boolean }) {
  const [leaving, setLeaving] = useState(false);
  const leavingRef = useRef(false);

  const reveal = useCallback(() => {
    if (leavingRef.current) return;
    leavingRef.current = true;
    setLeaving(true);
    setTimeout(onEnter, 750); // let the slide-up finish before unmounting
  }, [onEnter]);

  // Any scroll-up / key / tap enters the app (Win11 lock feel).
  useEffect(() => {
    const onWheel = (e: WheelEvent) => { if (e.deltaY < 0) reveal(); };
    const onKey = (e: KeyboardEvent) => { if (e.key !== 'Tab') reveal(); };
    window.addEventListener('wheel', onWheel, { passive: true });
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('wheel', onWheel);
      window.removeEventListener('keydown', onKey);
    };
  }, [reveal]);

  return (
    <div
      onClick={reveal}
      className="fixed inset-0 z-[100] flex cursor-pointer flex-col items-center justify-center overflow-hidden px-6 select-none"
      style={{
        transition: animate ? 'transform 700ms cubic-bezier(0.22,1,0.36,1), opacity 700ms ease' : undefined,
        transform: leaving ? 'translateY(-100%)' : 'translateY(0)',
        opacity: leaving ? 0 : 1,
      }}
    >
      {/* Minimalist, theme-aware wallpaper built purely from app color tokens. */}
      <div
        className="absolute inset-0 -z-10"
        style={{
          background:
            'radial-gradient(120% 90% at 25% 15%, rgb(var(--color-accent-subtle) / 0.55), transparent 55%),' +
            'radial-gradient(100% 80% at 85% 90%, rgb(var(--color-done-emphasis) / 0.18), transparent 55%),' +
            'rgb(var(--color-canvas-default))',
        }}
      />

      {/* Identity */}
      <div className="flex h-28 w-28 items-center justify-center overflow-hidden rounded-full bg-white shadow-lg ring-1 ring-border">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/brand/pischool-mark.jpg" alt="Pi School" className="h-20 w-20 object-contain" />
      </div>
      <div className="mt-5 text-2xl font-medium tracking-tight text-fg">refactor-platform</div>

      {/* Enter hint */}
      <div className="mt-16 flex flex-col items-center gap-1 text-fg-subtle animate-pulse">
        <ChevronUp className="h-5 w-5" />
        <span className="text-xs">Swipe up or press any key</span>
      </div>
    </div>
  );
}
