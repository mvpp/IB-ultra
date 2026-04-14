#!/usr/bin/env python3
import argparse

from asset_nav_common import dump_json, get_num, load_json, safe_div


def main():
    parser = argparse.ArgumentParser(
        description="Bridge asset-level NAV into equity value per share for reserve-driven businesses."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="asset_nav_output.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    reserve_model = payload.get("reserve_model", {})
    method = payload.get("asset_nav", payload.get("method", {}))
    summary = reserve_model.get("summary", {})
    balance_sheet = reserve_model.get("balance_sheet_bridge", {})
    share_bridge = reserve_model.get("share_bridge", {})
    market = payload.get("market", reserve_model.get("market", {}))

    asset_value = get_num(summary, "total_asset_npv")
    risk_haircut = float(method.get("risk_haircut", 0.0) or 0.0)
    exploration_value = get_num(method, "exploration_value")
    undeveloped_resource_value = get_num(method, "undeveloped_resource_value")
    corporate_overhead_npv = get_num(method, "corporate_overhead_npv")

    adjusted_asset_value = (
        asset_value * (1.0 - risk_haircut)
        + exploration_value
        + undeveloped_resource_value
        - corporate_overhead_npv
    )

    cash = get_num(balance_sheet, "cash")
    debt = get_num(balance_sheet, "debt")
    preferreds = get_num(balance_sheet, "preferred_equity")
    minorities = get_num(balance_sheet, "minority_interest")
    other_assets = get_num(balance_sheet, "other_assets")
    other_liabilities = get_num(balance_sheet, "other_liabilities")
    hedging_value = get_num(balance_sheet, "hedging_value")
    non_core_asset_value = get_num(balance_sheet, "non_core_asset_value")
    aro = get_num(balance_sheet, "asset_retirement_obligation")
    holding_company_adjustment = get_num(balance_sheet, "holding_company_adjustment")

    equity_value = (
        adjusted_asset_value
        + cash
        + hedging_value
        + other_assets
        + non_core_asset_value
        - debt
        - preferreds
        - minorities
        - other_liabilities
        - aro
        + holding_company_adjustment
    )
    diluted_shares = get_num(share_bridge, "diluted_shares")
    implied_value_per_share = safe_div(equity_value, diluted_shares, 0.0)
    current_price = market.get("current_price")

    result = {
        "label": method.get("label", "Asset NAV"),
        "asset_value": asset_value,
        "risk_haircut": risk_haircut,
        "adjusted_asset_value": adjusted_asset_value,
        "exploration_value": exploration_value,
        "undeveloped_resource_value": undeveloped_resource_value,
        "corporate_overhead_npv": corporate_overhead_npv,
        "cash": cash,
        "debt": debt,
        "preferred_equity": preferreds,
        "minority_interest": minorities,
        "other_assets": other_assets,
        "other_liabilities": other_liabilities,
        "hedging_value": hedging_value,
        "non_core_asset_value": non_core_asset_value,
        "asset_retirement_obligation": aro,
        "holding_company_adjustment": holding_company_adjustment,
        "equity_value": equity_value,
        "implied_value_per_share": implied_value_per_share,
        "upside_pct": (
            safe_div(implied_value_per_share - current_price, current_price)
            if current_price not in (None, 0, 0.0)
            else None
        ),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
