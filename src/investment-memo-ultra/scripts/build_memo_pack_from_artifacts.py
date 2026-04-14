#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from artifact_bridge import (
    deep_update,
    discover_phase1_workbook,
    discover_phase2_files,
    extract_phase1_payload,
    extract_phase2_payload,
    load_json,
)
from memo_common import dump_json
from memo_input_pack import build_memo_pack


def parse_key_values(pairs):
    output = {}
    for item in pairs or []:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        output[key.strip()] = value.strip()
    return output


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Bridge a finished phase-1 workbook and phase-2 valuation JSONs into a memo-ready input pack. "
            "Auto-discovers artifacts from --workdir unless explicit paths are provided."
        )
    )
    parser.add_argument("--workdir", default=".", help="Root directory for artifact discovery")
    parser.add_argument("--workbook", help="Explicit phase-1 workbook path")
    parser.add_argument("--valuation-dir", help="Directory containing phase-2 JSON artifacts")
    parser.add_argument("--supplement", help="Optional JSON file with overrides or extra metadata")
    parser.add_argument("--company-name", help="Override company name")
    parser.add_argument("--ticker", help="Override ticker")
    parser.add_argument("--sector-family", help="Override sector family")
    parser.add_argument("--industry", help="Override industry")
    parser.add_argument("--currency", help="Override currency")
    parser.add_argument("--current-price", type=float, help="Override current price")
    parser.add_argument("--moat-type", action="append", dest="moat_types", help="Append moat types")
    parser.add_argument("--company-attr", action="append", help="Extra company attributes in key=value form")
    parser.add_argument("--output", default="memo_input_pack.json", help="Path to JSON output")
    args = parser.parse_args()

    supplement = load_json(args.supplement) if args.supplement else {}
    workbook_path = args.workbook or discover_phase1_workbook(args.workdir)
    if not workbook_path:
        raise FileNotFoundError("Could not find a phase-1 workbook with the required tabs.")

    valuation_root = args.valuation_dir or args.workdir
    valuation_artifacts = discover_phase2_files(valuation_root)
    if not valuation_artifacts:
        raise FileNotFoundError("Could not find phase-2 valuation JSON artifacts.")

    company_overrides = parse_key_values(args.company_attr)
    if args.company_name:
        company_overrides["name"] = args.company_name
    if args.ticker:
        company_overrides["ticker"] = args.ticker
    if args.sector_family:
        company_overrides["sector_family"] = args.sector_family
    if args.industry:
        company_overrides["industry"] = args.industry
    if args.currency:
        company_overrides["currency"] = args.currency
    if args.moat_types:
        supplement.setdefault("moat_types", args.moat_types)

    phase1_overrides = dict(supplement)
    phase1_overrides.update(company_overrides)
    phase1_payload = extract_phase1_payload(workbook_path, overrides=phase1_overrides)
    if company_overrides:
        phase1_payload.setdefault("company", {})
        phase1_payload["company"].update(company_overrides)

    valuation_overrides = supplement.get("valuation", {})
    if args.current_price is not None:
        valuation_overrides = {**valuation_overrides, "current_price": args.current_price}
    phase2_payload = extract_phase2_payload(valuation_artifacts, overrides=valuation_overrides)

    combined = {
        "company": phase1_payload.get("company", {}),
        "model_summary": phase1_payload.get("model_summary", {}),
        "valuation": phase2_payload,
        "quality_inputs": phase1_payload.get("quality_inputs", {}),
        "monitoring_inputs": phase1_payload.get("monitoring_inputs", {}),
        "artifact_paths": {
            "phase1_workbook": str(workbook_path),
            "phase2": valuation_artifacts,
        },
    }
    if supplement:
        deep_update(combined, supplement)

    result = build_memo_pack(combined)
    result["artifact_paths"] = combined["artifact_paths"]
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
