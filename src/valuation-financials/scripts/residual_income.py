#!/usr/bin/env python3
import argparse

from financials_common import dump_json, get_num, load_json, safe_div


def build_forecast_rows(rows, opening_book_value_per_share):
    output = []
    book_value = float(opening_book_value_per_share)
    for row in rows:
        begin_bvps = row.get("begin_book_value_per_share", book_value)
        if begin_bvps is None:
            begin_bvps = book_value
        begin_bvps = float(begin_bvps)
        roe = row.get("roe")
        net_income_per_share = row.get("net_income_per_share")
        if net_income_per_share is None and roe is not None:
            net_income_per_share = begin_bvps * float(roe)
        dividends_per_share = row.get("dividends_per_share")
        payout_ratio = row.get("payout_ratio")
        if dividends_per_share is None and net_income_per_share is not None and payout_ratio is not None:
            dividends_per_share = float(net_income_per_share) * float(payout_ratio)
        end_bvps = row.get("end_book_value_per_share")
        if end_bvps is None and net_income_per_share is not None:
            end_bvps = begin_bvps + float(net_income_per_share) - float(dividends_per_share or 0.0)
        output.append(
            {
                "period": row["period"],
                "begin_book_value_per_share": begin_bvps,
                "roe": None if roe is None else float(roe),
                "net_income_per_share": None if net_income_per_share is None else float(net_income_per_share),
                "dividends_per_share": None if dividends_per_share is None else float(dividends_per_share),
                "end_book_value_per_share": None if end_bvps is None else float(end_bvps),
            }
        )
        if end_bvps is not None:
            book_value = float(end_bvps)
    return output


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run a residual-income valuation from a financials prep pack plus explicit forecast rows."
        )
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="residual_income_output.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    prep = payload.get("financials_prep", payload)
    method = payload.get("residual_income", payload.get("method", {}))

    book_bridge = prep.get("book_bridge", {})
    share_bridge = prep.get("share_bridge", {})
    earnings = prep.get("earnings", {})
    market = prep.get("market", {})

    book_basis = method.get("book_basis", "tangible")
    if book_basis == "reported":
        opening_bvps = method.get("opening_book_value_per_share") or book_bridge.get("book_value_per_share")
        default_return = earnings.get("normalized_roe")
    else:
        opening_bvps = method.get("opening_book_value_per_share") or book_bridge.get("tangible_book_value_per_share")
        default_return = earnings.get("normalized_rotce")

    forecast_rows = build_forecast_rows(method.get("forecast", []), opening_bvps)
    cost_of_equity = float(method["cost_of_equity"])
    terminal_growth = float(method.get("terminal_growth_rate", 0.03))
    terminal_return = float(method.get("terminal_return", default_return or cost_of_equity))

    pv_rows = []
    pv_residual_income = 0.0
    for index, row in enumerate(forecast_rows, start=1):
        begin_bvps = row["begin_book_value_per_share"]
        net_income_per_share = row["net_income_per_share"]
        if net_income_per_share is None and row.get("roe") is not None:
            net_income_per_share = begin_bvps * row["roe"]
            row["net_income_per_share"] = net_income_per_share
        residual_income_per_share = (
            float(net_income_per_share) - (cost_of_equity * begin_bvps)
            if net_income_per_share is not None
            else None
        )
        discount_factor = (1 + cost_of_equity) ** index
        pv_ri = safe_div(residual_income_per_share, discount_factor) if residual_income_per_share is not None else None
        pv_residual_income += float(pv_ri or 0.0)
        pv_rows.append(
            {
                **row,
                "discount_factor": discount_factor,
                "residual_income_per_share": residual_income_per_share,
                "pv_residual_income_per_share": pv_ri,
            }
        )

    terminal_base_bvps = pv_rows[-1]["end_book_value_per_share"] if pv_rows else float(opening_bvps)
    terminal_residual_income = terminal_base_bvps * (terminal_return - cost_of_equity)
    terminal_value_per_share_at_horizon = (
        terminal_residual_income / (cost_of_equity - terminal_growth)
        if cost_of_equity > terminal_growth
        else None
    )
    horizon_years = max(len(pv_rows), 1)
    pv_terminal_value_per_share = (
        safe_div(terminal_value_per_share_at_horizon, (1 + cost_of_equity) ** horizon_years)
        if terminal_value_per_share_at_horizon is not None
        else None
    )
    implied_value_per_share = (
        float(opening_bvps) + pv_residual_income + float(pv_terminal_value_per_share or 0.0)
    )
    diluted_shares = share_bridge.get("diluted_shares")
    implied_equity_value = (
        implied_value_per_share * float(diluted_shares)
        if diluted_shares is not None
        else None
    )

    result = {
        "label": "Residual Income",
        "method_family": "residual_income",
        "book_basis": book_basis,
        "opening_book_value_per_share": opening_bvps,
        "cost_of_equity": cost_of_equity,
        "terminal_growth_rate": terminal_growth,
        "terminal_return": terminal_return,
        "pv_rows": pv_rows,
        "pv_residual_income_per_share": pv_residual_income,
        "terminal_value_per_share_at_horizon": terminal_value_per_share_at_horizon,
        "pv_terminal_value_per_share": pv_terminal_value_per_share,
        "implied_value_per_share": implied_value_per_share,
        "implied_equity_value": implied_equity_value,
        "current_price": market.get("current_price"),
        "premium_discount_to_current": (
            safe_div(implied_value_per_share - market.get("current_price"), market.get("current_price"))
            if market.get("current_price") not in (None, 0, 0.0)
            else None
        ),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
