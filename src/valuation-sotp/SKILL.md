---
name: valuation-sotp
description: >
  面向 conglomerate、mixed business model 和需要分部差异化估值方法的公司的 phase-2 估值扩展包。
  适用于 segment normalization、segment method routing、SOTP、holdco discount、SOTP QC。
---

# Sum-Of-The-Parts Valuation Extension Pack

Use this pack when the company is a:

- conglomerate
- holding company
- mixed business model with segments that need different valuation families
- company whose consolidated DCF hides the value of dissimilar assets

This is an extension pack for `valuation-ultra`, not a replacement for the full phase-2 stack.

## What This Pack Owns

This pack handles cases where value is built bottom-up from business units or holdings, then
bridged back to a consolidated equity value:

- segment normalization
- segment-level method routing
- segment-by-segment valuation
- corporate / holdco adjustments
- holdco discount where justified

Do not force a single operating-company DCF when the segments have materially different economics,
peer sets, or valuation conventions.

## Script-First Rule

Use the bundled Python scripts before doing any SOTP arithmetic in chat:

- `scripts/segment_normalizer.py`
- `scripts/segment_method_router.py`
- `scripts/sotp_valuation.py`
- `scripts/holdco_discount.py`
- `scripts/sotp_target_summary.py`
- `scripts/sotp_qc.py`

Use Markdown reasoning only for:

- segment boundary judgment
- peer / multiple selection
- corporate cost allocation judgment
- holdco discount justification

## Workflow

### Step 1 — Normalize Segments

Use `scripts/segment_normalizer.py` to build:

- normalized segment financials
- consolidated tie-out context
- central cash / debt / investments
- diluted-share visibility

### Step 2 — Route Segment Methods

Use `scripts/segment_method_router.py` to assign each segment a valuation family such as:

- `EV/EBITDA`
- `EV/EBIT`
- `EV/Sales`
- `P/E`
- `P/B`
- direct equity value
- direct enterprise value

### Step 3 — Build SOTP

Use `scripts/sotp_valuation.py` to compute:

- segment value by method
- ownership-adjusted segment contribution
- central-item bridge
- gross equity value before holdco discount

### Step 4 — Holdco Discount + Summary

Use `scripts/holdco_discount.py` when a holdco or conglomerate discount is justified.

Use `scripts/sotp_target_summary.py` to combine SOTP with an optional secondary method such as a
consolidated DCF or market check.

### Step 5 — QC

Run `scripts/sotp_qc.py` before finalizing.

## Hard Rules

1. Segment value must tie back to explicit segment metrics or explicit direct-value inputs.
2. Central cash, debt, pensions, and investments must not be double counted.
3. Ownership percentage must be explicit for partially owned segments.
4. Holdco discount must be explicit, justified, and applied to a defined base.
5. Every final conclusion must reconcile to equity value per diluted share.

## Output Contract

This pack should produce:

- `segment_normalizer.json`
- `segment_method_router.json`
- `sotp_output.json`
- `holdco_discount.json`
- `target_price_summary.json`
- `sotp_qc.json`

These outputs should plug back into the same downstream memo workflow as the core valuation pack.
