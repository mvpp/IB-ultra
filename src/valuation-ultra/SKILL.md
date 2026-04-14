---
name: valuation-ultra
description: >
  在已完成三表模型基础上构建机构级估值结论。适用于 DCF、交易可比、SOTP、NAV、RAB、AFFO、P/B-ROE、rNPV、
  reverse DCF、情景分析、football field、目标价与投资结论输出。优先作为 3-statements-ultra-sec 的下一阶段使用。
  触发词：valuation、估值、target price、DCF、comps、SOTP、football field、reverse DCF、institutional valuation。
---

# Institutional Valuation Companion

Use this skill after a company already has a clean operating model, ideally from
`3-statements-ultra-sec`. This skill turns a completed forecast into a defensible
valuation range, target price, method weighting, and investment-ready output.

## Script-First Rule

For any deterministic numeric work, use the bundled Python scripts before writing calculations
inline in the chat.

- `scripts/valuation_prep.py`
- `scripts/cost_of_capital.py`
- `scripts/dcf_valuation.py`
- `scripts/reverse_dcf.py`
- `scripts/comps_valuation.py`
- `scripts/football_field.py`
- `scripts/valuation_qc.py`

Use Markdown reasoning only for:

- method selection
- peer selection judgment
- accounting classification judgment
- thesis, risks, catalysts, and narrative synthesis

## When To Use

Use this skill when the user wants any of:

- intrinsic value or target price
- DCF / reverse DCF / football field
- comps, SOTP, NAV, RAB, AFFO, P/B-ROE, residual income, rNPV
- base / bull / bear valuation
- valuation memo or underwriting output

Do not use this skill as the first step for a new company model. First build or verify
the forecast base with `3-statements-ultra-sec` or another robust 3-statement model.

## Entry Conditions

Before starting, verify these are available:

1. Historical and forecast `IS`, `BS`, `CF`
2. A usable assumptions layer
3. Net debt and diluted share count visibility
4. Enough disclosure to classify the company into a valuation family

If the company is a bank, insurer, REIT, E&P, biotech, regulated asset, or conglomerate, read:

- [references/industry-overrides.md](references/industry-overrides.md)
- [references/extension-pack-roadmap.md](references/extension-pack-roadmap.md)

before choosing the primary method.

If the company is a bank, insurer, or book-value-driven specialty finance company, prefer the
`valuation-financials` extension pack instead of forcing the core `DCF + comps` workflow.

If the company is a REIT, listed property platform, or stabilized asset-heavy developer, prefer
the `valuation-reit-property` extension pack instead of forcing a generic operating-company DCF.

If the company is a regulated electric, gas, or water utility, or a regulated infrastructure
platform whose value is anchored to allowed return and rate base, prefer the
`valuation-regulated-assets` extension pack instead of stretching the core pack.

If the company is an E&P, mining, royalty, or other reserve-driven resource business whose value
is anchored to asset NAV and commodity decks, prefer the `valuation-asset-nav` extension pack.

If the company is a clinical-stage biotech, binary pipeline story, or pipeline-led pharma whose
value is driven by asset-level approval risk rather than steady-state cash flow, prefer the
`valuation-biotech-rnpv` extension pack.

If the company is a conglomerate, holdco, or mixed business model whose segments need different
method families, prefer the `valuation-sotp` extension pack.

## Outputs

The valuation package should produce these workbook tabs or equivalent artifacts:

- `Valuation_Prep`
- `Capital_Cost`
- `DCF` or other primary-method tab
- `Comps`
- `Scenarios`
- `Football_Field`
- `Target_Price`
- `Valuation_QC`

And these sidecars:

- `_valuation_state.json`
- `_peer_set.json`
- `_valuation_log.md`

## Workflow

Run the valuation in 5 phases:

### Phase F — Valuation Prep

Read [references/bridge-layer.md](references/bridge-layer.md).

Use `scripts/valuation_prep.py` to compute the standardized bridge.

Build the standardized bridge from the 3-statement model into valuation inputs:

- NOPAT
- unlevered FCF
- reinvestment
- ROIC
- working capital intensity
- maintenance vs growth capex if needed
- net debt bridge
- diluted share bridge
- non-operating assets and claims

