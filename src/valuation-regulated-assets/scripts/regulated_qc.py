#!/usr/bin/env python3
import argparse

from regulated_common import dump_json, get_num, load_json


def add_check(failures, warnings, condition, message, severity="fail"):
    if condition:
        return
    if severity == "warn":
        warnings.append(message)
    else:
        failures.append(message)


def main():
    parser = argparse.ArgumentParser(
        description="Run deterministic QC checks across regulated-assets valuation outputs."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="regulated_qc.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    bridge = payload.get("regulatory_bridge", {})
    primary = payload.get("primary_method", {})
    secondary = payload.get("secondary_method", {})
    summary = payload.get("target_summary", {})
    limits = payload.get("limits", {})

    failures = []
    warnings = []

    rollforward = bridge.get("regulatory_rollforward", {})
    returns_bridge = bridge.get("returns_bridge", {})
    earnings_bridge = bridge.get("earnings_bridge", {})
    share_bridge = bridge.get("share_bridge", {})

    diluted_shares = get_num(share_bridge, "diluted_shares")
    add_check(failures, warnings, diluted_shares > 0, "Diluted shares must be positive and explicit.")

    closing_rate_base = get_num(rollforward, "closing_rate_base")
    add_check(failures, warnings, closing_rate_base > 0, "Closing rate base must be positive.")

    derived_closing_rate_base = get_num(rollforward, "derived_closing_rate_base")
    if derived_closing_rate_base > 0:
        add_check(
            failures,
            warnings,
            abs(closing_rate_base - derived_closing_rate_base) / derived_closing_rate_base <= 0.10,
            "Reported and derived closing rate base diverge materially.",
            severity="warn",
        )

    equity_ratio = get_num(returns_bridge, "equity_ratio")
    debt_ratio = get_num(returns_bridge, "debt_ratio")
    add_check(
        failures,
        warnings,
        0.0 < equity_ratio < 1.0,
        "Authorized equity ratio must be between 0 and 1.",
    )
    add_check(
        failures,
        warnings,
        0.0 < debt_ratio < 1.0,
        "Authorized debt ratio must be between 0 and 1.",
    )
    add_check(
        failures,
        warnings,
        abs((equity_ratio + debt_ratio) - 1.0) <= float(limits.get("capital_structure_tolerance", 0.10)),
        "Equity ratio plus debt ratio should approximately sum to 1.0.",
        severity="warn",
    )

    allowed_roe = get_num(returns_bridge, "allowed_roe")
    add_check(
        failures,
        warnings,
        allowed_roe > 0,
        "Allowed ROE must be positive and explicit.",
    )
    add_check(
        failures,
        warnings,
        allowed_roe <= float(limits.get("max_allowed_roe", 0.18)),
        "Allowed ROE is outside the configured sanity range.",
        severity="warn",
    )

    allowed_wacc = get_num(returns_bridge, "allowed_wacc")
    add_check(failures, warnings, allowed_wacc > 0, "Allowed WACC must be positive.", severity="warn")

    payout_ratio = earnings_bridge.get("payout_ratio")
    if payout_ratio is not None:
        add_check(
            failures,
            warnings,
            0.0 <= float(payout_ratio) <= float(limits.get("max_payout_ratio", 1.10)),
            "Payout ratio is outside the configured sanity range.",
            severity="warn",
        )

    dividend_coverage = earnings_bridge.get("dividend_coverage")
    if dividend_coverage is not None:
        add_check(
            failures,
            warnings,
            float(dividend_coverage) >= float(limits.get("min_dividend_coverage", 1.00)),
            "Dividend coverage is below the configured minimum.",
            severity="warn",
        )

    regulatory_lag_months = returns_bridge.get("regulatory_lag_months")
    if regulatory_lag_months is not None:
        add_check(
            failures,
            warnings,
            float(regulatory_lag_months) <= float(limits.get("max_regulatory_lag_months", 24.0)),
            "Regulatory lag is high enough to deserve explicit narrative treatment.",
            severity="warn",
        )

    rate_base_growth = rollforward.get("rate_base_growth")
    if rate_base_growth is not None:
        add_check(
            failures,
            warnings,
            float(rate_base_growth) >= float(limits.get("min_rate_base_growth", -0.10)),
            "Rate-base shrinkage is material and should be explained explicitly.",
            severity="warn",
        )
        add_check(
            failures,
            warnings,
            float(rate_base_growth) <= float(limits.get("max_rate_base_growth", 0.15)),
            "Rate-base growth is above the configured sanity range.",
            severity="warn",
        )

    for label, method in [("primary", primary), ("secondary", secondary)]:
        if not method:
            add_check(failures, warnings, False, f"Missing {label} method output.")
            continue
        growth_rate = (
            method.get("terminal_growth_rate")
            if method.get("terminal_growth_rate") is not None
            else method.get("dividend_growth_rate")
        )
        if method.get("cost_of_equity") is not None and growth_rate is not None:
            add_check(
                failures,
                warnings,
                float(method["cost_of_equity"]) > float(growth_rate),
                f"{label.title()} method requires cost of equity greater than growth rate.",
            )
        if label == "primary" and method.get("selected_multiple") is not None:
            add_check(
                failures,
                warnings,
                float(method["selected_multiple"]) > 0,
                "Primary RAB multiple must be positive.",
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
