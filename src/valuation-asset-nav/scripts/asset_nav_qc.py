#!/usr/bin/env python3
import argparse

from asset_nav_common import dump_json, get_num, load_json


def add_check(failures, warnings, condition, message, severity="fail"):
    if condition:
        return
    if severity == "warn":
        warnings.append(message)
    else:
        failures.append(message)


def main():
    parser = argparse.ArgumentParser(
        description="Run deterministic QC checks across asset-NAV valuation outputs."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="asset_nav_qc.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    reserve_model = payload.get("reserve_model", {})
    primary = payload.get("primary_method", {})
    secondary = payload.get("secondary_method", {})
    commodity_sensitivity = payload.get("commodity_sensitivity", {})
    summary = payload.get("target_summary", {})
    limits = payload.get("limits", {})

    failures = []
    warnings = []

    reserve_summary = reserve_model.get("summary", {})
    balance_sheet = reserve_model.get("balance_sheet_bridge", {})
    share_bridge = reserve_model.get("share_bridge", {})

    diluted_shares = get_num(share_bridge, "diluted_shares")
    add_check(failures, warnings, diluted_shares > 0, "Diluted shares must be positive and explicit.")

    asset_count = int(reserve_summary.get("asset_count", 0) or 0)
    add_check(failures, warnings, asset_count > 0, "Need at least one asset in the reserve model.")

    total_reserves = get_num(reserve_summary, "total_reserves_units")
    total_asset_npv = get_num(reserve_summary, "total_asset_npv")
    add_check(failures, warnings, total_asset_npv > 0, "Total asset NPV must be positive.")

    reserve_life = reserve_summary.get("weighted_reserve_life_years")
    if reserve_life is not None:
        add_check(
            failures,
            warnings,
            float(reserve_life) > 0,
            "Weighted reserve life must be positive.",
        )
        add_check(
            failures,
            warnings,
            float(reserve_life) <= float(limits.get("max_reserve_life_years", 40.0)),
            "Weighted reserve life is outside the configured sanity range.",
            severity="warn",
        )

    for asset in reserve_model.get("assets", []):
        if asset.get("forecast"):
            sustaining_pv = get_num(asset, "sustaining_capex_pv")
            if str(asset.get("asset_type", "")).lower() not in {"royalty", "streaming"}:
                add_check(
                    failures,
                    warnings,
                    sustaining_pv >= 0,
                    f"Sustaining capex PV should be explicit for asset {asset.get('name')}.",
                    severity="warn",
                )
            add_check(
                failures,
                warnings,
                get_num(asset, "asset_npv") > -float(limits.get("max_negative_asset_npv", 1e12)),
                f"Asset {asset.get('name')} has an implausible NPV.",
                severity="warn",
            )

    equity_value = get_num(primary, "equity_value")
    bridge_recomputed = (
        get_num(primary, "adjusted_asset_value")
        + get_num(primary, "cash")
        + get_num(primary, "hedging_value")
        + get_num(primary, "other_assets")
        + get_num(primary, "non_core_asset_value")
        - get_num(primary, "debt")
        - get_num(primary, "preferred_equity")
        - get_num(primary, "minority_interest")
        - get_num(primary, "other_liabilities")
        - get_num(primary, "asset_retirement_obligation")
        + get_num(primary, "holding_company_adjustment")
    )
    if equity_value:
        add_check(
            failures,
            warnings,
            abs(equity_value - bridge_recomputed) <= 1e-6,
            "Asset NAV output does not reconcile through the equity bridge.",
        )

    scenarios = commodity_sensitivity.get("scenarios", [])
    if scenarios:
        ordered = sorted(scenarios, key=lambda row: float(row.get("price_multiplier", 1.0)))
        monotonic = all(
            float(ordered[index]["value_per_share"]) <= float(ordered[index + 1]["value_per_share"])
            for index in range(len(ordered) - 1)
        )
        add_check(
            failures,
            warnings,
            monotonic,
            "Commodity sensitivity should be monotonic with higher price multipliers.",
        )

    current_pnav = secondary.get("current_pnav")
    if current_pnav is not None:
        add_check(
            failures,
            warnings,
            float(current_pnav) > 0,
            "Current P/NAV must be positive when provided.",
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
                midpoint > 0 and spread / midpoint <= float(limits.get("method_spread_warn", 0.40)),
                "Primary and secondary methods diverge materially.",
                severity="warn",
            )

    add_check(
        failures,
        warnings,
        summary.get("weighted_target_price") is not None and summary.get("weighted_target_price") > 0,
        "Target summary is missing a positive weighted target price.",
    )

    add_check(
        failures,
        warnings,
        total_reserves > 0 or reserve_summary.get("year1_production", 0) > 0,
        "Need positive reserve inventory or production visibility.",
    )

    add_check(
        failures,
        warnings,
        get_num(balance_sheet, "debt") >= 0,
        "Debt should not be negative.",
        severity="warn",
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
