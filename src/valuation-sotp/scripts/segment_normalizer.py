#!/usr/bin/env python3
import argparse

from sotp_common import dump_json, get_num, load_json, safe_div


def normalized_segment(row):
    revenue = get_num(row, "revenue")
    ebitda = get_num(row, "ebitda")
    ebit = get_num(row, "ebit")
    net_income = get_num(row, "net_income")
    book_value = get_num(row, "book_value")
    tangible_book_value = get_num(row, "tangible_book_value", book_value)
    ownership_pct = float(row.get("ownership_pct", 1.0) or 1.0)

    return {
        "name": row.get("name"),
        "segment_family": row.get("segment_family") or row.get("segment_type") or "operating",
        "description": row.get("description"),
        "ownership_pct": ownership_pct,
        "revenue": revenue,
        "ebitda": ebitda,
        "ebit": ebit,
        "net_income": net_income,
        "book_value": book_value,
        "tangible_book_value": tangible_book_value,
        "asset_nav": get_num(row, "asset_nav"),
        "direct_equity_value": row.get("direct_equity_value"),
        "direct_enterprise_value": row.get("direct_enterprise_value"),
        "net_debt": get_num(row, "net_debt"),
        "minority_interest": get_num(row, "minority_interest"),
        "method_hint": row.get("valuation_method") or row.get("method_hint"),
        "selected_multiple": row.get("selected_multiple"),
        "low_multiple": row.get("low_multiple"),
        "high_multiple": row.get("high_multiple"),
        "low_equity_value": row.get("low_equity_value"),
        "high_equity_value": row.get("high_equity_value"),
        "low_enterprise_value": row.get("low_enterprise_value"),
        "high_enterprise_value": row.get("high_enterprise_value"),
        "revenue_margin": safe_div(ebit, revenue),
        "ebitda_margin": safe_div(ebitda, revenue),
        "net_margin": safe_div(net_income, revenue),
    }


def consolidated_tie_out(consolidated, segments):
    if not consolidated:
        return {}

    totals = {
        "revenue": sum(row.get("revenue", 0.0) for row in segments),
        "ebitda": sum(row.get("ebitda", 0.0) for row in segments),
        "ebit": sum(row.get("ebit", 0.0) for row in segments),
        "net_income": sum(row.get("net_income", 0.0) for row in segments),
    }
    result = {}
    for key, segment_total in totals.items():
        consolidated_value = consolidated.get(key)
        if consolidated_value is None:
            continue
        consolidated_value = float(consolidated_value)
        result[key] = {
            "segment_total": segment_total,
            "consolidated_total": consolidated_value,
            "gap": segment_total - consolidated_value,
            "gap_pct": safe_div(segment_total - consolidated_value, consolidated_value),
        }
    return result


def main():
    parser = argparse.ArgumentParser(description="Normalize segment disclosures for SOTP valuation.")
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="segment_normalizer.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    segments = [normalized_segment(row) for row in payload.get("segments", [])]
    consolidated = payload.get("consolidated", {})
    central_items = payload.get("central_items", {})
    share_bridge = payload.get("share_bridge", {})
    market = payload.get("market", {})

    result = {
        "company": payload.get("company", {}),
        "segments": segments,
        "segment_count": len(segments),
        "consolidated": consolidated,
        "tie_out": consolidated_tie_out(consolidated, segments),
        "central_items": {
            "cash": get_num(central_items, "cash"),
            "debt": get_num(central_items, "debt"),
            "investments": get_num(central_items, "investments"),
            "pensions": get_num(central_items, "pensions"),
            "preferred": get_num(central_items, "preferred"),
            "minority_interest": get_num(central_items, "minority_interest"),
            "other_adjustments": get_num(central_items, "other_adjustments"),
            "holdco_discount_rate": get_num(central_items, "holdco_discount_rate"),
            "holdco_discount_base": central_items.get("holdco_discount_base") or "gross_equity_value_before_holdco",
        },
        "share_bridge": {
            "basic_shares": get_num(share_bridge, "basic_shares"),
            "diluted_shares": get_num(share_bridge, "diluted_shares"),
        },
        "market": {"current_price": market.get("current_price")},
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
