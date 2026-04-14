#!/usr/bin/env python3
import argparse

from memo_common import avg, dump_json, get_num, load_json, normalize_probabilities, pct_change, safe_div


def first_number(*values):
    for value in values:
        if value is None:
            continue
        return float(value)
    return None


def merge_section(payload, key, path):
    if not path:
        return payload
    fragment = load_json(path)
    if key in fragment:
        payload[key] = fragment[key]
    else:
        payload[key] = fragment
    return payload


def standardize_scenarios(valuation):
    scenarios = valuation.get("scenarios", [])
    output = []
    if isinstance(scenarios, dict):
        scenarios = [
            {"name": name, **values}
            for name, values in scenarios.items()
            if isinstance(values, dict)
        ]
    for scenario in scenarios:
        value_per_share = first_number(
            scenario.get("value_per_share"),
            scenario.get("target_price"),
            scenario.get("price"),
        )
        if value_per_share is None:
            continue
        output.append(
            {
                "name": str(scenario.get("name", "scenario")).lower(),
                "value_per_share": value_per_share,
                "probability": scenario.get("probability"),
            }
        )
    scenario_map = {row["name"]: row for row in output}
    for name, key in [("bear", "bear_target_price"), ("base", "base_target_price"), ("bull", "bull_target_price")]:
        if name not in scenario_map and valuation.get(key) is not None:
            output.append({"name": name, "value_per_share": float(valuation[key])})
    probabilities = normalize_probabilities(output)
    for row, probability in zip(output, probabilities):
        row["probability"] = probability
    return output


