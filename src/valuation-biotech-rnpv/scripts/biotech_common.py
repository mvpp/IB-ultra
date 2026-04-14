#!/usr/bin/env python3
import json
from datetime import date, datetime
from pathlib import Path


DEFAULT_STAGE_POS = {
    "preclinical": 0.08,
    "phase_1": 0.12,
    "phase_1_2": 0.18,
    "phase_2": 0.25,
    "phase_2_3": 0.40,
    "phase_3": 0.55,
    "filed": 0.85,
    "approved": 1.00,
}

DEFAULT_STAGE_LAUNCH_LAG = {
    "preclinical": 6,
    "phase_1": 5,
    "phase_1_2": 4,
    "phase_2": 4,
    "phase_2_3": 3,
    "phase_3": 2,
    "filed": 1,
    "approved": 0,
}

STAGE_ALIASES = {
    "pre-clinical": "preclinical",
    "preclinical": "preclinical",
    "phase 1": "phase_1",
    "phase i": "phase_1",
    "phase 1/2": "phase_1_2",
    "phase i/ii": "phase_1_2",
    "phase 2": "phase_2",
    "phase ii": "phase_2",
    "phase 2/3": "phase_2_3",
    "phase ii/iii": "phase_2_3",
    "phase 3": "phase_3",
    "phase iii": "phase_3",
    "nda": "filed",
    "bla": "filed",
    "maa": "filed",
    "filed": "filed",
    "approved": "approved",
    "commercial": "approved",
    "marketed": "approved",
}

APPROVAL_ALIASES = {
    "approved": "approved",
    "licensed": "approved",
    "authorized": "approved",
    "marketed": "approved",
    "filed": "filed",
    "submitted": "filed",
    "under review": "filed",
    "complete response letter": "crl",
    "crl": "crl",
    "withdrawn": "withdrawn",
    "discontinued": "discontinued",
}

SOURCE_TIERS = {
    "fda": 1,
    "ema": 1,
    "clinicaltrials": 1,
    "sec": 1,
    "company_sec": 1,
    "company_ir": 2,
    "company_pr": 2,
    "pubmed": 2,
    "conference": 2,
    "literature": 2,
}


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
        or payload.get("expected_value_per_share")
        or payload.get("value_per_share")
        or payload.get("nav_per_share")
    )


def normalize_stage(value):
    if value is None:
        return None
    text = str(value).strip().lower()
    return STAGE_ALIASES.get(text, text.replace(" ", "_"))


def normalize_approval_status(value):
    if value is None:
        return None
    text = str(value).strip().lower()
    return APPROVAL_ALIASES.get(text, text.replace(" ", "_"))


def source_tier(authority):
    if authority is None:
        return 99
    key = str(authority).strip().lower()
    return SOURCE_TIERS.get(key, 50)


def current_year():
    return date.today().year


def parse_year(value):
    if value in (None, ""):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip()
    if len(text) == 4 and text.isdigit():
        return int(text)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).year
    except Exception:
        pass
    for token in text.replace("/", "-").split("-"):
        if len(token) == 4 and token.isdigit():
            return int(token)
    return None


def get_nested(mapping, *keys):
    current = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current
