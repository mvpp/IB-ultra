#!/usr/bin/env python3
import argparse

from reit_common import dump_json, get_num, load_json, safe_div


def main():
    parser = argparse.ArgumentParser(
        description="Value a REIT or property company using AFFO per share and a selected market multiple."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="affo_output.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    prep = payload.get("property_bridge", payload)
    method = payload.get("affo_valuation", payload.get("method", {}))

    earnings = prep.get("earnings_bridge", {})
    balance_sheet = prep.get("balance_sheet_bridge", {})
    market = prep.get("market", {})

    affo_per_share = (
        method.get("affo_per_share")
        if method.get("affo_per_share") is not None
        else earnings.get("affo_per_share")
    )
    explicit_multiple = method.get("selected_multiple")
    peer_multiple = method.get("peer_selected_multiple")
    historical_multiple = method.get("historical_mean_multiple")
    peer_weight = float(method.get("peer_weight", 0.7))

    if explicit_multiple is not None:
        selected_multiple = float(explicit_multiple)
        multiple_source = "explicit"
    elif peer_multiple is not None and historical_multiple is not None:
        selected_multiple = float(peer_multiple) * peer_weight + float(historical_multiple) * (1.0 - peer_weight)
        multiple_source = "blend_peer_and_historical"
    elif peer_multiple is not None:
        selected_multiple = float(peer_multiple)
        multiple_source = "peer"
    elif historical_multiple is not None:
        selected_multiple = float(historical_multiple)
        multiple_source = "historical"
    else:
        selected_multiple = None
        multiple_source = None

    non_income_assets_per_share = (
        float(method["non_income_assets_per_share"])
        if method.get("non_income_assets_per_share") is not None
        else safe_div(get_num(balance_sheet, "other_assets"), prep.get("share_bridge", {}).get("diluted_shares"))
    )
    refi_penalty_per_share = float(method.get("refinance_penalty_per_share", 0.0))

    core_value_per_share = (
        float(affo_per_share) * selected_multiple
        if affo_per_share is not None and selected_multiple is not None
        else None
    )
    implied_value_per_share = (
        core_value_per_share + float(non_income_assets_per_share or 0.0) - refi_penalty_per_share
        if core_value_per_share is not None
        else None
    )
    diluted_shares = prep.get("share_bridge", {}).get("diluted_shares")
    implied_equity_value = (
        implied_value_per_share * float(diluted_shares)
        if implied_value_per_share is not None and diluted_shares is not None
        else None
    )

    result = {
        "label": "AFFO Multiple",
        "method_family": "reit_affo",
        "affo_per_share": affo_per_share,
        "selected_multiple": selected_multiple,
        "selected_multiple_source": multiple_source,
        "peer_selected_multiple": peer_multiple,
        "historical_mean_multiple": historical_multiple,
        "non_income_assets_per_share": non_income_assets_per_share,
        "refinance_penalty_per_share": refi_penalty_per_share,
        "core_value_per_share": core_value_per_share,
        "implied_value_per_share": implied_value_per_share,
        "implied_equity_value": implied_equity_value,
        "current_price": market.get("current_price"),
        "premium_discount_to_current": (
            safe_div(implied_value_per_share - market.get("current_price"), market.get("current_price"))
            if implied_value_per_share is not None and market.get("current_price") not in (None, 0, 0.0)
            else None
        ),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