def build_memo_pack(payload):
    company = payload.get("company", {})
    model_summary = payload.get("model_summary", {})
    valuation = payload.get("valuation", payload.get("valuation_summary", {}))
    quality_inputs = payload.get("quality_inputs", {})
    monitoring_inputs = payload.get("monitoring_inputs", {})
    market = payload.get("market", {})

    current_price = first_number(
        get_num(company, "current_price"),
        get_num(market, "current_price"),
        get_num(valuation, "current_price"),
    )
    weighted_target_price = first_number(
        get_num(valuation, "weighted_target_price"),
        get_num(valuation, "target_price"),
        get_num(valuation, "target_price_per_share"),
    )
    expected_value_per_share = first_number(get_num(valuation, "expected_value_per_share"), weighted_target_price)

    scenarios = standardize_scenarios(valuation)
    scenario_map = {row["name"]: row for row in scenarios}
    bear_target_price = first_number(
        get_num(valuation, "bear_target_price"),
        get_num(scenario_map.get("bear", {}), "value_per_share"),
    )
    base_target_price = first_number(
        get_num(valuation, "base_target_price"),
        get_num(scenario_map.get("base", {}), "value_per_share"),
    )
    bull_target_price = first_number(
        get_num(valuation, "bull_target_price"),
        get_num(scenario_map.get("bull", {}), "value_per_share"),
    )

    if scenarios and expected_value_per_share is None:
        expected_value_per_share = sum(
            row["value_per_share"] * row["probability"] for row in scenarios
        )
    if weighted_target_price is None:
        weighted_target_price = expected_value_per_share or base_target_price or bull_target_price

    revenue_growth_forecast = first_number(
        get_num(model_summary, "revenue_cagr_forecast"),
        get_num(model_summary, "revenue_growth_next_year"),
        get_num(model_summary, "revenue_growth_ltm"),
    )
    terminal_margin = first_number(
        get_num(model_summary, "ebit_margin_terminal"),
        get_num(model_summary, "operating_margin_terminal"),
        get_num(model_summary, "ebit_margin_ltm"),
    )
    terminal_roic = first_number(
        get_num(model_summary, "roic_terminal"),
        get_num(model_summary, "roic_ltm"),
        avg(quality_inputs.get("roic_history", [])),
    )

    reverse_dcf = valuation.get("reverse_dcf", {})
    market_implied_growth = first_number(
        get_num(reverse_dcf, "market_implied_growth"),
        get_num(reverse_dcf, "implied_growth"),
        get_num(reverse_dcf, "growth_rate"),
    )
    market_implied_margin = first_number(
        get_num(reverse_dcf, "market_implied_margin"),
        get_num(reverse_dcf, "implied_margin"),
        get_num(reverse_dcf, "terminal_margin"),
    )
    market_implied_roic = first_number(
        get_num(reverse_dcf, "market_implied_roic"),
        get_num(reverse_dcf, "implied_roic"),
    )

    upside_pct = pct_change(weighted_target_price, current_price) if current_price is not None else None
    downside_pct = pct_change(bear_target_price, current_price) if current_price is not None else None
    expected_return_pct = pct_change(expected_value_per_share, current_price) if current_price is not None else None
    margin_of_safety_pct = (
        safe_div(weighted_target_price - current_price, weighted_target_price)
        if current_price is not None and weighted_target_price is not None
        else None
    )
    risk_reward_ratio = (
        safe_div(weighted_target_price - current_price, current_price - bear_target_price)
        if None not in (weighted_target_price, current_price, bear_target_price) and current_price > bear_target_price
        else None
    )

    result = {
        "company": company,
        "market": {"current_price": current_price, **market},
        "model_summary": model_summary,
        "valuation": {**valuation, "scenarios": scenarios},
        "quality_inputs": quality_inputs,
        "monitoring_inputs": monitoring_inputs,
        "summary": {
            "current_price": current_price,
            "weighted_target_price": weighted_target_price,
            "expected_value_per_share": expected_value_per_share,
            "base_target_price": base_target_price,
            "bull_target_price": bull_target_price,
            "bear_target_price": bear_target_price,
            "upside_pct": upside_pct,
            "downside_pct": downside_pct,
            "expected_return_pct": expected_return_pct,
            "margin_of_safety_pct": margin_of_safety_pct,
            "risk_reward_ratio": risk_reward_ratio,
            "primary_method": valuation.get("primary_method"),
            "secondary_method": valuation.get("secondary_method"),
            "valuation_qc_passed": bool(valuation.get("valuation_qc_passed", False)),
            "revenue_growth_forecast": revenue_growth_forecast,
            "terminal_margin": terminal_margin,
            "terminal_roic": terminal_roic,
            "market_implied_growth": market_implied_growth,
            "market_implied_margin": market_implied_margin,
            "market_implied_roic": market_implied_roic,
            "growth_gap_pct": (
                revenue_growth_forecast - market_implied_growth
                if None not in (revenue_growth_forecast, market_implied_growth)
                else None
            ),
            "margin_gap_pct": (
                terminal_margin - market_implied_margin
                if None not in (terminal_margin, market_implied_margin)
                else None
            ),
            "roic_gap_pct": (
                terminal_roic - market_implied_roic
                if None not in (terminal_roic, market_implied_roic)
                else None
            ),
        },
    }
    return result


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Standardize phase-1 and phase-2 artifacts into a memo-ready input pack. Accepts one combined "
            "JSON file or separate files for company, model_summary, valuation, quality_inputs, and monitoring_inputs."
        )
    )
    parser.add_argument("--input", help="Optional combined input JSON")
    parser.add_argument("--company", help="Optional company JSON")
    parser.add_argument("--model", help="Optional model summary JSON")
    parser.add_argument("--valuation", help="Optional valuation JSON")
    parser.add_argument("--quality", help="Optional quality-input JSON")
    parser.add_argument("--monitoring", help="Optional monitoring-input JSON")
    parser.add_argument("--output", default="memo_input_pack.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input) if args.input else {}
    for key, path in [
        ("company", args.company),
        ("model_summary", args.model),
        ("valuation", args.valuation),
        ("quality_inputs", args.quality),
        ("monitoring_inputs", args.monitoring),
    ]:
        merge_section(payload, key, path)

    result = build_memo_pack(payload)
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
