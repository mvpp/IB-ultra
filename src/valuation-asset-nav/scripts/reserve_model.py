#!/usr/bin/env python3
import argparse
from math import ceil

from asset_nav_common import diluted_shares_total, dump_json, get_num, load_json, safe_div


def first_value(*values):
    for value in values:
        if value is not None:
            return value
    return None


def sequence_value(values, index, default):
    if isinstance(values, list):
        if not values:
            return default
        if index < len(values):
            return float(values[index])
        return float(values[-1])
    if values is None:
        return default
    return float(values)


def development_capex_value(values, index):
    if isinstance(values, list):
        return sequence_value(values, index, 0.0)
    if values is None:
        return 0.0
    return float(values) if index == 0 else 0.0


def commodity_prices(deck, commodity, years):
    commodity_key = str(commodity or "default").lower()
    entry = deck.get(commodity_key)
    if entry is None:
        entry = deck.get("default", {})
    if isinstance(entry, list):
        prices = [float(value) for value in entry]
        if not prices:
            prices = [0.0]
        while len(prices) < years:
            prices.append(prices[-1])
        return prices[:years]
    if isinstance(entry, (int, float)):
        return [float(entry)] * years
    prices = entry.get("prices")
    if prices:
        prices = [float(value) for value in prices]
        while len(prices) < years:
            prices.append(prices[-1])
        return prices[:years]
    spot_price = float(first_value(entry.get("spot_price"), entry.get("price"), 0.0) or 0.0)
    growth = float(entry.get("price_growth", 0.0) or 0.0)
    output = []
    current = spot_price
    for _ in range(years):
        output.append(current)
        current *= 1.0 + growth
    return output


def build_production_forecast(asset):
    explicit = asset.get("production_forecast")
    if explicit:
        return [float(value) for value in explicit]

    reserves_units = max(get_num(asset, "reserves_units"), 0.0)
    annual_production = asset.get("annual_production")
    production_years = asset.get("production_years")
    decline_rate = float(asset.get("decline_rate", 0.0) or 0.0)

    if annual_production is None and production_years:
        annual_production = safe_div(reserves_units, float(production_years), 0.0)
    annual_production = float(annual_production or 0.0)

    if production_years is None and annual_production > 0:
        production_years = max(1, int(ceil(reserves_units / annual_production))) if reserves_units > 0 else 1
    production_years = int(production_years or 0)

    forecast = []
    remaining = reserves_units
    current = annual_production
    for _ in range(production_years):
        if remaining <= 0 and reserves_units > 0:
            break
        volume = current
        if reserves_units > 0:
            volume = min(volume, remaining)
            remaining -= volume
        forecast.append(float(volume))
        current *= max(0.0, 1.0 - decline_rate)
    return forecast


