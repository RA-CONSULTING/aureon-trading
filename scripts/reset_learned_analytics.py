#!/usr/bin/env python3
"""\
🧠 Reset Learned Analytics (AdaptiveLearningEngine)

Why:
- The Learned analytics is currently using trade outcomes from an earlier tuning/training era.
- When you change the strategy objective (e.g., “net pennies after costs”), old outcomes can poison gating.

What this does:
- Creates a timestamped backup of `adaptive_learning_history.json`.
- Resets the file to an empty trade list and empty thresholds so current defaults apply.

Safe by default:
- Requires `--yes` to actually modify anything.

Usage:
  python scripts/reset_learned_analytics.py --yes

Optional:
  python scripts/reset_learned_analytics.py --yes --reason "penny-profit regime reset"
"""

from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import argparse

from learned_analytics_reset import reset_learned_analytics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--yes', action='store_true', help='Actually perform the reset (required).')
    parser.add_argument('--file', default='adaptive_learning_history.json', help='Path to learning history JSON.')
    parser.add_argument('--reason', default='manual reset', help='Reason recorded into the reset file.')
    parser.add_argument('--regime-tag', default='penny_profit_v1', help='Regime tag to make startup reset idempotent.')
    args = parser.parse_args()

    path = args.file

    if not args.yes:
        print('❌ Refusing to reset without --yes')
        print(f'   Target file: {path}')
        return 2

    result = reset_learned_analytics(
        history_path=path,
        reason=args.reason,
        regime_tag=args.regime_tag,
        archive=True,
    )

    if not result.did_reset:
        print(f'❌ Reset failed: {result.error or "unknown error"}')
        return 1

    if result.backup_path:
        print(f'📦 Archived existing learned history → {result.backup_path}')

    print(f'✅ Reset learned analytics: {path}')
    print('   - trades: 0')
    print('   - thresholds: defaults will be used on next startup')
    print('   Restart the bot process to pick up the reset.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
