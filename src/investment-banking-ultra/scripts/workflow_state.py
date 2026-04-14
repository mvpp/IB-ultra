#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[2]
MEMO_SCRIPTS = SRC_ROOT / "investment-memo-ultra" / "scripts"
sys.path.insert(0, str(MEMO_SCRIPTS))

from artifact_bridge import discover_phase1_workbook, discover_phase2_files  # noqa: E402


PHASE3_FILES = {
    "memo_pack": ["memo_input_pack.json"],
    "quality": ["quality_overlay.json"],
    "variant": ["variant_view_frame.json"],
    "decision": ["decision_framework.json"],
    "monitoring": ["monitoring_dashboard.json"],
    "memo": ["Investment_Memo.md", "investment_memo_outline.md", "investment_memo.md"],
    "memo_qc": ["memo_qc.json"],
    "memo_state": ["_memo_state.json"],
    "memo_log": ["_memo_log.md"],
    "evidence_registry": ["_evidence_registry.json"],
}


def latest_match(root, names):
    root = Path(root)
    candidates = []
    for name in names:
        candidates.extend(root.rglob(name))
    if not candidates:
        return None
    return str(max(candidates, key=lambda item: item.stat().st_mtime))


def discover_phase3_files(root):
    return {
        key: match
        for key, names in PHASE3_FILES.items()
        if (match := latest_match(root, names)) is not None
    }


def phase2_status(files):
    if not files:
        return "missing"
    if files.get("valuation_summary"):
        return "ready"
    ready_sets = [
        {"dcf", "comps", "reverse_dcf", "football_field", "valuation_qc"},
        {"financials_prep", "pb_roe", "residual_income", "financials_qc"},
        {"property_bridge", "reit_nav", "affo_output", "reit_qc"},
        {"regulatory_bridge", "rab_output", "ddm_output", "regulated_qc"},
        {"reserve_model", "asset_nav_output", "commodity_sensitivity", "pnav_market_check", "asset_nav_qc"},
        {"pipeline_registry", "pipeline_rnpv_output", "cash_runway_dilution", "launch_scenarios", "biotech_qc"},
        {"segment_normalizer", "segment_method_router", "sotp_output", "holdco_discount", "sotp_qc"},
    ]
    if any(required.issubset(set(files)) for required in ready_sets):
        return "ready"
    return "partial"


def phase3_status(files):
    if not files:
        return "missing"
    required = {"memo_pack", "quality", "variant", "decision", "monitoring", "memo"}
    if required.issubset(set(files)):
        return "ready"
    return "partial"


def recommended_action(phase1_ready, phase2, phase3):
    if not phase1_ready:
        return {
            "phase": 1,
            "action": "build_phase1_model",
            "skill": "3-statements-ultra-sec",
            "reason": "No finished phase-1 workbook was found.",
        }
    if phase2 != "ready":
        return {
            "phase": 2,
            "action": "build_phase2_valuation",
            "skill": "valuation-ultra",
            "reason": "A finished phase-1 workbook exists, but the valuation artifact set is missing or partial.",
        }
    if phase3 == "missing":
        return {
            "phase": 3,
            "action": "generate_phase3_bundle",
            "skill": "investment-banking-ultra",
            "reason": "Phase 1 and phase 2 are ready, so the deterministic memo bundle can be generated automatically.",
        }
    if phase3 == "partial":
        return {
            "phase": 3,
            "action": "refresh_phase3_bundle",
            "skill": "investment-banking-ultra",
            "reason": "Some memo artifacts already exist, but the bundle is incomplete.",
        }
    return {
        "phase": 3,
        "action": "review_or_refresh_memo",
        "skill": "investment-memo-ultra",
        "reason": "All three phases are present. Review the memo narrative or refresh QC if the upstream artifacts changed.",
    }


def build_state(workdir):
    workdir = Path(workdir).resolve()
    workbook = discover_phase1_workbook(workdir)
    phase2_files = discover_phase2_files(workdir)
    phase3_files = discover_phase3_files(workdir)

    phase1_ready = workbook is not None
    phase2 = phase2_status(phase2_files)
    phase3 = phase3_status(phase3_files)

    return {
        "workdir": str(workdir),
        "phase1": {
            "status": "ready" if phase1_ready else "missing",
            "workbook": str(workbook) if workbook else None,
        },
        "phase2": {
            "status": phase2,
            "artifacts": phase2_files,
        },
        "phase3": {
            "status": phase3,
            "artifacts": phase3_files,
        },
        "next_step": recommended_action(phase1_ready, phase2, phase3),
        "commands": {
            "state": f"{sys.executable} src/investment-banking-ultra/scripts/workflow_state.py --workdir {workdir}",
            "phase3_bundle": f"{sys.executable} src/investment-banking-ultra/scripts/run_phase3_bundle.py --workdir {workdir}",
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Inspect the repo and decide which investment-workflow phase should run next."
    )
    parser.add_argument("--workdir", default=".", help="Root directory to inspect")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    state = build_state(args.workdir)
    if args.output:
        Path(args.output).write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(args.output)
        return
    print(json.dumps(state, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
