#!/usr/bin/env python3
import json
import math
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_num(mapping, key, default=0.0):
    value = mapping.get(key, default)
    if value is None:
        return float(default)
    return float(value)


def safe_div(numerator, denominator, default=None):
    if denominator in (None, 0, 0.0):
        return default
    return numerator / denominator


def clamp(value, low, high):
    return max(low, min(high, value))


def diluted_shares_total(share_bridge):
    return (
        get_num(share_bridge, "basic_shares")
        + get_num(share_bridge, "option_dilution_shares")
        + get_num(share_bridge, "rsu_shares")
        + get_num(share_bridge, "convertible_shares")
        + get_num(share_bridge, "other_dilution_shares")
        - get_num(share_bridge, "buyback_shares")
    )


def percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    if pct <= 0:
        return ordered[0]
    if pct >= 1:
        return ordered[-1]
    index = (len(ordered) - 1) * pct
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def summarize_values(values):
    ordered = sorted(values)
    if not ordered:
        return {
            "count": 0,
            "min": None,
            "median": None,
            "mean": None,
            "max": None,
        }
    return {
        "count": len(ordered),
        "min": ordered[0],
        "median": percentile(ordered, 0.50),
        "mean": sum(ordered) / len(ordered),
        "max": ordered[-1],
    }


def total_and_per_share(total, diluted_shares):
    per_share = safe_div(total, diluted_shares)
    return total, per_share
