# Azyra Master Audit Reconciliation - Public Capability Note

This public note documents the Aureon warehouse reconciliation capability without exposing customer, owner, warehouse, stock-code, transaction, or local-path details.

Private live workbooks, screenshots, ledgers, transaction references, stock codes, owner names, warehouse names, and operator paths remain outside the public repository in the operator-controlled evidence folder.

## Capability

Aureon can build a master warehouse reconciliation workbook by joining:

- a fresh Azyra warehouse balance export,
- validated human audit/count rows,
- OCR review status,
- source-system quantity evidence,
- location-level evidence,
- live route gates,
- and row-level production status.

The resulting control workbook is designed to separate:

- rows ready for native Azyra upload,
- rows already correct in the live system,
- rows requiring manual review,
- rows blocked by missing source evidence,
- rows blocked by tracking/rotation requirements,
- and rows that must not be posted.

## Public Guardrails

- Public documentation must describe the route and controls, not the customer's operational data.
- Do not commit live Azyra exports, customer workbooks, evidence screenshots, transaction references, or owner/warehouse names.
- Do not publish stock codes, quantities, locations, or variance totals from a live customer environment.
- Keep local evidence under an untracked operator output directory.
- Use placeholders in examples: `<owner>`, `<warehouse>`, `<stock-code>`, `<manifest>`, `<transaction-reference>`.

## Live Route

Aureon's safe production route is:

```text
current Azyra export
  -> validated audit rows
  -> reconciliation workbook
  -> row-level gates
  -> native Azyra import/transfer/current-balance route
  -> after-state Stock Enquiry verification
  -> local evidence ledger
```

Every row must resolve to one of:

- `completed_live`
- `already_correct`
- `held_requires_review`
- `blocked`

No row should be silently skipped.

## Operator Rule

Use Aureon against Azyra for live work. Do not convert warehouse location moves into decrease/increase adjustment pairs unless a later explicit approval changes the route. Stock-count reconciliation/import work must only use rows that have cleared visual/OCR review, stock-code validation, live Azyra evidence, and the native Azyra import schema.
