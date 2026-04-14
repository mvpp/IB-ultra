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

## Recommended Setup — User Preference

**Before your first session**, add the following to your Claude user preferences (Settings → Profile → Custom Instructions, or your `CLAUDE.md` file). This prevents state loss after context compaction mid-session:

```
## 3-Statements-Ultra — Compaction Recovery Protocol
When I am building a 3-statement financial model using the 3-statements-ultra skill,
after ANY context compaction event, you MUST:
1. Re-read the 3-statements-ultra SKILL.md before writing any code
2. Open the Excel model file and read the _State tab — determine exact resume point
3. Read _model_log.md — recover prior session outputs (key totals, check results)
4. Read _pending_links.json — check if BS→CF back-fill is pending
5. Run RAW_MAP + ASM_MAP spot-check before using any row numbers
6. Never hardcode any IS/BS/CF forecast cell — every cell must be a string formula
7. Resume from the next incomplete step only — never re-run completed sections
Do not rely on conversation memory for row numbers or intermediate calculation results.
Disk state (_State, _model_log.md, _pending_links.json) is always authoritative.
```

---

## Quick Start

Just say one of these trigger phrases and the skill takes over:

```
三表模型
financial model
3-statement model
建模
从零建模
build a 3-statement model for [company name]
```

The skill will ask you which data sources you have available, then guide you through the 5 sessions.

For the full three-skill workflow, a practical sequence is:

```text
1. "build a 3-statement model for COHR"
2. Complete Sessions A-E
3. "value COHR using DCF and comps"
4. Let valuation-ultra build the valuation package
5. "write the investment memo for COHR"
6. Let investment-memo-ultra build the memo pack, outline, and QC output
```

---

## 5-Session Build Flow

| Session | Tab(s) Built | What Happens | Time |
|---------|-------------|--------------|------|
| **A** | Raw_Info + Assumptions | Data extraction from NLM / Excel / Web; granularity detection; assumptions setup | 15–30 min |
| **B** | IS | Income Statement, all segments, CN GAAP R8 plug, NCI | 15–20 min |
| **C** | BS | Balance Sheet, Cash as placeholder; writes `_pending_links.json` | 15–20 min |
| **D** | CF | Cash Flow, year-by-year; R3 Others plug; BS Cash back-fill; 9 QC checks | 15–25 min |
| **E** | Returns + Cross_Check + Summary | ROIC/ROE/DuPont; assumption validation; linked Summary tab | 15–20 min |

Each session is **fully independent** — you can close the chat between sessions. State is stored in the Excel `_State` tab and two sidecar files (`_model_log.md`, `_pending_links.json`).

---

## Data Sources

| Priority | Source | Setup | Token Cost | Notes |
|----------|--------|-------|-----------|-------|
| ✅ **1st choice** | **SEC filings -> NotebookLM** | NotebookLM auth + SEC email env | Very low | Default for US SEC filers in this fork |
| ✅ **2nd choice** | **NotebookLM notebook** (annual reports / filings pre-loaded) | Two steps (see below) | Very low | Good if filings are already loaded |
| ✅ **3rd choice** | **Excel** (historical IS/BS/CF already structured) | None | Low | Useful speed layer or non-SEC fallback |
| ✅ **Fallback** | **Web** (Sina / Yahoo Finance) | None | Low | Automatic — always runs as cross-check layer |
| ⚠️ **Avoid on Pro** | **Full PDF upload** (complete annual report, prospectus) | None | 🔴 Very high | 200+ page filings consume context fast |

**Why SEC first?** It keeps the model anchored to primary filings, then uses NotebookLM to extract structured financials and management commentary from the same SEC source set. That reduces source drift and makes assumptions easier to defend.

**Why NotebookLM matters in this fork?** NotebookLM's extraction flow can pull far richer operational intelligence than structured financials alone: segment drivers, management guidance, capex plans, working capital commentary, and competitive dynamics. In this fork, the preferred path is to seed NotebookLM with SEC filings first, then use those answers to populate Raw_Info and Assumptions.

