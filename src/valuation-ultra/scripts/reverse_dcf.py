#!/usr/bin/env python3
import argparse

from dcf_valuation import enterprise_value_from_inputs
from valuation_common import (
    diluted_shares_total,
    dump_json,
    enterprise_to_equity_adjustment_total,
    get_num,
    load_json,
    bisection_solve,
)


def apply_parameter(payload, solve_for, value):
    modified = dict(payload)
    if solve_for == "discount_rate":
        modified["discount_rate"] = value
        return modified
    terminal = dict(modified["terminal"])
    if solve_for == "terminal_growth_rate":
        terminal["growth_rate"] = value
        modified["terminal"] = terminal
        return modified
    if solve_for == "terminal_multiple":
        terminal["multiple"] = value
        modified["terminal"] = terminal
        return modified
    if solve_for == "cash_flow_multiplier":
        modified["forecast"] = [
            {**row, "unlevered_fcf": get_num(row, "unlevered_fcf") * value}
            for row in modified["forecast"]
        ]
        if terminal["method"] == "gordon_growth" and terminal.get("terminal_cash_flow") is not None:
            terminal["terminal_cash_flow"] = get_num(terminal, "terminal_cash_flow") * value
        if terminal["method"] == "exit_multiple":
            terminal["metric_value"] = get_num(terminal, "metric_value") * value
        modified["terminal"] = terminal
        return modified
    raise ValueError(f"Unsupported solve_for parameter: {solve_for}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Solve a reverse DCF parameter so model EV matches market EV. "
            "Supported solve_for: discount_rate, terminal_growth_rate, terminal_multiple, cash_flow_multiplier."
        )
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="reverse_dcf.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    market_enterprise_value = get_num(payload, "market_enterprise_value")
    solve_for = payload["solve_for"]
    bounds = payload.get("bounds", {})
    low = float(bounds.get("low"))
    high = float(bounds.get("high"))

    def objective(candidate):
        modified = apply_parameter(payload, solve_for, candidate)
        calc = enterprise_value_from_inputs(modified)
        return calc["enterprise_value"] - market_enterprise_value

    solved = bisection_solve(objective, low, high)
    solved_payload = apply_parameter(payload, solve_for, solved)
    calc = enterprise_value_from_inputs(solved_payload)
    ev_bridge = payload.get("ev_bridge", {})
    share_bridge = payload.get("share_bridge", {})
    adjustment_total = enterprise_to_equity_adjustment_total(ev_bridge)
    diluted_shares = (
        get_num(share_bridge, "diluted_shares")
        if share_bridge.get("diluted_shares") is not None
        else diluted_shares_total(share_bridge)
    )
    equity_value = calc["enterprise_value"] + adjustment_total
    result = {
        "solve_for": solve_for,
        "solved_value": solved,
        "market_enterprise_value": market_enterprise_value,
        "model_enterprise_value": calc["enterprise_value"],
        "equity_value": equity_value,
        "equity_value_per_share": (equity_value / diluted_shares) if diluted_shares else None,
        "dcf": calc,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
