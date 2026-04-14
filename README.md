# 3-Statements-Ultra — SEC-First Fork

**English** | [中文](README.zh.md)

**Version:** 4.8 · SEC-First Fork
**Build date:** April 2026
**Compatibility:** Claude Code / Cowork (Anthropic)

---

## What This Fork Changes

This fork preserves the original modeling logic but changes the default source workflow for
US SEC filers:

- SEC filings first
- NotebookLM second, driven by `notebooklm-py`
- Excel only as a secondary source
- Web only as cross-check / fallback

This repo now contains ten related skills:

- `3-statements-ultra-sec.skill` — build the operating model first
- `valuation-ultra.skill` — turn that operating model into a valuation package
- `valuation-financials.skill` — specialized phase-2 pack for banks, insurers, and book-value-driven financials
- `valuation-reit-property.skill` — specialized phase-2 pack for REITs, property platforms, and stabilized asset-heavy developers
- `valuation-regulated-assets.skill` — specialized phase-2 pack for regulated utilities and regulated infrastructure
- `valuation-asset-nav.skill` — specialized phase-2 pack for reserve-driven resource businesses
- `valuation-biotech-rnpv.skill` — specialized phase-2 pack for clinical biotech and pipeline-led pharma
- `valuation-sotp.skill` — specialized phase-2 pack for conglomerates, holdcos, and mixed-model companies
- `investment-memo-ultra.skill` — turn the model + valuation outputs into an institutional investment memo
- `investment-banking-ultra.skill` — orchestrate the full workflow and auto-bridge phase 2 into phase 3

Recommended sequence:

1. Use `investment-banking-ultra` if you want one guided workflow with automatic phase detection
2. Use `3-statements-ultra-sec` to build the 3-statement model
3. Use `valuation-ultra` for standard operating-company valuation
4. Use `valuation-financials` instead of forcing a generic DCF if the company is a bank, insurer, or book-value-driven financial
5. Use `valuation-reit-property` instead of forcing a generic DCF if the company is a REIT or property-heavy real-estate business
6. Use `valuation-regulated-assets`, `valuation-asset-nav`, `valuation-biotech-rnpv`, or `valuation-sotp` when the company needs one of those specialist valuation mechanics
7. Use `investment-memo-ultra` to build the final underwriting memo, monitoring dashboard, and decision framework

## What This Skill Does

Builds a complete, institutional-grade **three-statement financial model** (Income Statement, Balance Sheet, Cash Flow Statement) in Excel from scratch — with full formula linkage, zero hardcoded forecast cells, and a 9-step QC validation suite.

Output quality targets: IPO prospectus / equity research initiating coverage.

Key features:
- **CN GAAP / IFRS / US GAAP** — all three accounting standards supported
- **Quarterly / Semi-annual / Annual** granularity auto-detected from source data
- **Formula-only forecasts** — every IS/BS/CF cell is an Excel formula, never a hardcoded number
- **State persistence** — 5-session build with full resume-after-interruption support
- **9 QC checks** — BS CHECK, CF CHECK, NI CHECK, REV CHECK, hardcode scan, NCI continuity, formula integrity, gridlines, Summary links
- **Data registry** — built-in lineage tracking for every input and derived number

The companion valuation skill adds:

- `Valuation_Prep`
- `Capital_Cost`
- `DCF`
- `Comps`
- `Scenarios`
- `Football_Field`
- `Target_Price`
- `Valuation_QC`

and uses bundled Python scripts for calculation-heavy steps instead of prompt-only arithmetic.

The first specialist valuation extension adds:

- `financials_prep.json`
- `pb_roe_output.json`
- `residual_income_output.json`
- optional `embedded_value_output.json`
- `target_price_summary.json`
- `financials_qc.json`

The second specialist valuation extension adds:

- `property_bridge.json`
- `nav_output.json`
- `affo_output.json`
- `target_price_summary.json`
- `reit_qc.json`

The companion investment memo skill adds:

- `Memo_Input_Pack`
- `Quality_Overlay`
- `Variant_View_Frame`
- `Decision_Framework`
- `Monitoring_Dashboard`
- `Investment_Memo.md`
- `Memo_QC`

