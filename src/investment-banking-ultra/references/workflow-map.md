# Workflow Map

## Purpose

This skill coordinates the repo's ten skill artifacts:

- `3-statements-ultra-sec`
- `valuation-ultra`
- `valuation-financials`
- `valuation-reit-property`
- `valuation-regulated-assets`
- `valuation-asset-nav`
- `valuation-biotech-rnpv`
- `valuation-sotp`
- `investment-memo-ultra`
- `investment-banking-ultra`

## Phase Detection Rules

### Phase 1 — Ready

The workflow should treat phase 1 as ready when it can find one workbook containing:

- `Summary`
- `Assumptions`
- `IS`
- `BS`
- `CF`
- `Returns`
- `Cross_Check`
- `Raw_Info`
- `_Registry`
- `_State`

### Phase 2 — Ready

The workflow should treat phase 2 as ready when it can find either:

- `valuation_summary.json`

or a usable raw valuation pack, normally including:

- `dcf_output.json`
- `comps_output.json`
- `reverse_dcf.json`
- `football_field.json`
- `valuation_qc.json`

For banks, insurers, and book-value-driven financials, phase 2 may instead be satisfied by a
financials-specific pack, normally including:

- `financials_prep.json`
- `pb_roe_output.json`
- `residual_income_output.json`
- `target_price_summary.json`
- `financials_qc.json`

For REITs and property-heavy real-estate businesses, phase 2 may instead be satisfied by a
property-specific pack, normally including:

- `property_bridge.json`
- `nav_output.json`
- `affo_output.json`
- `target_price_summary.json`
- `reit_qc.json`

For regulated utilities and regulated infrastructure businesses, phase 2 may instead be satisfied
by a regulated-assets pack, normally including:

- `regulatory_bridge.json`
- `rab_output.json`
- `ddm_output.json`
- `target_price_summary.json`
- `regulated_qc.json`

For E&P, mining, royalty, and other reserve-driven resource businesses, phase 2 may instead be
satisfied by an asset-NAV pack, normally including:

- `reserve_model.json`
- `asset_nav_output.json`
- `commodity_sensitivity.json`
- `pnav_market_check.json`
- `target_price_summary.json`
- `asset_nav_qc.json`

For clinical-stage biotech and pipeline-led pharma businesses, phase 2 may instead be satisfied
by a biotech rNPV pack, normally including:

- `pipeline_registry.json`
- `pipeline_rnpv_output.json`
- `cash_runway_dilution.json`
- `launch_scenarios.json`
- `target_price_summary.json`
- `biotech_qc.json`

For conglomerates, holdcos, and mixed-model companies, phase 2 may instead be satisfied by a
SOTP pack, normally including:

- `segment_normalizer.json`
- `segment_method_router.json`
- `sotp_output.json`
- `holdco_discount.json`
- `target_price_summary.json`
- `sotp_qc.json`

### Phase 3 — Ready

The workflow should treat phase 3 as ready when it can find:

- `memo_input_pack.json`
- `quality_overlay.json`
- `variant_view_frame.json`
- `decision_framework.json`
- `monitoring_dashboard.json`
- `Investment_Memo.md` or `investment_memo_outline.md`

## Near One-Command Phase-3 Bridge

When phases 1 and 2 are ready, the default action should be:

```bash
python src/investment-banking-ultra/scripts/run_phase3_bundle.py --workdir .
```

That bundle should produce the deterministic phase-3 artifact set before any narrative rewrite.
