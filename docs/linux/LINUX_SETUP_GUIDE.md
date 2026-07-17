# Aureon on Linux — full setup guide

A native, from-source Linux install of the whole Aureon system — the same working
process set the Windows launcher starts, brought up with one command, or managed as a
systemd service. No Docker required (Docker paths still exist under `deploy/` if you
prefer them).

> **Safety.** The trading swarm starts in **dry/paper mode by default**
> (`AUREON_LIVE_TRADING=0`). Live trading is armed only with an explicit `--live` flag
> (or setting `AUREON_LIVE_TRADING=1`), and even then the hard boundary holds — the
> conscience veto and runtime gates stay in force, and `AUREON_LOCAL_ACTIONS_ARMED` /
> `AUREON_SOUL_ACT` stay unset (no autonomous irreversible execution).

## 1. Prerequisites

- **Python 3.11+** (`python3 --version`)
- **Node 20+** (optional — only to build/serve the Vite dashboards; `node --version`)
- Standard build tools (`build-essential`) if you compile any wheels.

## 2. Install

```bash
git clone <your-fork> aureon && cd aureon
scripts/linux/install-linux.sh
```

This creates `.venv`, installs the organism core (`pip install -e '.[operator]'`) plus the
Linux-safe full stack (`requirements-linux.txt` — `requirements.txt` minus the Windows/desktop
deps that don't belong on a server), seeds `.env` from `.env.example`, and builds the frontend
if Node is present. Add your keys to `.env` (optional — the system runs degraded without them).

## 3. Run the whole system (one command)

```bash
scripts/linux/aureon-up.sh                 # full stack, dry/paper (safe)
scripts/linux/aureon-up.sh --organism-only # just operator + organism + hnc (+ frontend)
scripts/linux/aureon-up.sh --no-frontend   # skip the Vite dashboard
scripts/linux/aureon-up.sh --live          # arm live trading (still runtime-gated)
```

`aureon-up.sh` runs `supervisord` (foreground) over `deploy/supervisord.linux.conf`, which
starts the verified-current `python -m aureon.*` process set. Stop / check status:

```bash
scripts/linux/aureon-status.sh   # supervisor status + health probes
scripts/linux/aureon-down.sh     # graceful shutdown
```

## 4. Dashboards & ports

| Surface | URL | Notes |
|---|---|---|
| Operator (grounded cognition, `/healthz`) | http://localhost:8790 | the cognition gateway + `/watch` PWA |
| Pro dashboard (`/health`) | http://localhost:8080 | primary trading UI |
| Frontend (Vite) | http://localhost:8081 | the React console |
| Market status server | http://localhost:8791 | live market feed |
| Mind hub | http://localhost:13002 | thought/action stream |

> **Port note:** the operator's *code default* is 8080, but every deploy asset (and this
> Linux stack) sets `AUREON_OPERATOR_PORT=8790` explicitly so it never collides with the pro
> dashboard on 8080. The launcher and systemd units set it for you.

## 5. Run as a service (systemd)

**Whole system** (supervisord under one unit):

```bash
sudo cp deploy/systemd/aureon.service /etc/systemd/system/
# edit WorkingDirectory / ExecStart / User to your install path (default /opt/aureon, user aureon)
sudo systemctl daemon-reload && sudo systemctl enable --now aureon
journalctl -u aureon -f
```

**Organism core only** (three standalone units + a target):

```bash
sudo cp deploy/systemd/aureon-*.service deploy/systemd/aureon.target /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now aureon.target
```

Set `AUREON_LIVE_TRADING=1` in `/opt/aureon/.env` (or a systemd drop-in) to arm live trading;
it stays runtime-gated regardless.

## 6. Troubleshooting

- **`No .venv found`** — run `scripts/linux/install-linux.sh` first.
- **A daemon keeps restarting** — check `state/logs/<program>.log`; most trading processes
  degrade gracefully without exchange keys (they idle rather than crash).
- **Frontend not served** — install Node 20+ and re-run the install (or `cd frontend && npm ci && npm run dev`).
- **`pip install` fails on `pycaw`/`comtypes`** — you used `requirements.txt` (Windows set). Use
  `requirements-linux.txt` (what the installer uses).

## 📚 Related
- [`LINUX_QUICK_START.md`](LINUX_QUICK_START.md) · [`LINUX_COMMAND_CHEAT_SHEET.md`](LINUX_COMMAND_CHEAT_SHEET.md)
- [`../deployment/`](../deployment/) — Docker / DigitalOcean paths
- [`../windows/WINDOWS_SETUP_GUIDE.md`](../windows/WINDOWS_SETUP_GUIDE.md) — the Windows equivalent