and keeps the final memo artifact-driven by routing scores, action bands, and QC through local scripts.

The workflow orchestrator adds:

- `workflow_state.py` — inspect which phase artifacts already exist
- `run_phase3_bundle.py` — build the memo pack, overlays, dashboard, memo outline, and QC in one command

---

## Environment Setup

```bash
# Recommended: use a dedicated venv under ~/Programs, not system Python
python3 -m venv ~/Programs/venv
source ~/Programs/venv/bin/activate

# Modeling skill dependencies
pip install openpyxl yfinance pandas python-dotenv sec-edgar-downloader

# NotebookLM automation
pip install "notebooklm-py[browser]"
python -m playwright install chromium

# Optional but recommended for valuation scripting / data prep
pip install numpy
```

Python 3.9+ required.

### SEC EDGAR `.env`

For SEC downloads, create `~/Programs/.env` with:

```dotenv
SEC_EDGAR_EMAIL=your-email@example.com
```

`sec_edgar_downloader` expects an email for EDGAR identification. This fork reads it from
that env file by default.

### NotebookLM Login

Run this once in the same environment:

```bash
source ~/Programs/venv/bin/activate
notebooklm login
notebooklm status --paths
```

Expected auth path:

```text
~/.notebooklm/storage_state.json
```

After that, both the CLI and the Python client can reuse the saved browser session.

### Optional Smoke Checks

```bash
source ~/Programs/venv/bin/activate
python src/3-statements-ultra-sec/scripts/sec_nlm_bootstrap.py --help
python src/3-statements-ultra-sec/scripts/nlm_extract_company_pack.py --help
python src/valuation-ultra/scripts/dcf_valuation.py --help
python src/valuation-ultra/scripts/comps_valuation.py --help
python src/valuation-financials/scripts/financials_prep.py --help
python src/valuation-financials/scripts/pb_roe_valuation.py --help
python src/valuation-financials/scripts/residual_income.py --help
python src/valuation-reit-property/scripts/property_bridge.py --help
python src/valuation-reit-property/scripts/reit_nav.py --help
python src/valuation-reit-property/scripts/affo_valuation.py --help
python src/valuation-regulated-assets/scripts/regulatory_bridge.py --help
python src/valuation-regulated-assets/scripts/rab_valuation.py --help
python src/valuation-asset-nav/scripts/reserve_model.py --help
python src/valuation-asset-nav/scripts/asset_nav.py --help
python src/valuation-biotech-rnpv/scripts/pipeline_registry.py --help
python src/valuation-biotech-rnpv/scripts/pipeline_rnpv.py --help
python src/valuation-sotp/scripts/segment_normalizer.py --help
python src/valuation-sotp/scripts/sotp_valuation.py --help
python src/investment-banking-ultra/scripts/workflow_state.py --help
python src/investment-banking-ultra/scripts/run_phase3_bundle.py --help
python src/investment-memo-ultra/scripts/memo_input_pack.py --help
python src/investment-memo-ultra/scripts/build_memo_pack_from_artifacts.py --help
python src/investment-memo-ultra/scripts/render_memo_outline.py --help
```

---

## Installation

### Cowork / Claude Code (skill file)

1. Download `3-statements-ultra-sec.skill`
2. Download `valuation-ultra.skill`
3. Download all six phase-2 specialist packs: `valuation-financials.skill`, `valuation-reit-property.skill`, `valuation-regulated-assets.skill`, `valuation-asset-nav.skill`, `valuation-biotech-rnpv.skill`, and `valuation-sotp.skill`
4. Download `investment-memo-ultra.skill`
5. Download `investment-banking-ultra.skill`
6. In Cowork: **Settings → Skills → Install from file** → select each `.skill` file
7. In Claude Code CLI: place the unzipped folders under your `.claude/skills/` directory

### Manual (Claude Code)