def main():
    parser = argparse.ArgumentParser(
        description="Build an asset-level reserve model for reserve-driven resource businesses."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="reserve_model.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    company = payload.get("company", {})
    assets = payload.get("assets", [])
    commodity_deck = payload.get("commodity_deck", {})
    balance_sheet = payload.get("balance_sheet", {})
    share_bridge = payload.get("share_bridge", {})
    market = payload.get("market", {})

    diluted_shares = (
        get_num(share_bridge, "diluted_shares")
        if share_bridge.get("diluted_shares") is not None
        else diluted_shares_total(share_bridge)
    )
    basic_shares = get_num(share_bridge, "basic_shares", diluted_shares)

    asset_rows = []
    total_reserves = 0.0
    total_year1_production = 0.0
    total_asset_npv = 0.0
    reserve_life_numerator = 0.0
    commodity_mix = {}

    for asset in assets:
        asset_name = asset.get("name")
        commodity = str(asset.get("commodity", "default")).lower()
        ownership_pct = float(asset.get("ownership_pct", 1.0) or 1.0)
        production = build_production_forecast(asset)
        years = len(production)
        prices = commodity_prices(commodity_deck, commodity, max(years, 1))
        price_realization = float(asset.get("price_realization", 1.0) or 1.0)
        unit_opex = asset.get("unit_operating_cost_forecast", asset.get("unit_operating_cost"))
        transport = asset.get("unit_transport_cost_forecast", asset.get("unit_transport_cost"))
        sustaining_capex = asset.get(
            "sustaining_capex_forecast",
            asset.get("sustaining_capex_per_unit", asset.get("sustaining_capex")),
        )
        development_capex = asset.get("development_capex_forecast", asset.get("development_capex"))
        royalty_rate = float(asset.get("royalty_rate", 0.0) or 0.0)
        tax_rate = float(asset.get("tax_rate", payload.get("tax_rate", 0.25)) or 0.0)
        discount_rate = float(asset.get("discount_rate", payload.get("discount_rate", 0.10)) or 0.10)
        abandonment_cost = float(asset.get("abandonment_cost", 0.0) or 0.0)
        asset_npv_override = asset.get("npv_override")

        forecast_rows = []
        revenue_pv = 0.0
        opex_pv = 0.0
        royalty_pv = 0.0
        sustaining_capex_pv = 0.0
        development_capex_pv = 0.0
        tax_pv = 0.0
        abandonment_pv = 0.0

        reserves_units = get_num(asset, "reserves_units")
        total_reserves += reserves_units * ownership_pct
        if production:
            total_year1_production += production[0] * ownership_pct
        commodity_mix[commodity] = commodity_mix.get(commodity, 0.0) + reserves_units * ownership_pct

        if asset_npv_override is not None:
            asset_npv = float(asset_npv_override)
        else:
            asset_npv = 0.0
            for index, volume in enumerate(production):
                realized_price = prices[index] * price_realization
                gross_revenue = volume * realized_price * ownership_pct
                royalty_cost = gross_revenue * royalty_rate
                operating_cost = volume * sequence_value(unit_opex, index, 0.0) * ownership_pct
                transport_cost = volume * sequence_value(transport, index, 0.0) * ownership_pct
                sustaining_cost = (
                    volume * sequence_value(sustaining_capex, index, 0.0) * ownership_pct
                    if not isinstance(sustaining_capex, list)
                    else sequence_value(sustaining_capex, index, 0.0) * ownership_pct
                )
                development_cost = development_capex_value(development_capex, index) * ownership_pct
                pretax_cash_flow = (
                    gross_revenue
                    - royalty_cost
                    - operating_cost
                    - transport_cost
                    - sustaining_cost
                    - development_cost
                )
                tax = max(pretax_cash_flow, 0.0) * tax_rate
                if index == years - 1 and abandonment_cost:
                    pretax_cash_flow -= abandonment_cost * ownership_pct
                    abandonment_pv += (abandonment_cost * ownership_pct) / ((1.0 + discount_rate) ** (index + 1))
                after_tax_cash_flow = pretax_cash_flow - tax
                discount_factor = (1.0 + discount_rate) ** (index + 1)
                discounted_cf = after_tax_cash_flow / discount_factor
                asset_npv += discounted_cf

                revenue_pv += gross_revenue / discount_factor
                opex_pv += (operating_cost + transport_cost) / discount_factor
                royalty_pv += royalty_cost / discount_factor
                sustaining_capex_pv += sustaining_cost / discount_factor
                development_capex_pv += development_cost / discount_factor
                tax_pv += tax / discount_factor

                forecast_rows.append(
                    {
                        "year": index + 1,
                        "production": float(volume),
                        "realized_price": realized_price,
                        "revenue": gross_revenue,
                        "royalty_cost": royalty_cost,
                        "operating_cost": operating_cost + transport_cost,
                        "sustaining_capex": sustaining_cost,
                        "development_capex": development_cost,
                        "pretax_cash_flow": pretax_cash_flow,
                        "tax": tax,
                        "after_tax_cash_flow": after_tax_cash_flow,
                        "discounted_after_tax_cash_flow": discounted_cf,
                    }
                )

        reserve_life_years = safe_div(reserves_units, production[0], None) if production and production[0] > 0 else None
        if reserve_life_years is not None and production:
            reserve_life_numerator += reserve_life_years * production[0] * ownership_pct

        total_asset_npv += asset_npv
        asset_rows.append(
            {
                "name": asset_name,
                "commodity": commodity,
                "ownership_pct": ownership_pct,
                "asset_type": asset.get("asset_type"),
                "reserves_units": reserves_units,
                "year1_production": production[0] * ownership_pct if production else 0.0,
                "production_years": len(production),
                "reserve_life_years": reserve_life_years,
                "discount_rate": discount_rate,
                "tax_rate": tax_rate,
                "revenue_pv": revenue_pv,
                "operating_cost_pv": opex_pv,
                "royalty_pv": royalty_pv,
                "sustaining_capex_pv": sustaining_capex_pv,
                "development_capex_pv": development_capex_pv,
                "tax_pv": tax_pv,
                "abandonment_pv": abandonment_pv,
                "asset_npv": asset_npv,
                "forecast": forecast_rows,
            }
        )

    weighted_reserve_life = (
        reserve_life_numerator / total_year1_production if total_year1_production not in (0, 0.0) else None
    )

    result = {
        "company": company,
        "assets": asset_rows,
        "summary": {
            "asset_count": len(asset_rows),
            "total_reserves_units": total_reserves,
            "year1_production": total_year1_production,
            "weighted_reserve_life_years": weighted_reserve_life,
            "total_asset_npv": total_asset_npv,
            "commodity_mix": commodity_mix,
        },
        "balance_sheet_bridge": {
            **balance_sheet,
            "cash": get_num(balance_sheet, "cash"),
            "debt": get_num(balance_sheet, "debt"),
            "preferred_equity": get_num(balance_sheet, "preferred_equity"),
            "minority_interest": get_num(balance_sheet, "minority_interest"),
            "other_assets": get_num(balance_sheet, "other_assets"),
            "other_liabilities": get_num(balance_sheet, "other_liabilities"),
            "hedging_value": get_num(balance_sheet, "hedging_value"),
            "non_core_asset_value": get_num(balance_sheet, "non_core_asset_value"),
            "asset_retirement_obligation": get_num(balance_sheet, "asset_retirement_obligation"),
            "holding_company_adjustment": get_num(balance_sheet, "holding_company_adjustment"),
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
