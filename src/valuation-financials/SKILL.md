---
name: valuation-financials
description: >
  面向银行、保险和部分 specialty finance 的 phase-2 估值扩展包。适用于 P/B vs ROE、ROTCE、
  residual income、embedded value、capital ratio bridge、tangible book bridge、financials QC。
  优先作为 valuation-ultra 的行业扩展包使用。
---

# Financials Valuation Extension Pack

Use this pack when the company is a:

- bank
- insurer
- specialty finance company where book value and spread economics dominate

This is an extension pack for `valuation-ultra`, not a replacement for the core phase-2 engine.

## What This Pack Owns

This pack handles financial businesses whose valuation anchor is usually:

- tangible book value or book value
- sustainable `ROE` / `ROTCE`
- residual income
- embedded value where disclosure allows

Do not force a standard unlevered DCF for these businesses unless there is a very specific reason.

## Script-First Rule

Use the bundled Python scripts before doing any financial-sector valuation arithmetic in chat:

- `scripts/financials_prep.py`
- `scripts/pb_roe_valuation.py`
- `scripts/residual_income.py`
- `scripts/embedded_value.py`
- `scripts/financials_target_summary.py`
- `scripts/financials_qc.py`

Use Markdown reasoning only for:

- balance-sheet classification judgment
- reserve quality judgment
- peer inclusion and exclusion
- why a `P/B`, residual income, or embedded-value anchor is most appropriate

## Workflow

### Step 1 — Financials Prep

Use `scripts/financials_prep.py` to build:

- book value bridge
- tangible book bridge
- capital ratio bridge
- normalized earnings and return metrics
- share bridge

### Step 2 — Primary Method

Use `scripts/pb_roe_valuation.py` when the main anchor is `P/B` tied to sustainable
`ROE` / `ROTCE`.

### Step 3 — Secondary Method

Use `scripts/residual_income.py` as the standard secondary method for banks and many insurers.

Use `scripts/embedded_value.py` when life-insurance disclosure or appraisal-value style logic
is available.

### Step 4 — Target Price Summary

Use `scripts/financials_target_summary.py` to combine the primary and secondary methods into:

- weighted target price
- bull / base / bear range
- method weights
- per-share conclusion

### Step 5 — QC

Run `scripts/financials_qc.py` before finalizing.

## Hard Rules

1. Tangible book and reported book must reconcile clearly when goodwill and intangibles matter.
2. Sustainable `ROE` / `ROTCE` must be explicit.
3. Capital ratios, reserve assumptions, and balance-sheet strength must be visible.
4. Every method must still end in equity value per share.
5. If embedded value is used, its components must be explicit.

## Output Contract

This pack should produce:

- `financials_prep.json`
- `pb_roe_output.json`
- `residual_income_output.json`
- optional `embedded_value_output.json`
- `target_price_summary.json`
- `financials_qc.json`

These outputs should plug back into the same downstream memo workflow as the core valuation pack.
