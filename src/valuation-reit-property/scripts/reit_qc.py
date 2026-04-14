#!/usr/bin/env python3
import argparse

from reit_common import dump_json, get_num, load_json


def add_check(failures, warnings, condition, message, severity="fail"):
    if condition:
        return
    if severity == "warn":
        warnings.append(message)
    else:
        failures.append(message)


def main():
    parser = argparse.ArgumentParser(
        description="Run deterministic QC checks across REIT/property valuation outputs."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="reit_qc.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    prep = payload.get("property_bridge", {})
    primary = payload.get("primary_method", {})
    secondary = payload.get("secondary_method", {})
    summary = payload.get("target_summary", {})
    limits = payload.get("limits", {})

    failures = []
    warnings = []

    property_rollup = prep.get("property_rollup", {})
    balance_sheet = prep.get("balance_sheet_bridge", {})
    earnings = prep.get("earnings_bridge", {})

    add_check(
        failures,
        warnings,
        get_num(property_rollup, "property_count") > 0,
        "Need at least one property or asset entry in the property bridge.",
    )
    add_check(
        failures,
        warnings,
        get_num(property_rollup, "gross_asset_value") > 0,
        "Gross asset value must be positive.",
    )

    weighted_occupancy = property_rollup.get("weighted_occupancy")
    if weighted_occupancy is not None:
        add_check(
            failures,
            warnings,
            0.0 <= float(weighted_occupancy) <= 1.0,
            "Weighted occupancy must be between 0% and 100%.",
        )

    affo_per_share = earnings.get("affo_per_share")
    if affo_per_share is not None:
        add_check(
            failures,
            warnings,
            float(affo_per_share) > 0,
            "AFFO per share should be positive for a stabilized REIT case.",
            severity="warn",
        )

    liquidity_sources = get_num(balance_sheet, "liquidity_sources")
    debt_maturities = get_num(balance_sheet, "debt_maturities_next_24m")
    if debt_maturities > 0:
        max_refi_multiple = float(limits.get("max_near_term_maturity_to_liquidity", 1.25))
        add_check(
            failures,
            warnings,
            liquidity_sources > 0 and debt_maturities / liquidity_sources <= max_refi_multiple,
            "Near-term debt maturities look high relative to available liquidity.",
            severity="warn",
        )

    nav_per_share = primary.get("nav_per_share") if primary.get("method_family") == "reit_nav" else None
    add_check(
        failures,
        warnings,
        nav_per_share is not None and float(nav_per_share) > 0,
        "Primary NAV method should produce a positive NAV per share.",
    )

    sensitivity = primary.get("sensitivity", []) if primary else []
    if sensitivity:
        ordered = sorted(sensitivity, key=lambda row: row["cap_rate_shift_bps"])
        nav_values = [row.get("nav_per_share") for row in ordered]
        monotonic = all(
            nav_values[idx] >= nav_values[idx + 1]
            for idx in range(len(nav_values) - 1)
            if None not in (nav_values[idx], nav_values[idx + 1])
        )
        add_check(
            failures,
            warnings,
            monotonic,
            "NAV sensitivity should fall as cap rates move higher.",
        )

    for row in prep.get("properties", []):
        cap_rate = row.get("cap_rate")
        status = str(row.get("status", "stabilized")).strip().lower()
        if cap_rate is not None and status not in {"development", "pipeline", "under_construction", "redevelopment"}:
            add_check(
                failures,
                warnings,
                0.02 <= float(cap_rate) <= float(limits.get("max_cap_rate", 0.15)),
                f"Cap rate for {row.get('name') or 'property'} is outside the expected sanity range.",
                severity="warn",
            )

    development_share = (
        get_num(property_rollup, "development_value") / get_num(property_rollup, "gross_asset_value")
        if get_num(property_rollup, "gross_asset_value") > 0
        else None
    )
    if development_share is not None:
        add_check(
            failures,
            warnings,
            development_share <= float(limits.get("max_development_share_warn", 0.35)),
            "Development assets are a large share of gross asset value.",
            severity="warn",
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
                midpoint > 0 and spread / midpoint <= float(limits.get("method_spread_warn", 0.30)),
                "Primary NAV and secondary AFFO methods diverge materially.",
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
