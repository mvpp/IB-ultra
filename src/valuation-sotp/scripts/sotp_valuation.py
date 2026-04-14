#!/usr/bin/env python3
import argparse

from sotp_common import dump_json, get_num, load_json, safe_div


def route_index(payload):
    return {row.get("name"): row for row in payload.get("segment_method_map", [])}


def multiple_range(route):
    selected = route.get("selected_multiple")
    low = route.get("low_multiple", selected)
    high = route.get("high_multiple", selected)
    return low, selected, high


def equity_values(segment, route):
    method = route.get("method")
    metric = route.get("metric_value")
    net_debt = get_num(segment, "net_debt")
    minority_interest = get_num(segment, "minority_interest")

    if method in {"ev_ebitda", "ev_ebit", "ev_sales"}:
        low_mult, mid_mult, high_mult = multiple_range(route)
        low_ev = float(metric or 0.0) * float(low_mult or 0.0)
        mid_ev = float(metric or 0.0) * float(mid_mult or 0.0)
        high_ev = float(metric or 0.0) * float(high_mult or 0.0)
        return (
            low_ev - net_debt - minority_interest,
            mid_ev - net_debt - minority_interest,
            high_ev - net_debt - minority_interest,
            "enterprise_value",
        )

    if method in {"pe", "pb"}:
        low_mult, mid_mult, high_mult = multiple_range(route)
        metric_value = float(metric or 0.0)
        return (
            metric_value * float(low_mult or 0.0),
            metric_value * float(mid_mult or 0.0),
            metric_value * float(high_mult or 0.0),
            "equity_value",
        )

    if method == "direct_enterprise_value":
        low_ev = segment.get("low_enterprise_value") or route.get("low_enterprise_value") or segment.get("direct_enterprise_value")
        mid_ev = segment.get("direct_enterprise_value") or route.get("metric_value") or 0.0
        high_ev = segment.get("high_enterprise_value") or route.get("high_enterprise_value") or mid_ev
        return (
            float(low_ev or 0.0) - net_debt - minority_interest,
            float(mid_ev or 0.0) - net_debt - minority_interest,
            float(high_ev or 0.0) - net_debt - minority_interest,
            "enterprise_value",
        )

    low_eq = segment.get("low_equity_value") or segment.get("direct_equity_value") or segment.get("asset_nav") or 0.0
    mid_eq = segment.get("direct_equity_value") or segment.get("asset_nav") or route.get("metric_value") or 0.0
    high_eq = segment.get("high_equity_value") or segment.get("direct_equity_value") or segment.get("asset_nav") or mid_eq
    return float(low_eq), float(mid_eq), float(high_eq), "equity_value"


def main():
    parser = argparse.ArgumentParser(description="Build a sum-of-the-parts valuation from normalized segments.")
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="sotp_output.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    normalized = payload.get("segment_normalizer", {})
    router = payload.get("segment_method_router", {})
    routes = route_index(router)

    segment_rows = []
    total_low = 0.0
    total_mid = 0.0
    total_high = 0.0

    for segment in normalized.get("segments", []):
        route = routes.get(segment.get("name"), {})
        low_eq, mid_eq, high_eq, value_type = equity_values(segment, route)
        ownership_pct = float(segment.get("ownership_pct", 1.0) or 1.0)
        low_adj = low_eq * ownership_pct
        mid_adj = mid_eq * ownership_pct
        high_adj = high_eq * ownership_pct
        total_low += low_adj
        total_mid += mid_adj
        total_high += high_adj
        segment_rows.append(
            {
                "name": segment.get("name"),
                "segment_family": segment.get("segment_family"),
                "method": route.get("method"),
                "metric_name": route.get("metric_name"),
                "metric_value": route.get("metric_value"),
                "value_type": value_type,
                "ownership_pct": ownership_pct,
                "equity_value_low": low_eq,
                "equity_value_mid": mid_eq,
                "equity_value_high": high_eq,
                "ownership_adjusted_equity_value_low": low_adj,
                "ownership_adjusted_equity_value_mid": mid_adj,
                "ownership_adjusted_equity_value_high": high_adj,
            }
        )

    central = normalized.get("central_items", {})
    central_adjustment = (
        get_num(central, "cash")
        + get_num(central, "investments")
        + get_num(central, "other_adjustments")
        - get_num(central, "debt")
        - get_num(central, "pensions")
        - get_num(central, "preferred")
        - get_num(central, "minority_interest")
    )
    gross_low = total_low + central_adjustment
    gross_mid = total_mid + central_adjustment
    gross_high = total_high + central_adjustment

    diluted_shares = get_num(normalized.get("share_bridge", {}), "diluted_shares")
    current_price = normalized.get("market", {}).get("current_price")

    result = {
        "label": payload.get("label", "SOTP"),
        "company": normalized.get("company", {}),
        "segments": segment_rows,
        "gross_segment_equity_value_low": total_low,
        "gross_segment_equity_value_mid": total_mid,
        "gross_segment_equity_value_high": total_high,
        "central_adjustment_total": central_adjustment,
        "gross_equity_value_before_holdco_low": gross_low,
        "gross_equity_value_before_holdco_mid": gross_mid,
        "gross_equity_value_before_holdco_high": gross_high,
        "current_diluted_shares": diluted_shares,
        "implied_value_per_share_low": safe_div(gross_low, diluted_shares, 0.0),
        "implied_value_per_share": safe_div(gross_mid, diluted_shares, 0.0),
        "implied_value_per_share_high": safe_div(gross_high, diluted_shares, 0.0),
        "upside_pct": (
            safe_div(safe_div(gross_mid, diluted_shares, 0.0) - current_price, current_price)
            if current_price not in (None, 0, 0.0)
            else None
        ),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
