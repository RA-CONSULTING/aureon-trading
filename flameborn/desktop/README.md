# Desktop Runtime Experiment

This folder contains the first reversible Electron migration scaffold.

## Goal

Wrap the existing FlameBorn web UI in a desktop shell while preserving:
- the stable web app
- the Cloudflare deployment path
- the local runtime split

## Current approach

Electron shell loads the existing local web UI:
- web UI: `http://127.0.0.1:4173`
- local runtime: `http://127.0.0.1:7331`

The shell can auto-start:
- `node server.mjs`
- `node runtime/server.mjs`
- `bash scripts/start_aureon_brain_local.sh` in Aureon-only mode

## Install

```bash
cd /home/l/CodexPROsSparrow/desktop
npm install
```

## Start

```bash
npm start
```

## Useful env flags

- `FLAMEBORN_SKIP_AUTO_SERVERS=true`
- `FLAMEBORN_DESKTOP_DEVTOOLS=true`
- `FLAMEBORN_WEB_URL=http://127.0.0.1:4173`
- `FLAMEBORN_RUNTIME_URL=http://127.0.0.1:7331`

## Security notes

- renderer has `nodeIntegration: false`
- preload bridge is explicit
- shell does not bypass OS permissions
- runtime remains responsible for command execution controls

## Desktop controls now exposed in the app

When running inside Electron, the web UI gets a desktop control panel with:
- desktop/web/runtime/Aureon status
- restart buttons for web, runtime, Aureon
- log folder opener
