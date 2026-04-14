#!/usr/bin/env python3
import argparse

from regulated_common import dump_json, get_num, load_json, safe_div


def present_value(amount, rate, year_index):
    return amount / ((1.0 + rate) ** year_index)


def main():
    parser = argparse.ArgumentParser(
        description="Value a regulated-assets business with a dividend discount model."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="ddm_output.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    bridge = payload.get("regulatory_bridge", {})
    method = payload.get("ddm_valuation", payload.get("method", {}))
    market = payload.get("market", bridge.get("market", {}))

    earnings_bridge = bridge.get("earnings_bridge", {})
    returns_bridge = bridge.get("returns_bridge", {})
    share_bridge = bridge.get("share_bridge", {})
    regulatory_rollforward = bridge.get("regulatory_rollforward", {})

    cost_of_equity = float(
        method.get("cost_of_equity")
        if method.get("cost_of_equity") is not None
        else market.get("cost_of_equity", 0.0)
    )
    forecast_years = int(method.get("forecast_years", 5))
    payout_ratio = (
        float(method["payout_ratio"])
        if method.get("payout_ratio") is not None
        else get_num(earnings_bridge, "payout_ratio")
    )
    initial_dividend = method.get("current_dividend_per_share")
    if initial_dividend is None:
        initial_dividend = earnings_bridge.get("dividend_per_share_ltm")
    if initial_dividend is None and market.get("current_price") is not None and market.get("dividend_yield") is not None:
        initial_dividend = float(market["current_price"]) * float(market["dividend_yield"])
    initial_dividend = float(initial_dividend or 0.0)

    dividend_growth_rate = method.get("dividend_growth_rate")
    if dividend_growth_rate is None:
        dividend_growth_rate = regulatory_rollforward.get("rate_base_growth")
    if dividend_growth_rate is None:
        dividend_growth_rate = 0.02
    dividend_growth_rate = float(dividend_growth_rate)

    terminal_growth_rate = float(
        method.get("terminal_growth_rate")
        if method.get("terminal_growth_rate") is not None
        else min(dividend_growth_rate, 0.03)
    )

    explicit_dividends = method.get("dividends_per_share_forecast", [])
    explicit_eps = method.get("earnings_per_share_forecast", [])
    forecast_rows = []
    pv_dividends = 0.0

    if explicit_dividends:
        forecast_dividends = [float(value) for value in explicit_dividends]
    elif explicit_eps:
        forecast_dividends = [float(value) * payout_ratio for value in explicit_eps]
    else:
        forecast_dividends = []
        for year in range(1, forecast_years + 1):
            forecast_dividends.append(initial_dividend * ((1.0 + dividend_growth_rate) ** year))

    for year_index, dividend_per_share in enumerate(forecast_dividends, start=1):
        pv_amount = present_value(dividend_per_share, cost_of_equity, year_index)
        forecast_rows.append(
            {
                "year": year_index,
                "dividend_per_share": dividend_per_share,
                "pv_dividend_per_share": pv_amount,
            }
        )
        pv_dividends += pv_amount

    last_dividend = forecast_dividends[-1] if forecast_dividends else initial_dividend
    terminal_dividend = last_dividend * (1.0 + terminal_growth_rate)
    terminal_value_per_share = (
        safe_div(terminal_dividend, cost_of_equity - terminal_growth_rate)
        if cost_of_equity > terminal_growth_rate
        else None
    )
    pv_terminal_value_per_share = (
        present_value(terminal_value_per_share, cost_of_equity, len(forecast_dividends))
        if terminal_value_per_share is not None and forecast_dividends
        else terminal_value_per_share
    )

    non_operating_adjustment_per_share = float(method.get("non_operating_adjustment_per_share", 0.0))
    implied_value_per_share = (
        pv_dividends + (pv_terminal_value_per_share or 0.0) + non_operating_adjustment_per_share
    )
    diluted_shares = get_num(share_bridge, "diluted_shares")
    implied_equity_value = implied_value_per_share * diluted_shares

    result = {
        "label": method.get("label", "DDM"),
        "forecast_years": len(forecast_dividends),
        "cost_of_equity": cost_of_equity,
        "payout_ratio": payout_ratio,
        "allowed_roe": get_num(returns_bridge, "allowed_roe"),
        "dividend_growth_rate": dividend_growth_rate,
        "terminal_growth_rate": terminal_growth_rate,
        "current_dividend_per_share": initial_dividend,
        "forecast": forecast_rows,
        "pv_dividends_per_share": pv_dividends,
        "terminal_value_per_share": terminal_value_per_share,
        "pv_terminal_value_per_share": pv_terminal_value_per_share,
        "non_operating_adjustment_per_share": non_operating_adjustment_per_share,
        "implied_value_per_share": implied_value_per_share,
        "equity_value": implied_equity_value,
        "upside_pct": (
            safe_div(implied_value_per_share - market.get("current_price"), market.get("current_price"))
            if market.get("current_price") not in (None, 0, 0.0)
            else None
        ),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
