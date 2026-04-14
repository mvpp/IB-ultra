#!/usr/bin/env python3
import argparse

from memo_common import dump_json, load_json, safe_div


def load_optional(path):
    return load_json(path) if path else {}


def main():
    parser = argparse.ArgumentParser(
        description="Create deterministic action bands and position guidance from memo inputs."
    )
    parser.add_argument("--memo-pack", required=True, help="Path to memo_input_pack JSON")
    parser.add_argument("--quality", help="Optional quality_overlay JSON")
    parser.add_argument("--config", help="Optional config JSON")
    parser.add_argument("--output", default="decision_framework.json", help="Path to JSON output")
    args = parser.parse_args()

    memo_pack = load_json(args.memo_pack)
    quality = load_optional(args.quality)
    config = load_optional(args.config)

    summary = memo_pack.get("summary", {})
    current_price = summary.get("current_price")
    weighted_target_price = summary.get("weighted_target_price")
    expected_value_per_share = summary.get("expected_value_per_share") or weighted_target_price
    bull_target_price = summary.get("bull_target_price")
    bear_target_price = summary.get("bear_target_price")

    hurdle_rate = float(config.get("required_return", 0.15))
    trim_buffer = float(config.get("trim_buffer", 0.00))

    action_price = (
        weighted_target_price / (1 + hurdle_rate)
        if current_price is not None and weighted_target_price is not None
        else None
    )
    trim_price = (
        bull_target_price * (1 - trim_buffer)
        if bull_target_price is not None
        else (weighted_target_price * 1.10 if weighted_target_price is not None else None)
    )
    expected_return_pct = summary.get("expected_return_pct")
    downside_pct = summary.get("downside_pct")
    risk_reward_ratio = (
        safe_div(weighted_target_price - current_price, current_price - bear_target_price)
        if None not in (weighted_target_price, current_price, bear_target_price) and current_price > bear_target_price
        else None
    )

    quality_score = quality.get("total_score")
    if quality_score is not None and quality_score >= 10 and expected_return_pct is not None and expected_return_pct >= hurdle_rate:
        conviction = "high"
    elif quality_score is not None and quality_score >= 7 and expected_return_pct is not None and expected_return_pct > 0:
        conviction = "medium"
    else:
        conviction = "low"

    if current_price is None or weighted_target_price is None:
        zone = "incomplete"
    elif action_price is not None and current_price <= action_price and expected_return_pct is not None and expected_return_pct >= hurdle_rate:
        zone = "accumulate"
    elif trim_price is not None and current_price >= trim_price:
        zone = "trim_or_review"
    elif current_price <= weighted_target_price:
        zone = "hold_or_build_selectively"
    else:
        zone = "watch"

    if conviction == "high":
        size_band = "5-8% starter, core-position candidate"
        pacing = "Build in 2-3 tranches around the action zone."
    elif conviction == "medium":
        size_band = "3-5% starter"
        pacing = "Build in 3 tranches and wait for confirmation."
    else:
        size_band = "1-2% tracking position or wait"
        pacing = "Prefer waiting for a better price or stronger confirming data."

    result = {
        "current_price": current_price,
        "weighted_target_price": weighted_target_price,
        "expected_value_per_share": expected_value_per_share,
        "bear_target_price": bear_target_price,
        "bull_target_price": bull_target_price,
        "required_return": hurdle_rate,
        "action_price": action_price,
        "trim_price": trim_price,
        "expected_return_pct": expected_return_pct,
        "downside_pct": downside_pct,
        "risk_reward_ratio": risk_reward_ratio,
        "conviction": conviction,
        "zone": zone,
        "size_band": size_band,
        "pacing": pacing,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
