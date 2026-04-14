#!/usr/bin/env python3
import argparse

from regulated_common import diluted_shares_total, dump_json, get_num, load_json, safe_div


def first_value(*values):
    for value in values:
        if value is not None:
            return value
    return None


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Build a regulated-assets valuation bridge from rate base, allowed-return, capital, "
            "earnings, and share data."
        )
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="regulatory_bridge.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    company = payload.get("company", {})
    regulatory = payload.get("regulatory", {})
    capital = payload.get("capital", {})
    earnings = payload.get("earnings", {})
    balance_sheet = payload.get("balance_sheet", {})
    share_bridge = payload.get("share_bridge", {})
    market = payload.get("market", {})

    diluted_shares = (
        get_num(share_bridge, "diluted_shares")
        if share_bridge.get("diluted_shares") is not None
        else diluted_shares_total(share_bridge)
    )
    basic_shares = get_num(share_bridge, "basic_shares", diluted_shares)

    opening_rate_base = first_value(
        regulatory.get("opening_rate_base"),
        regulatory.get("rate_base_opening"),
        capital.get("opening_rate_base"),
        capital.get("rate_base_opening"),
    )
    opening_rate_base = float(opening_rate_base or 0.0)

    capex_additions = first_value(
        regulatory.get("capex_additions"),
        regulatory.get("rate_base_additions"),
        capital.get("rate_base_additions"),
        capital.get("capex_ltm"),
    )
    capex_additions = float(capex_additions or 0.0)

    depreciation = first_value(
        regulatory.get("depreciation"),
        capital.get("regulated_depreciation"),
        capital.get("depreciation_ltm"),
    )
    depreciation = float(depreciation or 0.0)

    retirements = get_num(regulatory, "asset_retirements")
    acquired_assets = get_num(regulatory, "acquired_assets")
    regulatory_asset_net = get_num(regulatory, "regulatory_assets") - get_num(
        regulatory, "regulatory_liabilities"
    )

    reported_closing_rate_base = first_value(
        regulatory.get("closing_rate_base"),
        regulatory.get("rate_base_closing"),
        capital.get("closing_rate_base"),
        capital.get("rate_base_closing"),
    )
    derived_closing_rate_base = (
        opening_rate_base
        + capex_additions
        + acquired_assets
        + regulatory_asset_net
        - depreciation
        - retirements
    )
    closing_rate_base = float(
        reported_closing_rate_base
        if reported_closing_rate_base is not None
        else derived_closing_rate_base
    )
    average_rate_base = first_value(
        regulatory.get("average_rate_base"),
        (opening_rate_base + closing_rate_base) / 2.0,
    )
    average_rate_base = float(average_rate_base or 0.0)

    equity_ratio_input = regulatory.get("equity_ratio")
    debt_ratio_input = regulatory.get("debt_ratio")
    if equity_ratio_input is None and debt_ratio_input is None:
        equity_ratio = 0.50
        debt_ratio = 0.50
    elif equity_ratio_input is None:
        debt_ratio = float(debt_ratio_input)
        equity_ratio = 1.0 - debt_ratio
    elif debt_ratio_input is None:
        equity_ratio = float(equity_ratio_input)
        debt_ratio = 1.0 - equity_ratio
    else:
        equity_ratio = float(equity_ratio_input)
        debt_ratio = float(debt_ratio_input)

    allowed_roe = float(first_value(regulatory.get("allowed_roe"), market.get("allowed_roe")) or 0.0)
    cost_of_debt = float(
        first_value(regulatory.get("cost_of_debt"), capital.get("cost_of_debt"), market.get("cost_of_debt"))
        or 0.0
    )
    tax_rate = float(first_value(regulatory.get("tax_rate"), capital.get("tax_rate"), 0.25) or 0.0)
    after_tax_cost_of_debt = cost_of_debt * (1.0 - tax_rate)
    allowed_wacc = first_value(
        regulatory.get("allowed_wacc"),
        equity_ratio * allowed_roe + debt_ratio * after_tax_cost_of_debt,
    )
    allowed_wacc = float(allowed_wacc or 0.0)

    regulatory_equity_base = closing_rate_base * equity_ratio
    average_equity_base = average_rate_base * equity_ratio
    allowed_equity_earnings = average_equity_base * allowed_roe
    allowed_debt_return = average_rate_base * debt_ratio * after_tax_cost_of_debt
    allowed_total_return = average_rate_base * allowed_wacc
    rate_base_growth = safe_div(closing_rate_base - opening_rate_base, opening_rate_base)

    non_regulated_earnings = get_num(earnings, "non_regulated_earnings")
    holdco_costs = get_num(earnings, "holdco_costs")
    regulatory_true_up = get_num(earnings, "regulatory_true_up")
    normalized_net_income = (
        float(earnings["normalized_net_income"])
        if earnings.get("normalized_net_income") is not None
        else allowed_equity_earnings + non_regulated_earnings - holdco_costs + regulatory_true_up
    )
    normalized_eps = (
        float(earnings["normalized_eps"])
        if earnings.get("normalized_eps") is not None
        else safe_div(normalized_net_income, diluted_shares, 0.0)
    )

    payout_ratio_target = first_value(
        earnings.get("payout_ratio_target"),
        regulatory.get("payout_ratio_target"),
        capital.get("payout_ratio_target"),
    )
    dividend_per_share = earnings.get("dividend_per_share_ltm")
    dividends_total = earnings.get("dividends_total_ltm")
    if dividend_per_share is None and dividends_total is not None and diluted_shares:
        dividend_per_share = float(dividends_total) / diluted_shares
    if dividends_total is None and dividend_per_share is not None and diluted_shares:
        dividends_total = float(dividend_per_share) * diluted_shares
    if dividend_per_share is None and payout_ratio_target is not None and normalized_eps is not None:
        dividend_per_share = float(payout_ratio_target) * float(normalized_eps)
        dividends_total = dividend_per_share * diluted_shares

    payout_ratio = (
        float(earnings["payout_ratio"])
        if earnings.get("payout_ratio") is not None
        else safe_div(dividends_total, normalized_net_income)
    )
    dividend_coverage = (
        float(earnings["dividend_coverage"])
        if earnings.get("dividend_coverage") is not None
        else safe_div(normalized_net_income, dividends_total)
    )

    cash = get_num(balance_sheet, "cash")
    excess_cash = first_value(balance_sheet.get("excess_cash"), balance_sheet.get("cash"), 0.0)
    excess_cash = float(excess_cash or 0.0)
    total_debt = get_num(balance_sheet, "debt")
    holdco_debt = get_num(balance_sheet, "holdco_debt")
    regulated_debt = first_value(balance_sheet.get("regulated_debt"), total_debt - holdco_debt)
    regulated_debt = max(float(regulated_debt or 0.0), 0.0)
    preferred_equity = get_num(balance_sheet, "preferred_equity")
    minority_interest = get_num(balance_sheet, "minority_interest")
    other_assets = get_num(balance_sheet, "other_assets")
    other_liabilities = get_num(balance_sheet, "other_liabilities")
    non_regulated_value = get_num(balance_sheet, "non_regulated_value")
    holding_company_adjustment = get_num(balance_sheet, "holding_company_adjustment")

    result = {
        "company": company,
        "regulatory_rollforward": {
            "opening_rate_base": opening_rate_base,
            "capex_additions": capex_additions,
            "acquired_assets": acquired_assets,
            "regulatory_asset_net": regulatory_asset_net,
            "depreciation": depreciation,
            "asset_retirements": retirements,
            "derived_closing_rate_base": derived_closing_rate_base,
            "closing_rate_base": closing_rate_base,
            "average_rate_base": average_rate_base,
            "rate_base_growth": rate_base_growth,
        },
        "returns_bridge": {
            "allowed_roe": allowed_roe,
            "equity_ratio": equity_ratio,
            "debt_ratio": debt_ratio,
            "cost_of_debt": cost_of_debt,
            "after_tax_cost_of_debt": after_tax_cost_of_debt,
            "tax_rate": tax_rate,
            "allowed_wacc": allowed_wacc,
            "regulatory_equity_base": regulatory_equity_base,
            "average_equity_base": average_equity_base,
            "allowed_equity_earnings": allowed_equity_earnings,
            "allowed_debt_return": allowed_debt_return,
            "allowed_total_return": allowed_total_return,
            "regulatory_lag_months": get_num(regulatory, "regulatory_lag_months"),
        },
        "earnings_bridge": {
            **earnings,
            "normalized_net_income": normalized_net_income,
            "normalized_eps": normalized_eps,
            "dividend_per_share_ltm": dividend_per_share,
            "dividends_total_ltm": dividends_total,
            "payout_ratio": payout_ratio,
            "dividend_coverage": dividend_coverage,
            "non_regulated_earnings": non_regulated_earnings,
            "holdco_costs": holdco_costs,
            "regulatory_true_up": regulatory_true_up,
        },
        "balance_sheet_bridge": {
            **balance_sheet,
            "cash": cash,
            "excess_cash": excess_cash,
            "total_debt": total_debt,
            "regulated_debt": regulated_debt,
            "holdco_debt": holdco_debt,
            "preferred_equity": preferred_equity,
            "minority_interest": minority_interest,
            "other_assets": other_assets,
            "other_liabilities": other_liabilities,
            "non_regulated_value": non_regulated_value,
            "holding_company_adjustment": holding_company_adjustment,
            "net_debt": total_debt - cash,
        },
        "share_bridge": {
            **share_bridge,
            "basic_shares": basic_shares,
            "diluted_shares": diluted_shares,
        },
        "market": market,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
