import { AureonDataPoint, CoherenceDataPoint } from '@/types';
import { AQTSOrchestrator } from '@/core/aqtsOrchestrator';

const DATA_INTERVAL_MS = 150;
const DEFAULT_SOCKET_URL = import.meta.env.VITE_NEXUS_SOCKET_URL || 'ws://localhost:8790/command-stream';
const BINANCE_WS_BASE = 'wss://stream.binance.com:9443/ws';

export interface CommandSummary {
  id: string;
  type: string;
  status: string;
  payload?: Record<string, unknown>;
  createdAt: number;
  startedAt?: number;
  finishedAt?: number;
  error?: string;
}

export interface CommandCenterSnapshot {
  streaming: boolean;
  intervalMs: number | null;
  clients: number;
  activeCommand: CommandSummary | null;
  commandHistory: CommandSummary[];
  lastTick: StreamPayload | null;
}

export interface StreamPayload {
  aureon: AureonDataPoint;
  nexus: CoherenceDataPoint;
}

interface WebSocketCallbacks {
  onOpen: () => void;
  onMessage: (data: StreamPayload) => void;
  onError: (error: Error) => void;
  onClose: () => void;
  onStatus?: (snapshot: CommandCenterSnapshot) => void;
}

export type StreamSource = 'nexus_command' | 'binance_orderbook';

export interface StreamConnectionOptions {
  source?: StreamSource;
  symbol?: string;
}

export interface AureonWebSocketConnection {
  sendCommand: (command: string, payload?: Record<string, unknown>) => void;
  close: () => void;
}

export const connectWebSocket = (
  callbacks: WebSocketCallbacks,
  options: StreamConnectionOptions = {},
): AureonWebSocketConnection => {
  const source = options.source ?? 'nexus_command';
  if (typeof window === 'undefined' || typeof window.WebSocket === 'undefined') {
    return startSimulatedStream(callbacks);
  }

  if (source === 'binance_orderbook') {
    return connectToBinanceOrderBook(callbacks, options.symbol ?? 'ethusdt');
  }

  return connectToCommandServer(callbacks);
};

const connectToBinanceOrderBook = (
  callbacks: WebSocketCallbacks,
  symbol: string,
): AureonWebSocketConnection => {
  let socket: WebSocket | null = null;
  let closed = false;
  const normalizedSymbol = symbol.toLowerCase().replace('/', '').trim() || 'ethusdt';
  const wsUrl = `${BINANCE_WS_BASE}/${normalizedSymbol}@depth20@100ms`;
  const baseSnapshot: CommandCenterSnapshot = {
    streaming: true,
    intervalMs: 100,
    clients: 1,
    activeCommand: null,
    commandHistory: [],
    lastTick: null,
  };

  try {
    socket = new WebSocket(wsUrl);
  } catch (error) {
    callbacks.onError(error as Error);
    return startSimulatedStream(callbacks);
  }

  socket.addEventListener('open', () => {
    callbacks.onOpen();
    callbacks.onStatus?.(baseSnapshot);
  });

  socket.addEventListener('message', (event) => {
    try {
      const depthEvent = JSON.parse(event.data as string) as {
        b?: [string, string][];
        a?: [string, string][];
        E?: number;
      };
      const bids = depthEvent.b ?? [];
      const asks = depthEvent.a ?? [];
      if (bids.length === 0 || asks.length === 0) return;

      const bestBid = Number(bids[0][0]);
      const bestAsk = Number(asks[0][0]);
      const spread = Math.max(bestAsk - bestBid, 0);
      const midpoint = (bestAsk + bestBid) / 2;
      const bidVolume = bids.slice(0, 10).reduce((sum, [, qty]) => sum + Number(qty), 0);
      const askVolume = asks.slice(0, 10).reduce((sum, [, qty]) => sum + Number(qty), 0);
      const totalDepth = Math.max(bidVolume + askVolume, 1e-6);
      const imbalance = (bidVolume - askVolume) / totalDepth;
      const syntheticTime = Math.floor((depthEvent.E ?? Date.now()) / 1000);

      const tick: StreamPayload = {
        aureon: {
          time: syntheticTime,
          market: {
            open: midpoint,
            high: midpoint + spread,
            low: Math.max(midpoint - spread, 0),
            close: midpoint,
            volume: totalDepth,
          },
          sentiment: imbalance,
          policyRate: 0,
          dataIntegrity: Math.max(0, 1 - spread / Math.max(midpoint, 1)),
          crystalCoherence: Math.abs(imbalance),
          celestialModulators: Math.max(0, 1 - spread / Math.max(midpoint * 0.01, 1e-9)),
          polarisBaseline: spread,
          choeranceDrift: imbalance,
          pingPong: bidVolume / Math.max(askVolume, 1e-6),
          gravReflection: askVolume / Math.max(bidVolume, 1e-6),
          unityIndex: (Math.abs(imbalance) + Math.max(0, 1 - spread / Math.max(midpoint, 1))) / 2,
          inerchaVector: imbalance * midpoint,
          coherenceIndex: Math.abs(imbalance),
          prismStatus: imbalance > 0.2 ? 'Gold' : imbalance < -0.2 ? 'Red' : 'Blue',
          surgeMagnitude: Math.abs(imbalance),
        },
        nexus: {
          time: syntheticTime,
          cognitiveCapacity: Math.max(0.05, 1 - spread / Math.max(midpoint, 1)),
          sporeConcentration: Math.min(1, totalDepth / 1000),
          systemRigidity: Math.min(10, spread * 1000 / Math.max(midpoint, 1)),
        },
      };

      callbacks.onMessage(tick);
      callbacks.onStatus?.({ ...baseSnapshot, lastTick: tick });
    } catch (error) {
      callbacks.onError(error as Error);
    }
  });

  socket.addEventListener('error', () => {
    callbacks.onError(new Error(`Order book stream error for ${normalizedSymbol.toUpperCase()}.`));
  });

  socket.addEventListener('close', () => {
    if (closed) return;
    callbacks.onClose();
  });

  return {
    sendCommand: () => {
      // Binance depth socket is push-only; command channel is intentionally a no-op.
    },
    close: () => {
      if (closed) return;
      closed = true;
      socket?.close();
      callbacks.onClose();
    },
  };
};

