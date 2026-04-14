#!/usr/bin/env python3
import argparse

from regulated_common import dump_json, get_num, load_json, safe_div


def average(values):
    values = [float(value) for value in values if value is not None]
    return sum(values) / len(values) if values else None


def build_sensitivity(base_amount, adjustments, bridge, mode):
    results = []
    for item in adjustments:
        label = item.get("label")
        multiple = item.get("multiple")
        if multiple is None:
            continue
        regulated_value = base_amount * float(multiple)
        if mode == "enterprise_rab":
            implied_equity = (
                regulated_value
                + get_num(bridge["balance_sheet_bridge"], "cash")
                + get_num(bridge["balance_sheet_bridge"], "other_assets")
                + get_num(bridge["balance_sheet_bridge"], "non_regulated_value")
                - get_num(bridge["balance_sheet_bridge"], "total_debt")
                - get_num(bridge["balance_sheet_bridge"], "preferred_equity")
                - get_num(bridge["balance_sheet_bridge"], "minority_interest")
                - get_num(bridge["balance_sheet_bridge"], "other_liabilities")
                + get_num(bridge["balance_sheet_bridge"], "holding_company_adjustment")
            )
        else:
            implied_equity = (
                regulated_value
                + get_num(bridge["balance_sheet_bridge"], "non_regulated_value")
                + get_num(bridge["balance_sheet_bridge"], "excess_cash")
                + get_num(bridge["balance_sheet_bridge"], "other_assets")
                - get_num(bridge["balance_sheet_bridge"], "holdco_debt")
                - get_num(bridge["balance_sheet_bridge"], "preferred_equity")
                - get_num(bridge["balance_sheet_bridge"], "minority_interest")
                - get_num(bridge["balance_sheet_bridge"], "other_liabilities")
                + get_num(bridge["balance_sheet_bridge"], "holding_company_adjustment")
            )
        results.append(
            {
                "label": label or f"{multiple:.2f}x",
                "multiple": float(multiple),
                "equity_value": implied_equity,
                "value_per_share": safe_div(
                    implied_equity,
                    get_num(bridge["share_bridge"], "diluted_shares"),
                    0.0,
                ),
            }
        )
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Value a regulated-assets business using rate-base / regulatory-equity-base logic."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="rab_output.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    bridge = payload.get("regulatory_bridge", {})
    method = payload.get("rab_valuation", payload.get("method", {}))
    market = payload.get("market", bridge.get("market", {}))

    returns_bridge = bridge.get("returns_bridge", {})
    balance_sheet_bridge = bridge.get("balance_sheet_bridge", {})
    share_bridge = bridge.get("share_bridge", {})
    regulatory_rollforward = bridge.get("regulatory_rollforward", {})

    mode = method.get("mode", "equity_base")
    terminal_growth_rate = method.get("terminal_growth_rate")
    if terminal_growth_rate is None:
        terminal_growth_rate = regulatory_rollforward.get("rate_base_growth")
    if terminal_growth_rate is None:
        terminal_growth_rate = 0.02
    terminal_growth_rate = float(terminal_growth_rate)

    cost_of_equity = float(
        method.get("cost_of_equity")
        if method.get("cost_of_equity") is not None
        else market.get("cost_of_equity", 0.0)
    )
    allowed_roe = get_num(returns_bridge, "allowed_roe")
    justified_multiple = None
    if mode == "equity_base" and cost_of_equity > terminal_growth_rate:
        justified_multiple = safe_div(allowed_roe - terminal_growth_rate, cost_of_equity - terminal_growth_rate)
    elif mode == "enterprise_rab" and method.get("justified_multiple") is not None:
        justified_multiple = float(method["justified_multiple"])

    explicit_multiple = method.get("selected_multiple")
    peer_multiple = method.get("peer_multiple")
    historical_multiple = method.get("historical_multiple")
    selected_multiple = (
        float(explicit_multiple)
        if explicit_multiple is not None
        else average([peer_multiple, historical_multiple, justified_multiple])
    )
    if selected_multiple is None:
        selected_multiple = 1.0

    if mode == "enterprise_rab":
        base_label = "Closing rate base"
        base_amount = get_num(regulatory_rollforward, "closing_rate_base")
        regulated_value = base_amount * float(selected_multiple or 0.0)
        equity_value = (
            regulated_value
            + get_num(balance_sheet_bridge, "cash")
            + get_num(balance_sheet_bridge, "other_assets")
            + get_num(balance_sheet_bridge, "non_regulated_value")
            - get_num(balance_sheet_bridge, "total_debt")
            - get_num(balance_sheet_bridge, "preferred_equity")
            - get_num(balance_sheet_bridge, "minority_interest")
            - get_num(balance_sheet_bridge, "other_liabilities")
            + get_num(balance_sheet_bridge, "holding_company_adjustment")
        )
    else:
        base_label = "Regulatory equity base"
        base_amount = get_num(returns_bridge, "regulatory_equity_base")
        regulated_value = base_amount * float(selected_multiple or 0.0)
        equity_value = (
            regulated_value
            + get_num(balance_sheet_bridge, "non_regulated_value")
            + get_num(balance_sheet_bridge, "excess_cash")
            + get_num(balance_sheet_bridge, "other_assets")
            - get_num(balance_sheet_bridge, "holdco_debt")
            - get_num(balance_sheet_bridge, "preferred_equity")
            - get_num(balance_sheet_bridge, "minority_interest")
            - get_num(balance_sheet_bridge, "other_liabilities")
            + get_num(balance_sheet_bridge, "holding_company_adjustment")
        )

    diluted_shares = get_num(share_bridge, "diluted_shares")
    implied_value_per_share = safe_div(equity_value, diluted_shares, 0.0)
    current_price = market.get("current_price")

    sensitivity = build_sensitivity(
        base_amount,
        method.get(
            "multiple_sensitivity",
            [
                {"label": "Bear", "multiple": (selected_multiple or 0.0) * 0.90},
                {"label": "Base", "multiple": selected_multiple or 0.0},
                {"label": "Bull", "multiple": (selected_multiple or 0.0) * 1.10},
            ],
        ),
        bridge,
        mode,
    )

    result = {
        "label": method.get("label", "RAB / Rate Base"),
        "mode": mode,
        "base_metric": base_label,
        "base_amount": base_amount,
        "selected_multiple": selected_multiple,
        "peer_multiple": None if peer_multiple is None else float(peer_multiple),
        "historical_multiple": None if historical_multiple is None else float(historical_multiple),
        "justified_multiple": justified_multiple,
        "terminal_growth_rate": terminal_growth_rate,
        "cost_of_equity": cost_of_equity,
        "regulated_value": regulated_value,
        "equity_value": equity_value,
        "implied_value_per_share": implied_value_per_share,
        "upside_pct": (
            safe_div(implied_value_per_share - current_price, current_price)
            if current_price not in (None, 0, 0.0)
            else None
        ),
        "sensitivity": sensitivity,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
