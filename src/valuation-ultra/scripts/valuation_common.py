#!/usr/bin/env python3
import json
import math
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def get_num(mapping, key, default=0.0):
    value = mapping.get(key, default)
    if value is None:
        return float(default)
    return float(value)


def safe_div(numerator, denominator, default=None):
    if denominator in (0, 0.0, None):
        return default
    return numerator / denominator


def percentile(values, pct):
    if not values:
        return None
    if pct <= 0:
        return min(values)
    if pct >= 1:
        return max(values)
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def summarize_values(values):
    ordered = sorted(values)
    count = len(ordered)
    if not ordered:
        return {
            "count": 0,
            "min": None,
            "p25": None,
            "median": None,
            "mean": None,
            "p75": None,
            "max": None,
        }
    return {
        "count": count,
        "min": ordered[0],
        "p25": percentile(ordered, 0.25),
        "median": percentile(ordered, 0.50),
        "mean": sum(ordered) / count,
        "p75": percentile(ordered, 0.75),
        "max": ordered[-1],
    }


def trimmed_values(values, trim_percent):
    ordered = sorted(values)
    if not ordered:
        return []
    trim_percent = float(trim_percent or 0.0)
    if trim_percent <= 0:
        return ordered
    trim_n = int(len(ordered) * trim_percent)
    if trim_n == 0 or len(ordered) - (2 * trim_n) < 1:
        return ordered
    return ordered[trim_n: len(ordered) - trim_n]


def enterprise_to_equity_adjustment_total(bridge):
    cash = get_num(bridge, "cash")
    if bridge.get("include_restricted_cash", False):
        cash += get_num(bridge, "restricted_cash")
    return (
        cash
        + get_num(bridge, "investments")
        + get_num(bridge, "other_non_operating_assets")
        - get_num(bridge, "total_debt")
        - get_num(bridge, "lease_liabilities")
        - get_num(bridge, "preferred_equity")
        - get_num(bridge, "minority_interest")
        - get_num(bridge, "pension_deficit")
        - get_num(bridge, "other_non_operating_liabilities")
    )


def diluted_shares_total(share_bridge):
    return (
        get_num(share_bridge, "basic_shares")
        + get_num(share_bridge, "option_dilution_shares")
        + get_num(share_bridge, "rsu_shares")
        + get_num(share_bridge, "convertible_shares")
        + get_num(share_bridge, "other_dilution_shares")
        - get_num(share_bridge, "buyback_shares")
    )


def bisection_solve(fn, low, high, tolerance=1e-9, max_iter=200):
    f_low = fn(low)
    f_high = fn(high)
    if f_low == 0:
        return low
    if f_high == 0:
        return high
    if f_low * f_high > 0:
        raise ValueError("Bisection bounds do not bracket a root.")
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        f_mid = fn(mid)
        if abs(f_mid) < tolerance or abs(high - low) < tolerance:
            return mid
        if f_low * f_mid <= 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid
    return (low + high) / 2.0