1. **Authenticate NotebookLM once** so the CLI and Python client can reuse your browser session.
2. **One-time OAuth auth** (~5 min, done once):

```bash
pip install "notebooklm-py[browser]"
python -m playwright install chromium
notebooklm login
notebooklm status --paths
```

After auth, bootstrap a US SEC filer with:

```bash
python scripts/sec_nlm_bootstrap.py --ticker COHR
python scripts/nlm_extract_company_pack.py --notebook-id <NOTEBOOK_ID>
```

If you keep your env file in `~/Programs/.env`, the SEC bootstrap script will read
`SEC_EDGAR_EMAIL` from there by default.

---

## Output — Excel File Structure

```
[1] Summary        ← business profile, financial highlights, catalysts, risks
[2] Assumptions    ← all forecast drivers (single source of truth)
[3] IS             ← Income Statement
[4] BS             ← Balance Sheet
[5] CF             ← Cash Flow (indirect method)
[6] Returns        ← ROIC / ROE / ROA / DuPont
[7] Cross_Check    ← assumption validation log vs external sources
[8] Raw_Info       ← extracted historical data (never re-read after build)
[_Registry]        ← data lineage registry (built in Session E)
[_State]           ← session metadata (delete after MODEL_COMPLETE)
```

---

## Key Rules (Summary)

| Rule | Description |
|------|-------------|
| **Rule Zero** | Every IS/BS/CF forecast cell must be an Excel formula string — never a float or int |
| **R3 Others plug** | Only permitted non-cash CF plug; keeps BS CHECK and CF CHECK both = 0 |
| **R6 Cash last** | BS Cash is always 0 placeholder until SESSION D back-fills from CF Ending Cash |
| **Code block limit** | Max 400 lines per Python block; execute before writing the next |
| **One source** | After Raw_Info is complete, all data flows via `=Raw_Info!` links only |

---

## Frequently Asked Questions

**Q: Can I use this without NotebookLM?**
Yes. NotebookLM is optional. If you don't have it, the skill falls back to Web (Sina / Yahoo Finance) as the primary data source.

**Q: What if I only have annual data but the company reports quarterly?**
The skill auto-detects granularity using yfinance. If quarterly data is available from any source, it uses quarterly. You can override with a manual answer during Phase 0.

**Q: Can I pause mid-session and resume later?**
Yes. Every code block writes a progress marker to the `_State` tab in Excel. The startup protocol at the beginning of each session automatically finds the last completed step and resumes from there.

**Q: Why do I need to run 5 separate sessions instead of one?**
Quarterly IS models produce 300+ lines of Python code per section. A single large script hits the LLM output cap and is silently truncated — the Excel file ends up partially written with no error. The 5-session, one-section-at-a-time approach prevents this entirely.

**Q: What if BS CHECK ≠ 0 after Session C?**
This is expected and correct. BS Cash is a placeholder (0) until Session D back-fills it from CF Ending Cash. Do not try to force-balance BS in Session C.

**Q: Does this work for US GAAP companies (e.g., NYSE/NASDAQ-listed)?**
Yes. Use `ticker = "TICKER"` format (e.g. `"AAPL"`) in Phase 0. The skill detects IFRS/US GAAP from the source and applies the correct IS template.

---

## What Was Removed in the Public Edition

This is a sanitized version of the original private skill. The following have been removed or replaced:

- **Bark push notification module** — `bark-notify.md` and all `bark()` function calls removed. The original skill sent push notifications to a private device during long-running sessions; this is not needed for general use.
- **Internal session paths** — hardcoded internal deployment paths (e.g. Python package install locations specific to the original environment) replaced with standard `pip install` instructions.
- **Internal data pipeline references** — references to a proprietary external `data-validator` script replaced with a self-contained openpyxl implementation in R11.

All core modeling logic, QC checks, templates, and session protocols are unchanged.

---

## vs. the Official `financial-analysis:3-statements` Skill

