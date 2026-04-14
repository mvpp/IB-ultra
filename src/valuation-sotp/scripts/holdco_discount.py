#!/usr/bin/env python3
import argparse

from sotp_common import dump_json, get_num, load_json, safe_div


def main():
    parser = argparse.ArgumentParser(description="Apply a holdco discount to a SOTP valuation.")
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="holdco_discount.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    sotp = payload.get("sotp_output", {})
    config = payload.get("holdco_discount", {})
    central = payload.get("central_items", {})

    rate = float(
        config.get("rate")
        if config.get("rate") is not None
        else central.get("holdco_discount_rate")
        if central.get("holdco_discount_rate") is not None
        else 0.0
    )
    base = config.get("base") or central.get("holdco_discount_base") or "gross_equity_value_before_holdco"
    if base == "gross_segment_equity_value":
        discountable_low = get_num(sotp, "gross_segment_equity_value_low")
        discountable_mid = get_num(sotp, "gross_segment_equity_value_mid")
        discountable_high = get_num(sotp, "gross_segment_equity_value_high")
    else:
        discountable_low = get_num(sotp, "gross_equity_value_before_holdco_low")
        discountable_mid = get_num(sotp, "gross_equity_value_before_holdco_mid")
        discountable_high = get_num(sotp, "gross_equity_value_before_holdco_high")

    discounted_low = get_num(sotp, "gross_equity_value_before_holdco_low") - discountable_low * rate
    discounted_mid = get_num(sotp, "gross_equity_value_before_holdco_mid") - discountable_mid * rate
    discounted_high = get_num(sotp, "gross_equity_value_before_holdco_high") - discountable_high * rate
    diluted_shares = get_num(sotp, "current_diluted_shares")
    current_price = payload.get("market", {}).get("current_price")

    result = {
        "label": payload.get("label", "Holdco Discounted SOTP"),
        "holdco_discount_rate": rate,
        "holdco_discount_base": base,
        "discountable_value_low": discountable_low,
        "discountable_value_mid": discountable_mid,
        "discountable_value_high": discountable_high,
        "discount_amount_low": discountable_low * rate,
        "discount_amount_mid": discountable_mid * rate,
        "discount_amount_high": discountable_high * rate,
        "equity_value_low": discounted_low,
        "equity_value_mid": discounted_mid,
        "equity_value_high": discounted_high,
        "value_per_share_low": safe_div(discounted_low, diluted_shares, 0.0),
        "value_per_share": safe_div(discounted_mid, diluted_shares, 0.0),
        "value_per_share_high": safe_div(discounted_high, diluted_shares, 0.0),
        "upside_pct": (
            safe_div(safe_div(discounted_mid, diluted_shares, 0.0) - current_price, current_price)
            if current_price not in (None, 0, 0.0)
            else None
        ),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
