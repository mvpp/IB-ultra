---
name: valuation-regulated-assets
description: >
  面向公用事业、受监管基础设施和受监管资产平台的 phase-2 估值扩展包。适用于 RAB / rate-base valuation、
  DDM、regulated return bridge、allowed ROE vs cost of equity、payout and coverage QC。
  优先作为 valuation-ultra 的受监管资产估值扩展包使用。
---

# Regulated Assets Valuation Extension Pack

Use this pack when the company is a:

- regulated electric, gas, or water utility
- regulated network or infrastructure platform
- business whose value is anchored to allowed return on regulated asset base

This is an extension pack for `valuation-ultra`, not a replacement for the core phase-2 engine.

## What This Pack Owns

This pack handles regulated-asset businesses whose valuation anchor is usually:

- regulated asset base or rate base
- allowed `ROE`, capital structure, and rate-base growth
- dividend discount model where payout policy is stable and meaningful

Do not force a generic unlevered DCF when regulated return mechanics clearly dominate the equity
story.

## Script-First Rule

Use the bundled Python scripts before doing any regulated-utility valuation arithmetic in chat:

- `scripts/regulatory_bridge.py`
- `scripts/rab_valuation.py`
- `scripts/ddm_valuation.py`
- `scripts/regulated_target_summary.py`
- `scripts/regulated_qc.py`

Use Markdown reasoning only for:

- regulatory-case quality and visibility
- allowed-return durability
- peer inclusion and exclusion
- capital-allocation and dividend-policy judgment

## Workflow

### Step 1 — Regulatory Bridge

Use `scripts/regulatory_bridge.py` to build:

- rate-base roll-forward
- authorized capital structure and return bridge
- normalized earnings and dividend bridge
- holdco and non-regulated adjustments
- share bridge

### Step 2 — Primary Method

Use `scripts/rab_valuation.py` when the main anchor is `RAB` / rate-base value.

### Step 3 — Secondary Method

Use `scripts/ddm_valuation.py` as the standard secondary method when payout policy and dividend
visibility make it appropriate.

### Step 4 — Target Price Summary

Use `scripts/regulated_target_summary.py` to combine the primary and secondary methods into:

- weighted target price
- bull / base / bear range
- method weights
- per-share conclusion

### Step 5 — QC

Run `scripts/regulated_qc.py` before finalizing.

## Hard Rules

1. Opening and closing rate base must reconcile, either from reported values or an explicit
   roll-forward.
2. Allowed `ROE`, authorized equity ratio, and cost of equity must be visible.
3. The equity-value bridge must distinguish regulated value from holdco and non-regulated
   adjustments.
4. Dividend coverage and payout must be explicit when `DDM` is used.
5. Regulatory-case, lag, and capital-recovery risk must be visible before a target price is
   finalized.

## Output Contract

This pack should produce:

- `regulatory_bridge.json`
- `rab_output.json`
- `ddm_output.json`
- `target_price_summary.json`
- `regulated_qc.json`

These outputs should plug back into the same downstream memo workflow as the core valuation pack.
