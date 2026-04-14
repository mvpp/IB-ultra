#!/usr/bin/env python3
import argparse

from sotp_common import dump_json, get_num, load_json


def route_method(segment):
    explicit = segment.get("method_hint")
    if explicit:
        return str(explicit).strip().lower().replace("/", "_").replace("-", "_")

    family = str(segment.get("segment_family", "operating")).strip().lower()
    if family in {"bank", "insurance", "financials", "specialty_finance"}:
        return "pb"
    if family in {"reit", "property", "real_estate"}:
        return "direct_equity_value"
    if family in {"biotech", "pharma_pipeline"}:
        return "direct_equity_value"
    if family in {"regulated", "utility", "regulated_assets"}:
        return "ev_ebit"
    if family in {"asset_nav", "ep", "mining", "resource"}:
        return "direct_equity_value"
    if get_num(segment, "ebitda") > 0:
        return "ev_ebitda"
    if get_num(segment, "ebit") > 0:
        return "ev_ebit"
    if get_num(segment, "net_income") > 0:
        return "pe"
    if get_num(segment, "revenue") > 0:
        return "ev_sales"
    return "direct_equity_value"


def metric_for_method(segment, method):
    if method == "ev_ebitda":
        return "ebitda", get_num(segment, "ebitda")
    if method == "ev_ebit":
        return "ebit", get_num(segment, "ebit")
    if method == "ev_sales":
        return "revenue", get_num(segment, "revenue")
    if method == "pe":
        return "net_income", get_num(segment, "net_income")
    if method == "pb":
        tangible_book = get_num(segment, "tangible_book_value")
        if tangible_book > 0:
            return "tangible_book_value", tangible_book
        return "book_value", get_num(segment, "book_value")
    if method == "direct_enterprise_value":
        return "direct_enterprise_value", segment.get("direct_enterprise_value")
    return "direct_equity_value", (
        segment.get("direct_equity_value")
        or segment.get("asset_nav")
        or segment.get("direct_enterprise_value")
    )


def main():
    parser = argparse.ArgumentParser(description="Route SOTP segments to valuation methods.")
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="segment_method_router.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    routes = []
    for segment in payload.get("segments", []):
        method = route_method(segment)
        metric_name, metric_value = metric_for_method(segment, method)
        routes.append(
            {
                "name": segment.get("name"),
                "segment_family": segment.get("segment_family"),
                "method": method,
                "metric_name": metric_name,
                "metric_value": metric_value,
                "selected_multiple": segment.get("selected_multiple"),
                "low_multiple": segment.get("low_multiple"),
                "high_multiple": segment.get("high_multiple"),
                "reason": segment.get("method_hint") or f"family:{segment.get('segment_family')}",
            }
        )

    result = {
        "company": payload.get("company", {}),
        "segment_method_map": routes,
        "central_items": payload.get("central_items", {}),
        "share_bridge": payload.get("share_bridge", {}),
        "market": payload.get("market", {}),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
