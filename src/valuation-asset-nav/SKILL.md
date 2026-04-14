---
name: valuation-asset-nav
description: >
  面向油气、矿业、 royalty / reserve-driven resource businesses 的 phase-2 估值扩展包。适用于
  reserve model、asset NAV、commodity sensitivity、P/NAV market check、NAV bridge QC。
  优先作为 valuation-ultra 的资产净值估值扩展包使用。
---

# Asset NAV Valuation Extension Pack

Use this pack when the company is a:

- E&P company
- mining or reserve-driven resource business
- royalty platform or other asset-heavy business where reserve NAV dominates

This is an extension pack for `valuation-ultra`, not a replacement for the core phase-2 engine.

## What This Pack Owns

This pack handles businesses whose valuation anchor is usually:

- asset-level reserve or resource value
- commodity-deck-driven cash flow
- `P/NAV` market framing
- bridge from asset value to equity value per share

Do not force a generic unlevered DCF when reserve life, commodity decks, and asset NAV clearly
drive the equity story.

## Script-First Rule

Use the bundled Python scripts before doing any resource-sector valuation arithmetic in chat:

- `scripts/reserve_model.py`
- `scripts/asset_nav.py`
- `scripts/commodity_sensitivity.py`
- `scripts/pnav_market_check.py`
- `scripts/asset_nav_target_summary.py`
- `scripts/asset_nav_qc.py`

Use Markdown reasoning only for:

- commodity deck judgment
- asset quality and jurisdiction risk
- peer inclusion and exclusion
- reserve quality, decline profile, and capital-allocation judgment

## Workflow

### Step 1 — Reserve Model

Use `scripts/reserve_model.py` to build:

- asset-level production and reserve rollup
- commodity-deck-driven cash flow
- asset-level `NPV`
- reserve-life and production summary
- balance-sheet and share bridge carry-through

### Step 2 — Primary Method

Use `scripts/asset_nav.py` when the main anchor is asset `NAV`.

### Step 3 — Secondary Methods

Use `scripts/commodity_sensitivity.py` to stress the asset value against commodity deck changes.

Use `scripts/pnav_market_check.py` as the standard secondary market check for reserve-driven
businesses.

### Step 4 — Target Price Summary

Use `scripts/asset_nav_target_summary.py` to combine the primary and secondary methods into:

- weighted target price
- bull / base / bear range
- method weights
- per-share conclusion

### Step 5 — QC

Run `scripts/asset_nav_qc.py` before finalizing.

## Hard Rules

1. Asset-level reserve or production assumptions must be visible.
2. Commodity deck and discount-rate assumptions must be visible.
3. `NAV` must reconcile through cash, debt, hedges, preferreds, minorities, and other claims.
4. Commodity sensitivity must be visible for any name materially exposed to price moves.
5. Reserve-life, sustaining-capex, and abandonment assumptions must be visible before a target
   price is finalized.

## Output Contract

This pack should produce:

- `reserve_model.json`
- `asset_nav_output.json`
- `commodity_sensitivity.json`
- `pnav_market_check.json`
- `target_price_summary.json`
- `asset_nav_qc.json`

These outputs should plug back into the same downstream memo workflow as the core valuation pack.
