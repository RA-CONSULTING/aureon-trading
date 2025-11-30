#!/usr/bin/env tsx
import 'dotenv/config';
import http from 'http';
import path from 'path';
import fs from 'fs';
import cors from 'cors';
import express from 'express';
import { WebSocketServer, WebSocket } from 'ws';
import { randomUUID } from 'crypto';
import { spawn, type ChildProcessWithoutNullStreams } from 'child_process';

import { AQTSOrchestrator } from '../src/core/aqtsOrchestrator';
import type { AureonDataPoint, CoherenceDataPoint } from '../src/types';

const PORT = Number(process.env.NEXUS_COMMAND_PORT || 8790);
const SOCKET_PATH = process.env.NEXUS_COMMAND_SOCKET_PATH || '/command-stream';
const DEFAULT_INTERVAL = Number(process.env.NEXUS_STREAM_INTERVAL || 200);
const PYTHON_BIN = process.env.NEXUS_PYTHON_BIN || 'python3';
const NEXUS_SCRIPT = process.env.NEXUS_SCRIPT || path.resolve(process.cwd(), 'aureon_nexus.py');

interface StreamPayload {
  aureon: AureonDataPoint;
  nexus: CoherenceDataPoint;
}

type CommandStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

interface CommandRecord {
  id: string;
  type: string;
  payload?: Record<string, unknown>;
  status: CommandStatus;
  createdAt: number;
  startedAt?: number;
  finishedAt?: number;
  error?: string;
  log: Array<{ ts: number; stream: 'stdout' | 'stderr'; chunk: string }>;
}

const app = express();
app.use(cors());
app.use(express.json());

const httpServer = http.createServer(app);
const wss = new WebSocketServer({ server: httpServer, path: SOCKET_PATH });

const orchestrator = new AQTSOrchestrator();
let streamInterval: NodeJS.Timeout | null = null;
let currentInterval = DEFAULT_INTERVAL;
let lastPayload: StreamPayload | null = null;
const clients = new Set<WebSocket>();

let activeProcess: ChildProcessWithoutNullStreams | null = null;
let activeCommand: CommandRecord | null = null;
const commandHistory: CommandRecord[] = [];
const MAX_HISTORY = 20;

function broadcast(event: Record<string, unknown>) {
  const payload = JSON.stringify(event);
  for (const client of clients) {
    if (client.readyState === WebSocket.OPEN) {
      client.send(payload);
    }
  }
}

function summarizeCommand(command: CommandRecord) {
  const { id, type, payload, status, createdAt, startedAt, finishedAt, error } = command;
  return { id, type, payload, status, createdAt, startedAt, finishedAt, error };
}

function snapshot() {
  return {
    streaming: Boolean(streamInterval),
    intervalMs: streamInterval ? currentInterval : null,
    clients: clients.size,
    activeCommand: activeCommand ? summarizeCommand(activeCommand) : null,
    commandHistory: commandHistory.map(summarizeCommand),
    lastTick: lastPayload,
  };
}

function pushNextPoint() {
  const result = orchestrator.next();
  const payload: StreamPayload = {
    aureon: result.aureonPoint,
    nexus: result.nexusPoint,
  };
  lastPayload = payload;
  broadcast({ type: 'stream_tick', payload });
}

function startStream(intervalMs?: number) {
  const interval = typeof intervalMs === 'number' && Number.isFinite(intervalMs)
    ? Math.max(50, intervalMs)
    : DEFAULT_INTERVAL;

  if (streamInterval) {
    clearInterval(streamInterval);
  }

  currentInterval = interval;
  streamInterval = setInterval(pushNextPoint, interval);
  pushNextPoint();
  broadcast({ type: 'system_status', payload: snapshot() });
  return { intervalMs: interval };
}

function stopStream() {
  if (!streamInterval) {
    return { stopped: false };
  }
  clearInterval(streamInterval);
  streamInterval = null;
  broadcast({ type: 'system_status', payload: snapshot() });
  return { stopped: true };
}

function registerCommand(type: string, payload?: Record<string, unknown>) {
  const command: CommandRecord = {
    id: randomUUID(),
    type,
    payload,
    status: 'queued',
    createdAt: Date.now(),
    log: [],
  };
  commandHistory.push(command);
  if (commandHistory.length > MAX_HISTORY) {
    commandHistory.shift();
  }
  broadcast({ type: 'command_update', payload: summarizeCommand(command) });
  return command;
}

function trackCommandOutput(command: CommandRecord, stream: 'stdout' | 'stderr', chunk: string) {
  command.log.push({ ts: Date.now(), stream, chunk });
  broadcast({ type: 'command_log', payload: { id: command.id, stream, chunk } });
}

function finalizeCommand(command: CommandRecord, status: CommandStatus, error?: string) {
  command.status = status;
  command.finishedAt = Date.now();
  if (error) {
    command.error = error;
  }
  activeCommand = null;
  activeProcess = null;
  broadcast({ type: 'command_update', payload: summarizeCommand(command) });
  broadcast({ type: 'system_status', payload: snapshot() });
}

