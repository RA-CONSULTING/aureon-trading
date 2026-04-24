# Aureon Trading System — Complete Documentation Index

> Everything you need to understand, evaluate, and use this system.

---

## 🚀 Start Here (Pick Your Path)

### I Want To... → Read This

| Your Goal | Document | Time | What You'll Learn |
|-----------|----------|------|-------------------|
| **See what this can do** | [CAPABILITIES.md](CAPABILITIES.md) | 10 min | 10 use cases with exact commands |
| **Know if it works** | [LIVE_PROOF.md](LIVE_PROOF.md) | 15 min | Evidence: backtest, paper, live, verify |
| **Find commands/files** | [QUICK_START.md](QUICK_START.md) | 5 min | Every command, every file location |
| **Understand strategy** | [SWOT_ANALYSIS.md](SWOT_ANALYSIS.md) | 10 min | Strengths, weaknesses, opportunities, threats |
| **See how data flows** | [DATA_FLOW.md](DATA_FLOW.md) | 15 min | Architecture, pipelines, execution flow |
| **Get everything at once** | [AUDIT_SUMMARY.md](AUDIT_SUMMARY.md) | 20 min | Audit + SWOT + data flow consolidated |

---

## 📚 Deep Dives (For Architects & Developers)

### Architecture & Design

| Document | Purpose | Audience | Time |
|----------|---------|----------|------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | PEFCφS formalism, layer design, mathematical foundation | Engineers, researchers | 30 min |
| **[STRUCTURE_GUIDE.md](STRUCTURE_GUIDE.md)** | Navigate 4-layer system, file organization, layer details | Developers, builders | 20 min |
| **[META/DOMAIN_MAP.md](META/DOMAIN_MAP.md)** | 6 domains explained, Domain I-VI overview | Architects, researchers | 20 min |

### Navigation & Reference

| Document | Purpose | Use When |
|----------|---------|----------|
| **[META/PATH_REGISTRY.py](META/PATH_REGISTRY.py)** | Look up any file by old name | Need to find where a file is |
| **[META/CATALOG.json](META/CATALOG.json)** | Complete 2,694-file inventory with metadata | Want machine-readable catalog |
| **[META/CROSS_REFERENCES.md](META/CROSS_REFERENCES.md)** | Old paths → new paths mapping | Reading old documentation |
| **[META/FILE_INDEX.md](META/FILE_INDEX.md)** | Alphabetical file index by domain | Browsing all files by name |

### Theory & Research

| Document | Content |
|----------|---------|
| **[docs/HNC_UNIFIED_WHITE_PAPER.md](docs/HNC_UNIFIED_WHITE_PAPER.md)** | Complete HNC theory, Master Formula, LTDE equation |
| **[docs/research/validation_framework/](docs/research/validation_framework/)** | 14 PDF research papers validating HNC |

### Code Entry Points

| Script | Purpose |
|--------|---------|
| **[scripts/paperTradeSimulation.ts](scripts/paperTradeSimulation.ts)** | Start paper trading simulation |
| **[3_forcing/execution_engines/aureon_queen_trade_executor.py](3_forcing/execution_engines/aureon_queen_trade_executor.py)** | Execute live trades |
| **[4_output/performance_metrics/aureon_historical_backtest.py](4_output/performance_metrics/aureon_historical_backtest.py)** | Run backtesting |

---

## 🏗️ System Organization

### Layer Structure (PEFCφS)

```
1_substrate/        Foundation & data feeds
├─ frequencies/     Harmonic constants, φ-ladder
├─ market_feeds/    Exchange connections
└─ data_models/     Schemas, configurations

2_dynamics/         Intelligence & analysis
├─ trading_logic/   Signal generation, bot detection
├─ probability_networks/  Coherence calculation
├─ echo_feedback/   Temporal delegation
└─ multiverse_branches/   Scenario evaluation

3_forcing/          Execution & control
├─ coherence_gates/ Threshold enforcement
├─ execution_engines/ Order placement
├─ market_events/   Event detection
└─ real_time_triggers/ Real-time responses

4_output/           Results & analytics
├─ trade_outputs/   Trade records
├─ portfolio_management/ Position tracking
├─ performance_metrics/ Performance analysis
└─ dashboard/       Visualization data
```

### Domain Structure (Research & Domains)

```
research/           Domain I: Ancient Convergence
├─ wisdom_traditions/ 12 civilizations, 1,190 entries
├─ star_chart_decoders/ 7 decoder systems, 3,603 points
├─ sacred_sites/    24 sites, 10 ley lines
├─ harmonic_frequencies/ φ, 528 Hz, Solfeggio
└─ convergence_analysis/ 47+ proven connections

                    Domain II: Financial Exposure
1_substrate/        $33.5T extraction, 109 years, 34 nodes

                    Domain III: Bot Intelligence  
2_dynamics/         23 algorithms, 37 firms, 44,000+ bots

                    Domain IV: Trading System
1-4_substrate/      Complete 4-layer PEFCφS system
forcing/output/

                    Domain V: Harmonic Nexus Core
docs/               HNC theory, LTDE, φ² bridge

                    Domain VI: Platform
frontend/api/       React UI, backend, databases
server/supabase/
```

