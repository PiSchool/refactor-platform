'use client';

import { useEffect, useRef } from 'react';

/** Read a platform colour token (stored as an "r g b" triple). */
function cssRgb(name: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  const raw = getComputedStyle(document.documentElement).getPropertyValue(`--color-${name}`).trim();
  return raw ? `rgb(${raw.split(/\s+/).join(',')})` : fallback;
}

/** xterm palette derived from the active platform theme, so the agent view
 *  follows dark / light / dimmed instead of being permanently dark. */
function xtermTheme() {
  return {
    background: cssRgb('canvas-inset', '#0d1117'),
    foreground: cssRgb('fg-default', '#e6edf3'),
    cursor: cssRgb('fg-default', '#e6edf3'),
    cursorAccent: cssRgb('canvas-inset', '#0d1117'),
  };
}

/** Read-only xterm terminal. Live sessions stream over WS from byte 0 (full
 *  scrollback), then live deltas. Ended sessions load the finalized log. */
export function Terminal({ sessionId, live }: { sessionId: string; live: boolean }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let term: any, fit: any, ws: WebSocket | null = null, disposed = false;
    let observer: MutationObserver | null = null;

    (async () => {
      const { Terminal: XTerm } = await import('@xterm/xterm');
      const { FitAddon } = await import('@xterm/addon-fit');
      if (disposed || !ref.current) return;
      term = new XTerm({ convertEol: true, fontSize: 12, theme: xtermTheme(), scrollback: 100000, disableStdin: true });
      fit = new FitAddon();
      term.loadAddon(fit);
      term.open(ref.current);
      try { fit.fit(); } catch {}
      const onResize = () => { try { fit.fit(); } catch {} };
      window.addEventListener('resize', onResize);

      // Follow platform theme switches live.
      observer = new MutationObserver(() => { term.options.theme = xtermTheme(); });
      observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

      if (live) {
        const proto = location.protocol === 'https:' ? 'wss' : 'ws';
        ws = new WebSocket(`${proto}://${location.host}/ws/sessions/${sessionId}/terminal`);
        ws.binaryType = 'arraybuffer';
        ws.onmessage = (e) => {
          if (typeof e.data === 'string') return; // status frames
          term.write(new Uint8Array(e.data));
        };
      } else {
        const res = await fetch(`/api/sessions/${sessionId}/terminal-log`);
        term.write(await res.text());
      }
      (term as any)._cleanup = () => window.removeEventListener('resize', onResize);
    })();

    return () => {
      disposed = true;
      observer?.disconnect();
      if (ws) ws.close();
      if (term) { term._cleanup?.(); term.dispose(); }
    };
  }, [sessionId, live]);

  return <div ref={ref} className="h-full min-h-0 w-full overflow-hidden rounded-md border border-border bg-canvas-inset p-1" />;
}
