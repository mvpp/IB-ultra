#!/usr/bin/env python3
import argparse

from reit_common import dump_json, load_json, normalize_weights, pick_value, safe_div


def main():
    parser = argparse.ArgumentParser(
        description="Combine REIT/property primary and secondary method outputs into a target-price summary."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="target_price_summary.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    primary = payload.get("primary_method", {})
    secondary = payload.get("secondary_method", {})
    tertiary = payload.get("tertiary_method", {})
    config = payload.get("config", {})
    market = payload.get("market", {})
    current_price = market.get("current_price")

    methods = []
    for slot, item, default_weight in [
        ("primary", primary, 0.60),
        ("secondary", secondary, 0.40),
        ("tertiary", tertiary, 0.00),
    ]:
        if not item:
            continue
        value_per_share = pick_value(item)
        if value_per_share is None:
            continue
        methods.append(
            {
                "slot": slot,
                "label": item.get("label", slot.title()),
                "value_per_share": float(value_per_share),
                "weight": float(item.get("weight", config.get(f"{slot}_weight", default_weight))),
            }
        )

    normalize_weights(methods)

    weighted_target_price = (
        sum(method["value_per_share"] * method["weight"] for method in methods)
        if methods
        else None
    )
    ordered = sorted((method["value_per_share"] for method in methods))
    bear_target_price = ordered[0] if ordered else None
    bull_target_price = ordered[-1] if ordered else None

    result = {
        "current_price": current_price,
        "weighted_target_price": weighted_target_price,
        "expected_value_per_share": weighted_target_price,
        "base_target_price": weighted_target_price,
        "bull_target_price": bull_target_price,
        "bear_target_price": bear_target_price,
        "primary_method": primary.get("label"),
        "secondary_method": secondary.get("label"),
        "method_weights": {method["label"]: method["weight"] for method in methods},
        "methods": methods,
        "upside_pct": (
            safe_div(weighted_target_price - current_price, current_price)
            if None not in (weighted_target_price, current_price) and current_price not in (0, 0.0)
            else None
        ),
        "valuation_qc_passed": payload.get("valuation_qc_passed"),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