There is an official 3-statement skill available in the Claude marketplace (`financial-analysis:3-statements`). The two skills serve different purposes and have meaningfully different quality standards. Here is an honest comparison.

### What the official skill does well

It is fast. If you already have a partially filled Excel template and just need the formulas linked up, the official skill does that job in a single session without setup. It works well for quick, rough-cut models where speed matters more than structural correctness.

### Where this skill differs — and why it matters for serious work

**1. Cash is never plugged.**

This is the most fundamental difference. The official skill calculates Cash by plugging: `Cash = Total Liabilities + Equity − Non-Cash Assets`. This forces the balance sheet to balance, but it is structurally wrong. Cash derived this way has no connection to actual cash generation — it is a residual that will be wildly incorrect whenever any other balance sheet item is even slightly off. In a real model, Cash must equal CF Ending Cash, derived from the full cash flow waterfall. This skill enforces that rule unconditionally: Cash is left as a placeholder in Session C and back-filled from the CF statement in Session D, period.

**2. Revenue is split by segment with independent drivers.**

The official skill treats revenue as a single line. This skill builds each business segment as an independently driven row — separate YoY growth %, separate volume × ASP structure if applicable, separate seasonality percentages for quarterly models. A single-line revenue assumption is adequate for a back-of-envelope; it is not adequate for an equity research or IC memo-quality model where you need to stress individual product lines or geography.

**3. Every forecast cell is an Excel formula — no exceptions.**

Rule Zero of this skill is that no forecast cell in IS/BS/CF may hold a hardcoded number. Every cell must be a string formula referencing the Assumptions tab or another cell. The official skill routinely writes numeric values directly into forecast cells, which means the model breaks silently the moment any assumption changes — the cell does not recalculate because it contains a number, not a formula.

**4. CN GAAP is modelled natively.**

Chinese GAAP income statements have items between 营业总成本 and 营业利润 (其他收益, 信用减值损失, 资产减值损失, etc.) that are not present in IFRS or US GAAP. This skill handles them with a dedicated R8 plug row that captures the residual between source 营业利润 and model-derived EBIT. Ignoring these items — as a generic template will — produces systematically wrong EBIT for A-share and HK-listed CN GAAP companies.

**5. Nine QC checks must pass before the model is marked complete.**

The model cannot be finished without all of BS CHECK = 0, CF CHECK = 0, NI CHECK ≈ 0, REV CHECK = 0, a hardcode scan across all forecast columns, NCI continuity check, formula integrity spot-check, gridlines-off check, and Summary zero-hardcode check. The official skill has no equivalent QC gate.

**6. NCI is always rolled forward.**

If a company has minority interest, NCI on the balance sheet must compound each period: `NCI_end = NCI_prior + Attr_to_NCI − NCI_Dividends`. Setting forecast NCI to zero — or flat at the last historical value — is a common error that makes both the BS and the IS attribution wrong. This skill enforces the roll-forward and validates it in QC-5.

### Summary table

| | `3-statements-ultra` | `financial-analysis:3-statements` (official) |
|---|---|---|
| Cash derivation | `= CF Ending Cash` (always) | Plugged from BS residual |
| Revenue structure | Per-segment, independent drivers | Single line |
| Forecast cells | 100% Excel formulas | Mix of formulas and hardcodes |
| CN GAAP support | Native (R8 plug, 营业利润 reconciliation) | Generic template |
| QC validation | 9 mandatory checks | None |
| NCI roll-forward | Enforced | Not guaranteed |
| Quarterly granularity | Full (35 IS columns per year) | Annual only |
| Setup required | 5 sessions, ~1–2 hours total | Single session |
| Best for | IPO / equity research quality models | Quick template population |

### When to use which

Use the official skill if you need a rough model in 20 minutes and the numbers do not need to hold up to scrutiny.

Use this skill if the model will be used in an IC memo, a research note, an investor presentation, or any context where someone will actually check whether it balances — and whether the assumptions flow through correctly.

---

## License

This skill is shared for personal and research use. No warranty is provided. Financial models produced by this skill should be independently verified before use in investment decisions.
