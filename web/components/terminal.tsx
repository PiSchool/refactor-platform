'use client';

import { useEffect, useRef } from 'react';
import { fetchArtifactText } from '@/lib/api';
import { ResumableTerminalStream } from '@/lib/terminal-stream';
import type { ArtifactRef } from '@/lib/types';

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

/** Read-only xterm terminal with durable byte-offset replay and reconnect. */
export function Terminal({ sessionId, live, artifact }: {
  sessionId: string; live: boolean; artifact?: ArtifactRef;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let term: any, fit: any, stream: ResumableTerminalStream | null = null, disposed = false;
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
        stream = new ResumableTerminalStream({
          url: (offset) => (
            `${proto}://${location.host}/ws/sessions/${encodeURIComponent(sessionId)}/terminal?offset=${offset}`
          ),
          write: (data) => term.write(data),
          reset: () => term.reset(),
          recover: async (offset) => {
            if (!artifact) {
              return { data: new Uint8Array(), totalBytes: offset, reset: false };
            }
            const response = await fetch(artifact.viewUrl, { credentials: 'same-origin' });
            if (!response.ok) throw new Error(`terminal recovery failed (${response.status})`);
            const complete = new Uint8Array(await response.arrayBuffer());
            const reset = complete.byteLength < offset;
            return {
              data: reset ? complete : complete.slice(offset),
              totalBytes: complete.byteLength,
              reset,
            };
          },
          onError: (error) => {
            if (!disposed) term.write(`\r\n(terminal stream unavailable: ${error})`);
          },
        });
        stream.start();
      } else if (artifact) {
        try {
          term.write(await fetchArtifactText(artifact));
        } catch (error) {
          term.write(`(terminal unavailable: ${error})`);
        }
      } else {
        term.write('(terminal unavailable)');
      }
      (term as any)._cleanup = () => window.removeEventListener('resize', onResize);
    })();

    return () => {
      disposed = true;
      observer?.disconnect();
      stream?.stop();
      if (term) { term._cleanup?.(); term.dispose(); }
    };
  }, [sessionId, live, artifact?.viewUrl]);

  return <div ref={ref} className="h-full min-h-0 w-full overflow-hidden rounded-md border border-border bg-canvas-inset p-1" />;
}
