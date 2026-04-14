# Extension Pack Roadmap

## Design Principle

Do not create 20 separate phase-2 skills just because there are 20 sectors.

Phase 2 should be split by **valuation mechanics**, not by industry label.

That means:

- one core `valuation-ultra` for the shared engine
- a small set of specialist extension packs for businesses whose math, inputs, and QC differ
  materially from a normal operating-company `DCF + comps` workflow

## What Stays In Core

The core `valuation-ultra` skill should continue to own:

- `valuation_prep.py`
- `cost_of_capital.py`
- `dcf_valuation.py`
- `comps_valuation.py`
- `reverse_dcf.py`
- `football_field.py`
- `valuation_qc.py`

This is the right default for:

- software / internet
- semiconductors
- most industrials
- devices / medtech
- consumer and staples
- many business services companies

## When An Extension Pack Is Needed

Add an extension pack when at least 2 of these are true:

1. The primary valuation anchor is not a normal unlevered cash-flow model.
2. Book value, regulated asset base, reserve NAV, property NAV, or asset probabilities matter
   more than standard DCF mechanics.
3. The company needs pack-specific disclosure fields that do not naturally fit the core bridge.
4. The QC checks are materially different from the core QC.
5. The peer set and market anchors use different market conventions.

## Canonical Pack Interface

Every extension pack should plug into the same downstream phase-2 outputs.

### Required Inputs

- `company.json`
- `valuation_prep.json`
- `capital_cost.json` if relevant
- `market_snapshot.json`
- `peer_set.json` if relevant
- pack-specific input JSON

### Required Outputs

- `primary_method_output.json`
- `secondary_method_output.json`
- `target_price_summary.json`
- `pack_qc.json`

Optional:

- `asset_level_valuation.json`
- `sensitivity_output.json`
- `probability_tree.json`
- `holding_company_bridge.json`

### Output Contract Rules

- Every pack must still produce a per-share conclusion.
- Every pack must still reconcile to equity value.
- Every pack must still feed the same football-field and target-price layers.
- Every pack must state whether it replaces or supplements core DCF.

## Recommended Extension Packs

### 1. `valuation-financials`

Status:

- implemented
- packaged as `valuation-financials.skill`

Coverage:

- banks
- insurers
- specialty finance where book value and spreads dominate

Primary methods:

- `P/B` vs sustainable `ROE` / `ROTCE`
- residual income
- embedded value for life insurers where disclosure allows

Additional inputs:

- CET1 / Tier 1
- NIM or spread metrics
- credit cost / reserve assumptions
- tangible book value
- normalized ROE / ROTCE
- combined ratio / investment yield for insurers

Scripts:

- `financials_prep.py`
- `pb_roe_valuation.py`
- `residual_income.py`
- `embedded_value.py`
- `financials_qc.py`

QC focus:

- tangible book reconciliation
- capital ratio consistency
- reserve adequacy
- ROE / ROTCE normalization sanity
- avoid forcing unlevered DCF unless explicitly justified

### 2. `valuation-reit-property`

Status:

- implemented
- packaged as `valuation-reit-property.skill`

Coverage:

- REITs
- property developers with stabilized assets
- listed property platforms

Primary methods:

- NAV
- AFFO multiple

Additional inputs:

- property-level NOI
- occupancy / same-store growth
- cap-rate assumptions
- development pipeline split
- maintenance capex
- debt maturity ladder

Scripts:

- `property_bridge.py`
- `reit_nav.py`
- `affo_valuation.py`
- `reit_qc.py`

QC focus:

- cap-rate sensitivity
- stabilized vs development asset split
- AFFO normalization
- leverage and refinance risk

### 3. `valuation-regulated-assets`

Status:

- implemented
- packaged as `valuation-regulated-assets.skill`

Coverage:

- electric / gas / water utilities
- regulated infrastructure
- assets valued off allowed returns and rate base

Primary methods:

- RAB / rate-base valuation
- DDM where policy and payout make it appropriate

Additional inputs:

- opening / closing rate base
- allowed ROE
- allowed leverage
- regulatory lag
- capex plan and rate-base growth
- payout policy

Scripts:

- `regulatory_bridge.py`
- `rab_valuation.py`
- `ddm_valuation.py`
- `regulated_qc.py`

QC focus:

- allowed return vs WACC
- rate-base roll-forward
- dividend coverage
- regulatory-case sensitivity

### 4. `valuation-asset-nav`

Status:

- implemented
- packaged as `valuation-asset-nav.skill`

Coverage:

- E&P
- mining
- royalty / reserve-driven resource businesses
- other asset-heavy cases where reserve NAV dominates

Primary methods:

- asset NAV
- `P/NAV`
- EV/EBITDA market check

Additional inputs:

- reserve / resource inventory
- commodity deck
- decline curves or production plan
- unit cash costs
- sustaining capex
- asset-level tax / royalty assumptions

Scripts:

- `reserve_model.py`
- `asset_nav.py`
- `commodity_sensitivity.py`
- `pnav_market_check.py`
- `asset_nav_qc.py`

QC focus:

- deck sensitivity
- asset-life consistency
- sustaining-capex realism
- NAV bridge to equity value

### 5. `valuation-biotech-rnpv`

Status:

- implemented
- packaged as `valuation-biotech-rnpv.skill`

Coverage:

- clinical biotech
- binary pipeline stories
- pharma names where asset-level pipeline value matters more than steady-state DCF

Primary methods:

- rNPV
- cash runway / dilution bridge
- scenario-weighted launch value

Additional inputs:

- asset list
- clinical stage
- probability of success
- launch timing
- peak sales
- margin / royalty structure
- cash burn and financing assumptions

Scripts:

- `pipeline_registry.py`
- `pipeline_rnpv.py`
- `cash_runway_dilution.py`
- `launch_scenarios.py`
- `biotech_qc.py`

QC focus:

- asset-by-asset probability consistency
- cash runway and dilution realism
- launch timing sensitivity
- double-counting prevention between approved and pipeline assets

### 6. `valuation-sotp`

Status:

- implemented
- packaged as `valuation-sotp.skill`

Coverage:

- conglomerates
- mixed business models
- companies with segments that need different method families

Primary methods:

- SOTP
- consolidated DCF as secondary check

Additional inputs:

- segment financials
- segment method map
- corporate cost allocation
- central cash / debt / investments
- holdco discount assumptions

Scripts:

- `segment_normalizer.py`
- `segment_method_router.py`
- `sotp_valuation.py`
- `holdco_discount.py`
- `sotp_qc.py`

QC focus:

- segment-to-consolidated tie-out
- no double counting of central items
- holdco discount explicitly justified

## Build Order

Recommended build order:

1. `valuation-financials`
2. `valuation-reit-property`
3. `valuation-biotech-rnpv`
4. `valuation-regulated-assets`
5. `valuation-asset-nav`
6. `valuation-sotp`

Reason:

- financials and REITs are common and structurally impossible to do well with generic DCF-first logic
- biotech has distinct binary math and dilution risk
- regulated assets and reserve NAV need specialist bridges
- SOTP becomes more powerful once the other packs already exist

## Optional Future Packs

Only add these if repeated use cases justify them:

- `valuation-cyclicals-normalization`
- `valuation-special-situations`
- `valuation-early-stage-venture`

These should remain optional because many of their needs can be handled inside the core engine
through assumptions and scenario design.
