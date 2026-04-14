#!/usr/bin/env python3
import argparse

from asset_nav_common import dump_json, get_num, load_json, safe_div


def recompute_asset_value(asset, price_multiplier=1.0):
    discount_rate = float(asset.get("discount_rate", 0.10) or 0.10)
    tax_rate = float(asset.get("tax_rate", 0.25) or 0.25)
    total = 0.0
    for row in asset.get("forecast", []):
        revenue = float(row.get("revenue", 0.0)) * price_multiplier
        royalty_cost = revenue * safe_div(float(row.get("royalty_cost", 0.0)), float(row.get("revenue", 0.0)), 0.0)
        operating_cost = float(row.get("operating_cost", 0.0))
        sustaining_capex = float(row.get("sustaining_capex", 0.0))
        development_capex = float(row.get("development_capex", 0.0))
        pretax_cash_flow = revenue - royalty_cost - operating_cost - sustaining_capex - development_capex
        tax = max(pretax_cash_flow, 0.0) * tax_rate
        after_tax_cash_flow = pretax_cash_flow - tax
        discount_factor = (1.0 + discount_rate) ** int(row.get("year", 1))
        total += after_tax_cash_flow / discount_factor
    if not asset.get("forecast"):
        total = float(asset.get("asset_npv", 0.0))
    return total


def main():
    parser = argparse.ArgumentParser(description="Stress asset NAV under commodity price scenarios.")
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="commodity_sensitivity.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    reserve_model = payload.get("reserve_model", {})
    asset_nav_output = payload.get("asset_nav_output", {})
    method = payload.get("commodity_sensitivity", payload.get("method", {}))
    summary = reserve_model.get("summary", {})
    balance_sheet = reserve_model.get("balance_sheet_bridge", {})
    share_bridge = reserve_model.get("share_bridge", {})

    scenarios = method.get(
        "scenarios",
        [
            {"label": "Bear", "price_multiplier": 0.85},
            {"label": "Base", "price_multiplier": 1.00},
            {"label": "Bull", "price_multiplier": 1.15},
        ],
    )
    asset_value = get_num(summary, "total_asset_npv")
    base_adjustment = get_num(asset_nav_output, "equity_value") - get_num(asset_nav_output, "adjusted_asset_value")
    risk_haircut = get_num(asset_nav_output, "risk_haircut")
    exploration_value = get_num(asset_nav_output, "exploration_value")
    undeveloped_resource_value = get_num(asset_nav_output, "undeveloped_resource_value")
    corporate_overhead_npv = get_num(asset_nav_output, "corporate_overhead_npv")
    diluted_shares = get_num(share_bridge, "diluted_shares")

    rows = []
    for scenario in scenarios:
        multiplier = float(scenario.get("price_multiplier", 1.0))
        scenario_asset_value = 0.0
        for asset in reserve_model.get("assets", []):
            scenario_asset_value += recompute_asset_value(asset, price_multiplier=multiplier)
        scenario_adjusted_asset_value = (
            scenario_asset_value * (1.0 - risk_haircut)
            + exploration_value
            + undeveloped_resource_value
            - corporate_overhead_npv
        )
        equity_value = scenario_adjusted_asset_value + base_adjustment
        rows.append(
            {
                "label": scenario.get("label"),
                "price_multiplier": multiplier,
                "asset_value": scenario_asset_value,
                "adjusted_asset_value": scenario_adjusted_asset_value,
                "equity_value": equity_value,
                "value_per_share": safe_div(equity_value, diluted_shares, 0.0),
            }
        )

    result = {
        "base_asset_value": asset_value,
        "scenarios": rows,
        "balance_sheet_context": {
            "cash": get_num(balance_sheet, "cash"),
            "debt": get_num(balance_sheet, "debt"),
            "hedging_value": get_num(balance_sheet, "hedging_value"),
        },
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
