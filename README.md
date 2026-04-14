# IB-ultra

**English** | [中文](README.zh.md)

**Version:** April 2026  
**Compatibility:** Claude Code / Cowork (Anthropic)

---

## What This Repo Is

`IB-ultra` is a modular investment workflow, not a single prompt or a single skill.

It is designed to help you run:

1. Phase 1: build a real 3-statement operating model
2. Phase 2: build a valuation package
3. Phase 3: build an institutional-style investment memo

The workflow is file-based. Each phase writes artifacts to disk, and the next phase reads them.

That means the system is built for:

- repeatable work
- resume-after-interruption workflows
- model / valuation / memo consistency

It is not built for:

- one-shot rough models
- skipping directly to a polished memo with no underlying model
- forcing every company through the same generic valuation method

---

## One-Minute Mental Model

If you are new here, think about the repo like this:

- `3-statements-ultra-sec` answers: "What happened historically, and what does the operating model look like?"
- `valuation-ultra` or a specialist phase-2 pack answers: "What is the business worth?"
- `investment-memo-ultra` answers: "What is the investment case, what does the market imply, and what should we monitor?"
- `investment-banking-ultra` answers: "Which phase is missing right now, and which skill should run next?"

So the intended workflow is:

1. build the model
2. build the valuation
3. build the memo
4. let the phases hand files to one another automatically

---

## Skills In This Repo

### Core workflow

- `3-statements-ultra-sec.skill`
  Phase 1 operating model, SEC-first and NotebookLM-assisted for US filers
- `valuation-ultra.skill`
  Default Phase 2 valuation engine for standard operating companies
- `investment-memo-ultra.skill`
  Phase 3 memo / monitoring / decision package
- `investment-banking-ultra.skill`
  Orchestrator that inspects the workspace and routes to the next missing phase

### Phase 2 specialist packs

- `valuation-financials.skill`
  Banks, insurers, book-value-driven financials
- `valuation-reit-property.skill`
  REITs, property platforms, stabilized real estate
- `valuation-regulated-assets.skill`
  Utilities and regulated infrastructure
- `valuation-asset-nav.skill`
  Reserve-driven resource businesses
- `valuation-biotech-rnpv.skill`
  Clinical biotech and pipeline-led pharma
- `valuation-sotp.skill`
  Conglomerates, holdcos, mixed-model businesses

---

## First-Time Setup Checklist

If you are setting this up on a new machine, do these steps in order:

1. Create a dedicated Python environment under `~/Programs/venv`
2. Install the Python dependencies
3. Create `~/Programs/.env` with your SEC EDGAR email
4. Run `notebooklm login` once in that same environment
5. Install the `.skill` files into Cowork / Claude Code
6. Run the smoke-check commands once
7. Start each company in its own clean workspace folder

If those seven steps are done, the repo is ready to run locally.

---

## Environment Setup

Use a dedicated environment. Do not use system Python.

```bash
python3 -m venv ~/Programs/venv
source ~/Programs/venv/bin/activate

pip install openpyxl yfinance pandas python-dotenv sec-edgar-downloader
pip install "notebooklm-py[browser]"
python -m playwright install chromium
pip install numpy
```

Python 3.9+ is recommended.

### SEC EDGAR `.env`

Create `~/Programs/.env`:

```dotenv
SEC_EDGAR_EMAIL=your-email@example.com
```

The SEC bootstrap scripts read this value when downloading filings.

### NotebookLM Login

Run once:

```bash
source ~/Programs/venv/bin/activate
notebooklm login
notebooklm status --paths
```

Expected auth file:

```text
~/.notebooklm/storage_state.json
```

After that, the CLI and Python client can reuse the saved session.

---

## Installation

### Install into Cowork / Claude Code

Install these `.skill` files:

1. `3-statements-ultra-sec.skill`
2. `valuation-ultra.skill`
3. `valuation-financials.skill`
4. `valuation-reit-property.skill`
5. `valuation-regulated-assets.skill`
6. `valuation-asset-nav.skill`
7. `valuation-biotech-rnpv.skill`
8. `valuation-sotp.skill`
9. `investment-memo-ultra.skill`
10. `investment-banking-ultra.skill`

### Manual unzip example

```bash
unzip 3-statements-ultra-sec.skill -d ~/.claude/skills/3-statements-ultra-sec/
unzip valuation-ultra.skill -d ~/.claude/skills/valuation-ultra/
unzip valuation-financials.skill -d ~/.claude/skills/valuation-financials/
unzip valuation-reit-property.skill -d ~/.claude/skills/valuation-reit-property/
unzip valuation-regulated-assets.skill -d ~/.claude/skills/valuation-regulated-assets/
unzip valuation-asset-nav.skill -d ~/.claude/skills/valuation-asset-nav/
unzip valuation-biotech-rnpv.skill -d ~/.claude/skills/valuation-biotech-rnpv/
unzip valuation-sotp.skill -d ~/.claude/skills/valuation-sotp/
unzip investment-memo-ultra.skill -d ~/.claude/skills/investment-memo-ultra/
unzip investment-banking-ultra.skill -d ~/.claude/skills/investment-banking-ultra/
```

---

## How To Invoke The Skills

If you are not sure where to start, use the orchestrator:

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

Safest default:

```text
Use investment-banking-ultra and let it determine the next phase.
```

