#!/usr/bin/env python3
import argparse

from memo_common import dump_json, load_json


def main():
    parser = argparse.ArgumentParser(
        description="Frame market-implied versus underwritten assumptions from the memo input pack."
    )
    parser.add_argument("--input", required=True, help="Path to memo_input_pack JSON")
    parser.add_argument("--output", default="variant_view_frame.json", help="Path to JSON output")
    args = parser.parse_args()

    pack = load_json(args.input)
    summary = pack.get("summary", {})

    comparisons = []
    for name, label in [
        ("growth_gap_pct", "Revenue growth"),
        ("margin_gap_pct", "Margin"),
        ("roic_gap_pct", "ROIC"),
    ]:
        gap = summary.get(name)
        if gap is None:
            continue
        comparisons.append(
            {
                "dimension": label,
                "gap_pct": gap,
                "absolute_gap_pct": abs(gap),
            }
        )
    comparisons.sort(key=lambda item: item["absolute_gap_pct"], reverse=True)
    primary = comparisons[0] if comparisons else None

    result = {
        "current_price": summary.get("current_price"),
        "weighted_target_price": summary.get("weighted_target_price"),
        "market_implied_growth": summary.get("market_implied_growth"),
        "underwritten_growth": summary.get("revenue_growth_forecast"),
        "market_implied_margin": summary.get("market_implied_margin"),
        "underwritten_margin": summary.get("terminal_margin"),
        "market_implied_roic": summary.get("market_implied_roic"),
        "underwritten_roic": summary.get("terminal_roic"),
        "upside_pct": summary.get("upside_pct"),
        "primary_mismatch": primary,
        "comparisons": comparisons,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
