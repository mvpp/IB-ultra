#!/usr/bin/env python3
import argparse

from biotech_common import dump_json, get_num, load_json, safe_div


DEFAULT_SALES_CURVE = [0.15, 0.35, 0.55, 0.75, 0.90, 1.00]


def sales_factor(asset, year_index):
    curve = asset.get("sales_curve") or []
    if curve:
        if year_index < len(curve):
            return float(curve[year_index])
        return float(curve[-1])
    ramp_years = max(1, int(asset.get("ramp_years", 5) or 5))
    if year_index < len(DEFAULT_SALES_CURVE):
        return DEFAULT_SALES_CURVE[min(year_index, ramp_years - 1)]
    if year_index < ramp_years:
        return min(1.0, DEFAULT_SALES_CURVE[-1] + (year_index - len(DEFAULT_SALES_CURVE) + 1) * 0.05)
    return 1.0


def discount_factor(discount_rate, years_out):
    return (1.0 + discount_rate) ** years_out


def commercial_pv(asset, valuation_year):
    launch_year = int(asset.get("expected_launch_year", valuation_year))
    peak_sales = get_num(asset, "peak_sales")
    current_sales = get_num(asset, "current_sales")
    if peak_sales <= 0 and current_sales > 0:
        peak_sales = current_sales
    commercial_years = max(1, int(asset.get("commercial_years", 10) or 10))
    patent_expiry_year = asset.get("patent_expiry_year")
    discount_rate = get_num(asset, "discount_rate", 0.125)
    operating_margin = get_num(asset, "operating_margin", 0.65)
    tax_rate = get_num(asset, "tax_rate", 0.21)
    ownership_pct = get_num(asset, "ownership_pct", 1.0)
    royalty_rate = get_num(asset, "royalty_rate")
    economics_type = str(asset.get("economics_type", "owned")).lower()
    approved = asset.get("stage") == "approved" or asset.get("approval_status") == "approved"

    horizon_end = launch_year + commercial_years - 1
    if patent_expiry_year:
        horizon_end = min(horizon_end, int(patent_expiry_year))

    rows = []
    pv = 0.0
    for year in range(launch_year, horizon_end + 1):
        year_index = max(0, year - launch_year)
        if year <= valuation_year and current_sales > 0:
            revenue = current_sales
        elif approved and current_sales > 0:
            revenue = max(current_sales, peak_sales * sales_factor(asset, year_index))
        else:
            revenue = peak_sales * sales_factor(asset, year_index)
        if economics_type == "royalty":
            contribution = revenue * royalty_rate
        else:
            contribution = revenue * operating_margin * ownership_pct
            if economics_type == "profit_share":
                contribution = revenue * operating_margin * ownership_pct
        after_tax_cf = contribution * (1.0 - tax_rate)
        years_out = max(1, year - valuation_year)
        pv_cf = after_tax_cf / discount_factor(discount_rate, years_out)
        pv += pv_cf
        rows.append(
            {
                "year": year,
                "revenue": revenue,
                "contribution": contribution,
                "after_tax_cash_flow": after_tax_cf,
                "discounted_after_tax_cash_flow": pv_cf,
            }
        )
    return pv, rows


def development_cost_pv(asset, valuation_year):
    launch_year = int(asset.get("expected_launch_year", valuation_year))
    discount_rate = get_num(asset, "discount_rate", 0.125)
    remaining_rnd_cost = get_num(asset, "remaining_rnd_cost")
    milestone_costs = get_num(asset, "milestone_costs")
    schedule = asset.get("milestone_schedule", [])

    rows = []
    pv = 0.0
    years_remaining = max(1, launch_year - valuation_year)
    if remaining_rnd_cost > 0:
        annual = remaining_rnd_cost / years_remaining
        for offset in range(1, years_remaining + 1):
            year = valuation_year + offset
            discounted = annual / discount_factor(discount_rate, offset)
            pv += discounted
            rows.append({"year": year, "label": "R&D", "cost": annual, "discounted_cost": discounted})

    if schedule:
        for row in schedule:
            year = int(row.get("year") or (valuation_year + int(row.get("year_offset", 0))))
            amount = float(row.get("amount", 0.0))
            years_out = max(1, year - valuation_year)
            discounted = amount / discount_factor(discount_rate, years_out)
            pv += discounted
            rows.append({"year": year, "label": row.get("label", "Milestone"), "cost": amount, "discounted_cost": discounted})
    elif milestone_costs > 0:
        year = max(valuation_year + 1, launch_year - 1)
        years_out = max(1, year - valuation_year)
        discounted = milestone_costs / discount_factor(discount_rate, years_out)
        pv += discounted
        rows.append({"year": year, "label": "Milestones", "cost": milestone_costs, "discounted_cost": discounted})

    return pv, rows


