#!/usr/bin/env python3
import argparse

from financials_common import dump_json, load_json, safe_div


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate adjusted net worth, value of in-force, and optional franchise value into an embedded-value output."
        )
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="embedded_value_output.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    method = payload.get("embedded_value", payload.get("method", payload))
    diluted_shares = float(method["diluted_shares"])

    adjusted_net_worth = float(method.get("adjusted_net_worth", 0.0))
    value_in_force = float(method.get("value_in_force", 0.0))
    franchise_value = float(method.get("franchise_value", 0.0))
    holding_company_adjustment = float(method.get("holding_company_adjustment", 0.0))
    required_capital_friction = float(method.get("required_capital_friction", 0.0))

    embedded_value_total = (
        adjusted_net_worth
        + value_in_force
        + franchise_value
        + holding_company_adjustment
        - required_capital_friction
    )
    embedded_value_per_share = safe_div(embedded_value_total, diluted_shares)

    result = {
        "label": "Embedded Value",
        "method_family": "embedded_value",
        "adjusted_net_worth": adjusted_net_worth,
        "value_in_force": value_in_force,
        "franchise_value": franchise_value,
        "holding_company_adjustment": holding_company_adjustment,
        "required_capital_friction": required_capital_friction,
        "embedded_value_total": embedded_value_total,
        "embedded_value_per_share": embedded_value_per_share,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
