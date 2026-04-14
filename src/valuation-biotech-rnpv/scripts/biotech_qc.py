#!/usr/bin/env python3
import argparse

from biotech_common import dump_json, get_num, load_json


def add_check(failures, warnings, condition, message, severity="fail"):
    if condition:
        return
    if severity == "warn":
        warnings.append(message)
    else:
        failures.append(message)


def main():
    parser = argparse.ArgumentParser(description="Run deterministic QC checks across biotech valuation outputs.")
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="biotech_qc.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    registry = payload.get("pipeline_registry", {})
    primary = payload.get("primary_method", {})
    dilution = payload.get("cash_runway_dilution", {})
    scenarios = payload.get("launch_scenarios", {})
    summary = payload.get("target_summary", {})
    limits = payload.get("limits", {})

    failures = []
    warnings = []
    valuation_year = int(registry.get("valuation_year", 0) or 0)

    assets = registry.get("assets", [])
    add_check(failures, warnings, len(assets) > 0, "Need at least one pipeline asset.")
    add_check(
        failures,
        warnings,
        get_num(registry.get("share_bridge", {}), "diluted_shares") > 0,
        "Diluted shares must be positive and explicit.",
    )

    seen_names = set()
    for asset in assets:
        key = (str(asset.get("name")).strip().lower(), str(asset.get("indication")).strip().lower())
        duplicate = key in seen_names
        seen_names.add(key)
        add_check(
            failures,
            warnings,
            not duplicate,
            f"Possible duplicate asset / indication pair for {asset.get('name')}.",
            severity="warn",
        )

        probability = float(asset.get("probability_of_success", 0.0))
        add_check(
            failures,
            warnings,
            0.0 <= probability <= 1.0,
            f"Probability of success must be between 0 and 1 for {asset.get('name')}.",
        )

        if asset.get("stage") == "approved" or asset.get("approval_status") == "approved":
            add_check(
                failures,
                warnings,
                abs(probability - 1.0) <= 1e-6,
                f"Approved asset {asset.get('name')} should have probability of success equal to 1.0.",
                severity="warn",
            )

        flags = asset.get("source_flags", {})
        add_check(
            failures,
            warnings,
            bool(flags.get("has_company_source")),
            f"Asset {asset.get('name')} is missing company disclosure provenance.",
        )
        if asset.get("stage") != "approved":
            add_check(
                failures,
                warnings,
                bool(flags.get("has_trial_source") or flags.get("has_regulatory_source")),
                f"Pipeline asset {asset.get('name')} needs trial-registry or regulatory provenance.",
            )

        launch_year = asset.get("expected_launch_year")
        if launch_year is not None and asset.get("stage") != "approved":
            add_check(
                failures,
                warnings,
                int(launch_year) >= valuation_year,
                f"Expected launch year for {asset.get('name')} is earlier than the valuation year.",
                severity="warn",
            )

    runway_months = dilution.get("runway_months")
    if runway_months is not None:
        add_check(
            failures,
            warnings,
            float(runway_months) >= float(limits.get("min_runway_months_warn", 6.0)),
            "Cash runway is short relative to the configured warning threshold.",
            severity="warn",
        )

    dilution_pct = dilution.get("dilution_pct")
    if dilution_pct is not None:
        add_check(
            failures,
            warnings,
            float(dilution_pct) <= float(limits.get("max_dilution_warn", 0.35)),
            "Expected dilution is above the configured warning threshold.",
            severity="warn",
        )

    scenario_rows = scenarios.get("scenarios", [])
    by_name = {row.get("name"): row for row in scenario_rows}
    if {"bear", "base", "bull"}.issubset(set(by_name)):
        add_check(
            failures,
            warnings,
            float(by_name["bear"]["value_per_share"]) <= float(by_name["base"]["value_per_share"]) <= float(by_name["bull"]["value_per_share"]),
            "Bear / base / bull scenarios should be monotonic.",
        )

    add_check(
        failures,
        warnings,
        primary.get("equity_value") is not None and primary.get("implied_value_per_share") is not None,
        "Primary rNPV output is incomplete.",
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
