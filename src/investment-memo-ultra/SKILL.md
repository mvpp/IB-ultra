---
name: investment-memo-ultra
description: >
  在三表模型和估值完成后，生成机构级投资备忘录与决策框架。适用于 investment memo、underwriting memo、
  variant view、key forces、monitoring dashboard、position framework、pre-mortem、quality overlay。
  优先作为 3-statements-ultra-sec 与 valuation-ultra 的第三阶段使用。
---

# Institutional Investment Memo Companion

Use this skill after a company already has:

- a completed operating model, ideally from `3-statements-ultra-sec`
- a completed valuation package, ideally from `valuation-ultra`

This skill turns those outputs into a decision-ready, institutional-style investment memo.

## What This Skill Is

This is a separate phase-3 companion, not a replacement for phase 1 or phase 2.

- `3-statements-ultra-sec` builds the operating model
- `valuation-ultra` builds the valuation package
- `investment-memo-ultra` builds the final underwriting / investment memo

The narrative structure can borrow the strongest ideas from memo-style skills such as
`tech-earnings-deepdive` and `us-value-investing`, but the memo here must be
artifact-driven and script-first for any deterministic calculation.

## Script-First Rule

For hard facts, scores, action bands, monitoring thresholds, or QC, use the bundled Python
scripts before writing conclusions in chat.

- `scripts/build_memo_pack_from_artifacts.py`
- `scripts/memo_input_pack.py`
- `scripts/quality_overlay.py`
- `scripts/variant_view_frame.py`
- `scripts/decision_engine.py`
- `scripts/monitoring_dashboard.py`
- `scripts/render_memo_outline.py`
- `scripts/memo_qc.py`

Use Markdown reasoning only for:

- thesis writing
- variant perception wording
- management / industry judgment
- qualitative risk ranking
- evidence synthesis and source prioritization

## When To Use

Use this skill when the user wants any of:

- an investment memo
- an underwriting memo
- a variant view / market-is-wrong thesis
- a decision framework after valuation
- catalysts, risks, monitoring dashboard, or kill conditions
- a portfolio action framework tied to model + valuation outputs

Do not use this skill as the first step for a new company. Build the model and valuation first.

## Entry Conditions

Before starting, verify these are available:

1. A completed 3-statement model or equivalent summary outputs
2. A completed valuation package with target-price logic
3. Current price visibility
4. Enough facts to classify the company into a sector family

Read [references/artifact-contract.md](references/artifact-contract.md) before building the
memo pack.

If a finished phase-1 workbook and phase-2 JSON directory already exist, prefer
`scripts/build_memo_pack_from_artifacts.py` over manual schema assembly. It auto-discovers the
 workbook, imports valuation artifacts, and produces a memo-ready pack in one step.

## Outputs

The memo package should produce these artifacts:

- `Memo_Input_Pack`
- `Quality_Overlay`
- `Variant_View_Frame`
- `Decision_Framework`
- `Monitoring_Dashboard`
- `Investment_Memo.md`
- `Memo_QC`

And these sidecars:

- `_memo_state.json`
- `_memo_log.md`
- `_evidence_registry.json`

## Workflow

Run the memo in 5 phases:

### Phase K — Memo Input Pack

Read [references/artifact-contract.md](references/artifact-contract.md).

Preferred order:

1. Use `scripts/build_memo_pack_from_artifacts.py` when a finished phase-1 workbook and
   phase-2 valuation JSONs already exist on disk.
2. Use `scripts/memo_input_pack.py` only when the inputs are already normalized JSON fragments
   or when the bridge cannot auto-discover the artifacts.

The bridge script should be the default path for real workflows because it reduces schema-prep
work and keeps phase 3 near one-command.

Minimum required in the pack:

- company identity and current price
- model summary and forecast snapshot
- valuation methods and scenario values
- quality inputs
- monitoring inputs

### Phase L — Cross-Checks And Overlays

Read [references/memo-framework.md](references/memo-framework.md).

Use:

- `scripts/quality_overlay.py`
- `scripts/variant_view_frame.py`
- `scripts/decision_engine.py`
- `scripts/monitoring_dashboard.py`

This phase should produce:

- quality/value cross-check score
- market-implied vs model-implied framing
- action bands and sizing ranges
- monitoring dashboard and trigger table

### Phase M — Memo Outline

Read [references/sector-module-mapping.md](references/sector-module-mapping.md) if the company
is sector-specific or the memo needs emphasis rules.

Use `scripts/render_memo_outline.py` to generate a structured markdown outline populated with
deterministic facts. Then fill in the thesis, variant view, and qualitative sections.

### Phase N — Narrative Synthesis

Read:

- [references/memo-framework.md](references/memo-framework.md)
- [references/perspectives-and-bias.md](references/perspectives-and-bias.md)

Write the actual memo around the computed artifacts.

The memo should include:

- Executive Summary
- Key Forces
- Business & Earnings Deep Dive
- Valuation Summary
- Variant View
- Quality Overlay
- Risks & Pre-Mortem
- Catalysts & Monitoring
- Decision Framework
- Evidence Sources

### Phase O — QC And Finalization

Use `scripts/memo_qc.py` before finalizing.

Do not finalize if any of these remain unresolved:

- target price or current price do not reconcile to the memo pack
- required memo sections are missing
- the variant view is disconnected from valuation / reverse DCF outputs
- risks, catalysts, and monitoring triggers are not explicit
- the memo is missing evidence tiers or open diligence questions

## Hard Rules

1. Do not recompute valuation logic inside the memo unless the valuation package is broken.
2. Every numeric claim in the memo should come from a script output, model artifact, or cited source.
3. Separate deterministic outputs from judgment. Tables and scores go in scripts; narrative goes in the memo.
4. The memo must include both the bull case and the failure path.
5. The decision framework must tie to current price, target price, and downside case.
6. The quality overlay is a cross-check, not the primary thesis.
7. Remove promotional or marketing language. The memo should read like institutional research.

## Narrative Standard

This skill intentionally keeps the best parts of deep-dive memo frameworks:

- key forces first
- variant perception rather than summary-only writing
- multi-angle judgment
- anti-bias and pre-mortem
- actionable monitoring triggers

But it closes the common gaps:

- no missing reference files
- no prompt-only arithmetic
- no sector-specific memo forced on every company
- no detached valuation section
- no free-floating action call without scenario math

## Minimal Deliverable

If time or data is limited, still deliver:

- one clean memo input pack
- one quality overlay
- one variant frame
- one decision framework
- one monitoring dashboard
- one memo draft with all required headings
- one QC pass or explicit QC gap list
