#!/usr/bin/env python3
import argparse

from reit_common import dump_json, get_num, load_json, safe_div


DEVELOPMENT_STATUSES = {"development", "pipeline", "under_construction", "redevelopment"}


def nav_for_shift(prep, method, shift_bps):
    cap_rate_overrides = method.get("cap_rate_overrides", {})
    default_cap_rate = method.get("default_cap_rate")
    development_haircut = float(method.get("development_haircut_pct", 0.0))
    platform_value = get_num(method, "platform_value")
    asset_value_total = 0.0

    for row in prep.get("properties", []):
        status = str(row.get("status", "stabilized")).strip().lower()
        ownership_pct = float(row.get("ownership_pct", 1.0))
        if status in DEVELOPMENT_STATUSES:
            asset_value_total += float(row.get("owned_market_value") or 0.0) * (1.0 - development_haircut)
            continue

        property_type = str(row.get("type", "default"))
        selected_cap_rate = cap_rate_overrides.get(property_type)
        if selected_cap_rate is None:
            selected_cap_rate = row.get("cap_rate", default_cap_rate)
        if selected_cap_rate in (None, 0, 0.0):
            asset_value_total += float(row.get("owned_market_value") or 0.0)
            continue

        shifted_cap_rate = float(selected_cap_rate) + (shift_bps / 10000.0)
        if shifted_cap_rate <= 0:
            return None
        stabilized_noi = float(row.get("stabilized_noi") or row.get("annual_noi") or 0.0)
        asset_value_total += (stabilized_noi * ownership_pct) / shifted_cap_rate

    property_rollup = prep.get("property_rollup", {})
    balance_sheet = prep.get("balance_sheet_bridge", {})
    nav_total = (
        asset_value_total
        + get_num(property_rollup, "jv_value")
        + get_num(property_rollup, "other_real_estate_value")
        + get_num(balance_sheet, "available_cash")
        + get_num(balance_sheet, "other_assets")
        + platform_value
        - get_num(balance_sheet, "debt")
        - get_num(balance_sheet, "preferred_equity")
        - get_num(balance_sheet, "minority_interest")
        - get_num(balance_sheet, "other_liabilities")
        - get_num(method, "holding_company_adjustment")
    )
    return {
        "gross_property_value": asset_value_total + get_num(property_rollup, "jv_value") + get_num(property_rollup, "other_real_estate_value"),
        "nav_total": nav_total,
        "platform_value": platform_value,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Value a REIT or property company using property NAV with cap-rate sensitivity."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="nav_output.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    prep = payload.get("property_bridge", payload)
    method = payload.get("reit_nav", payload.get("method", {}))

    share_bridge = prep.get("share_bridge", {})
    market = prep.get("market", {})
    diluted_shares = share_bridge.get("diluted_shares")

    base_shift = int(method.get("cap_rate_shift_bps", 0))
    base_case = nav_for_shift(prep, method, base_shift)
    nav_per_share = (
        safe_div(base_case["nav_total"], diluted_shares)
        if base_case is not None and diluted_shares not in (None, 0, 0.0)
        else None
    )

    sensitivity_rows = []
    for shift in method.get("sensitivity_bps", [-100, -50, 0, 50, 100]):
        case = nav_for_shift(prep, method, int(shift))
        if case is None:
            continue
        sensitivity_rows.append(
            {
                "cap_rate_shift_bps": int(shift),
                "nav_total": case["nav_total"],
                "nav_per_share": safe_div(case["nav_total"], diluted_shares),
            }
        )

    result = {
        "label": "NAV",
        "method_family": "reit_nav",
        "gross_property_value": None if base_case is None else base_case["gross_property_value"],
        "platform_value": None if base_case is None else base_case["platform_value"],
        "nav_total": None if base_case is None else base_case["nav_total"],
        "nav_per_share": nav_per_share,
        "implied_value_per_share": nav_per_share,
        "implied_equity_value": None if base_case is None else base_case["nav_total"],
        "current_price": market.get("current_price"),
        "premium_discount_to_nav": (
            safe_div(market.get("current_price") - nav_per_share, nav_per_share)
            if nav_per_share not in (None, 0, 0.0) and market.get("current_price") is not None
            else None
        ),
        "cap_rate_shift_bps": base_shift,
        "development_haircut_pct": float(method.get("development_haircut_pct", 0.0)),
        "sensitivity": sensitivity_rows,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
