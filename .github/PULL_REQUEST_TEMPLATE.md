<!-- Thank you for contributing to Aureon. Keep PRs focused and reviewable. -->

## Summary

<!-- What does this change do, and why? -->

## Changes

<!-- Bullet the key changes. -->
-

## Verification

<!-- How did you verify it works? Check what applies. -->
- [ ] `ruff check aureon/operator/ aureon/saas/` clean
- [ ] `mypy aureon/operator/ aureon/saas/` clean
- [ ] `AUREON_LLM_OFFLINE=1 pytest tests/test_operator_*.py tests/test_saas_*.py tests/test_connectome.py -q` green
- [ ] `frontend` builds (`npm run build`) — if the frontend changed
- [ ] No secrets, credentials, or private data added

## Notes

<!-- Anything reviewers should know: trade-offs, follow-ups, staged items. -->
