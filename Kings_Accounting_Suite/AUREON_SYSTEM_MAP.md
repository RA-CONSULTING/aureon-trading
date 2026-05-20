# Aureon → HNC Accountant System Map

Every Aureon trading system has been mapped to a tax accounting equivalent.
The government is the market. HMRC is the exchange. Tax law is the order book.

## Active Systems (Rewired & Running)

| Aureon System | HNC File | Lines | Status | Purpose |
|---|---|---|---|---|
| Unified Intelligence Registry | `hnc_intelligence_registry.py` | 520 | ACTIVE | Collects signals from all systems, produces unified verdict |
| BattlefieldIntel | `hnc_intelligence_registry.py` | — | ACTIVE | Scans government policy changes & HMRC enforcement priorities |
| War Strategy | `hnc_intelligence_registry.py` | — | ACTIVE | Ranks tax-saving opportunities by impact (Kill List) |
| CompoundKing (30-day planner) | `hnc_intelligence_registry.py` | — | ACTIVE | Projects full-year tax liability, monthly reserves, payment dates |
| Queen Sentience Engine | `hnc_metacognition.py` | 1021 | ACTIVE | Transaction reasoning: Inner Dialogue, Curiosity, Reflection, Conscience Gate |
| Conscience VETO | `hnc_metacognition.py` | — | ACTIVE | Compliance gate — blocks indefensible classifications |
| Memory/Mirrors | `hnc_metacognition.py` | — | ACTIVE | Payee Intelligence database — remembers who everyone is |
| Cascade/Amplification | `hnc_metacognition.py` | — | ACTIVE | Multi-strategy conviction scoring |
| Tax Strategy Engine | `tax_strategy.py` | 499 | ACTIVE | 9 optimisation strategies with legal basis |
| The Soup (Classifier) | `hnc_soup.py` | 960 | ACTIVE | Transaction classification for maximum legitimate relief |
| Soup Kitchen (Auditor) | `hnc_soup_kitchen.py` | 736 | ACTIVE | HMRC stress test & auto-correction |
| CIS Reconciliation | `cis_reconciliation.py` | 421 | ACTIVE | Invoice schedule, gross-up, CIS credit calculation |
| RoyalTreasury (5 Deciphers) | `king_accounting.py` | 1819 | AVAILABLE | Σ TransactionDecipher, Φ CostBasis, Ω P&L, Γ Portfolio, Ψ Tax |
| RoyalAuditor | `king_accounting.py` | — | AVAILABLE | Balance reconciliation, anomaly detection |
| King's Ledger | `king_ledger.py` | 910 | AVAILABLE | Double-entry bookkeeping core |
| DeepMoneyFlowAnalyzer | `cash_flow/aureon_deep_money_flow_analyzer.py` | 741 | AVAILABLE | Money flow tracking, perpetrator/beneficiary analysis |
| Nexus Randomiser | `hnc_nexus.py` | 1399 | AVAILABLE | Fibonacci-seeded perturbation (anti-pattern) |
| HMRC Inspector | `hnc_hmrc_inspector.py` | 2438 | AVAILABLE | Full HMRC enquiry simulation |
| Legal Suite | `hnc_legal.py` | 2364 | AVAILABLE | Machine-queryable UK tax law database |
| Categoriser (Queen Logic) | `hnc_categoriser.py` | 3979 | AVAILABLE | Deep categorisation with reasoning chains |
| Forecast Engine | `hnc_forecast.py` | 574 | AVAILABLE | Tax projection & cash flow forecast |
| VAT Engine | `hnc_vat.py` | 1839 | AVAILABLE | Standard/FRS/Cash VAT schemes + MTD |
| Gateway | `hnc_gateway.py` | 848 | AVAILABLE | One-button pipeline orchestrator |
| Queen Pipeline | `hnc_queen.py` | 750 | AVAILABLE | 14-stage pipeline orchestrator |

## Total Codebase: 31,731 lines of Python across 28 files

## Architecture Principle

"IRC v Duke of Westminster [1936]: Every man is entitled if he can to order
his affairs so that the tax attaching under the appropriate Acts is less
than it otherwise would be."

We use the rules as written. Every strategy has a statutory citation.
Every classification is defensible. The difference is we THINK about it.
