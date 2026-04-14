#!/usr/bin/env python3
import argparse
from pathlib import Path

from memo_common import dump_json, load_json, markdown_headings, number_strings


REQUIRED_HEADINGS = [
    "executive summary",
    "key forces",
    "business & earnings deep dive",
    "valuation summary",
    "variant view",
    "quality overlay",
    "risks & pre-mortem",
    "catalysts & monitoring",
    "decision framework",
    "evidence sources",
]


def add_check(failures, warnings, condition, message, severity="fail"):
    if condition:
        return
    if severity == "warn":
        warnings.append(message)
    else:
        failures.append(message)


def contains_any(text, values):
    return any(value in text for value in values)


def main():
    parser = argparse.ArgumentParser(
        description="Run deterministic QC checks on an investment memo draft."
    )
    parser.add_argument("--memo", required=True, help="Path to markdown memo")
    parser.add_argument("--memo-pack", required=True, help="Path to memo_input_pack JSON")
    parser.add_argument("--quality", required=True, help="Path to quality_overlay JSON")
    parser.add_argument("--decision", required=True, help="Path to decision_framework JSON")
    parser.add_argument("--monitoring", required=True, help="Path to monitoring_dashboard JSON")
    parser.add_argument("--output", default="memo_qc.json", help="Path to JSON output")
    args = parser.parse_args()

    memo_text = Path(args.memo).read_text(encoding="utf-8").lower()
    headings = markdown_headings(args.memo)
    memo_pack = load_json(args.memo_pack)
    quality = load_json(args.quality)
    decision = load_json(args.decision)
    monitoring = load_json(args.monitoring)

    failures = []
    warnings = []

    for heading in REQUIRED_HEADINGS:
        add_check(
            failures,
            warnings,
            heading in headings,
            f"Missing required heading: {heading}",
        )

    summary = memo_pack.get("summary", {})
    add_check(
        failures,
        warnings,
        summary.get("current_price") is not None and summary.get("current_price") > 0,
        "Current price is missing from the memo pack.",
    )
    add_check(
        failures,
        warnings,
        summary.get("weighted_target_price") is not None and summary.get("weighted_target_price") > 0,
        "Weighted target price is missing from the memo pack.",
    )
    add_check(
        failures,
        warnings,
        decision.get("zone") not in (None, "incomplete"),
        "Decision framework is incomplete.",
    )
    add_check(
        failures,
        warnings,
        quality.get("rating") is not None,
        "Quality overlay rating is missing.",
    )
    add_check(
        failures,
        warnings,
        monitoring.get("overall_status") is not None,
        "Monitoring dashboard is missing an overall status.",
    )

    add_check(
        failures,
        warnings,
        contains_any(memo_text, number_strings(summary.get("current_price"))),
        "Memo does not appear to mention the current price.",
        severity="warn",
    )
    add_check(
        failures,
        warnings,
        contains_any(memo_text, number_strings(summary.get("weighted_target_price"))),
        "Memo does not appear to mention the weighted target price.",
        severity="warn",
    )
    add_check(
        failures,
        warnings,
        quality.get("rating", "").lower() in memo_text,
        "Memo does not appear to mention the quality-overlay rating.",
        severity="warn",
    )

    result = {
        "passed": not failures,
        "failures": failures,
        "warnings": warnings,
        "headings_found": headings,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
