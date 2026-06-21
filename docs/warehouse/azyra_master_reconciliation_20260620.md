# Azyra Master Audit Reconciliation - 2026-06-20

This note records the current master audit reconciliation package built from the validated human audit rows and the latest live Azyra warehouse balance export. It was refreshed on 2026-06-21 after the live historical-quantity posting transactions `A1014965` and `A1014966`.

## Local Outputs

Master reconciliation folder:

`C:\Users\Gary.Leckey\OneDrive - SFG Forwarding Ltd\Documents\sfg azrya intergrations\outputs\aureon_goal_contract_dispatcher\master_azyra_reconciliation_20260620`

Key files:

- Human-readable master workbook: `Azyra_Master_Audit_Reconciliation_20260620.xlsx`
- Live-status workbook copy: `..\historical_quantity_live_fix_20260620\Azyra_Master_Audit_Reconciliation_20260621_LIVE_STATUS.xlsx`
- Human-readable live-status copy: `..\historical_quantity_live_fix_20260620\Azyra_Master_Audit_Human_Readable_20260621_LIVE_STATUS.xlsx`
- Fresh Azyra export: `current_azyra_exports\Warehouse Balances Spreadsheet 89QU7W00J_20260621_163056.xlsx`
- Stock/UOM delta CSV: `human_vs_azyra_delta_candidates.csv`
- Location-level delta CSV: `human_vs_azyra_location_delta_candidates.csv`
- Validated human count batch CSV: `azyra_count_batch_file_validated_human_rows.csv`
- Summary JSON: `master_reconciliation_summary.json`

## Fresh Azyra Export

Exported through Aureon/Azyra, not manual user-self entry.

- Azyra environment: `SFG Live`
- Route: `WMS > Reports > Warehouse > Warehouse Balances Spreadsheet`
- Owner: `Decora Antrim`
- Warehouse: `Antrim`
- Condition: `All Conditions`
- Location filter: blank, all locations
- Stock-code filter: blank, all stock codes
- Detail by tracking number: checked
- Include stock codes with zero balance: checked
- Format: Excel `.xlsx`
- Report as at: `21/06/2026 16:30`

Export counts:

- Detail rows: `2,672`
- Free quantity total: `11,147`
- Balance quantity total: `12,231`
- Picking quantity total: `1,084`
- Stock codes: `1,750`
- Locations: `779`

## Human Audit Input

Input from the first audit-scan batch:

`C:\Users\Gary.Leckey\OneDrive - SFG Forwarding Ltd\Documents\sfg azrya intergrations\outputs\aureon_goal_contract_dispatcher\audit_scans_1st_batch_20260619`

Counts currently carried into the master reconciliation:

- Validated human batch rows: `708`
- Human stock/UOM aggregates: `392`
- Validated human quantity total: `2,075`
- Original OCR held rows: `140`
- Excluded rows: `5`
- Download audit photos indexed: `60`
- Download photo rows promoted: `424`
- Download photo held rows: `21`
- Download stock photos still pending transcription: `0`

## Reconciliation Result

The master workbook marries the validated human count to the live Azyra export at both stock/UOM level and location level.

- Stock/UOM delta rows: `392`
- Stock/UOM absolute variance total: `2,312`
- Stock/UOM positive variance rows: `246`
- Stock/UOM negative variance rows: `115`
- Stock/UOM zero variance rows: `31`
- Location delta rows: `626`
- Location absolute variance total: `2,137`
- Location positive variance rows: `534`
- Location negative variance rows: `62`
- Location zero variance rows: `30`

The workbook contains these sheets:

- `Dashboard`
- `Progress_Control`
- `Human_vs_Azyra_Delta`
- `Human_vs_Azyra_Location`
- `Human_Count_Ready`
- `Azyra_Current_Aggregate`
- `Azyra_Current_By_Location`
- `Azyra_Current_Detail`
- `Azyra_Count_Batch_File`
- `Download_Photo_Status`
- `Review_Holds`
- `Aureon_Route_Status`
- `Live_Batch_Gates`
- `Live Status 20260621`
- `Live Qty Sweep`

## Live Status

Status: `partial_live_a1014965_a1014966_completed`

Current live gate: `held_live_azyra_opening_balances_import_blocked_tracked_stock_validation`

Cleared:

- Fresh live Azyra warehouse balance export downloaded on `2026-06-21`.
- Master reconciliation workbook rebuilt from that export.
- Validated human rows are isolated in the count batch CSV.
- Historical quantity sweep has 35 rows classified: 5 completed live, 28 already correct, 2 held, 0 pending.
- Azyra stock-check overage transaction `A1014965` completed: `WL50-PS75PR` +4 at `C26B`; `WL50-PS165UR` +4 at `E19A`.
- Azyra stock-check decrease transaction `A1014966` completed: `WL50-PS105TO` -5 at `B16B`; `WL50-PS180CP` -8 split across `C17A`/`C17B`; `LP6052` -4 at `D24A`.
- After Stock Enquiry proves `WL50-PS105TO` 8 total/free 8/picking 0, `WL50-PS180CP` 10 total/free 10/picking 0, and `LP6052` 6 total/free 6/picking 0.
- Warehouse-floor location move batch has 13 rows classified: 2 posted live (`T101950`, `T101951`), 1 already correct, 10 held, 0 pending.

Still held:

- `161` total review/hold rows remain outside the validated batch.
- Azyra Opening Balances import route accepted the base file but rejected tracked stock without real tracking/rotation metadata.
- Historical held SKU `WL50-PS75CP` is not reposted because later outwards explain the current zero unit balance; the remaining issue is a storage-piece/unit review at `D8B`.
- Historical held SKU `WL50-PS60MO` is not decreased because the extra `D24B` two-unit row is from a separate Inwards transaction, not proved duplicate historical stock.
- Do not force tracked-stock metadata or blind decrease lines.

## Operator Guardrail

Use Aureon against Azyra for all live work. Do not post decrease/increase adjustment pairs for this audit package unless a later explicit approval changes the process. This package is a stock-count reconciliation/import package, and the live import must only use rows that have cleared visual/OCR review, stock-code validation, and the native Azyra import schema.