This phase is mandatory. Do not jump directly from `CF` into `DCF`.

### Phase G — Capital Cost + EV Bridge

Read [references/method-router.md](references/method-router.md).

Use `scripts/cost_of_capital.py` for cost-of-capital calculations.

Build:

- cost of equity
- cost of debt
- target capital structure
- WACC if enterprise-value method
- equity-only discount rate if book-value / DDM / residual-income method
- enterprise-value to equity-value bridge

### Phase H — Primary + Secondary Valuation Methods

Choose one primary and at least one secondary method.

Use `scripts/dcf_valuation.py` for DCF and `scripts/comps_valuation.py` for trading comps.

Examples:

- semiconductor: mid-cycle DCF + trading comps
- REIT: NAV + AFFO comps
- bank: P/B vs ROTCE + residual income
- biotech: rNPV + cash bridge

Do not rely on a single method unless the company is truly one-method dominated and the
reason is explicit.

### Phase I — Scenario / Reverse DCF / Sensitivities

Read [references/qc-and-output.md](references/qc-and-output.md).

Minimum required:

- base / bull / bear
- key-driver sensitivity table
- reverse DCF or market-implied expectations

If the company has meaningful binary risk, add probability weighting.

Use `scripts/reverse_dcf.py` for reverse DCF and `scripts/football_field.py` for range aggregation.

### Phase J — Investment Output

Produce:

- valuation summary
- weighted target price range
- upside / downside vs current price
- key assumptions
- variant perception
- principal risks
- monitoring points

## Hard Rules

1. Every valuation conclusion must reconcile from model outputs to equity value per share.
2. Every enterprise value method must include a full EV-to-equity bridge.
3. Every per-share output must use diluted shares, not basic shares, unless explicitly justified.
4. Every DCF must reconcile growth, margins, reinvestment, and ROIC in the terminal period.
5. Every comps output must document peer selection and outlier treatment.
6. Every final target price must cite both a primary and a secondary method.
7. If valuation depends on non-GAAP adjustments, show them explicitly and preserve GAAP anchors.

## Method Selection

Use [references/method-router.md](references/method-router.md) to choose the method family.

Use the decision logic in this order:

1. Determine whether value is driven by franchise cash flow, asset base, regulated returns,
   reserve value, or binary pipeline outcomes.
2. Determine whether enterprise-value or equity-value framing is appropriate.
3. Choose the primary method.
4. Add a secondary method for triangulation.
5. Add reverse DCF if the market narrative is extreme or valuation is controversial.

## Extension Architecture

This skill is the core phase-2 engine, not the final answer for every special sector.

Keep the shared stack here:

- valuation prep
- cost of capital
- DCF
- trading comps
- reverse DCF
- football field
- QC

Use extension packs for sectors whose valuation mechanics differ materially from standard
cash-flow-based operating companies.

The current target extension packs are documented in
[references/extension-pack-roadmap.md](references/extension-pack-roadmap.md):

- `valuation-financials`
- `valuation-reit-property`
- `valuation-regulated-assets`
- `valuation-asset-nav`
- `valuation-biotech-rnpv`
- `valuation-sotp`

Do not create one phase-2 skill per sector unless the math, disclosure structure, and QC truly
diverge from the core engine. Prefer a small number of valuation-family packs over many
industry-labeled forks.

Today, `valuation-financials`, `valuation-reit-property`, `valuation-regulated-assets`,
`valuation-asset-nav`, `valuation-biotech-rnpv`, and `valuation-sotp` are implemented
extension packs.

## Validation Gate

Before presenting a target price, read [references/qc-and-output.md](references/qc-and-output.md)
and confirm all required checks pass.

Run `scripts/valuation_qc.py` before finalizing.

Do not finalize if any of these remain unresolved:

- EV bridge does not reconcile
- diluted share count is unclear
- terminal assumptions imply impossible economics
- primary method conflicts sharply with model quality
- peer set is low quality or inconsistent

## Minimal Deliverable

If time or data is limited, still deliver:

- one primary method
- one secondary method
- EV bridge
- diluted share bridge
- one sensitivity table
- one reverse DCF or market-implied expectation check
- a concise target-price summary with risks
