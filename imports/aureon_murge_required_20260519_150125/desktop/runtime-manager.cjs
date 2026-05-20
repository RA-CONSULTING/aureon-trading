const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');

const ROOT_DIR = path.resolve(__dirname, '..');
const LOG_DIR = path.join(ROOT_DIR, 'logs', 'desktop');
const WEB_URL = process.env.FLAMEBORN_WEB_URL || 'http://127.0.0.1:4173';
const RUNTIME_URL = process.env.FLAMEBORN_RUNTIME_URL || 'http://127.0.0.1:7331';
const AUREON_URL = process.env.FLAMEBORN_AUREON_URL || 'http://127.0.0.1:5566';

function ensureLogDir() {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function requestOk(targetUrl) {
  return new Promise((resolve) => {
    const req = http.get(targetUrl, (res) => {
      res.resume();
      resolve(res.statusCode >= 200 && res.statusCode < 500);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(1500, () => {
      req.destroy();
      resolve(false);
    });
  });
}

function requestJson(targetUrl) {
  return new Promise((resolve) => {
    const req = http.get(targetUrl, (res) => {
      let body = '';
      res.on('data', (chunk) => {
        body += chunk.toString('utf8');
      });
      res.on('end', () => {
        try {
          resolve(JSON.parse(body || '{}'));
        } catch {
          resolve(null);
        }
      });
    });
    req.on('error', () => resolve(null));
    req.setTimeout(2000, () => {
      req.destroy();
      resolve(null);
    });
  });
}

async function waitForUrl(targetUrl, attempts = 40, delayMs = 500) {
  for (let index = 0; index < attempts; index += 1) {
    if (await requestOk(targetUrl)) return true;
    await wait(delayMs);
  }
  return false;
}

function spawnLogged(command, args, name, extraEnv = {}) {
  ensureLogDir();
  const logPath = path.join(LOG_DIR, `${name}.log`);
  const logFd = fs.openSync(logPath, 'a');
  const child = spawn(command, args, {
    cwd: ROOT_DIR,
    env: { ...process.env, ...extraEnv },
    detached: false,
    stdio: ['ignore', logFd, logFd],
  });
  child.on('close', () => {
    try { fs.closeSync(logFd); } catch {}
  });
  return { child, logPath };
}

const SERVICE_DEFS = {
  web: {
    name: 'web',
    url: WEB_URL,
    healthUrl: `${WEB_URL}/api/aureon/status`,
    command: process.execPath,
    args: ['server.mjs'],
    logName: 'web-app',
    env: {
      HOST: '127.0.0.1',
      AUREON_API_BASE_URL: AUREON_URL,
      AUREON_CHAT_PATH: '/api/message',
      AUREON_VAULT_PATH: path.join(ROOT_DIR, 'logs', 'aureon-vault'),
    },
  },
  runtime: {
    name: 'runtime',
    url: RUNTIME_URL,
    healthUrl: `${RUNTIME_URL}/health`,
    command: process.execPath,
    args: ['runtime/server.mjs'],
    logName: 'local-runtime',
    env: {},
  },
  aureon: {
    name: 'aureon',
    url: AUREON_URL,
    healthUrl: `${AUREON_URL}/api/status`,
    command: '/bin/bash',
    args: ['scripts/start_aureon_brain_local.sh'],
    logName: 'aureon-bridge',
    env: { FLAMEBORN_SKIP_WEB_SERVER: 'true' },
  },
};

class RuntimeManager {
  constructor() {
    this.processes = new Map();
  }

  async ensureServices() {
    const status = {
      services: {},
      started: [],
      logs: {},
    };

    if (String(process.env.FLAMEBORN_DESKTOP_AUTO_AUREON || 'true').toLowerCase() !== 'false') {
      status.services.aureon = await this.ensureService('aureon', false);
      if (status.services.aureon.startedByDesktop) status.started.push('aureon');
      if (status.services.aureon.logPath) status.logs.aureon = status.services.aureon.logPath;
    } else {
      status.services.aureon = await this.inspectService('aureon');
    }

    for (const key of ['web', 'runtime']) {
      status.services[key] = await this.ensureService(key, false);
      if (status.services[key].startedByDesktop) status.started.push(key);
      if (status.services[key].logPath) status.logs[key] = status.services[key].logPath;
    }

    return status;
  }

  async inspectService(name) {
    const def = SERVICE_DEFS[name];
    const reachable = await requestOk(def.healthUrl);
    const managed = this.processes.get(name) || null;
    return {
      name,
      url: def.url,
      healthUrl: def.healthUrl,
      reachable,
      startedByDesktop: Boolean(managed),
      runningPid: managed?.pid || null,
      logPath: path.join(LOG_DIR, `${def.logName}.log`),
    };
  }

  async ensureService(name, forceRestart = false) {
    const def = SERVICE_DEFS[name];
    if (!def) throw new Error(`Unknown service: ${name}`);

    if (forceRestart) {
      await this.stopService(name);
    }

    const reachable = await requestOk(def.healthUrl);
    if (!reachable) {
      const proc = spawnLogged(def.command, def.args, def.logName, def.env);
      this.processes.set(name, proc.child);
      const running = await waitForUrl(def.healthUrl, name === 'aureon' ? 60 : 40, 500);
      return {
        name,
        url: def.url,
        healthUrl: def.healthUrl,
        reachable: running,
        startedByDesktop: true,
        runningPid: proc.child.pid,
        logPath: proc.logPath,
      };
    }

    return {
      name,
      url: def.url,
      healthUrl: def.healthUrl,
      reachable: true,
      startedByDesktop: this.processes.has(name),
      runningPid: this.processes.get(name)?.pid || null,
      logPath: path.join(LOG_DIR, `${def.logName}.log`),
    };
  }

  async stopService(name) {
    const child = this.processes.get(name);
    if (!child) return false;
    if (!child.killed) {
      child.kill('SIGTERM');
      await wait(400);
    }
    this.processes.delete(name);
    return true;
  }

  async restartService(name) {
    return this.ensureService(name, true);
  }

  getLogPath(name) {
    const def = SERVICE_DEFS[name];
    if (!def) throw new Error(`Unknown service: ${name}`);
    return path.join(LOG_DIR, `${def.logName}.log`);
  }

  async getStatus() {
    const webReachable = await requestOk(SERVICE_DEFS.web.healthUrl);
    const runtimeReachable = await requestOk(SERVICE_DEFS.runtime.healthUrl);
    const aureonReachable = await requestOk(SERVICE_DEFS.aureon.healthUrl);
    const runtimeInfo = runtimeReachable ? await requestJson(`${RUNTIME_URL}/api/runtime/info`) : null;
    const sandboxStatus = runtimeReachable ? await requestJson(`${RUNTIME_URL}/api/sandbox/status`) : null;

    return {
      webUrl: WEB_URL,
      runtimeUrl: RUNTIME_URL,
      aureonUrl: AUREON_URL,
      webReachable,
      runtimeReachable,
      aureonReachable,
      runtimeInfo,
      sandboxStatus,
      services: {
        web: await this.inspectService('web'),
        runtime: await this.inspectService('runtime'),
        aureon: await this.inspectService('aureon'),
      },
      managedProcesses: Array.from(this.processes.keys()),
      autoStartDisabled: process.env.FLAMEBORN_SKIP_AUTO_SERVERS === 'true',
      logsRoot: LOG_DIR,
    };
  }

  shutdown() {
    for (const child of this.processes.values()) {
      if (!child.killed) {
        child.kill('SIGTERM');
      }
    }
    this.processes.clear();
  }
}

module.exports = {
  RuntimeManager,
  WEB_URL,
  RUNTIME_URL,
  AUREON_URL,
};
