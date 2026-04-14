#!/usr/bin/env python3
import json
import re
from datetime import date, datetime
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def get_num(mapping, key, default=None):
    if mapping is None:
        return default
    value = mapping.get(key, default)
    if value is None:
        return default
    return float(value)


def safe_div(numerator, denominator, default=None):
    if denominator in (0, 0.0, None):
        return default
    return numerator / denominator


def clamp(value, low, high):
    return max(low, min(high, value))


def avg(values):
    values = [float(v) for v in values if v is not None]
    if not values:
        return None
    return sum(values) / len(values)


def pct_change(target, current):
    return safe_div(target - current, current)


def scenario_default_probability(name):
    mapping = {
        "bear": 0.25,
        "base": 0.50,
        "bull": 0.25,
    }
    return mapping.get(str(name).strip().lower(), None)


def normalize_probabilities(rows):
    weights = []
    for row in rows:
        probability = row.get("probability")
        if probability is None:
            probability = scenario_default_probability(row.get("name"))
        if probability is None:
            probability = 1.0
        weights.append(float(probability))
    total = sum(weights)
    if total == 0:
        return [1.0 / len(rows)] * len(rows) if rows else []
    return [weight / total for weight in weights]


def markdown_headings(path):
    text = Path(path).read_text(encoding="utf-8")
    return [
        match.group(2).strip().lower()
        for match in re.finditer(r"^(#{1,6})\s+(.+?)\s*$", text, flags=re.MULTILINE)
    ]


def iso_days_until(date_str, today=None):
    if not date_str:
        return None
    today = today or date.today()
    event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    return (event_date - today).days


def number_strings(value):
    if value is None:
        return []
    value = float(value)
    variants = {
        f"{value:.0f}",
        f"{value:.1f}",
        f"{value:.2f}",
        f"{value:,.0f}",
        f"{value:,.1f}",
        f"{value:,.2f}",
    }
    if abs(value) <= 1:
        variants.update(
            {
                f"{value:.3f}",
                f"{value * 100:.1f}%",
                f"{value * 100:.2f}%",
                f"{value * 100:.0f}%",
            }
        )
    return sorted(variants)
