#!/usr/bin/env python3
import argparse

from biotech_common import dump_json, load_json, normalize_weights, pick_value, safe_div


def method_range(payload, fallback):
    if payload is None:
        return None
    mid = pick_value(payload)
    if mid is None:
        return None
    low = (
        payload.get("bear_value_per_share")
        or payload.get("low_value_per_share")
        or payload.get("low")
        or mid
    )
    high = (
        payload.get("bull_value_per_share")
        or payload.get("high_value_per_share")
        or payload.get("high")
        or mid
    )
    return {
        "slot": fallback["slot"],
        "label": payload.get("label", fallback["label"]),
        "mid": float(mid),
        "low": float(low),
        "high": float(high),
        "weight": float(payload.get("weight", fallback["weight"])),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Combine biotech primary and secondary method outputs into a target-price summary."
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
        ("primary", primary, 0.70),
        ("secondary", secondary, 0.30),
        ("tertiary", tertiary, 0.00),
    ]:
        if not item:
            continue
        method = method_range(
            item,
            {
                "slot": slot,
                "label": slot.title(),
                "weight": config.get(f"{slot}_weight", default_weight),
            },
        )
        if method:
            methods.append(method)

    normalize_weights(methods)
    weighted_target_price = sum(method["mid"] * method["weight"] for method in methods) if methods else None
    weighted_bear = sum(method["low"] * method["weight"] for method in methods) if methods else None
    weighted_bull = sum(method["high"] * method["weight"] for method in methods) if methods else None
    point_estimates = sorted(method["mid"] for method in methods) if methods else []

    result = {
        "current_price": current_price,
        "weighted_target_price": weighted_target_price,
        "expected_value_per_share": weighted_target_price,
        "base_target_price": weighted_target_price,
        "bull_target_price": weighted_bull if weighted_bull is not None else (point_estimates[-1] if point_estimates else None),
        "bear_target_price": weighted_bear if weighted_bear is not None else (point_estimates[0] if point_estimates else None),
        "primary_method": primary.get("label"),
        "secondary_method": secondary.get("label"),
        "method_weights": {method["label"]: method["weight"] for method in methods},
        "methods": [
            {
                "slot": method["slot"],
                "label": method["label"],
                "value_per_share": method["mid"],
                "bear_value_per_share": method["low"],
                "bull_value_per_share": method["high"],
                "weight": method["weight"],
            }
            for method in methods
        ],
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