function runNexusCommand(command: CommandRecord) {
  if (activeProcess) {
    throw new Error('Another command is already running');
  }
  if (!fs.existsSync(NEXUS_SCRIPT)) {
    throw new Error(`Cannot find aureon_nexus.py at ${NEXUS_SCRIPT}`);
  }

  const cycles = Number(command.payload?.cycles ?? 5);
  const interval = Number(command.payload?.interval ?? 5);
  const symbol = typeof command.payload?.symbol === 'string' ? command.payload.symbol : 'BTCUSDT';

  const args = [NEXUS_SCRIPT, '--cycles', String(cycles), '--interval', String(interval), '--symbol', symbol];
  const proc = spawn(PYTHON_BIN, args, {
    cwd: process.cwd(),
    env: { ...process.env, AUREON_COMMAND_GATEWAY: '1' },
  });

  activeCommand = command;
  activeProcess = proc;
  command.status = 'running';
  command.startedAt = Date.now();

  broadcast({ type: 'command_update', payload: summarizeCommand(command) });
  broadcast({ type: 'system_status', payload: snapshot() });

  proc.stdout.on('data', (buffer) => {
    trackCommandOutput(command, 'stdout', buffer.toString());
  });

  proc.stderr.on('data', (buffer) => {
    trackCommandOutput(command, 'stderr', buffer.toString());
  });

  proc.on('close', (code, signal) => {
    if (signal === 'SIGINT') {
      finalizeCommand(command, 'cancelled');
    } else if (code === 0) {
      finalizeCommand(command, 'completed');
    } else {
      finalizeCommand(command, 'failed', `Process exited with code ${code ?? 'unknown'}`);
    }
  });

  proc.on('error', (error) => {
    finalizeCommand(command, 'failed', error.message);
  });
}

function stopActiveCommand() {
  if (!activeProcess || !activeCommand) {
    return false;
  }
  activeProcess.kill('SIGINT');
  trackCommandOutput(activeCommand, 'stderr', '\nCommand interrupted by operator.\n');
  return true;
}

function handleCommand(type: string, payload?: Record<string, unknown>) {
  switch (type) {
    case 'start_stream':
      return { success: true, result: startStream(Number(payload?.intervalMs)) };
    case 'stop_stream':
      return { success: true, result: stopStream() };
    case 'run_nexus': {
      const command = registerCommand(type, payload);
      runNexusCommand(command);
      return { success: true, command: summarizeCommand(command) };
    }
    case 'stop_active_command':
      return { success: stopActiveCommand() };
    default:
      throw new Error(`Unknown command type: ${type}`);
  }
}

app.get('/health', (_req, res) => {
  res.json({ ok: true, status: snapshot() });
});

app.get('/api/command-center/status', (_req, res) => {
  res.json(snapshot());
});

app.post('/api/command-center/stream/start', (req, res) => {
  try {
    const { intervalMs } = req.body || {};
    const result = startStream(Number(intervalMs));
    res.json({ success: true, result });
  } catch (error) {
    res.status(400).json({ success: false, error: error instanceof Error ? error.message : 'Unknown error' });
  }
});

app.post('/api/command-center/stream/stop', (_req, res) => {
  const result = stopStream();
  res.json({ success: true, result });
});

app.post('/api/command-center/nexus/run', (req, res) => {
  try {
    const { cycles, interval, symbol } = req.body || {};
    const response = handleCommand('run_nexus', { cycles, interval, symbol });
    res.json(response);
  } catch (error) {
    res.status(400).json({ success: false, error: error instanceof Error ? error.message : 'Unknown error' });
  }
});

app.post('/api/command-center/nexus/stop', (_req, res) => {
  const success = stopActiveCommand();
  res.json({ success });
});

wss.on('connection', (socket) => {
  clients.add(socket);
  socket.send(JSON.stringify({ type: 'system_status', payload: snapshot() }));
  if (lastPayload) {
    socket.send(JSON.stringify({ type: 'stream_tick', payload: lastPayload }));
  }

  socket.on('message', (raw) => {
    try {
      const parsed = JSON.parse(raw.toString());
      if (parsed?.type === 'ping') {
        socket.send(JSON.stringify({ type: 'pong', ts: Date.now() }));
        return;
      }
      if (parsed?.type === 'status_request') {
        socket.send(JSON.stringify({ type: 'system_status', payload: snapshot() }));
        return;
      }
      if (parsed?.type === 'command') {
        const response = handleCommand(String(parsed.command), parsed.payload);
        socket.send(JSON.stringify({ type: 'command_response', payload: response }));
      }
    } catch (error) {
      socket.send(JSON.stringify({ type: 'command_response', error: error instanceof Error ? error.message : 'Invalid payload' }));
    }
  });

  socket.on('close', () => {
    clients.delete(socket);
    broadcast({ type: 'system_status', payload: snapshot() });
  });
});

httpServer.listen(PORT, () => {
  console.log(`🛰️  Nexus Command Server listening on http://localhost:${PORT}`);
  console.log(`📡 WebSocket stream available at ws://localhost:${PORT}${SOCKET_PATH}`);
});
