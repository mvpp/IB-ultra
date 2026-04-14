#!/usr/bin/env python3
import argparse

from financials_common import diluted_shares_total, dump_json, get_num, load_json, safe_div


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Build a financial-sector valuation prep JSON from book value, capital, earnings, and share inputs. "
            "Supports banks, insurers, and specialty finance cases."
        )
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="financials_prep.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    company = payload.get("company", {})
    balance_sheet = payload.get("balance_sheet", {})
    capital = payload.get("capital", {})
    earnings = payload.get("earnings", {})
    share_bridge = payload.get("share_bridge", {})

    diluted_shares = (
        get_num(share_bridge, "diluted_shares")
        if share_bridge.get("diluted_shares") is not None
        else diluted_shares_total(share_bridge)
    )
    basic_shares = get_num(share_bridge, "basic_shares", diluted_shares)

    common_equity = get_num(balance_sheet, "common_equity")
    goodwill = get_num(balance_sheet, "goodwill")
    intangibles = get_num(balance_sheet, "intangibles")
    preferred_equity = get_num(balance_sheet, "preferred_equity")
    tangible_common_equity = (
        common_equity - goodwill - intangibles - preferred_equity
        if balance_sheet.get("tangible_common_equity") is None
        else get_num(balance_sheet, "tangible_common_equity")
    )
    book_value_per_share = safe_div(common_equity, diluted_shares)
    tangible_book_value_per_share = safe_div(tangible_common_equity, diluted_shares)

    regulatory_minimum = (
        capital.get("regulatory_minimum_cet1")
        or capital.get("regulatory_minimum_tier1")
        or capital.get("regulatory_minimum_capital")
    )
    reported_capital_ratio = (
        capital.get("cet1_ratio")
        or capital.get("tier1_ratio")
        or capital.get("total_capital_ratio")
    )
    rwa = capital.get("risk_weighted_assets")
    excess_capital_pct = (
        reported_capital_ratio - regulatory_minimum
        if None not in (reported_capital_ratio, regulatory_minimum)
        else None
    )
    excess_capital_amount = (
        excess_capital_pct * float(rwa)
        if rwa is not None and excess_capital_pct is not None and excess_capital_pct > 0
        else 0.0
    )
    excess_capital_per_share = safe_div(excess_capital_amount, diluted_shares, 0.0)

    net_income_ltm = get_num(earnings, "net_income_ltm")
    normalized_net_income = (
        get_num(earnings, "normalized_net_income")
        if earnings.get("normalized_net_income") is not None
        else net_income_ltm
    )
    average_common_equity = (
        earnings.get("average_common_equity")
        if earnings.get("average_common_equity") is not None
        else common_equity
    )
    average_tangible_common_equity = (
        earnings.get("average_tangible_common_equity")
        if earnings.get("average_tangible_common_equity") is not None
        else tangible_common_equity
    )
    normalized_roe = (
        safe_div(normalized_net_income, float(average_common_equity))
        if average_common_equity not in (None, 0, 0.0)
        else earnings.get("normalized_roe")
    )
    normalized_rotce = (
        safe_div(normalized_net_income, float(average_tangible_common_equity))
        if average_tangible_common_equity not in (None, 0, 0.0)
        else earnings.get("normalized_rotce")
    )
    payout_ratio = (
        safe_div(get_num(earnings, "dividends_ltm"), normalized_net_income)
        if earnings.get("payout_ratio") is None and normalized_net_income not in (0, 0.0)
        else earnings.get("payout_ratio")
    )

    result = {
        "company": company,
        "book_bridge": {
            "common_equity": common_equity,
            "goodwill": goodwill,
            "intangibles": intangibles,
            "preferred_equity": preferred_equity,
            "tangible_common_equity": tangible_common_equity,
            "book_value_per_share": book_value_per_share,
            "tangible_book_value_per_share": tangible_book_value_per_share,
        },
        "capital": {
            **capital,
            "reported_capital_ratio": reported_capital_ratio,
            "regulatory_minimum": regulatory_minimum,
            "excess_capital_pct": excess_capital_pct,
            "excess_capital_amount": excess_capital_amount,
            "excess_capital_per_share": excess_capital_per_share,
        },
        "earnings": {
            **earnings,
            "net_income_ltm": net_income_ltm,
            "normalized_net_income": normalized_net_income,
            "normalized_roe": normalized_roe,
            "normalized_rotce": normalized_rotce,
            "payout_ratio": payout_ratio,
        },
        "share_bridge": {
            **share_bridge,
            "basic_shares": basic_shares,
            "diluted_shares": diluted_shares,
        },
        "market": payload.get("market", {}),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
