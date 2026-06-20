# Azyra Master Audit Reconciliation - 2026-06-20

This note records the current master audit reconciliation package built from the validated human audit rows and a fresh live Azyra warehouse balance export.

## Local Outputs

Master reconciliation folder:

`C:\Users\Gary.Leckey\OneDrive - SFG Forwarding Ltd\Documents\sfg azrya intergrations\outputs\aureon_goal_contract_dispatcher\master_azyra_reconciliation_20260620`

Key files:

- Human-readable master workbook: `Azyra_Master_Audit_Reconciliation_20260620.xlsx`
- Fresh Azyra export: `current_azyra_exports\Warehouse Balances Spreadsheet 89QU7U006.xlsx`
- Stock/UOM delta CSV: `human_vs_azyra_delta_candidates.csv`
- Location-level delta CSV: `human_vs_azyra_location_delta_candidates.csv`
- Validated human count batch CSV: `azyra_count_batch_file_validated_human_rows.csv`
- Summary JSON: `master_reconciliation_summary.json`

## Fresh Azyra Export

Exported through Aureon/Azyra, not manual user-self entry.

- Azyra environment: `SFG Live`
- Route: `WMS > Reports > Warehouse > Warehouse Balances Spreadsheet`
- Owner: `All Third Parties`
- Warehouse: `Antrim`
- Condition: `All Conditions`
- Location filter: blank, all locations
- Stock-code filter: blank, all stock codes
- Detail by tracking number: checked
- Include stock codes with zero balance: checked
- Format: Excel `.xlsx`
- Report as at: `20/06/2026 09:37`

Export counts:

- Detail rows: `13,473`
- Free quantity total: `18,997`
- Balance quantity total: `20,815`
- Picking quantity total: `1,818`
- Stock codes: `7,875`
- Locations: `779`

## Human Audit Input

Input from the first audit-scan batch:

`C:\Users\Gary.Leckey\OneDrive - SFG Forwarding Ltd\Documents\sfg azrya intergrations\outputs\aureon_goal_contract_dispatcher\audit_scans_1st_batch_20260619`

Counts currently carried into the master reconciliation:

- Validated human batch rows: `284`
- Human stock/UOM aggregates: `207`
- Validated human quantity total: `737`
- Original OCR held rows: `132`
- Excluded rows: `5`
- Download audit photos indexed: `60`
- Download stock photos still pending transcription: `59`

## Reconciliation Result

The master workbook marries the validated human count to the live Azyra export at both stock/UOM level and location level.

- Stock/UOM delta rows: `207`
- Stock/UOM absolute variance total: `1,086`
- Stock/UOM positive variance rows: `35`
- Stock/UOM negative variance rows: `93`
- Stock/UOM zero variance rows: `79`
- Location delta rows: `284`
- Location absolute variance total: `358`
- Location positive variance rows: `114`
- Location negative variance rows: `39`
- Location zero variance rows: `131`

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
- `Live_Batch_Gates`

## Live Status

Status: `prepared_not_live_posted`

Current live gate: `held_requires_import_route_photo_transcription_and_review_clearance`

Cleared:

- Fresh live Azyra warehouse balance export downloaded on `2026-06-20`.
- Master reconciliation workbook rebuilt from that export.
- Validated human rows are isolated in the count batch CSV.

Still held:

- `59` download stock photos still need OCR/transcription before they can be added.
- `132` original OCR held rows remain outside the live batch.
- Azyra native batch stock-count import route/schema is not yet proven.
- No live stock-count mutation or adjustment batch has been posted from this package.

## Operator Guardrail

Use Aureon against Azyra for all live work. Do not post decrease/increase adjustment pairs for this audit package unless a later explicit approval changes the process. This package is a stock-count reconciliation/import package, and the live import must only use rows that have cleared visual/OCR review, stock-code validation, and the native Azyra import schema.
