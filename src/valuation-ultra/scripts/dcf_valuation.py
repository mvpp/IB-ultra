#!/usr/bin/env python3
import argparse

from valuation_common import (
    diluted_shares_total,
    dump_json,
    enterprise_to_equity_adjustment_total,
    get_num,
    load_json,
)


def enterprise_value_from_inputs(payload, discount_rate_override=None, terminal_override=None):
    forecast = payload["forecast"]
    discount_rate = float(discount_rate_override if discount_rate_override is not None else payload["discount_rate"])
    mid_year = bool(payload.get("mid_year_convention", True))
    pv_rows = []
    enterprise_value = 0.0
    for idx, row in enumerate(forecast, start=1):
        year_fraction = idx - 0.5 if mid_year else idx
        fcf = get_num(row, "unlevered_fcf")
        pv_factor = 1.0 / ((1.0 + discount_rate) ** year_fraction)
        pv_fcf = fcf * pv_factor
        enterprise_value += pv_fcf
        pv_rows.append(
            {
                "period": row["period"],
                "unlevered_fcf": fcf,
                "year_fraction": year_fraction,
                "pv_factor": pv_factor,
                "pv_fcf": pv_fcf,
            }
        )

    terminal = dict(payload["terminal"])
    if terminal_override:
        terminal.update(terminal_override)
    last_year_fraction = len(forecast) - 0.5 if mid_year else len(forecast)
    if terminal["method"] == "gordon_growth":
        growth_rate = get_num(terminal, "growth_rate")
        terminal_cash_flow = get_num(terminal, "terminal_cash_flow", get_num(forecast[-1], "unlevered_fcf"))
        terminal_value = (terminal_cash_flow * (1.0 + growth_rate)) / (discount_rate - growth_rate)
    elif terminal["method"] == "exit_multiple":
        terminal_value = get_num(terminal, "metric_value") * get_num(terminal, "multiple")
    else:
        raise ValueError(f"Unsupported terminal method: {terminal['method']}")
    pv_terminal = terminal_value / ((1.0 + discount_rate) ** last_year_fraction)
    enterprise_value += pv_terminal
    return {
        "discount_rate": discount_rate,
        "pv_rows": pv_rows,
        "terminal": terminal,
        "terminal_value": terminal_value,
        "pv_terminal_value": pv_terminal,
        "enterprise_value": enterprise_value,
    }


def build_sensitivity(payload):
    sensitivity = payload.get("sensitivity")
    if not sensitivity:
        return None
    terminal = payload["terminal"]
    discount_rates = sensitivity.get("discount_rates", [])
    matrix = []
    if terminal["method"] == "gordon_growth":
        terminal_growth_rates = sensitivity.get("terminal_growth_rates", [])
        for rate in discount_rates:
            row = {"discount_rate": rate, "values": []}
            for growth in terminal_growth_rates:
                calc = enterprise_value_from_inputs(payload, discount_rate_override=rate, terminal_override={"growth_rate": growth})
                row["values"].append({"terminal_growth_rate": growth, "enterprise_value": calc["enterprise_value"]})
            matrix.append(row)
        return {"type": "gordon_growth", "matrix": matrix}
    if terminal["method"] == "exit_multiple":
        terminal_multiples = sensitivity.get("terminal_multiples", [])
        for rate in discount_rates:
            row = {"discount_rate": rate, "values": []}
            for multiple in terminal_multiples:
                calc = enterprise_value_from_inputs(payload, discount_rate_override=rate, terminal_override={"multiple": multiple})
                row["values"].append({"terminal_multiple": multiple, "enterprise_value": calc["enterprise_value"]})
            matrix.append(row)
        return {"type": "exit_multiple", "matrix": matrix}
    return None


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run DCF valuation from JSON inputs. Required fields: forecast[{period,unlevered_fcf}], "
            "discount_rate, terminal{method,...}. Optional: ev_bridge, share_bridge, sensitivity."
        )
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="dcf_output.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    calc = enterprise_value_from_inputs(payload)
    ev_bridge = payload.get("ev_bridge", {})
    share_bridge = payload.get("share_bridge", {})
    adjustment_total = enterprise_to_equity_adjustment_total(ev_bridge)
    diluted_shares = (
        get_num(share_bridge, "diluted_shares")
        if share_bridge.get("diluted_shares") is not None
        else diluted_shares_total(share_bridge)
    )
    equity_value = calc["enterprise_value"] + adjustment_total
    equity_value_per_share = equity_value / diluted_shares if diluted_shares else None

    result = {
        **calc,
        "ev_bridge": {
            **ev_bridge,
            "enterprise_to_equity_adjustment_total": adjustment_total,
        },
        "share_bridge": {
            **share_bridge,
            "diluted_shares": diluted_shares,
        },
        "equity_value": equity_value,
        "equity_value_per_share": equity_value_per_share,
        "sensitivity": build_sensitivity(payload),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
