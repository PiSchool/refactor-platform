export type TerminalRecovery = {
  data: Uint8Array;
  totalBytes: number;
  reset: boolean;
};

type SocketFactory = (url: string) => WebSocket;
type Schedule = (callback: () => void, delay: number) => ReturnType<typeof setTimeout>;

export type TerminalStreamOptions = {
  url: (offset: number) => string;
  write: (data: Uint8Array) => void;
  reset: () => void;
  recover: (offset: number) => Promise<TerminalRecovery>;
  onDone?: () => void;
  onError?: (error: unknown) => void;
  createSocket?: SocketFactory;
  schedule?: Schedule;
  cancelSchedule?: (handle: ReturnType<typeof setTimeout>) => void;
  maxReconnects?: number;
};

type StatusFrame = {
  type: 'status';
  state: 'live' | 'ended';
  offset: number;
  reset?: boolean;
};

function reconnectDelay(attempt: number): number {
  return Math.min(250 * (2 ** attempt), 4000);
}

function statusFrame(value: string): StatusFrame | null {
  try {
    const parsed = JSON.parse(value) as Partial<StatusFrame>;
    if (
      parsed.type === 'status'
      && (parsed.state === 'live' || parsed.state === 'ended')
      && Number.isSafeInteger(parsed.offset)
      && Number(parsed.offset) >= 0
    ) {
      return parsed as StatusFrame;
    }
  } catch {
    // Unknown text frames do not belong in the terminal byte stream.
  }
  return null;
}

export class ResumableTerminalStream {
  private socket: WebSocket | null = null;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private offset = 0;
  private reconnects = 0;
  private disposed = false;
  private ended = false;

  constructor(private readonly options: TerminalStreamOptions) {}

  start(): void {
    if (!this.disposed && !this.socket) this.connect();
  }

  stop(): void {
    this.disposed = true;
    if (this.timer !== null) {
      (this.options.cancelSchedule ?? clearTimeout)(this.timer);
      this.timer = null;
    }
    this.socket?.close();
    this.socket = null;
  }

  receivedBytes(): number {
    return this.offset;
  }

  private connect(): void {
    if (this.disposed || this.ended) return;
    const createSocket = this.options.createSocket ?? ((url: string) => new WebSocket(url));
    const socket = createSocket(this.options.url(this.offset));
    this.socket = socket;
    socket.binaryType = 'arraybuffer';
    socket.onmessage = (event) => { void this.message(event.data); };
    socket.onerror = () => socket.close();
    socket.onclose = () => {
      if (this.socket === socket) this.socket = null;
      if (!this.disposed && !this.ended) this.reconnect();
    };
  }

  private async message(data: unknown): Promise<void> {
    if (this.disposed) return;
    if (typeof data === 'string') {
      const status = statusFrame(data);
      if (!status) return;
      if (status.reset) {
        this.offset = 0;
        this.options.reset();
      }
      if (status.state === 'ended') {
        this.ended = true;
        await this.finish(status.offset);
      }
      return;
    }
    if (!(data instanceof ArrayBuffer)) return;
    const bytes = new Uint8Array(data);
    if (!bytes.byteLength) return;
    this.options.write(bytes);
    this.offset += bytes.byteLength;
    this.reconnects = 0;
  }

  private reconnect(): void {
    const maximum = this.options.maxReconnects ?? 6;
    if (this.reconnects >= maximum) {
      void this.recoverAfterDisconnect();
      return;
    }
    const attempt = this.reconnects;
    this.reconnects += 1;
    const schedule = this.options.schedule ?? setTimeout;
    this.timer = schedule(() => {
      this.timer = null;
      this.connect();
    }, reconnectDelay(attempt));
  }

  private async applyRecovery(): Promise<void> {
    const recovery = await this.options.recover(this.offset);
    if (recovery.reset) {
      this.options.reset();
      this.offset = 0;
    }
    if (recovery.data.byteLength) this.options.write(recovery.data);
    this.offset = recovery.totalBytes;
  }

  private async finish(expectedOffset: number): Promise<void> {
    try {
      if (this.offset !== expectedOffset) await this.applyRecovery();
      if (this.offset !== expectedOffset) {
        throw new Error(
          `terminal recovery stopped at byte ${this.offset}; expected ${expectedOffset}`,
        );
      }
      this.options.onDone?.();
    } catch (error) {
      this.options.onError?.(error);
    }
  }

  private async recoverAfterDisconnect(): Promise<void> {
    if (this.disposed || this.ended) return;
    this.ended = true;
    try {
      await this.applyRecovery();
    } catch (error) {
      this.options.onError?.(error);
      return;
    }
    this.options.onError?.(new Error('live terminal disconnected after bounded retries'));
  }
}