---

## Recommended First Run

On your first real company:

1. Create a fresh folder, for example `~/Programs/company-work/COHR`
2. Open that folder in Claude Code / Cowork
3. Start with:

```text
Use investment-banking-ultra to start an end-to-end analysis for COHR.
```

4. Let the orchestrator tell you whether phase 1, phase 2, or phase 3 is missing
5. Follow the recommended next step

This is the easiest way to avoid skipping required artifacts.

---

## How The Phases Work

### Phase 1: Operating model

Skill:

- `3-statements-ultra-sec`

What it does:

- downloads SEC filings for US filers
- seeds NotebookLM with those filings
- extracts historical financials and operating context
- builds `Raw_Info`, `Assumptions`, `IS`, `BS`, `CF`, `Returns`, `Summary`, `Cross_Check`

Expected outputs:

- Excel workbook with:
  `Summary`, `Assumptions`, `IS`, `BS`, `CF`, `Returns`, `Cross_Check`, `Raw_Info`, `_Registry`, `_State`
- `_model_log.md`
- `_pending_links.json`

Phase 1 is considered complete only when the workbook and sidecars are present and `_State` contains the expected checkpoint keys.

### Phase 2: Valuation

Default skill:

- `valuation-ultra`

Typical outputs:

- `valuation_prep.json`
- `capital_cost.json`
- `dcf_output.json`
- `comps_output.json`
- `reverse_dcf.json`
- `football_field.json`
- `valuation_qc.json`
- `valuation_summary.json`

When to switch to a specialist pack:

- banks / insurers: `valuation-financials`
- REIT / real estate: `valuation-reit-property`
- utilities / regulated assets: `valuation-regulated-assets`
- reserve NAV businesses: `valuation-asset-nav`
- biotech / pipeline stories: `valuation-biotech-rnpv`
- conglomerates / holdcos: `valuation-sotp`

Phase 2 is script-first. The bundled Python scripts should do the heavy calculation work.

### Phase 3: Memo

Skill:

- `investment-memo-ultra`

What it does:

- reads the finished phase-1 and phase-2 artifacts
- builds a normalized memo input pack
- computes quality overlay, variant view, decision framework, and monitoring dashboard
- renders a memo draft and runs memo QC

Typical outputs:

- `memo_input_pack.json`
- `quality_overlay.json`
- `variant_view_frame.json`
- `decision_framework.json`
- `monitoring_dashboard.json`
- `Investment_Memo.md`
- `memo_qc.json`

### Orchestrator

Skill:

- `investment-banking-ultra`

What it does:

- inspects the current workspace
- determines whether phase 1, 2, or 3 is missing
- points you to the right next skill
- can run the deterministic phase-3 bridge bundle once phase 1 and 2 are ready

Key helper scripts:

- `src/investment-banking-ultra/scripts/workflow_state.py`
- `src/investment-banking-ultra/scripts/run_phase3_bundle.py`

---

## Artifact Handoff

The intended artifact chain is:

1. Phase 1 writes the workbook plus sidecars
2. Phase 2 writes a valuation artifact set
3. Bridge scripts normalize those files into a memo-ready pack
4. Phase 3 writes the memo bundle

The repo is designed around artifact handoff on disk, not around relying on long chat memory.

---

## Smoke Checks

Run these once after setup:

```bash
source ~/Programs/venv/bin/activate
python src/3-statements-ultra-sec/scripts/sec_nlm_bootstrap.py --help
python src/3-statements-ultra-sec/scripts/nlm_extract_company_pack.py --help
python src/valuation-ultra/scripts/dcf_valuation.py --help
python src/valuation-ultra/scripts/comps_valuation.py --help
python src/valuation-financials/scripts/financials_prep.py --help
python src/valuation-reit-property/scripts/property_bridge.py --help
python src/valuation-regulated-assets/scripts/regulatory_bridge.py --help
python src/valuation-asset-nav/scripts/reserve_model.py --help
python src/valuation-biotech-rnpv/scripts/pipeline_registry.py --help
python src/valuation-sotp/scripts/segment_normalizer.py --help
python src/investment-banking-ultra/scripts/workflow_state.py --help
python src/investment-banking-ultra/scripts/run_phase3_bundle.py --help
python src/investment-memo-ultra/scripts/build_memo_pack_from_artifacts.py --help
```

If these run, your machine is configured correctly.

---

## Upstream Origins

This is a fork-and-extension project.

- Phase 1 is forked from [`willpowerju-lgtm/3-statement-ultra-for-finance`](https://github.com/willpowerju-lgtm/3-statement-ultra-for-finance)
- Phase 3 draws its memo structure and stylistic inspiration from [`star23/Day1Global-Skills`](https://github.com/star23/Day1Global-Skills), especially `tech-earnings-deepdive` and `us-value-investing`
- The specialist phase-2 packs, artifact bridge, and `investment-banking-ultra` orchestrator are native additions in this repo

---

## Current Scope

Best for:

- institutional-style modeling / valuation / memo workflows
- repeatable phase handoff
- cases where the model, valuation, and memo should reconcile

Not optimized for:

- 20-minute rough models
- skipping phases and going straight to a polished memo
- forcing every industry into generic DCF logic

---

## License

Shared for personal and research use. No warranty is provided. Any financial model or valuation output should be independently verified before use in real investment decisions.
