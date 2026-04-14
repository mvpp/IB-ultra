#!/usr/bin/env python3
import argparse

from financials_common import dump_json, get_num, load_json, safe_div


def justified_multiple(roe, cost_of_equity, growth_rate):
    if None in (roe, cost_of_equity, growth_rate):
        return None
    if cost_of_equity <= growth_rate:
        return None
    return (roe - growth_rate) / (cost_of_equity - growth_rate)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Value a bank or insurer using P/B or P/TBV tied to sustainable ROE or ROTCE. "
            "Input may be a financials_prep JSON or a purpose-built method JSON."
        )
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="pb_roe_output.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    prep = payload.get("financials_prep", payload)
    method = payload.get("method", payload.get("pb_roe", {}))

    book_bridge = prep.get("book_bridge", {})
    share_bridge = prep.get("share_bridge", {})
    capital = prep.get("capital", {})
    earnings = prep.get("earnings", {})
    market = prep.get("market", {})

    book_basis = method.get("book_basis", "tangible")
    if book_basis == "reported":
        book_value_per_share = book_bridge.get("book_value_per_share")
        return_metric = method.get("return_metric", "normalized_roe")
        sustainable_return = method.get(return_metric) or earnings.get(return_metric) or earnings.get("normalized_roe")
    else:
        book_value_per_share = book_bridge.get("tangible_book_value_per_share")
        return_metric = method.get("return_metric", "normalized_rotce")
        sustainable_return = method.get(return_metric) or earnings.get(return_metric) or earnings.get("normalized_rotce")

    cost_of_equity = method.get("cost_of_equity")
    growth_rate = method.get("growth_rate", 0.03)
    justified_pb = justified_multiple(
        None if sustainable_return is None else float(sustainable_return),
        None if cost_of_equity is None else float(cost_of_equity),
        None if growth_rate is None else float(growth_rate),
    )
    peer_multiple = method.get("peer_selected_multiple")
    explicit_multiple = method.get("selected_multiple")
    blend_weight = float(method.get("justified_weight", 0.5))

    if explicit_multiple is not None:
        selected_multiple = float(explicit_multiple)
        multiple_source = "explicit"
    elif peer_multiple is not None and justified_pb is not None:
        selected_multiple = float(peer_multiple) * (1.0 - blend_weight) + justified_pb * blend_weight
        multiple_source = "blend_peer_and_justified"
    elif peer_multiple is not None:
        selected_multiple = float(peer_multiple)
        multiple_source = "peer"
    else:
        selected_multiple = justified_pb
        multiple_source = "justified"

    excess_capital_per_share = get_num(capital, "excess_capital_per_share", 0.0)
    include_excess_capital = bool(method.get("include_excess_capital", True))
    core_value_per_share = (
        selected_multiple * float(book_value_per_share)
        if selected_multiple is not None and book_value_per_share is not None
        else None
    )
    implied_value_per_share = (
        core_value_per_share + (excess_capital_per_share if include_excess_capital else 0.0)
        if core_value_per_share is not None
        else None
    )
    diluted_shares = share_bridge.get("diluted_shares")
    implied_equity_value = (
        implied_value_per_share * float(diluted_shares)
        if implied_value_per_share is not None and diluted_shares is not None
        else None
    )

    result = {
        "label": "P/B vs ROE" if book_basis == "reported" else "P/TBV vs ROTCE",
        "method_family": "financials_pb",
        "book_basis": book_basis,
        "return_metric": return_metric,
        "book_value_per_share": book_value_per_share,
        "sustainable_return": sustainable_return,
        "cost_of_equity": cost_of_equity,
        "growth_rate": growth_rate,
        "justified_multiple": justified_pb,
        "peer_selected_multiple": peer_multiple,
        "selected_multiple": selected_multiple,
        "selected_multiple_source": multiple_source,
        "excess_capital_per_share": excess_capital_per_share if include_excess_capital else 0.0,
        "core_value_per_share": core_value_per_share,
        "implied_value_per_share": implied_value_per_share,
        "implied_equity_value": implied_equity_value,
        "current_price": market.get("current_price"),
        "premium_discount_to_current": (
            safe_div(implied_value_per_share - market.get("current_price"), market.get("current_price"))
            if implied_value_per_share is not None and market.get("current_price") not in (None, 0, 0.0)
            else None
        ),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
