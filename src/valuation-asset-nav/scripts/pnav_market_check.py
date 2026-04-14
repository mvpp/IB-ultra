#!/usr/bin/env python3
import argparse

from asset_nav_common import dump_json, get_num, load_json, safe_div


def average(values):
    values = [float(value) for value in values if value is not None]
    return sum(values) / len(values) if values else None


def main():
    parser = argparse.ArgumentParser(
        description="Apply a P/NAV market check to an underwritten asset NAV."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="pnav_market_check.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    asset_nav_output = payload.get("asset_nav_output", {})
    reserve_model = payload.get("reserve_model", {})
    method = payload.get("pnav_market_check", payload.get("method", {}))
    market = payload.get("market", reserve_model.get("market", {}))
    share_bridge = reserve_model.get("share_bridge", {})

    diluted_shares = get_num(share_bridge, "diluted_shares")
    nav_equity_value = get_num(asset_nav_output, "equity_value")
    nav_per_share = safe_div(nav_equity_value, diluted_shares, 0.0)
    current_price = market.get("current_price")
    current_market_cap = (
        float(current_price) * diluted_shares if current_price not in (None, 0, 0.0) and diluted_shares else None
    )
    current_pnav = (
        safe_div(current_market_cap, nav_equity_value)
        if current_market_cap not in (None, 0, 0.0) and nav_equity_value not in (None, 0, 0.0)
        else None
    )

    selected_multiple = method.get("selected_pnav")
    if selected_multiple is None:
        selected_multiple = average(
            [
                method.get("peer_pnav"),
                method.get("historical_pnav"),
                current_pnav if method.get("include_current_pnav_in_average", False) else None,
            ]
        )
    if selected_multiple is None:
        selected_multiple = current_pnav if current_pnav is not None else 1.0
    selected_multiple = float(selected_multiple)

    implied_equity_value = nav_equity_value * selected_multiple
    implied_value_per_share = nav_per_share * selected_multiple

    result = {
        "label": method.get("label", "P/NAV Market Check"),
        "nav_equity_value": nav_equity_value,
        "nav_per_share": nav_per_share,
        "current_price": current_price,
        "current_market_cap": current_market_cap,
        "current_pnav": current_pnav,
        "peer_pnav": None if method.get("peer_pnav") is None else float(method["peer_pnav"]),
        "historical_pnav": None if method.get("historical_pnav") is None else float(method["historical_pnav"]),
        "selected_pnav": selected_multiple,
        "implied_equity_value": implied_equity_value,
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
