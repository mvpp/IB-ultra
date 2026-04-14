---
name: valuation-reit-property
description: >
  面向 REIT、地产平台和稳定化资产开发商的 phase-2 估值扩展包。适用于 NAV、AFFO multiple、
  property bridge、cap-rate sensitivity、development split、leverage and refinance QC。
  优先作为 valuation-ultra 的地产估值扩展包使用。
---

# REIT / Property Valuation Extension Pack

Use this pack when the company is a:

- REIT
- listed property platform
- property developer with stabilized, income-producing assets

This is an extension pack for `valuation-ultra`, not a replacement for the core phase-2 engine.

## What This Pack Owns

This pack handles real-estate businesses whose valuation anchor is usually:

- property NAV
- `AFFO` or `FFO` multiple
- cap-rate and occupancy sensitivity
- development pipeline value split from stabilized assets

Do not force a generic unlevered DCF when the market convention is clearly `NAV + AFFO`.

## Script-First Rule

Use the bundled Python scripts before doing any REIT/property valuation arithmetic in chat:

- `scripts/property_bridge.py`
- `scripts/reit_nav.py`
- `scripts/affo_valuation.py`
- `scripts/reit_target_summary.py`
- `scripts/reit_qc.py`

Use Markdown reasoning only for:

- asset quality judgment
- market cap-rate selection
- peer inclusion and exclusion
- development pipeline quality and execution risk

## Workflow

### Step 1 — Property Bridge

Use `scripts/property_bridge.py` to build:

- property-level value rollup
- stabilized vs development asset split
- occupancy and same-store operating metrics
- balance-sheet bridge and leverage visibility
- normalized `FFO` / `AFFO` and per-share outputs

### Step 2 — Primary Method

Use `scripts/reit_nav.py` when the main anchor is `NAV`.

### Step 3 — Secondary Method

Use `scripts/affo_valuation.py` as the standard secondary method for stabilized REITs and listed
property platforms.

### Step 4 — Target Price Summary

Use `scripts/reit_target_summary.py` to combine the primary and secondary methods into:

- weighted target price
- bull / base / bear range
- method weights
- per-share conclusion

### Step 5 — QC

Run `scripts/reit_qc.py` before finalizing.

## Hard Rules

1. Stabilized and development assets must be separated explicitly.
2. Cap rates, occupancy, and recurring capex assumptions must be visible.
3. NAV must reconcile all real-estate assets, cash, debt, preferreds, minorities, and other claims.
4. `AFFO` must be explicit and per-share.
5. Refinance and leverage risk must be visible before a target price is finalized.

## Output Contract

This pack should produce:

- `property_bridge.json`
- `nav_output.json`
- `affo_output.json`
- `target_price_summary.json`
- `reit_qc.json`

These outputs should plug back into the same downstream memo workflow as the core valuation pack.
