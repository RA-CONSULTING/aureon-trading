import { AureonDataPoint, CoherenceDataPoint } from '@/types';
import { AQTSOrchestrator } from '@/core/aqtsOrchestrator';

const DATA_INTERVAL_MS = 150;
const DEFAULT_SOCKET_URL = import.meta.env.VITE_NEXUS_SOCKET_URL || 'ws://localhost:8790/command-stream';

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

export interface AureonWebSocketConnection {
  sendCommand: (command: string, payload?: Record<string, unknown>) => void;
  close: () => void;
}

export const connectWebSocket = (callbacks: WebSocketCallbacks): AureonWebSocketConnection => {
  if (typeof window === 'undefined' || typeof window.WebSocket === 'undefined') {
    return startSimulatedStream(callbacks);
  }

  return connectToCommandServer(callbacks);
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
