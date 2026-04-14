#!/usr/bin/env python3
import argparse

from reit_common import diluted_shares_total, dump_json, get_num, load_json, safe_div


DEVELOPMENT_STATUSES = {"development", "pipeline", "under_construction", "redevelopment"}


def property_market_value(row):
    status = str(row.get("status", "stabilized")).strip().lower()
    ownership_pct = float(row.get("ownership_pct", 1.0))
    explicit_market_value = row.get("market_value")
    estimated_market_value = row.get("estimated_market_value")
    development_cost = get_num(row, "development_cost")
    stabilized_noi = row.get("stabilized_noi")
    annual_noi = row.get("annual_noi")
    cap_rate = row.get("cap_rate")

    if explicit_market_value is not None:
        base_value = float(explicit_market_value)
    elif status in DEVELOPMENT_STATUSES:
        if estimated_market_value is not None:
            base_value = float(estimated_market_value)
        elif development_cost > 0:
            base_value = development_cost
        else:
            base_value = None
    else:
        noi = stabilized_noi if stabilized_noi is not None else annual_noi
        if noi is not None and cap_rate not in (None, 0, 0.0):
            base_value = float(noi) / float(cap_rate)
        else:
            base_value = None

    owned_value = base_value * ownership_pct if base_value is not None else None
    return base_value, owned_value


def compute_ffo(earnings):
    if earnings.get("normalized_ffo") is not None:
        return get_num(earnings, "normalized_ffo")
    if earnings.get("ffo") is not None:
        return get_num(earnings, "ffo")
    return (
        get_num(earnings, "net_income_ltm")
        + get_num(earnings, "real_estate_depreciation")
        + get_num(earnings, "impairment_addback")
        + get_num(earnings, "loss_on_sale_addback")
        - get_num(earnings, "gain_on_sale")
        - get_num(earnings, "preferred_dividends")
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Build a REIT/property valuation bridge from property rolls, earnings, leverage, and share data."
        )
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="property_bridge.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    company = payload.get("company", {})
    properties = payload.get("properties", [])
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

    processed_properties = []
    stabilized_noi_total = 0.0
    stabilized_value_total = 0.0
    development_value_total = 0.0
    occupancy_weight = 0.0
    occupancy_value = 0.0
    stabilized_asset_count = 0
    development_asset_count = 0

    for row in properties:
        status = str(row.get("status", "stabilized")).strip().lower()
        ownership_pct = float(row.get("ownership_pct", 1.0))
        annual_noi = row.get("annual_noi")
        stabilized_noi = row.get("stabilized_noi", annual_noi)
        occupancy = row.get("occupancy")
        cap_rate = row.get("cap_rate")
        base_value, owned_value = property_market_value(row)

        weight = owned_value if owned_value not in (None, 0, 0.0) else (
            float(stabilized_noi) * ownership_pct if stabilized_noi not in (None, 0, 0.0) else ownership_pct
        )
        if occupancy is not None:
            occupancy_weight += weight
            occupancy_value += weight * float(occupancy)

        processed = {
            "name": row.get("name"),
            "type": row.get("type"),
            "status": status,
            "ownership_pct": ownership_pct,
            "annual_noi": None if annual_noi is None else float(annual_noi),
            "stabilized_noi": None if stabilized_noi is None else float(stabilized_noi),
            "occupancy": None if occupancy is None else float(occupancy),
            "cap_rate": None if cap_rate is None else float(cap_rate),
            "market_value": base_value,
            "owned_market_value": owned_value,
            "development_cost": get_num(row, "development_cost"),
        }
        processed_properties.append(processed)

        if status in DEVELOPMENT_STATUSES:
            development_asset_count += 1
            development_value_total += float(owned_value or 0.0)
        else:
            stabilized_asset_count += 1
            stabilized_noi_total += float(stabilized_noi or 0.0) * ownership_pct
            stabilized_value_total += float(owned_value or 0.0)

    weighted_occupancy = safe_div(occupancy_value, occupancy_weight)
    same_store_noi_growth = (
        earnings.get("same_store_noi_growth")
        if earnings.get("same_store_noi_growth") is not None
        else capital.get("same_store_noi_growth")
    )

    recurring_capex = (
        get_num(earnings, "normalized_affo_adjustments")
        if earnings.get("recurring_capex") is None and earnings.get("normalized_affo") is not None
        else get_num(earnings, "recurring_capex")
    )
    if recurring_capex == 0.0:
        recurring_capex = get_num(earnings, "maintenance_capex") + get_num(earnings, "leasing_costs")

    normalized_ffo = compute_ffo(earnings)
    normalized_affo = (
        get_num(earnings, "normalized_affo")
        if earnings.get("normalized_affo") is not None
        else normalized_ffo
        - recurring_capex
        - get_num(earnings, "straight_line_rent_adjustment")
    )

    cash = get_num(balance_sheet, "cash")
    restricted_cash = get_num(balance_sheet, "restricted_cash")
    include_restricted_cash = bool(balance_sheet.get("include_restricted_cash_in_nav", False))
    debt = get_num(balance_sheet, "debt")
    preferred_equity = get_num(balance_sheet, "preferred_equity")
    minority_interest = get_num(balance_sheet, "minority_interest")
    other_assets = get_num(balance_sheet, "other_assets")
    other_liabilities = get_num(balance_sheet, "other_liabilities")
    jv_value = get_num(capital, "jv_value")
    other_real_estate_value = get_num(capital, "other_real_estate_value")

    gross_asset_value = stabilized_value_total + development_value_total + jv_value + other_real_estate_value
    available_cash = cash + (restricted_cash if include_restricted_cash else 0.0)
    net_debt = debt - available_cash
    liquidity_sources = cash + get_num(capital, "revolver_availability")

    result = {
        "company": company,
        "properties": processed_properties,
        "property_rollup": {
            "property_count": len(processed_properties),
            "stabilized_asset_count": stabilized_asset_count,
            "development_asset_count": development_asset_count,
            "stabilized_noi": stabilized_noi_total,
            "weighted_occupancy": weighted_occupancy,
            "same_store_noi_growth": same_store_noi_growth,
            "stabilized_value": stabilized_value_total,
            "development_value": development_value_total,
            "jv_value": jv_value,
            "other_real_estate_value": other_real_estate_value,
            "gross_asset_value": gross_asset_value,
        },
        "earnings_bridge": {
            **earnings,
            "normalized_ffo": normalized_ffo,
            "normalized_affo": normalized_affo,
            "recurring_capex": recurring_capex,
            "ffo_per_share": safe_div(normalized_ffo, diluted_shares),
            "affo_per_share": safe_div(normalized_affo, diluted_shares),
        },
        "balance_sheet_bridge": {
            **balance_sheet,
            "cash": cash,
            "restricted_cash": restricted_cash,
            "available_cash": available_cash,
            "debt": debt,
            "preferred_equity": preferred_equity,
            "minority_interest": minority_interest,
            "other_assets": other_assets,
            "other_liabilities": other_liabilities,
            "net_debt": net_debt,
            "debt_maturities_next_24m": get_num(capital, "debt_maturities_next_24m"),
            "liquidity_sources": liquidity_sources,
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
