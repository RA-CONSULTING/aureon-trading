# Aureon on Linux — quick start

Three commands from a fresh clone:

```bash
scripts/linux/install-linux.sh     # venv + deps + .env + frontend build
scripts/linux/aureon-up.sh         # bring up the whole system (dry/paper, safe)
scripts/linux/aureon-status.sh     # see it breathing
```

Then open **http://localhost:8790/healthz** (operator) and **http://localhost:8081**
(frontend console).

- **Organism only** (no trading swarm): `scripts/linux/aureon-up.sh --organism-only`
- **Arm live trading** (still runtime-gated): `scripts/linux/aureon-up.sh --live`
- **Stop**: `scripts/linux/aureon-down.sh`
- **As a service**: `sudo systemctl enable --now aureon` (see the setup guide)

Default is **dry/paper** — nothing trades live until you pass `--live`, and the hard
boundary (no autonomous irreversible execution) holds regardless.

Full detail: [`LINUX_SETUP_GUIDE.md`](LINUX_SETUP_GUIDE.md).
