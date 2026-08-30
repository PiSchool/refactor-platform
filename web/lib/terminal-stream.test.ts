import { describe, expect, it } from 'vitest';

import { ResumableTerminalStream } from './terminal-stream';

class FakeSocket {
  binaryType = '';
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;

  close() {}

  bytes(value: string) {
    const encoded = new TextEncoder().encode(value);
    this.onmessage?.({ data: encoded.buffer } as MessageEvent);
  }

  status(value: object) {
    this.onmessage?.({ data: JSON.stringify(value) } as MessageEvent);
  }

  disconnect() {
    this.onclose?.();
  }
}

async function settled() {
  await Promise.resolve();
  await Promise.resolve();
}

describe('resumable terminal stream', () => {
  it('reconnects from the exact received byte without duplication', async () => {
    const sockets: FakeSocket[] = [];
    const urls: string[] = [];
    const scheduled: Array<() => void> = [];
    let output = '';
    let done = 0;
    const stream = new ResumableTerminalStream({
      url: (offset) => `/terminal?offset=${offset}`,
      createSocket: (url) => {
        urls.push(url);
        const socket = new FakeSocket();
        sockets.push(socket);
        return socket as unknown as WebSocket;
      },
      schedule: (callback) => {
        scheduled.push(callback);
        return 1 as unknown as ReturnType<typeof setTimeout>;
      },
      write: (data) => { output += new TextDecoder().decode(data); },
      reset: () => { output = ''; },
      recover: async (offset) => ({ data: new Uint8Array(), totalBytes: offset, reset: false }),
      onDone: () => { done += 1; },
    });

    stream.start();
    sockets[0].bytes('abc');
    sockets[0].disconnect();
    scheduled.shift()?.();
    sockets[1].bytes('de');
    sockets[1].status({ type: 'status', state: 'ended', offset: 5 });
    await settled();

    expect(urls).toEqual(['/terminal?offset=0', '/terminal?offset=3']);
    expect(output).toBe('abcde');
    expect(stream.receivedBytes()).toBe(5);
    expect(done).toBe(1);
  });

  it('resets when the durable log is shorter than the client offset', async () => {
    const sockets: FakeSocket[] = [];
    let output = '';
    const stream = new ResumableTerminalStream({
      url: (offset) => `/terminal?offset=${offset}`,
      createSocket: () => {
        const socket = new FakeSocket();
        sockets.push(socket);
        return socket as unknown as WebSocket;
      },
      write: (data) => { output += new TextDecoder().decode(data); },
      reset: () => { output = ''; },
      recover: async (offset) => ({ data: new Uint8Array(), totalBytes: offset, reset: false }),
    });

    stream.start();
    sockets[0].bytes('stale');
    sockets[0].status({ type: 'status', state: 'live', offset: 0, reset: true });
    sockets[0].bytes('new');
    sockets[0].status({ type: 'status', state: 'ended', offset: 3 });
    await settled();

    expect(output).toBe('new');
    expect(stream.receivedBytes()).toBe(3);
  });

  it('bounds retries and recovers the durable tail', async () => {
    const sockets: FakeSocket[] = [];
    const scheduled: Array<() => void> = [];
    const errors: unknown[] = [];
    let output = '';
    const stream = new ResumableTerminalStream({
      url: (offset) => `/terminal?offset=${offset}`,
      createSocket: () => {
        const socket = new FakeSocket();
        sockets.push(socket);
        return socket as unknown as WebSocket;
      },
      schedule: (callback) => {
        scheduled.push(callback);
        return 1 as unknown as ReturnType<typeof setTimeout>;
      },
      maxReconnects: 2,
      write: (data) => { output += new TextDecoder().decode(data); },
      reset: () => { output = ''; },
      recover: async () => ({
        data: new TextEncoder().encode('final'),
        totalBytes: 5,
        reset: false,
      }),
      onError: (error) => { errors.push(error); },
    });

    stream.start();
    sockets[0].disconnect();
    scheduled.shift()?.();
    sockets[1].disconnect();
    scheduled.shift()?.();
    sockets[2].disconnect();
    await settled();

    expect(sockets).toHaveLength(3);
    expect(output).toBe('final');
    expect(errors).toHaveLength(1);
  });
});