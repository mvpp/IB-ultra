#!/usr/bin/env python3
import argparse

from valuation_common import (
    diluted_shares_total,
    dump_json,
    enterprise_to_equity_adjustment_total,
    get_num,
    load_json,
    summarize_values,
    trimmed_values,
)


def collect_peer_values(peers, peer_metric, trim_percent):
    included = []
    excluded = []
    raw_values = []
    for peer in peers:
        if peer.get("include", True) is False:
            excluded.append({"ticker": peer.get("ticker"), "reason": "explicitly excluded"})
            continue
        metrics = peer.get("metrics", {})
        if peer_metric not in metrics or metrics[peer_metric] in (None, ""):
            excluded.append({"ticker": peer.get("ticker"), "reason": f"missing {peer_metric}"})
            continue
        value = float(metrics[peer_metric])
        if value <= 0:
            excluded.append({"ticker": peer.get("ticker"), "reason": f"non-positive {peer_metric}"})
            continue
        raw_values.append(value)
        included.append({"ticker": peer.get("ticker"), "value": value})
    trimmed = trimmed_values(raw_values, trim_percent)
    return included, excluded, raw_values, trimmed


def implied_value(method, selected_multiple, target, bridge_adjustment, diluted_shares):
    target_metrics = target.get("metrics", {})
    basis = method["valuation_basis"]
    target_metric = get_num(target_metrics, method["target_metric"])
    if basis == "enterprise":
        enterprise_value = selected_multiple * target_metric
        equity_value = enterprise_value + bridge_adjustment
        price = equity_value / diluted_shares if diluted_shares else None
        return enterprise_value, equity_value, price
    if basis == "equity_per_share":
        price = selected_multiple * target_metric
        equity_value = price * diluted_shares if diluted_shares else None
        return None, equity_value, price
    if basis == "equity_total":
        equity_value = selected_multiple * target_metric
        price = equity_value / diluted_shares if diluted_shares else None
        return None, equity_value, price
    raise ValueError(f"Unsupported valuation basis: {basis}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Calculate comp-based valuation from peer metrics. Input requires target, peers, methods, "
            "and optional outlier_policy.trim_percent."
        )
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="comps_output.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    target = payload["target"]
    peers = payload.get("peers", [])
    methods = payload.get("methods", [])
    trim_percent = get_num(payload.get("outlier_policy", {}), "trim_percent")
    share_bridge = target.get("share_bridge", {})
    diluted_shares = (
        get_num(share_bridge, "diluted_shares")
        if share_bridge.get("diluted_shares") is not None
        else diluted_shares_total(share_bridge)
    )
    bridge_adjustment = enterprise_to_equity_adjustment_total(target.get("ev_bridge", {}))

    results = []
    for method in methods:
        included, excluded, raw_values, trimmed = collect_peer_values(peers, method["peer_metric"], trim_percent)
        if not trimmed:
            results.append(
                {
                    "label": method["label"],
                    "error": f"No usable peer values for {method['peer_metric']}",
                    "included_peers": included,
                    "excluded_peers": excluded,
                }
            )
            continue
        stats = summarize_values(trimmed)
        stat_name = method.get("stat", "median")
        selected_multiple = stats[stat_name]
        enterprise_value, equity_value, price = implied_value(
            method,
            selected_multiple,
            target,
            bridge_adjustment,
            diluted_shares,
        )
        results.append(
            {
                "label": method["label"],
                "peer_metric": method["peer_metric"],
                "target_metric": method["target_metric"],
                "valuation_basis": method["valuation_basis"],
                "selected_stat": stat_name,
                "selected_multiple": selected_multiple,
                "summary_stats": stats,
                "raw_values": raw_values,
                "trimmed_values": trimmed,
                "included_peers": included,
                "excluded_peers": excluded,
                "implied_enterprise_value": enterprise_value,
                "implied_equity_value": equity_value,
                "implied_value_per_share": price,
            }
        )

    result = {
        "target": target.get("name", target.get("ticker")),
        "diluted_shares": diluted_shares,
        "enterprise_to_equity_adjustment_total": bridge_adjustment,
        "methods": results,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
