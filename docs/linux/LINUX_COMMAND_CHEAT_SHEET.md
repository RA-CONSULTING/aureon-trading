# Aureon on Linux — command cheat sheet

All commands run from the repo root with the venv active (`. .venv/bin/activate`) or via
`.venv/bin/python`. This mirrors the Windows cheat sheet, using the current `aureon.*` modules.

## Lifecycle
| Do | Command |
|---|---|
| Install | `scripts/linux/install-linux.sh` |
| Bring up the whole system | `scripts/linux/aureon-up.sh` |
| Organism core only | `scripts/linux/aureon-up.sh --organism-only` |
| Arm live trading (gated) | `scripts/linux/aureon-up.sh --live` |
| Status + health | `scripts/linux/aureon-status.sh` |
| Stop | `scripts/linux/aureon-down.sh` |
| Service (whole system) | `sudo systemctl enable --now aureon` |
| Service (organism only) | `sudo systemctl enable --now aureon.target` |

## Individual processes (what supervisord starts)
| Process | Command |
|---|---|
| HNC live daemon (Λ driver) | `python -m aureon.core.hnc_live_daemon` |
| Organism daemon (connectome breath) | `python -m aureon.core.organism_daemon` |
| Operator (cognition gateway, :8790) | `AUREON_OPERATOR_PORT=8790 python -m aureon.operator.operator_server` |
| Market status server (:8791) | `python -m aureon.exchanges.unified_market_status_server --port 8791` |
| Market data feeder | `python -m aureon.data_feeds.ws_market_data_feeder --binance --kraken --alpaca --capital` |
| Market trader (dry unless `--live`) | `python -m aureon.exchanges.unified_market_trader --interval 30` |
| Orca kill cycle | `python -m aureon.bots.orca_complete_kill_cycle --autonomous --initial-capital 10000` |
| Strategy unity | `python -m aureon.trading.parallel_strategy_unity --watch` |
| Queen eternal machine | `python -m aureon.queen.queen_eternal_machine --interval 10` |
| Mind hub (:13002) | `python -m aureon.autonomous.aureon_mind_thought_action_hub` |
| Self-questioning | `python -m aureon.autonomous.aureon_self_questioning_ai --loop` |
| Runtime observer | `python -m aureon.autonomous.aureon_organism_runtime_observer --watch --refresh-core` |
| Autonomous self-run | `python -m aureon.autonomous.aureon_autonomous_self_run_loop --forever` |
| Pro dashboard (:8080) | `python -m aureon.monitors.aureon_pro_dashboard` |
| Frontend (:8081) | `cd frontend && npm run dev -- --host 0.0.0.0 --port 8081` |

## Console entry points (after `pip install -e .`)
| Script | Runs |
|---|---|
| `aureon-operator` | the operator gateway |
| `aureon-organism` | the organism daemon |
| `aureon-hnc` | the HNC live daemon |

## Safety switches
| Env | Default | Effect |
|---|---|---|
| `AUREON_LIVE_TRADING` | `0` (dry/paper) | `1` arms live trading — still conscience/runtime-gated |
| `AUREON_START_SWARM` | `true` | `false` = organism core only |
| `AUREON_START_FRONTEND` | `true` | `false` = no Vite dashboard |
| `AUREON_OPERATOR_PORT` | `8790` (set by the launcher) | operator HTTP port |
| `AUREON_LOCAL_ACTIONS_ARMED` / `AUREON_SOUL_ACT` | unset | leave unset — arming these is the irreversible-action boundary |
