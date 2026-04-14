---
name: valuation-biotech-rnpv
description: >
  面向临床阶段 biotech、二元管线故事和以资产级 pipeline value 为核心的 pharma 的 phase-2 估值扩展包。
  适用于 pipeline registry、official source provenance、rNPV、cash runway / dilution bridge、
  launch scenarios、biotech QC。
---

# Biotech rNPV Valuation Extension Pack

Use this pack when the company is a:

- clinical-stage biotech
- binary pipeline story
- pharma or specialty biotech where asset-level pipeline value matters more than steady-state DCF

This is an extension pack for `valuation-ultra`, not a replacement for the core phase-2 engine.

## What This Pack Owns

This pack handles biotech businesses whose valuation anchor is usually:

- asset-level `rNPV`
- cash runway and financing dilution
- scenario-weighted launch value
- source-traceable pipeline facts from official registries and regulatory databases

Do not force a generic unlevered DCF when the equity story is dominated by binary clinical and
regulatory outcomes.

## Source-First Rule

Before modeling, read [references/source-hierarchy.md](references/source-hierarchy.md).

Pipeline facts should come from a source hierarchy like:

- company `10-K` / `10-Q` / `20-F` / `6-K`, pipeline pages, and official investor materials
- ClinicalTrials.gov for trial status, phase, enrollment, and dates
- FDA and EMA databases for approvals, filings, label status, and withdrawals
- official publications or conference abstracts for efficacy and safety readouts

Probabilities of success, peak sales, launch timing, and discount rates are assumptions, not facts.
Make them explicit.

## Script-First Rule

Use the bundled Python scripts before doing any biotech valuation arithmetic in chat:

- `scripts/pipeline_registry.py`
- `scripts/pipeline_rnpv.py`
- `scripts/cash_runway_dilution.py`
- `scripts/launch_scenarios.py`
- `scripts/biotech_target_summary.py`
- `scripts/biotech_qc.py`

Use Markdown reasoning only for:

- probability-of-success judgment
- market sizing and peak-sales judgment
- asset quality and differentiation
- partner economics and competitive intensity

## Workflow

### Step 1 — Pipeline Registry

Use `scripts/pipeline_registry.py` to build:

- a source-traceable asset registry
- normalized stage and approval status
- trial and regulatory linkage
- launch-timing defaults when explicit timing is absent
- cash, burn, and share-bridge context

### Step 2 — Primary Method

Use `scripts/pipeline_rnpv.py` when the main anchor is asset-level `rNPV`.

### Step 3 — Financing + Scenario Layer

Use `scripts/cash_runway_dilution.py` to estimate financing need and dilution.

Use `scripts/launch_scenarios.py` to build bear / base / bull launch outcomes and a probability-
weighted expected value.

### Step 4 — Target Price Summary

Use `scripts/biotech_target_summary.py` to combine the primary and secondary methods into:

- weighted target price
- bear / base / bull range
- method weights
- per-share conclusion

### Step 5 — QC

Run `scripts/biotech_qc.py` before finalizing.

## Hard Rules

1. Each asset must have source provenance attached.
2. Approved and pipeline assets must not be double-counted.
3. Probabilities of success must be explicit or clearly defaulted from stage heuristics.
4. Cash runway and expected dilution must be visible before a target price is finalized.
5. Every final conclusion must reconcile to equity value per share on current or pro forma diluted
   shares.

## Output Contract

This pack should produce:

- `pipeline_registry.json`
- `pipeline_rnpv_output.json`
- `cash_runway_dilution.json`
- `launch_scenarios.json`
- `target_price_summary.json`
- `biotech_qc.json`

These outputs should plug back into the same downstream memo workflow as the core valuation pack.