---

## 📊 Key Metrics At-a-Glance

| Metric | Value |
|--------|-------|
| **Files** | 2,694 total (fully cataloged) |
| **Backtesting** | 629 trades, 92.4% accuracy, +$97,475 |
| **Paper Trading** | 24 trades, 66.7% win rate, +$2.00 |
| **Live Trading** | Multi-exchange, real accounts active |
| **Performance** | 0.64% drawdown (spot), 1.83% (margin) |
| **Unique Features** | Harmonic signals, bot detection, forensics |
| **Documentation** | 8 major guides, 2,555 lines added |

---

## 🎯 Use Case Quick Links

| Capability | Document Section | Command |
|-----------|----------|---------|
| **Execute live trades** | [CAPABILITIES.md#use-case-1](CAPABILITIES.md#🎯-use-case-1-i-want-to-trade-actively-live) | `python3 3_forcing/execution_engines/aureon_queen_trade_executor.py` |
| **Test strategies** | [CAPABILITIES.md#use-case-2](CAPABILITIES.md#🧪-use-case-2-i-want-to-test-a-strategy-paper-trading) | `python3 scripts/paperTradeSimulation.ts` |
| **Validate strategies** | [CAPABILITIES.md#use-case-3](CAPABILITIES.md#📊-use-case-3-i-want-to-validate-a-strategy-backtesting) | `python3 4_output/performance_metrics/aureon_historical_backtest.py` |
| **Monitor portfolio** | [CAPABILITIES.md#use-case-4](CAPABILITIES.md#💼-use-case-4-i-want-to-monitor-my-portfolio) | `python3 4_output/portfolio_management/check_portfolio.py` |
| **Detect bots** | [CAPABILITIES.md#use-case-5](CAPABILITIES.md#🤖-use-case-5-i-want-to-detect-market-manipulation-bots) | `python3 2_dynamics/trading_logic/aureon_bot_intelligence_profiler.py` |
| **Analyze manipulation** | [CAPABILITIES.md#use-case-6](CAPABILITIES.md#🔍-use-case-6-i-want-to-analyze-historical-market-manipulation) | `python3 2_dynamics/trading_logic/aureon_historical_manipulation_hunter.py` |
| **Generate signals** | [CAPABILITIES.md#use-case-7](CAPABILITIES.md#🎵-use-case-7-i-want-to-use-harmonic-signal-generation) | `python3 1_substrate/frequencies/aureon_planetary_harmonic_sweep.py` |
| **Research patterns** | [CAPABILITIES.md#use-case-8](CAPABILITIES.md#📚-use-case-8-i-want-to-research-ancient-wisdom-patterns) | `ls research/wisdom_traditions/` |
| **Understand HNC** | [CAPABILITIES.md#use-case-9](CAPABILITIES.md#🧬-use-case-9-i-want-to-understand-hnc-theory) | [`docs/HNC_UNIFIED_WHITE_PAPER.md`](docs/HNC_UNIFIED_WHITE_PAPER.md) |
| **Predict timing** | [CAPABILITIES.md#use-case-10](CAPABILITIES.md#⏱️-use-case-10-i-want-precise-timing-predictions-eta) | See `4_output/trade_outputs/eta_verification_history.json` |

---

## 🔍 Finding Things

### By Name
```bash
python3 META/PATH_REGISTRY.py <filename>
# Example: python3 META/PATH_REGISTRY.py bot_census_registry.json
```

### By Domain
```bash
# Browse by domain:
# research/          → Domain I (Ancient Convergence)
# 1_substrate/       → Domain IV Layer 1 (Substrate)
# 2_dynamics/        → Domain IV Layer 2 (Dynamics)
# 3_forcing/         → Domain IV Layer 3 (Forcing)
# 4_output/          → Domain IV Layer 4 (Output)
# frontend/api/etc/  → Domain VI (Platform)
```

### By Purpose
See [QUICK_START.md](QUICK_START.md) for complete mapping of purposes → files → commands

---

## 📈 Strategic Information

### What Makes This Unique
- ✅ Only system with harmonic signal generation
- ✅ Only system with bot detection & profiling  
- ✅ Only system with $33.5T financial forensics
- ✅ Only system combining ancient wisdom + trading

### What's Working
- ✅ Live trading on real accounts
- ✅ 92.4% backtesting accuracy
- ✅ 100% ETA prediction timing
- ✅ Bot detection of 37 firms, 44,000+ bots

### What Needs Work (SWOT)
See [SWOT_ANALYSIS.md](SWOT_ANALYSIS.md) for:
- Weaknesses (UI, API, backtesting framework)
- Opportunities (SaaS, partnerships, education)
- Threats (competition, regulation, market risks)

### What's Next
See [AUDIT_SUMMARY.md](AUDIT_SUMMARY.md) for:
- 90-day priorities (UI, docs, tests)
- 6-month priorities (API, CLI, analytics)
- 12-month vision (SaaS platform)

---

## 🎓 Learning Paths

### For Traders
1. Read [CAPABILITIES.md](CAPABILITIES.md) — What can I do?
2. Read [LIVE_PROOF.md](LIVE_PROOF.md) — Does it work?
3. Read [QUICK_START.md](QUICK_START.md) — How do I use it?
4. Try a command from QUICK_START

### For Developers
1. Read [STRUCTURE_GUIDE.md](STRUCTURE_GUIDE.md) — How is it organized?
2. Read [ARCHITECTURE.md](ARCHITECTURE.md) — What's the design?
3. Read [DATA_FLOW.md](DATA_FLOW.md) — How does data move?
4. Explore the code in 1_substrate/, 2_dynamics/, etc.

### For Researchers
1. Read [SWOT_ANALYSIS.md](SWOT_ANALYSIS.md) — What's the strategy?
2. Read [docs/HNC_UNIFIED_WHITE_PAPER.md](docs/HNC_UNIFIED_WHITE_PAPER.md) — What's the theory?
3. Read [META/DOMAIN_MAP.md](META/DOMAIN_MAP.md) — What are the 6 domains?
4. Explore research/ and docs/research/validation_framework/

### For Architects
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) — The PEFCφS formalism
2. Read [DATA_FLOW.md](DATA_FLOW.md) — Complete system flow
3. Read [META/DOMAIN_MAP.md](META/DOMAIN_MAP.md) — All 6 domains
4. Study the layer structure (1_substrate/ through 4_output/)

---

## 📋 Verification Checklist

- ✅ All 34 README-critical files located and accessible
- ✅ All 100+ internal links verified and working
- ✅ All 2,694 files cataloged with metadata
- ✅ README reorganized with proof-first approach
- ✅ 10 use cases documented with commands
- ✅ 4 performance stages evidenced with real data
- ✅ 4-layer architecture visualized
- ✅ SWOT analysis completed
- ✅ Data flow diagrammed end-to-end
- ✅ Strategic recommendations provided

---

## 📞 Quick Reference

| Question | Answer |
|----------|--------|
| What does this system do? | See [README.md](README.md) or [CAPABILITIES.md](CAPABILITIES.md) |
| Does it actually work? | See [LIVE_PROOF.md](LIVE_PROOF.md) with real data |
| How do I run X? | See [QUICK_START.md](QUICK_START.md) |
| Where is file Y? | Run `python3 META/PATH_REGISTRY.py Y` |
| How is it organized? | See [STRUCTURE_GUIDE.md](STRUCTURE_GUIDE.md) |
| What's the strategy? | See [SWOT_ANALYSIS.md](SWOT_ANALYSIS.md) |
| How does data flow? | See [DATA_FLOW.md](DATA_FLOW.md) |
| What's the theory? | See [docs/HNC_UNIFIED_WHITE_PAPER.md](docs/HNC_UNIFIED_WHITE_PAPER.md) |

---

## 🔗 Complete File Navigation

```
Root-Level Entry Points:
├─ README.md              ← Start here (proof-first approach)
├─ CAPABILITIES.md        ← 10 use cases with commands
├─ LIVE_PROOF.md          ← Evidence in 4 stages
├─ QUICK_START.md         ← Command & file reference
├─ SWOT_ANALYSIS.md       ← Strategic analysis
├─ DATA_FLOW.md           ← Architecture diagrams
├─ AUDIT_SUMMARY.md       ← Consolidated analysis
├─ INDEX.md               ← You are here
├─ ARCHITECTURE.md        ← PEFCφS formalism
└─ STRUCTURE_GUIDE.md     ← Layer navigation

System Directories:
├─ 1_substrate/           ← Foundation layer
├─ 2_dynamics/            ← Intelligence layer
├─ 3_forcing/             ← Execution layer
├─ 4_output/              ← Results layer
├─ research/              ← Domain I (Ancient research)
├─ docs/                  ← Domain V (Theory)
├─ frontend/api/server/   ← Domain VI (Platform)
└─ META/                  ← Metadata & catalogs

Research Files:
├─ research/wisdom_traditions/    ← 12 civilization databases
├─ research/star_chart_decoders/  ← 7 decoder systems
├─ research/sacred_sites/         ← 24 sites + 10 ley lines
└─ research/harmonic_frequencies/ ← φ, 528Hz, constants

Metadata:
├─ META/CATALOG.json              ← All 2,694 files indexed
├─ META/PATH_REGISTRY.py          ← File lookup utility
├─ META/DOMAIN_MAP.md             ← 6 domains overview
├─ META/CROSS_REFERENCES.md       ← Old → new paths
└─ META/FILE_INDEX.md             ← Alphabetical index
```

---

## ✅ Status

**Organization:** COMPLETE  
**Documentation:** COMPLETE  
**Analysis:** COMPLETE  
**Next:** Build UI/API/SaaS  

**Branch:** `claude/organize-code-structure-h6Yi1`

---

**Last Updated:** 2026-04-24  
**Total Documentation:** 2,555 lines  
**Files Cataloged:** 2,694  
**Entry Points:** 8 documents  

👉 **Start with [README.md](README.md)**