def main():
    parser = argparse.ArgumentParser(description="Build an asset-level biotech rNPV output.")
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="pipeline_rnpv_output.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    registry = payload.get("pipeline_registry", {})
    valuation_year = int(registry.get("valuation_year") or payload.get("valuation_year"))
    balance_sheet = registry.get("balance_sheet_bridge", {})
    share_bridge = registry.get("share_bridge", {})
    market = payload.get("market", registry.get("market", {}))

    asset_rows = []
    total_rnpv = 0.0
    approved_asset_value = 0.0
    pipeline_asset_value = 0.0

    for asset in registry.get("assets", []):
        commercial_value, commercial_rows = commercial_pv(asset, valuation_year)
        dev_cost_value, dev_rows = development_cost_pv(asset, valuation_year)
        probability = float(asset.get("probability_of_success", 0.0))
        stage = asset.get("stage")
        approval_status = asset.get("approval_status")
        if stage == "approved" or approval_status == "approved":
            probability = 1.0

        risk_adjusted_value = commercial_value * probability - dev_cost_value
        total_rnpv += risk_adjusted_value
        if stage == "approved" or approval_status == "approved":
            approved_asset_value += risk_adjusted_value
        else:
            pipeline_asset_value += risk_adjusted_value

        asset_rows.append(
            {
                "asset_id": asset.get("asset_id"),
                "name": asset.get("name"),
                "indication": asset.get("indication"),
                "stage": stage,
                "approval_status": approval_status,
                "probability_of_success": probability,
                "launch_year": asset.get("expected_launch_year"),
                "discount_rate": get_num(asset, "discount_rate", 0.125),
                "peak_sales": get_num(asset, "peak_sales"),
                "current_sales": get_num(asset, "current_sales"),
                "commercial_value_pv": commercial_value,
                "development_cost_pv": dev_cost_value,
                "unrisked_value": commercial_value - dev_cost_value,
                "risk_adjusted_value": risk_adjusted_value,
                "commercial_forecast": commercial_rows,
                "development_costs": dev_rows,
            }
        )

    balance_sheet_adjustment = (
        get_num(balance_sheet, "cash")
        + get_num(balance_sheet, "marketable_securities")
        + get_num(balance_sheet, "other_assets")
        - get_num(balance_sheet, "debt")
        - get_num(balance_sheet, "other_liabilities")
    )
    equity_value = total_rnpv + balance_sheet_adjustment
    diluted_shares = get_num(share_bridge, "diluted_shares")
    implied_value_per_share = safe_div(equity_value, diluted_shares, 0.0)
    current_price = market.get("current_price")

    result = {
        "label": payload.get("label", "Pipeline rNPV"),
        "valuation_year": valuation_year,
        "assets": asset_rows,
        "approved_asset_value": approved_asset_value,
        "pipeline_asset_value": pipeline_asset_value,
        "total_rnpv": total_rnpv,
        "balance_sheet_adjustment_total": balance_sheet_adjustment,
        "equity_value": equity_value,
        "current_diluted_shares": diluted_shares,
        "implied_value_per_share": implied_value_per_share,
        "upside_pct": (
            safe_div(implied_value_per_share - current_price, current_price)
            if current_price not in (None, 0, 0.0)
            else None
        ),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
