#!/usr/bin/env python3
import argparse

from valuation_common import dump_json, get_num, load_json


def resolve_weights(capital_structure):
    if "target_debt_weight" in capital_structure and "target_equity_weight" in capital_structure:
        debt_weight = get_num(capital_structure, "target_debt_weight")
        equity_weight = get_num(capital_structure, "target_equity_weight")
    elif "debt_value" in capital_structure and "equity_value" in capital_structure:
        debt_value = get_num(capital_structure, "debt_value")
        equity_value = get_num(capital_structure, "equity_value")
        total = debt_value + equity_value
        if total <= 0:
            raise ValueError("Capital structure total must be positive.")
        debt_weight = debt_value / total
        equity_weight = equity_value / total
    elif "target_debt_to_total_capital" in capital_structure:
        debt_weight = get_num(capital_structure, "target_debt_to_total_capital")
        equity_weight = 1.0 - debt_weight
    else:
        raise ValueError("Provide either explicit target weights or debt/equity values.")
    if abs((debt_weight + equity_weight) - 1.0) > 1e-6:
        raise ValueError("Debt and equity weights must sum to 1.")
    return debt_weight, equity_weight


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Calculate cost of equity, after-tax cost of debt, and WACC from JSON inputs. "
            "Required fields: risk_free_rate, beta, equity_risk_premium, pre_tax_cost_of_debt, "
            "marginal_tax_rate, capital_structure."
        )
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="capital_cost.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    capital_structure = payload.get("capital_structure", {})
    debt_weight, equity_weight = resolve_weights(capital_structure)
    cost_of_equity = (
        get_num(payload, "risk_free_rate")
        + get_num(payload, "beta") * get_num(payload, "equity_risk_premium")
        + get_num(payload, "country_risk_premium")
        + get_num(payload, "size_premium")
        + get_num(payload, "company_specific_premium")
    )
    pre_tax_cost_of_debt = get_num(payload, "pre_tax_cost_of_debt")
    marginal_tax_rate = get_num(payload, "marginal_tax_rate")
    after_tax_cost_of_debt = pre_tax_cost_of_debt * (1.0 - marginal_tax_rate)
    wacc = (equity_weight * cost_of_equity) + (debt_weight * after_tax_cost_of_debt)

    result = {
        "cost_of_equity": cost_of_equity,
        "pre_tax_cost_of_debt": pre_tax_cost_of_debt,
        "after_tax_cost_of_debt": after_tax_cost_of_debt,
        "marginal_tax_rate": marginal_tax_rate,
        "capital_structure": {
            "target_debt_weight": debt_weight,
            "target_equity_weight": equity_weight,
        },
        "wacc": wacc,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
