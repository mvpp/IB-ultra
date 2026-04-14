---
name: investment-banking-ultra
description: >
  统一编排三阶段投研流程：先建三表，再做估值，最后生成机构级投资备忘录。适用于 end-to-end
  investment workflow、resume workflow、phase status check、artifact bridging、memo bundle generation。
  优先在你希望一次性推进 phase 1 -> phase 2 -> phase 3 时使用。
---

# Institutional Workflow Orchestrator

Use this skill when the user wants one guided workflow across:

- `3-statements-ultra-sec`
- `valuation-ultra`
- `valuation-financials`
- `valuation-reit-property`
- `valuation-regulated-assets`
- `valuation-asset-nav`
- `valuation-biotech-rnpv`
- `valuation-sotp`
- `investment-memo-ultra`

This skill does not replace the companion skills. It coordinates them, checks what already
exists in the working directory, and removes the manual glue between phase 2 and phase 3.

## Script-First Rule

Use these scripts before reasoning about workflow state in chat:

- `scripts/workflow_state.py`
- `scripts/run_phase3_bundle.py`

Use the underlying companion skills for phase-specific work:

- `../3-statements-ultra-sec/SKILL.md`
- `../valuation-ultra/SKILL.md`
- `../valuation-financials/SKILL.md`
- `../valuation-reit-property/SKILL.md`
- `../valuation-regulated-assets/SKILL.md`
- `../valuation-asset-nav/SKILL.md`
- `../valuation-biotech-rnpv/SKILL.md`
- `../valuation-sotp/SKILL.md`
- `../investment-memo-ultra/SKILL.md`

## When To Use

Use this skill when the user wants any of:

- one guided phase-1 -> phase-2 -> phase-3 workflow
- resume the workflow without remembering which phase is complete
- auto-bridge a finished workbook and valuation artifacts into memo artifacts
- check which artifacts are missing before continuing

## Workflow

### Step 1 — Inspect State

Run `scripts/workflow_state.py --workdir <root>`.

This should discover:

- phase-1 workbook status
- phase-2 valuation artifact status
- phase-3 memo artifact status
- the next recommended phase

### Step 2 — Route To The Right Phase

Use the state result in this order:

1. If phase 1 is missing, switch to `3-statements-ultra-sec` and build the operating model.
2. If phase 1 is ready but phase 2 is missing or partial, switch to `valuation-ultra` for standard
   operating companies, `valuation-financials` for banks or insurers, or
   `valuation-reit-property` for REITs and property-heavy real-estate businesses, or
   `valuation-regulated-assets` for regulated utilities and regulated infrastructure, or
   `valuation-asset-nav` for reserve-driven resource businesses, or
   `valuation-biotech-rnpv` for clinical-stage biotech and pipeline-led pharma names, or
   `valuation-sotp` for conglomerates, holdcos, and mixed-model companies.
3. If phases 1 and 2 are ready, run `scripts/run_phase3_bundle.py` to generate the memo pack,
   overlays, dashboard, and memo outline in one step.
4. If phase 3 artifacts already exist, refresh only the stale or missing phase-3 outputs.

### Step 3 — Finalize The Memo

After `run_phase3_bundle.py` completes, use `investment-memo-ultra` to refine the narrative,
fill judgment-heavy sections, and confirm the QC output is acceptable.

## Hard Rules

1. Do not start phase 2 before a real phase-1 workbook exists.
2. Do not start phase 3 before phase-2 valuation outputs exist.
3. Do not rebuild memo math manually if phase-1 and phase-2 artifacts are already on disk.
4. Always regenerate phase-3 artifacts from the latest workbook and valuation JSONs after the
   model or valuation changes.
5. Use the umbrella skill for orchestration, not for replacing the specialist logic of the
   companion skills.

## Minimal Deliverable

If the user wants the workflow unblocked quickly, still deliver:

- one `workflow_state.json` or equivalent status readout
- one clear next-phase recommendation
- if phases 1 and 2 are ready, one complete phase-3 artifact bundle
