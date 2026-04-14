#!/usr/bin/env python3
import argparse

from biotech_common import dump_json, get_num, load_json, normalize_weights, safe_div


def scenario_value(asset, scenario, valuation_year):
    probability = float(asset.get("probability_of_success", 0.0))
    if asset.get("stage") == "approved" or asset.get("approval_status") == "approved":
        probability = 1.0
    probability = min(1.0, probability * float(scenario.get("pos_multiplier", 1.0)))

    discount_rate = get_num(asset, "discount_rate", 0.125)
    launch_delay = int(scenario.get("launch_delay_years", 0) or 0)
    sales_multiplier = float(scenario.get("sales_multiplier", 1.0) or 1.0)

    commercial_value = get_num(asset, "commercial_value_pv")
    if launch_delay > 0:
        commercial_value = commercial_value / ((1.0 + discount_rate) ** launch_delay)
    elif launch_delay < 0:
        commercial_value = commercial_value * ((1.0 + discount_rate) ** abs(launch_delay))

    commercial_value *= sales_multiplier
    development_cost_pv = get_num(asset, "development_cost_pv")
    return commercial_value * probability - development_cost_pv


def main():
    parser = argparse.ArgumentParser(
        description="Build bear/base/bull biotech launch scenarios from pipeline rNPV and dilution inputs."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="launch_scenarios.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    pipeline_output = payload.get("pipeline_rnpv_output", {})
    dilution = payload.get("cash_runway_dilution", {})
    valuation_year = int(pipeline_output.get("valuation_year") or payload.get("valuation_year"))

    scenarios = payload.get(
        "launch_scenarios",
        [
            {"name": "bear", "probability": 0.25, "pos_multiplier": 0.75, "sales_multiplier": 0.70, "launch_delay_years": 1, "dilution_multiplier": 1.20},
            {"name": "base", "probability": 0.50, "pos_multiplier": 1.00, "sales_multiplier": 1.00, "launch_delay_years": 0, "dilution_multiplier": 1.00},
            {"name": "bull", "probability": 0.25, "pos_multiplier": 1.15, "sales_multiplier": 1.20, "launch_delay_years": -1, "dilution_multiplier": 0.80},
        ],
    )
    normalize_weights(scenarios, key="probability")

    current_shares = get_num(pipeline_output, "current_diluted_shares")
    base_adjustment = get_num(pipeline_output, "balance_sheet_adjustment_total")
    base_new_shares = get_num(dilution, "new_shares")
    output_rows = []
    weighted_expected_value = 0.0

    for scenario in scenarios:
        asset_total = 0.0
        for asset in pipeline_output.get("assets", []):
            asset_total += scenario_value(asset, scenario, valuation_year)
        pro_forma_shares = current_shares + base_new_shares * float(scenario.get("dilution_multiplier", 1.0))
        equity_value = asset_total + base_adjustment
        value_per_share = safe_div(equity_value, pro_forma_shares, 0.0)
        probability = float(scenario.get("probability", 0.0))
        weighted_expected_value += value_per_share * probability
        output_rows.append(
            {
                "name": scenario.get("name"),
                "probability": probability,
                "asset_value": asset_total,
                "equity_value": equity_value,
                "pro_forma_diluted_shares": pro_forma_shares,
                "value_per_share": value_per_share,
                "pos_multiplier": scenario.get("pos_multiplier", 1.0),
                "sales_multiplier": scenario.get("sales_multiplier", 1.0),
                "launch_delay_years": scenario.get("launch_delay_years", 0),
                "dilution_multiplier": scenario.get("dilution_multiplier", 1.0),
            }
        )

    result = {
        "label": payload.get("label", "Launch Scenarios"),
        "scenarios": output_rows,
        "expected_value_per_share": weighted_expected_value,
        "base_value_per_share": next((row["value_per_share"] for row in output_rows if row["name"] == "base"), None),
        "bear_value_per_share": next((row["value_per_share"] for row in output_rows if row["name"] == "bear"), None),
        "bull_value_per_share": next((row["value_per_share"] for row in output_rows if row["name"] == "bull"), None),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
