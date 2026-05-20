# Everything Codex Can Do

This document is the operator-facing capability map for Codex in this desktop
workspace. Aureon should use it as a bridge target: read each capability,
compare it with Aureon's own systems, wire what is missing, test the result,
and publish a completion report with evidence.

## Operating Contract

- Codex can read the repo, understand the request, plan the work, edit files,
  run tests, inspect a local UI, and explain what changed.
- Codex keeps changes scoped, protects unrelated user work, avoids destructive
  git commands, and does not reveal secrets.
- Codex can direct Aureon, but Aureon should own its own execution path by
  producing evidence files, UI panels, tests, and completion reports from inside
  the repo.
- Codex will not remove runtime, financial, legal, credential, or safety
  boundaries. Live orders, filings, payments, credentials, and external
  mutations require the existing runtime gates and user authority.

## Capability Map

| Codex capability | What Codex can do | Aureon bridge requirement |
| --- | --- | --- |
| Prompt intake | Accept natural language, infer intent, and decide what kind of work is needed. | Aureon must create typed goal contracts with owner, route, source evidence, and next action. |
| Planning | Break a broad goal into ordered steps, blockers, risks, and acceptance criteria. | Aureon must publish a plan with who, what, where, when, how, act, tests, and completion state. |
| Repo cartography | Search files, inspect modules, understand dependencies, and avoid blind edits. | Aureon must route every code task through repo self-catalog, path ownership, and test discovery. |
| File editing | Apply focused patches and preserve unrelated dirty work. | Aureon must use a safe code authoring lane with patch summaries and no silent overwrites. |
| Shell execution | Run PowerShell commands, Python modules, npm builds, tests, status checks, and logs. | Aureon must record command, cwd, return code, stdout/stderr tail, and pass/fail evidence. |
| Test and build verification | Run focused pytest suites, frontend builds, smoke checks, and regression tests. | Aureon must attach required tests to every work order and mark untested work as incomplete. |
| Browser inspection | Open local URLs, inspect rendered text, catch frontend runtime errors, and verify UI state. | Aureon must add a browser smoke bridge that checks local console pages and writes visual/runtime evidence. |
| Frontend implementation | Build React/TypeScript UI panels, mount components, respect design patterns, and build the app. | Aureon must generate mounted console cards for new evidence artifacts and run `npm run build`. |
| Backend/API integration | Add Python modules, endpoints, status reports, JSON artifacts, and runtime adapters. | Aureon must keep API schemas documented and test endpoint/status behavior. |
| Evidence publication | Produce summaries, audit JSON, Markdown reports, public frontend JSON, and status cards. | Aureon must publish state, docs/audits, frontend/public, and console visibility for completed work. |
| Git operations | Review dirty files, avoid runtime/private state, scan for secrets, commit, and push when asked. | Aureon must build a release bridge that classifies files, runs checks, proposes commits, and pushes only on explicit operator request. |
| Web research | Search the web when facts may be stale, use official/primary sources for technical work, and cite sources. | Aureon must route research tasks through source-linked learning and preserve references in vault/audits. |
| OpenAI/API documentation | Use official OpenAI docs for current API/model guidance. | Aureon must know when to consult official docs instead of stale local assumptions. |
| Documents and PDFs | Create and edit document artifacts, render/verify documents, and produce human-readable reports. | Aureon must route document work through its voice/document system and verify generated artifacts. |
| Image generation | Generate bitmap visuals or edit images when requested. | Aureon must treat generated visuals as presentation assets, not hidden evidence. |
| Automations | Create reminders, monitors, and recurring follow-ups where supported. | Aureon must record schedules and keep automation prompts self-contained. |
| Agent delegation | When explicitly authorized, split work across agents with clear ownership. | Aureon must build a coder-swarm director with disjoint file ownership and integration evidence. |
| Desktop/VM handoff | Use safe desktop or remote-run handoff paths for inspection and execution. | Aureon must keep desktop control dry-run by default and require explicit arming for live actions. |
| Data processing | Read structured files, JSON, CSV, documents, logs, and generated reports. | Aureon must preserve raw evidence separately from human-readable summaries. |
| Security review | Identify credential risks, unsafe mutations, missing tests, stale evidence, and runtime blockers. | Aureon must keep credential values hidden and publish blocker reasons instead of pretending readiness. |
| Trading runtime analysis | Inspect runtime status, stale reasons, exchange readiness, HNC/Auris evidence, and trading checklists. | Aureon must keep decision evidence fresh, runtime-gated, timestamped, and tied to live/source truth. |
| Accounting support | Generate, verify, and explain accounting support packs without submitting filings. | Aureon must keep official filing/payment manual-only and preserve existing totals unless explicitly changed. |
| README/runbook updates | Keep public docs current with real paths, commands, capabilities, and safety boundaries. | Aureon must update docs after system changes and exclude secrets/local private packs. |
| Clarification | Ask concise questions only when a missing answer blocks safe execution. | Aureon must record assumptions and ask only blocking questions before continuing. |
| Final reporting | Explain what was done, what was tested, what failed, and what remains. | Aureon must produce completion reports with evidence, not just claims. |

## What Aureon Must Build From This

1. Ingest this Markdown file as source evidence.
2. Classify every capability into Aureon equivalents, partial matches, and gaps.
3. For every gap, generate an exact code work order with target files, tests, and
   expected public evidence.
4. Use Aureon's own coding organism path to write or update the needed system
   code.
5. Run focused tests and frontend build checks where relevant.
6. Publish a completion report showing:
   - what it read,
   - what it understood,
   - what it changed,
   - how it tested itself,
   - what passed,
   - what still needs work.

## Acceptance Criteria

- The file is available to the coding organism UI as an upload/loadable source.
- Aureon can route a prompt that references this file.
- Aureon writes a public ingestion/progress report.
- Aureon reports its own validation results.
- The report names incomplete bridges instead of hiding them.

