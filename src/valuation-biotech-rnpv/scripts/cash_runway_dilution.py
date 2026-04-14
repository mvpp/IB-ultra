#!/usr/bin/env python3
import argparse

from biotech_common import dump_json, get_num, load_json, safe_div


def main():
    parser = argparse.ArgumentParser(
        description="Estimate biotech cash runway, financing need, and dilution."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="cash_runway_dilution.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    registry = payload.get("pipeline_registry", {})
    config = payload.get("cash_runway_dilution", payload.get("method", {}))
    valuation_year = int(registry.get("valuation_year") or payload.get("valuation_year"))
    balance_sheet = registry.get("balance_sheet_bridge", {})
    cash_flow = registry.get("cash_flow_bridge", {})
    share_bridge = registry.get("share_bridge", {})
    market = payload.get("market", registry.get("market", {}))

    liquidity = get_num(balance_sheet, "liquidity")
    debt = get_num(balance_sheet, "debt")
    annual_cash_burn = get_num(cash_flow, "annual_cash_burn")
    runway_months = cash_flow.get("runway_months")
    if runway_months is None:
        runway_months = safe_div(liquidity, safe_div(annual_cash_burn, 12.0, None))

    buffer_months = float(config.get("minimum_cash_buffer_months", 12.0))
    next_inflection_years = [
        int(asset.get("next_value_inflection_year"))
        for asset in registry.get("assets", [])
        if asset.get("next_value_inflection_year") is not None and asset.get("stage") != "approved"
    ]
    next_inflection_year = min(next_inflection_years) if next_inflection_years else valuation_year + 1
    years_to_inflection = max(0, next_inflection_year - valuation_year)
    required_liquidity = annual_cash_burn * years_to_inflection + annual_cash_burn * (buffer_months / 12.0)
    financing_shortfall = max(0.0, required_liquidity - liquidity)

    current_price = market.get("current_price")
    raise_discount = float(config.get("raise_discount", 0.15) or 0.15)
    raise_price = float(config.get("raise_price") or (current_price * (1.0 - raise_discount) if current_price else 0.0))
    diluted_shares = get_num(share_bridge, "diluted_shares")
    new_shares = safe_div(financing_shortfall, raise_price, 0.0) if raise_price not in (0, 0.0, None) else 0.0
    pro_forma_diluted_shares = diluted_shares + new_shares
    dilution_pct = safe_div(new_shares, diluted_shares, 0.0)

    net_cash_current = liquidity - debt
    net_cash_per_share_current = safe_div(net_cash_current, diluted_shares, 0.0)
    net_cash_per_share_pro_forma = safe_div(net_cash_current + financing_shortfall, pro_forma_diluted_shares, 0.0)

    result = {
        "label": config.get("label", "Cash Runway / Dilution"),
        "liquidity": liquidity,
        "debt": debt,
        "annual_cash_burn": annual_cash_burn,
        "runway_months": runway_months,
        "next_value_inflection_year": next_inflection_year,
        "years_to_inflection": years_to_inflection,
        "minimum_cash_buffer_months": buffer_months,
        "required_liquidity": required_liquidity,
        "financing_shortfall": financing_shortfall,
        "raise_price": raise_price,
        "new_shares": new_shares,
        "pro_forma_diluted_shares": pro_forma_diluted_shares,
        "dilution_pct": dilution_pct,
        "net_cash_per_share_current": net_cash_per_share_current,
        "net_cash_per_share_pro_forma": net_cash_per_share_pro_forma,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
