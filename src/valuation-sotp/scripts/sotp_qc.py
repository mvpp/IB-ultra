#!/usr/bin/env python3
import argparse

from sotp_common import dump_json, get_num, load_json


def add_check(failures, warnings, condition, message, severity="fail"):
    if condition:
        return
    if severity == "warn":
        warnings.append(message)
    else:
        failures.append(message)


def main():
    parser = argparse.ArgumentParser(description="Run deterministic QC checks for SOTP valuation outputs.")
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="sotp_qc.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    normalized = payload.get("segment_normalizer", {})
    router = payload.get("segment_method_router", {})
    primary = payload.get("primary_method", {})
    summary = payload.get("target_summary", {})
    limits = payload.get("limits", {})

    failures = []
    warnings = []
    segments = normalized.get("segments", [])
    routes = {row.get("name"): row for row in router.get("segment_method_map", [])}

    add_check(failures, warnings, len(segments) >= 2, "SOTP should have at least two segments.")
    add_check(
        failures,
        warnings,
        get_num(normalized.get("share_bridge", {}), "diluted_shares") > 0,
        "Diluted shares must be positive and explicit.",
    )

    seen = set()
    for segment in segments:
        name = str(segment.get("name")).strip().lower()
        duplicate = name in seen
        seen.add(name)
        add_check(failures, warnings, not duplicate, f"Duplicate segment name detected: {segment.get('name')}.")
        ownership = float(segment.get("ownership_pct", 0.0) or 0.0)
        add_check(
            failures,
            warnings,
            0.0 < ownership <= 1.0,
            f"Ownership percentage must be between 0 and 1 for {segment.get('name')}.",
        )
        route = routes.get(segment.get("name"))
        add_check(
            failures,
            warnings,
            route is not None,
            f"Missing routed method for segment {segment.get('name')}.",
        )
        if not route:
            continue
        method = route.get("method")
        metric_value = route.get("metric_value")
        if method in {"ev_ebitda", "ev_ebit", "ev_sales", "pe", "pb"}:
            add_check(
                failures,
                warnings,
                metric_value not in (None, 0, 0.0),
                f"Segment {segment.get('name')} is missing a usable metric for {method}.",
            )
            add_check(
                failures,
                warnings,
                route.get("selected_multiple") not in (None, 0, 0.0),
                f"Segment {segment.get('name')} is missing a selected multiple for {method}.",
            )
        else:
            add_check(
                failures,
                warnings,
                any(
                    value not in (None, 0, 0.0)
                    for value in [
                        segment.get("direct_equity_value"),
                        segment.get("asset_nav"),
                        segment.get("direct_enterprise_value"),
                    ]
                ),
                f"Segment {segment.get('name')} needs an explicit direct value input for {method}.",
            )

    for key, row in normalized.get("tie_out", {}).items():
        gap_pct = row.get("gap_pct")
        if gap_pct is None:
            continue
        add_check(
            failures,
            warnings,
            abs(float(gap_pct)) <= float(limits.get("max_tie_out_gap_pct", 0.1)),
            f"Segment total does not tie closely to consolidated {key}.",
            severity="warn",
        )

    holdco_rate = primary.get("holdco_discount_rate")
    if holdco_rate is not None:
        add_check(
            failures,
            warnings,
            0.0 <= float(holdco_rate) <= float(limits.get("max_holdco_discount_rate", 0.35)),
            "Holdco discount rate is outside the configured sane range.",
            severity="warn",
        )

    low = primary.get("value_per_share_low") or primary.get("implied_value_per_share_low")
    mid = primary.get("value_per_share") or primary.get("implied_value_per_share")
    high = primary.get("value_per_share_high") or primary.get("implied_value_per_share_high")
    if None not in (low, mid, high):
        add_check(
            failures,
            warnings,
            float(low) <= float(mid) <= float(high),
            "Primary SOTP range should be monotonic.",
        )

    add_check(
        failures,
        warnings,
        summary.get("weighted_target_price") is not None and summary.get("weighted_target_price") > 0,
        "Target summary is missing a positive weighted target price.",
    )

    result = {
        "passed": not failures,
        "failures": failures,
        "warnings": warnings,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
