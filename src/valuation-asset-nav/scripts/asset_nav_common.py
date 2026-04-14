#!/usr/bin/env python3
import json
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_num(mapping, key, default=0.0):
    if mapping is None:
        return float(default)
    value = mapping.get(key, default)
    if value is None:
        return float(default)
    return float(value)


def safe_div(numerator, denominator, default=None):
    if denominator in (None, 0, 0.0):
        return default
    return numerator / denominator


def diluted_shares_total(share_bridge):
    return (
        get_num(share_bridge, "basic_shares")
        + get_num(share_bridge, "option_dilution_shares")
        + get_num(share_bridge, "rsu_shares")
        + get_num(share_bridge, "convertible_shares")
        + get_num(share_bridge, "other_dilution_shares")
        - get_num(share_bridge, "buyback_shares")
    )


def normalize_weights(rows, key="weight"):
    total = sum(float(row.get(key, 0.0)) for row in rows)
    if not rows:
        return rows
    if total <= 0:
        even = 1.0 / len(rows)
        for row in rows:
            row[key] = even
        return rows
    for row in rows:
        row[key] = float(row.get(key, 0.0)) / total
    return rows


def pick_value(payload):
    if payload is None:
        return None
    return (
        payload.get("implied_value_per_share")
        or payload.get("value_per_share")
        or payload.get("nav_per_share")
    )