```bash
# Unzip the modeling skill
unzip 3-statements-ultra-sec.skill -d ~/.claude/skills/3-statements-ultra-sec/

# Unzip the valuation skill
unzip valuation-ultra.skill -d ~/.claude/skills/valuation-ultra/

# Unzip the financials extension pack
unzip valuation-financials.skill -d ~/.claude/skills/valuation-financials/

# Unzip the REIT/property extension pack
unzip valuation-reit-property.skill -d ~/.claude/skills/valuation-reit-property/

# Unzip the regulated-assets extension pack
unzip valuation-regulated-assets.skill -d ~/.claude/skills/valuation-regulated-assets/

# Unzip the asset-NAV extension pack
unzip valuation-asset-nav.skill -d ~/.claude/skills/valuation-asset-nav/

# Unzip the biotech rNPV extension pack
unzip valuation-biotech-rnpv.skill -d ~/.claude/skills/valuation-biotech-rnpv/

# Unzip the SOTP extension pack
unzip valuation-sotp.skill -d ~/.claude/skills/valuation-sotp/

# Unzip the memo skill
unzip investment-memo-ultra.skill -d ~/.claude/skills/investment-memo-ultra/

# Unzip the orchestrator skill
unzip investment-banking-ultra.skill -d ~/.claude/skills/investment-banking-ultra/
```

---

## How The Workflow Fits Together

### Phase 1 — Modeling (`3-statements-ultra-sec`)

Use the SEC-first skill to:

1. Download SEC filings when the company is a US SEC filer
2. Seed a dedicated NotebookLM notebook with those filings
3. Extract historical financials and qualitative drivers into `Raw_Info`
4. Build `Assumptions`, `IS`, `BS`, `CF`, `Returns`, and summary outputs

Important helper scripts:

- `src/3-statements-ultra-sec/scripts/sec_nlm_bootstrap.py`
- `src/3-statements-ultra-sec/scripts/nlm_extract_company_pack.py`

### Phase 2 — Valuation (`valuation-ultra`)

Use the valuation skill after the operating model is finished.

It works in this order:

1. `valuation_prep.py` standardizes the bridge from model outputs to NOPAT, UFCF, ROIC, net debt, and diluted shares
2. `cost_of_capital.py` computes cost of equity, after-tax debt cost, and WACC
3. `dcf_valuation.py` and `comps_valuation.py` produce primary and secondary valuation outputs
4. `reverse_dcf.py` and `football_field.py` produce implied-expectation and range outputs
5. `valuation_qc.py` enforces validation before a target price is finalized

The valuation skill is script-first for hard calculations and uses prompt reasoning only for:

- method selection
- peer selection
- accounting judgment
- investment narrative and risks

For financial businesses, use the first specialist extension pack instead of forcing the core workflow:

- `valuation-financials` for banks, insurers, and book-value-driven specialty finance
- methods: `P/B` or `P/TBV` vs `ROE` / `ROTCE`, residual income, and embedded value where disclosure allows

For real-estate businesses, use the second specialist extension pack instead of forcing the core workflow:

- `valuation-reit-property` for REITs, property platforms, and stabilized asset-heavy developers
- methods: `NAV`, `AFFO` multiple, cap-rate sensitivity, and development-vs-stabilized asset split

For other specialist valuation families, use the matching extension pack instead of stretching the
core workflow:

- `valuation-regulated-assets` for regulated utilities and regulated infrastructure
- `valuation-asset-nav` for reserve-driven resource businesses
- `valuation-biotech-rnpv` for clinical biotech and pipeline-led pharma
- `valuation-sotp` for conglomerates, holdcos, and mixed-model companies

The current architecture is:

- one core `valuation-ultra` for shared `DCF + comps + reverse DCF + QC`
- six implemented specialist extension packs:
- `valuation-financials`
- `valuation-reit-property`
- `valuation-regulated-assets`
- `valuation-asset-nav`
- `valuation-biotech-rnpv`
- `valuation-sotp`

See `src/valuation-ultra/references/extension-pack-roadmap.md`.

### Phase 3 — Investment Memo (`investment-memo-ultra`)

Use the memo skill after the valuation package is finished.

It works in this order:

