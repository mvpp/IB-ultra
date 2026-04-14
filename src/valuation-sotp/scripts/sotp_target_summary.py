#!/usr/bin/env python3
import argparse

from sotp_common import dump_json, load_json, normalize_weights, pick_value, safe_div


def method_range(payload, fallback):
    if payload is None:
        return None
    mid = pick_value(payload)
    if mid is None:
        return None
    low = (
        payload.get("value_per_share_low")
        or payload.get("implied_value_per_share_low")
        or payload.get("bear_value_per_share")
        or payload.get("low")
        or mid
    )
    high = (
        payload.get("value_per_share_high")
        or payload.get("implied_value_per_share_high")
        or payload.get("bull_value_per_share")
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
    parser = argparse.ArgumentParser(description="Combine SOTP and optional secondary methods into a target-price summary.")
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="target_price_summary.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    primary = payload.get("primary_method", {})
    secondary = payload.get("secondary_method", {})
    tertiary = payload.get("tertiary_method", {})
    market = payload.get("market", {})
    config = payload.get("config", {})
    current_price = market.get("current_price")

    methods = []
    for slot, item, default_weight in [
        ("primary", primary, 0.7),
        ("secondary", secondary, 0.3),
        ("tertiary", tertiary, 0.0),
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
    weighted_mid = sum(row["mid"] * row["weight"] for row in methods) if methods else None
    weighted_low = sum(row["low"] * row["weight"] for row in methods) if methods else None
    weighted_high = sum(row["high"] * row["weight"] for row in methods) if methods else None

    result = {
        "current_price": current_price,
        "weighted_target_price": weighted_mid,
        "expected_value_per_share": weighted_mid,
        "base_target_price": weighted_mid,
        "bear_target_price": weighted_low,
        "bull_target_price": weighted_high,
        "primary_method": primary.get("label"),
        "secondary_method": secondary.get("label"),
        "method_weights": {row["label"]: row["weight"] for row in methods},
        "methods": [
            {
                "slot": row["slot"],
                "label": row["label"],
                "value_per_share": row["mid"],
                "bear_value_per_share": row["low"],
                "bull_value_per_share": row["high"],
                "weight": row["weight"],
            }
            for row in methods
        ],
        "upside_pct": (
            safe_div(weighted_mid - current_price, current_price)
            if None not in (weighted_mid, current_price) and current_price not in (0, 0.0)
            else None
        ),
        "valuation_qc_passed": payload.get("valuation_qc_passed"),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
