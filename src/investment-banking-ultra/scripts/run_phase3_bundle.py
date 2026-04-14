#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[2]
MEMO_SCRIPTS = SRC_ROOT / "investment-memo-ultra" / "scripts"


def run_script(script_name, args):
    script_path = MEMO_SCRIPTS / script_name
    command = [sys.executable, str(script_path), *args]
    subprocess.run(command, check=True)


def append_log(log_path, lines):
    text = "\n".join(lines).rstrip() + "\n"
    if log_path.exists():
        existing = log_path.read_text(encoding="utf-8").rstrip()
        if existing:
            text = existing + "\n\n" + text
    log_path.write_text(text, encoding="utf-8")


def maybe_company_overrides(args):
    pairs = []
    for key, value in [
        ("name", args.company_name),
        ("ticker", args.ticker),
        ("sector_family", args.sector_family),
        ("industry", args.industry),
        ("currency", args.currency),
    ]:
        if value:
            pairs.extend(["--company-attr", f"{key}={value}"])
    return pairs


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run the deterministic phase-3 bridge and memo-artifact bundle from a finished phase-1 workbook "
            "and phase-2 valuation outputs."
        )
    )
    parser.add_argument("--workdir", default=".", help="Root directory for artifact discovery")
    parser.add_argument("--workbook", help="Explicit phase-1 workbook path")
    parser.add_argument("--valuation-dir", help="Explicit phase-2 valuation-artifact directory")
    parser.add_argument("--supplement", help="Optional memo supplement JSON")
    parser.add_argument("--output-dir", default=".", help="Directory where memo artifacts should be written")
    parser.add_argument("--company-name", help="Override company name")
    parser.add_argument("--ticker", help="Override ticker")
    parser.add_argument("--sector-family", help="Override sector family")
    parser.add_argument("--industry", help="Override industry")
    parser.add_argument("--currency", help="Override currency")
    parser.add_argument("--current-price", type=float, help="Override current price")
    parser.add_argument("--moat-type", action="append", dest="moat_types", help="Append moat types")
    parser.add_argument("--memo-output", default="Investment_Memo.md", help="Markdown output filename")
    parser.add_argument("--skip-qc", action="store_true", help="Skip memo_qc generation")
    args = parser.parse_args()

    workdir = Path(args.workdir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    memo_pack_path = output_dir / "memo_input_pack.json"
    quality_path = output_dir / "quality_overlay.json"
    variant_path = output_dir / "variant_view_frame.json"
    decision_path = output_dir / "decision_framework.json"
    monitoring_path = output_dir / "monitoring_dashboard.json"
    memo_path = output_dir / args.memo_output
    memo_qc_path = output_dir / "memo_qc.json"
    memo_state_path = output_dir / "_memo_state.json"
    memo_log_path = output_dir / "_memo_log.md"
    evidence_registry_path = output_dir / "_evidence_registry.json"

    bridge_args = ["--workdir", str(workdir), "--output", str(memo_pack_path)]
    if args.workbook:
        bridge_args.extend(["--workbook", args.workbook])
    if args.valuation_dir:
        bridge_args.extend(["--valuation-dir", args.valuation_dir])
    if args.supplement:
        bridge_args.extend(["--supplement", args.supplement])
    if args.current_price is not None:
        bridge_args.extend(["--current-price", str(args.current_price)])
    if args.moat_types:
        for moat_type in args.moat_types:
            bridge_args.extend(["--moat-type", moat_type])
    bridge_args.extend(maybe_company_overrides(args))

    run_script("build_memo_pack_from_artifacts.py", bridge_args)
    run_script("quality_overlay.py", ["--input", str(memo_pack_path), "--output", str(quality_path)])
    run_script("variant_view_frame.py", ["--input", str(memo_pack_path), "--output", str(variant_path)])
    run_script(
        "decision_engine.py",
        ["--memo-pack", str(memo_pack_path), "--quality", str(quality_path), "--output", str(decision_path)],
    )
    run_script("monitoring_dashboard.py", ["--input", str(memo_pack_path), "--output", str(monitoring_path)])
    run_script(
        "render_memo_outline.py",
        [
            "--memo-pack",
            str(memo_pack_path),
            "--quality",
            str(quality_path),
            "--variant",
            str(variant_path),
            "--decision",
            str(decision_path),
            "--monitoring",
            str(monitoring_path),
            "--output",
            str(memo_path),
        ],
    )
    if not args.skip_qc:
        run_script(
            "memo_qc.py",
            [
                "--memo",
                str(memo_path),
                "--memo-pack",
                str(memo_pack_path),
                "--quality",
                str(quality_path),
                "--decision",
                str(decision_path),
                "--monitoring",
                str(monitoring_path),
                "--output",
                str(memo_qc_path),
            ],
        )

    memo_pack = json.loads(memo_pack_path.read_text(encoding="utf-8"))
    evidence_registry = {
        "company": memo_pack.get("company", {}),
        "artifact_paths": memo_pack.get("artifact_paths", {}),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "notes": [
            "This registry is a starter artifact generated from phase-1 and phase-2 files.",
            "Add transcript, ownership, industry, and diligence evidence as the memo is refined.",
        ],
    }
    evidence_registry_path.write_text(json.dumps(evidence_registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    state = {
        "status": "outline_generated" if args.skip_qc else "qc_generated",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            "memo_pack": str(memo_pack_path),
            "quality_overlay": str(quality_path),
            "variant_view_frame": str(variant_path),
            "decision_framework": str(decision_path),
            "monitoring_dashboard": str(monitoring_path),
            "memo": str(memo_path),
            "memo_qc": None if args.skip_qc else str(memo_qc_path),
            "evidence_registry": str(evidence_registry_path),
        },
        "sources": memo_pack.get("artifact_paths", {}),
    }
    memo_state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    append_log(
        memo_log_path,
        [
            f"## {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}",
            "",
            "- Generated phase-3 artifact bundle from discovered phase-1 and phase-2 artifacts.",
            f"- Memo pack: `{memo_pack_path.name}`",
            f"- Memo draft: `{memo_path.name}`",
            f"- QC: `{'skipped' if args.skip_qc else memo_qc_path.name}`",
        ],
    )

    print(json.dumps({"output_dir": str(output_dir), "memo": str(memo_path), "memo_pack": str(memo_pack_path)}, indent=2))


if __name__ == "__main__":
    main()