1. `build_memo_pack_from_artifacts.py` auto-discovers the finished phase-1 workbook plus phase-2 JSONs and produces a memo-ready pack
2. `memo_input_pack.py` remains available when you already have normalized JSON fragments
3. `quality_overlay.py` computes the four-dimension quality cross-check
4. `variant_view_frame.py` frames market-implied vs underwritten assumptions
5. `decision_engine.py` computes action bands, hurdle-aware action price, and sizing ranges
6. `monitoring_dashboard.py` turns drivers, risks, and catalysts into a dashboard
7. `render_memo_outline.py` generates a markdown memo skeleton populated with hard facts
8. `memo_qc.py` checks that the final memo includes the required sections and ties to the core numbers

The memo skill is script-first for:

- hard fact tables
- quality scoring
- action-price math
- monitoring thresholds
- memo QC

Prompt reasoning is reserved for:

- thesis writing
- key forces
- management and competitive judgment
- pre-mortem and risk ranking

### Workflow Orchestrator (`investment-banking-ultra`)

Use the orchestrator skill when you do not want to remember which phase should run next.

It works in this order:

1. `workflow_state.py` scans the working directory and detects phase-1, phase-2, and phase-3 artifacts
2. If phase 1 is missing, it routes you into `3-statements-ultra-sec`
3. If phase 1 is ready but phase 2 is missing, it routes you into `valuation-ultra`
4. If phases 1 and 2 are ready, `run_phase3_bundle.py` generates the deterministic memo bundle in one command
5. Then `investment-memo-ultra` refines the narrative and final judgment sections

Recommended bridge command:

```bash
source ~/Programs/venv/bin/activate
python src/investment-banking-ultra/scripts/run_phase3_bundle.py --workdir .
```

---

## How To Use This Repo

This repo is no longer “one big 3-statement skill.” It is a modular workflow:

1. `investment-banking-ultra` inspects the workspace and tells you which phase should run next.
2. `3-statements-ultra-sec` builds the operating model and its disk-state artifacts.
3. `valuation-ultra` or a specialist phase-2 pack builds the valuation outputs.
4. `investment-memo-ultra` turns those artifacts into a decision-ready memo package.

If you want the cleanest end-to-end flow, start with the orchestrator and let it route you.

---

## One-Minute Mental Model

If you are new to this repo, think about it like this:

- Phase 1 answers: "What happened historically, and what does the operating model look like?"
- Phase 2 answers: "What is the business worth under explicit valuation methods?"
- Phase 3 answers: "What is the investment case, what does the market imply, and what should we monitor?"
- The orchestrator answers: "Which phase is missing right now, and which skill should run next?"

So the workflow is not:

- “write one giant prompt and hope it does everything”

It is:

1. build a model
2. build a valuation
3. build a memo
4. let the skills hand artifacts to one another through files on disk

---

## First-Time Setup Checklist

If you are setting this up on a new machine, the minimum path is:

1. Create a dedicated Python environment under `~/Programs/venv`
2. Install the Python dependencies listed in `Environment Setup`
3. Create `~/Programs/.env` with `SEC_EDGAR_EMAIL=...`
4. Run `notebooklm login` once in that same environment
5. Install the `.skill` files into Cowork / Claude Code
6. Run the smoke-check commands once to confirm the scripts are callable
7. Start each company in its own clean workspace folder

If those seven things are done, the repo is ready to run locally.

---

## How To Invoke The Skills

If you are unsure where to start, use the orchestrator:

```text
Use investment-banking-ultra to start an end-to-end analysis for COHR.
```

If you want to run phases directly:

- Phase 1:
  `Use 3-statements-ultra-sec to build a 3-statement model for COHR from SEC filings.`
- Phase 2 standard:
  `Use valuation-ultra to value COHR with DCF, comps, and reverse DCF.`
- Phase 2 specialist:
  `Use valuation-financials for JPM.`
  `Use valuation-reit-property for PLD.`
  `Use valuation-regulated-assets for a regulated utility.`
  `Use valuation-asset-nav for an E&P company.`
  `Use valuation-biotech-rnpv for a clinical-stage biotech.`
  `Use valuation-sotp for a conglomerate.`
