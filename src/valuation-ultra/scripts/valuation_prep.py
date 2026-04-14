#!/usr/bin/env python3
import argparse

from valuation_common import (
    diluted_shares_total,
    dump_json,
    enterprise_to_equity_adjustment_total,
    get_num,
    load_json,
    safe_div,
)


def build_forecast_rows(forecast_rows, addback_sbc):
    output = []
    previous_nopat = None
    for row in forecast_rows:
        period = row["period"]
        ebit = get_num(row, "ebit")
        tax_rate = get_num(row, "tax_rate")
        da = get_num(row, "da")
        capex = get_num(row, "capex")
        change_nwc = get_num(row, "change_nwc")
        sbc = get_num(row, "sbc")
        acquisitions = get_num(row, "acquisitions")
        asset_sales = get_num(row, "asset_sales")
        invested_capital_start = row.get("invested_capital_start")
        invested_capital_end = row.get("invested_capital_end")
        nopat = ebit * (1 - tax_rate)
        sbc_addback = sbc if addback_sbc else 0.0
        reinvestment = capex + change_nwc + acquisitions - asset_sales
        unlevered_fcf = nopat + da + sbc_addback - reinvestment
        if invested_capital_start is not None and invested_capital_end is not None:
            avg_invested_capital = (float(invested_capital_start) + float(invested_capital_end)) / 2.0
        else:
            avg_invested_capital = float(invested_capital_end or invested_capital_start or 0.0)
        roic = safe_div(nopat, avg_invested_capital)
        delta_revenue = None
        if output:
            delta_revenue = get_num(row, "revenue") - output[-1]["revenue"]
        sales_to_capital = None if delta_revenue is None else safe_div(delta_revenue, reinvestment)
        incremental_roic = None if previous_nopat is None else safe_div(nopat - previous_nopat, reinvestment)
        previous_nopat = nopat
        output.append(
            {
                "period": period,
                "revenue": get_num(row, "revenue"),
                "ebit": ebit,
                "tax_rate": tax_rate,
                "nopat": nopat,
                "da": da,
                "sbc": sbc,
                "sbc_addback_used": sbc_addback,
                "capex": capex,
                "change_nwc": change_nwc,
                "acquisitions": acquisitions,
                "asset_sales": asset_sales,
                "reinvestment": reinvestment,
                "unlevered_fcf": unlevered_fcf,
                "invested_capital_start": invested_capital_start,
                "invested_capital_end": invested_capital_end,
                "avg_invested_capital": avg_invested_capital,
                "roic": roic,
                "incremental_roic": incremental_roic,
                "sales_to_capital": sales_to_capital,
            }
        )
    return output


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic valuation-prep JSON from model export inputs. "
            "Input fields: forecast[{period,revenue,ebit,tax_rate,da,capex,change_nwc,...}], "
            "ev_bridge{}, share_bridge{}, policy{addback_sbc,include_restricted_cash}."
        )
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="valuation_prep.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    policy = payload.get("policy", {})
    ev_bridge = payload.get("ev_bridge", {})
    share_bridge = payload.get("share_bridge", {})
    if "include_restricted_cash" in policy:
        ev_bridge = {**ev_bridge, "include_restricted_cash": bool(policy["include_restricted_cash"])}

    forecast_rows = build_forecast_rows(payload.get("forecast", []), bool(policy.get("addback_sbc", False)))
    adjustment_total = enterprise_to_equity_adjustment_total(ev_bridge)
    diluted_shares = diluted_shares_total(share_bridge)
    net_debt = (
        get_num(ev_bridge, "total_debt")
        + get_num(ev_bridge, "lease_liabilities")
        - get_num(ev_bridge, "cash")
        - (get_num(ev_bridge, "restricted_cash") if ev_bridge.get("include_restricted_cash", False) else 0.0)
    )

    result = {
        "policy": {
            "addback_sbc": bool(policy.get("addback_sbc", False)),
            "include_restricted_cash": bool(ev_bridge.get("include_restricted_cash", False)),
        },
        "forecast": forecast_rows,
        "ev_bridge": {
            **ev_bridge,
            "enterprise_to_equity_adjustment_total": adjustment_total,
            "net_debt": net_debt,
        },
        "share_bridge": {
            **share_bridge,
            "diluted_shares": diluted_shares,
        },
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
