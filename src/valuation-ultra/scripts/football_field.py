#!/usr/bin/env python3
import argparse

from valuation_common import dump_json, get_num, load_json, percentile


def normalize_methods(methods):
    lows = [get_num(method, "low", get_num(method, "mid")) for method in methods]
    highs = [get_num(method, "high", get_num(method, "mid")) for method in methods]
    global_low = min(lows)
    global_high = max(highs)
    span = global_high - global_low if global_high != global_low else 1.0
    normalized = []
    for method in methods:
        low = get_num(method, "low", get_num(method, "mid"))
        mid = get_num(method, "mid")
        high = get_num(method, "high", mid)
        normalized.append(
            {
                **method,
                "low": low,
                "mid": mid,
                "high": high,
                "normalized_low": (low - global_low) / span,
                "normalized_mid": (mid - global_low) / span,
                "normalized_high": (high - global_low) / span,
            }
        )
    return normalized, global_low, global_high


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate valuation ranges into football-field-friendly JSON."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="football_field.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    methods = payload.get("methods", [])
    normalized, global_low, global_high = normalize_methods(methods)
    mids = [row["mid"] for row in normalized]
    result = {
        "methods": normalized,
        "current_price": payload.get("current_price"),
        "global_low": global_low,
        "global_high": global_high,
        "median_of_mids": percentile(mids, 0.50) if mids else None,
        "p25_of_mids": percentile(mids, 0.25) if mids else None,
        "p75_of_mids": percentile(mids, 0.75) if mids else None,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