- Phase 3:
  `Use investment-memo-ultra to write the investment memo once phase 1 and phase 2 are complete.`

The safest default is still:

```text
Use investment-banking-ultra and let it determine the next phase.
```

---

## Phase 1 In Practice

`3-statements-ultra-sec` is the operating-model engine.

Use it when you need:

- a real 3-statement model, not a quick template fill
- SEC-first sourcing for US filers
- NotebookLM-assisted extraction from the same filing set
- resumable state across multiple sessions

Its expected outputs are:

- one Excel workbook containing `Summary`, `Assumptions`, `IS`, `BS`, `CF`, `Returns`, `Cross_Check`, `Raw_Info`, `_Registry`, `_State`
- `_model_log.md`
- `_pending_links.json`

The orchestrator now treats those sidecars and `_State` checkpoints as part of phase-1 readiness, not optional extras.

---

## Phase 2 In Practice

`valuation-ultra` is the default phase-2 engine for standard operating businesses. It covers:

- valuation prep
- cost of capital
- DCF
- comps
- reverse DCF
- football field
- valuation QC

When the company needs different valuation mechanics, switch to the specialist pack instead of stretching the generic DCF flow:

- `valuation-financials`: banks, insurers, book-value-driven financials
- `valuation-reit-property`: REITs, property platforms, stabilized real estate
- `valuation-regulated-assets`: utilities and regulated infrastructure
- `valuation-asset-nav`: reserve-driven resource businesses
- `valuation-biotech-rnpv`: clinical biotech and pipeline-led pharma
- `valuation-sotp`: conglomerates, holdcos, mixed-model businesses

Phase 2 is script-first. The heavy calculation steps should come from the bundled Python scripts, while the model is still responsible for method choice, peer judgment, and narrative interpretation.

---

## Phase 3 In Practice

`investment-memo-ultra` is a companion memo skill, not a replacement for phases 1 and 2.

It expects finished phase-1 and phase-2 artifacts, then builds:

- `memo_input_pack.json`
- `quality_overlay.json`
- `variant_view_frame.json`
- `decision_framework.json`
- `monitoring_dashboard.json`
- `Investment_Memo.md`
- `memo_qc.json`

The memo layer is also script-first for deterministic outputs such as quality scoring, action bands, monitoring thresholds, and memo QC.

---

## Artifact Handoff

The intended artifact chain is:

1. Phase 1 creates the workbook plus its sidecars.
2. Phase 2 creates either the core valuation set or one specialist-pack valuation set.
3. The bridge scripts normalize those outputs into a memo-ready pack.
4. Phase 3 generates the memo bundle from those normalized artifacts.

That handoff is the center of this repo. The skills are meant to cooperate through files on disk, not by relying on chat memory.

---

## Upstream Origins

This repo is a fork-and-extension project.

- Phase 1 is forked from [`willpowerju-lgtm/3-statement-ultra-for-finance`](https://github.com/willpowerju-lgtm/3-statement-ultra-for-finance), then adapted into a SEC-first / NotebookLM-first workflow with stricter artifact gating and resume logic.
- Phase 3 draws its memo structure and stylistic inspiration from [`star23/Day1Global-Skills`](https://github.com/star23/Day1Global-Skills), especially the `tech-earnings-deepdive` and `us-value-investing` skills, but has been rebuilt here into an artifact-driven, script-heavy memo workflow.
- The specialist phase-2 packs, artifact bridge, and `investment-banking-ultra` orchestrator are repo-native additions in this project.

---

## Current Scope

This repo is best for:

- institutional-style modeling and valuation workflows
- repeatable phase handoff on disk
- cases where you want the model, valuation, and memo to reconcile to one another

This repo is not optimized for:

- one-shot “20 minute” rough models
- skipping phase outputs and jumping straight to a polished memo
- treating every industry as a generic DCF business

---

## License

This skill is shared for personal and research use. No warranty is provided. Financial models produced by this skill should be independently verified before use in investment decisions.

---

## License

This skill is shared for personal and research use. No warranty is provided. Financial models produced by this skill should be independently verified before use in investment decisions.
