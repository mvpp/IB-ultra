#!/usr/bin/env python3
import argparse

from valuation_common import dump_json, get_num, load_json


def add_check(failures, warnings, condition, message, severity="fail"):
    if condition:
        return
    if severity == "warn":
        warnings.append(message)
    else:
        failures.append(message)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic QC checks across valuation outputs. Input may include dcf, capital_cost, "
            "valuation_prep, methods, sensitivity, reverse_dcf, and limits."
        )
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="valuation_qc.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    failures = []
    warnings = []
    methods = payload.get("methods", [])
    capital_cost = payload.get("capital_cost", {})
    dcf = payload.get("dcf", {})
    valuation_prep = payload.get("valuation_prep", {})
    limits = payload.get("limits", {})

    add_check(failures, warnings, len(methods) >= 2, "Need both a primary and a secondary method.")

    diluted_shares = get_num(valuation_prep.get("share_bridge", {}), "diluted_shares")
    add_check(failures, warnings, diluted_shares > 0, "Diluted shares must be positive and explicit.")

    debt_weight = capital_cost.get("capital_structure", {}).get("target_debt_weight")
    equity_weight = capital_cost.get("capital_structure", {}).get("target_equity_weight")
    if debt_weight is not None and equity_weight is not None:
        add_check(
            failures,
            warnings,
            abs((debt_weight + equity_weight) - 1.0) <= 1e-6,
            "Capital structure weights do not sum to 1.",
        )

    if dcf:
        discount_rate = get_num(dcf, "discount_rate")
        terminal = dcf.get("terminal", {})
        if terminal.get("method") == "gordon_growth":
            growth_rate = get_num(terminal, "growth_rate")
            add_check(failures, warnings, discount_rate > growth_rate, "DCF requires discount rate > terminal growth.")
            nominal_gdp_cap = get_num(limits, "nominal_gdp_cap", 0.05)
            add_check(
                failures,
                warnings,
                growth_rate <= nominal_gdp_cap,
                "Terminal growth exceeds the nominal GDP cap.",
            )
        explicit_pv = sum(get_num(row, "pv_fcf") for row in dcf.get("pv_rows", []))
        modeled_ev = explicit_pv + get_num(dcf, "pv_terminal_value")
        add_check(
            failures,
            warnings,
            abs(modeled_ev - get_num(dcf, "enterprise_value")) <= 1e-6,
            "DCF enterprise value does not reconcile to explicit PV plus terminal PV.",
        )
        if diluted_shares > 0 and dcf.get("equity_value_per_share") is not None:
            implied_price = get_num(dcf, "equity_value") / diluted_shares
            add_check(
                failures,
                warnings,
                abs(implied_price - get_num(dcf, "equity_value_per_share")) <= 1e-6,
                "DCF per-share value does not reconcile to equity value divided by diluted shares.",
            )

    add_check(
        failures,
        warnings,
        payload.get("sensitivity", {}).get("run", False),
        "Sensitivity output is missing.",
    )
    add_check(
        failures,
        warnings,
        payload.get("reverse_dcf", {}).get("run", False),
        "Reverse DCF or implied expectations output is missing.",
    )

    result = {
        "passed": not failures,
        "failures": failures,
        "warnings": warnings,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
