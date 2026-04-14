#!/usr/bin/env python3
import argparse

from financials_common import dump_json, get_num, load_json


def add_check(failures, warnings, condition, message, severity="fail"):
    if condition:
        return
    if severity == "warn":
        warnings.append(message)
    else:
        failures.append(message)


def main():
    parser = argparse.ArgumentParser(
        description="Run deterministic QC checks across financial-sector valuation outputs."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="financials_qc.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    prep = payload.get("financials_prep", {})
    primary = payload.get("primary_method", {})
    secondary = payload.get("secondary_method", {})
    tertiary = payload.get("tertiary_method", {})
    summary = payload.get("target_summary", {})
    limits = payload.get("limits", {})

    failures = []
    warnings = []

    diluted_shares = get_num(prep.get("share_bridge", {}), "diluted_shares")
    add_check(failures, warnings, diluted_shares > 0, "Diluted shares must be positive and explicit.")

    tangible_bvps = prep.get("book_bridge", {}).get("tangible_book_value_per_share")
    reported_bvps = prep.get("book_bridge", {}).get("book_value_per_share")
    add_check(
        failures,
        warnings,
        (tangible_bvps is not None and tangible_bvps > 0) or (reported_bvps is not None and reported_bvps > 0),
        "Need positive reported or tangible book value per share.",
    )

    regulatory_minimum = prep.get("capital", {}).get("regulatory_minimum")
    reported_capital_ratio = prep.get("capital", {}).get("reported_capital_ratio")
    if regulatory_minimum is not None and reported_capital_ratio is not None:
        add_check(
            failures,
            warnings,
            float(reported_capital_ratio) >= float(regulatory_minimum),
            "Reported capital ratio is below the regulatory minimum.",
        )

    normalized_roe = prep.get("earnings", {}).get("normalized_roe")
    max_roe = float(limits.get("max_normalized_roe", 0.30))
    if normalized_roe is not None:
        add_check(
            failures,
            warnings,
            0.0 <= float(normalized_roe) <= max_roe,
            "Normalized ROE is outside the configured sanity range.",
            severity="warn",
        )

    for label, method in [("primary", primary), ("secondary", secondary)]:
        if not method:
            add_check(failures, warnings, False, f"Missing {label} method output.")
            continue
        growth_rate = (
            method.get("growth_rate")
            if method.get("growth_rate") is not None
            else method.get("terminal_growth_rate")
        )
        if method.get("cost_of_equity") is not None and growth_rate is not None:
            add_check(
                failures,
                warnings,
                float(method["cost_of_equity"]) > float(growth_rate),
                f"{label.title()} method requires cost of equity greater than growth rate.",
            )
        if method.get("selected_multiple") is not None:
            add_check(
                failures,
                warnings,
                float(method["selected_multiple"]) > 0,
                f"{label.title()} selected multiple must be positive.",
            )

    if tertiary:
        embedded_value_total = tertiary.get("embedded_value_total")
        component_sum = (
            get_num(tertiary, "adjusted_net_worth")
            + get_num(tertiary, "value_in_force")
            + get_num(tertiary, "franchise_value")
            + get_num(tertiary, "holding_company_adjustment")
            - get_num(tertiary, "required_capital_friction")
        )
        add_check(
            failures,
            warnings,
            abs(float(embedded_value_total) - component_sum) <= 1e-6,
            "Embedded value output does not reconcile to its component parts.",
        )

    if primary and secondary:
        primary_value = primary.get("implied_value_per_share")
        secondary_value = secondary.get("implied_value_per_share")
        if primary_value is not None and secondary_value is not None:
            spread = abs(float(primary_value) - float(secondary_value))
            midpoint = (float(primary_value) + float(secondary_value)) / 2.0
            add_check(
                failures,
                warnings,
                midpoint > 0 and spread / midpoint <= float(limits.get("method_spread_warn", 0.35)),
                "Primary and secondary methods diverge materially.",
                severity="warn",
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
