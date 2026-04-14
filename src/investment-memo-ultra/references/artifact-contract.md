# Artifact Contract

## Purpose

Phase 3 should consume structured outputs from phases 1 and 2 instead of re-parsing the entire
model from scratch inside the memo.

Use `scripts/memo_input_pack.py` to standardize the handoff.

For the common case where phase 1 already produced a finished workbook and phase 2 already
produced valuation JSONs, prefer `scripts/build_memo_pack_from_artifacts.py`. It auto-discovers:

- the phase-1 workbook with `Summary`, `Assumptions`, `IS`, `BS`, `CF`, `Returns`,
  `Cross_Check`, `Raw_Info`, `_Registry`, `_State`
- phase-2 JSON artifacts such as `dcf_output.json`, `comps_output.json`, `reverse_dcf.json`,
  `football_field.json`, `valuation_qc.json`, and `_valuation_state.json`

Then it converts those artifacts into the minimal JSON shape below and hands the result to
`memo_input_pack.py`.

## Required Input Buckets

### `company`

Required fields:

- `name`
- `ticker`
- `sector_family`
- `industry`
- `currency`
- `current_price`

Recommended:

- `report_date`
- `market_cap`
- `enterprise_value`
- `primary_exchange`

### `model_summary`

Historical or current snapshot from phase 1.

Common fields:

- `revenue_growth_ltm`
- `gross_margin_ltm`
- `ebit_margin_ltm`
- `fcf_margin_ltm`
- `roe_ltm`
- `roic_ltm`
- `net_debt_to_ebitda`
- `interest_coverage`
- `customer_concentration_top1`
- `customer_concentration_top5`

Optional forecast summary:

- `revenue_cagr_forecast`
- `ebit_margin_terminal`
- `fcf_margin_terminal`
- `roic_terminal`

### `valuation`

Required fields:

- `current_price` if not already in `company`
- `weighted_target_price`
- `base_target_price`
- `bull_target_price`
- `bear_target_price`
- `primary_method`
- `secondary_method`

Recommended:

- `expected_value_per_share`
- `method_weights`
- `valuation_qc_passed`
- `reverse_dcf`

### `quality_inputs`

Artifact-driven version of the value overlay.

Preferred fields:

- `roe_history`
- `roic_history`
- `debt_to_assets`
- `net_debt_to_ebitda`
- `interest_coverage`
- `fcf_to_net_income`
- `fcf_margin`
- `gross_margin`
- `operating_margin`
- `moat_types`
- `cash_runway_months`
- `cet1_ratio`
- `loan_to_value`

Sector-specific fields may be added freely.

### `monitoring_inputs`

This is the raw material for the dashboard.

Suggested structure:

```json
{
  "drivers": [
    {
      "name": "Revenue growth",
      "metric": "revenue_growth",
      "current": 0.16,
      "base": 0.15,
      "bull": 0.18,
      "bear": 0.10,
      "direction": "higher_better"
    }
  ],
  "risks": [
    {
      "name": "Net debt / EBITDA",
      "metric": "net_debt_to_ebitda",
      "current": 2.4,
      "warning": 3.0,
      "breach": 3.5,
      "direction": "lower_better"
    }
  ],
  "catalysts": [
    {
      "name": "Product launch",
      "date": "2026-09-15",
      "importance": "high",
      "linked_metric": "revenue_growth"
    }
  ]
}
```

## Minimal JSON Shape

```json
{
  "company": {},
  "model_summary": {},
  "valuation": {},
  "quality_inputs": {},
  "monitoring_inputs": {}
}
```

## Expected Output Artifacts

`memo_input_pack.py` should produce:

- standardized company + price fields
- valuation spread and scenario return fields
- market-implied gap fields if reverse DCF is available
- risk/reward fields for downstream scripts

Then downstream memo scripts use this pack instead of independent ad hoc inputs.

## Automatic Bridge Notes

The bridge currently derives the phase-1 handoff directly from the workbook and supports
formula evaluation for non-recalculated `.xlsx` files. This matters because many generated
workbooks do not carry cached formula values until Excel recalculates them.

Recommended command:

```bash
python src/investment-memo-ultra/scripts/build_memo_pack_from_artifacts.py \
  --workdir . \
  --output memo_input_pack.json
```