const connectToCommandServer = (callbacks: WebSocketCallbacks): AureonWebSocketConnection => {
  let socket: WebSocket | null = null;
  let fallbackConnection: AureonWebSocketConnection | null = null;
  let connectTimeout: number | null = null;
  let manualClose = false;
  const pendingCommands: Array<{ command: string; payload?: Record<string, unknown> }> = [];

  const fallback = () => {
    if (fallbackConnection) {
      return fallbackConnection;
    }
    if (connectTimeout) {
      window.clearTimeout(connectTimeout);
      connectTimeout = null;
    }
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.close();
    }
    fallbackConnection = startSimulatedStream(callbacks);
    while (pendingCommands.length > 0) {
      const item = pendingCommands.shift();
      if (item) {
        fallbackConnection.sendCommand(item.command, item.payload);
      }
    }
    return fallbackConnection;
  };

  try {
    socket = new WebSocket(DEFAULT_SOCKET_URL);
  } catch (error) {
    console.warn('Failed to open Nexus command WebSocket. Falling back to simulation.', error);
    return startSimulatedStream(callbacks);
  }

  connectTimeout = window.setTimeout(() => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      callbacks.onError(new Error('Command server did not respond. Switching to local simulation.'));
      fallback();
    }
  }, 4000);

  socket.addEventListener('open', () => {
    if (connectTimeout) {
      window.clearTimeout(connectTimeout);
    }
    callbacks.onOpen();
    while (pendingCommands.length > 0 && socket && socket.readyState === WebSocket.OPEN) {
      const { command, payload } = pendingCommands.shift()!;
      socket.send(JSON.stringify({ type: 'command', command, payload }));
    }
  });

  socket.addEventListener('message', (event) => {
    try {
      const parsed = JSON.parse(event.data as string);
      switch (parsed?.type) {
        case 'stream_tick':
          callbacks.onMessage(parsed.payload as StreamPayload);
          break;
        case 'system_status':
          callbacks.onStatus?.(parsed.payload as CommandCenterSnapshot);
          break;
        case 'command_response':
          if (parsed.error) {
            callbacks.onError(new Error(parsed.error as string));
          }
          break;
        default:
          break;
      }
    } catch (error) {
      callbacks.onError(error as Error);
    }
  });

  socket.addEventListener('error', (event) => {
    console.error('Command server WebSocket error', event);
    if (!fallbackConnection) {
      callbacks.onError(new Error('Command server connection lost. Switching to simulation.'));
      fallback();
    }
  });

  socket.addEventListener('close', () => {
    if (connectTimeout) {
      window.clearTimeout(connectTimeout);
    }

    if (manualClose) {
      callbacks.onClose();
      return;
    }

    if (fallbackConnection) {
      // Already running in simulation mode; let that connection own lifecycle
      return;
    }

    callbacks.onError(new Error('Command server closed the connection. Switching to simulation.'));
    fallback();
  });

  return {
    sendCommand: (command, payload) => {
      if (socket && socket.readyState === WebSocket.OPEN && !fallbackConnection) {
        socket.send(JSON.stringify({ type: 'command', command, payload }));
      } else if (!fallbackConnection) {
        pendingCommands.push({ command, payload });
      } else if (fallbackConnection) {
        fallbackConnection.sendCommand(command, payload);
      }
    },
    close: () => {
      manualClose = true;
      if (connectTimeout) {
        window.clearTimeout(connectTimeout);
      }
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
      fallbackConnection?.close();
    },
  };
};

const startSimulatedStream = (callbacks: WebSocketCallbacks): AureonWebSocketConnection => {
  const orchestrator = new AQTSOrchestrator();
  let closed = false;

  // Simulate async connection delay to mirror real server behavior
  const openTimer = setTimeout(() => callbacks.onOpen(), 250);

  const intervalId = setInterval(() => {
    if (closed) return;
    try {
      const output = orchestrator.next();
      callbacks.onMessage({ aureon: output.aureonPoint, nexus: output.nexusPoint });
    } catch (error) {
      callbacks.onError(error as Error);
      clearInterval(intervalId);
    }
  }, DATA_INTERVAL_MS);

  return {
    sendCommand: (command) => {
      if (command === 'stop_stream' && !closed) {
        closed = true;
        clearTimeout(openTimer);
        clearInterval(intervalId);
        callbacks.onClose();
      }
    },
    close: () => {
      if (closed) return;
      closed = true;
      clearTimeout(openTimer);
      clearInterval(intervalId);
      callbacks.onClose();
    },
  };
};
