#!/usr/bin/env python3
import argparse

from memo_common import avg, clamp, dump_json, get_num, load_json


def score_from_thresholds(value, thresholds):
    if value is None:
        return 0
    excellent, good, average = thresholds
    if value >= excellent:
        return 3
    if value >= good:
        return 2
    if value >= average:
        return 1
    return 0


def sector_family(company):
    return str(company.get("sector_family", "")).strip().lower()


def returns_dimension(pack):
    company = pack.get("company", {})
    quality = pack.get("quality_inputs", {})
    model = pack.get("model_summary", {})
    family = sector_family(company)

    if family in {"bank", "banks", "insurance", "financials"}:
        metric_name = "roe"
        metric_value = avg(quality.get("roe_history", [])) or get_num(model, "roe_ltm")
        thresholds = (0.16, 0.12, 0.08)
    elif family in {"reit", "real_estate", "infrastructure", "utilities", "energy", "materials"}:
        metric_name = "roic"
        metric_value = avg(quality.get("roic_history", [])) or get_num(model, "roic_ltm")
        thresholds = (0.12, 0.08, 0.05)
    else:
        metric_name = "roic"
        metric_value = avg(quality.get("roic_history", [])) or get_num(model, "roic_ltm") or avg(quality.get("roe_history", []))
        thresholds = (0.20, 0.15, 0.10)

    score = score_from_thresholds(metric_value, thresholds)
    return {
        "name": "Returns quality",
        "metric_name": metric_name,
        "metric_value": metric_value,
        "score": score,
        "note": "Measures whether the company is earning attractive returns on capital or equity.",
    }


def balance_sheet_dimension(pack):
    company = pack.get("company", {})
    quality = pack.get("quality_inputs", {})
    model = pack.get("model_summary", {})
    family = sector_family(company)

    if family in {"biotech", "clinical_stage_biotech"}:
        metric_name = "cash_runway_months"
        metric_value = get_num(quality, "cash_runway_months")
        thresholds = (24.0, 18.0, 12.0)
        score = score_from_thresholds(metric_value, thresholds)
    elif family in {"bank", "banks", "insurance", "financials"}:
        metric_name = "cet1_ratio"
        metric_value = get_num(quality, "cet1_ratio")
        thresholds = (0.13, 0.11, 0.09)
        score = score_from_thresholds(metric_value, thresholds)
    elif family in {"reit", "real_estate"}:
        metric_name = "loan_to_value"
        metric_value = get_num(quality, "loan_to_value")
        if metric_value is None:
            score = 0
        elif metric_value <= 0.35:
            score = 3
        elif metric_value <= 0.45:
            score = 2
        elif metric_value <= 0.55:
            score = 1
        else:
            score = 0
    else:
        metric_name = "net_debt_to_ebitda"
        metric_value = get_num(quality, "net_debt_to_ebitda", get_num(model, "net_debt_to_ebitda"))
        interest_coverage = get_num(quality, "interest_coverage", get_num(model, "interest_coverage"))
        if metric_value is None:
            score = 0
        elif metric_value <= 0:
            score = 3
        elif metric_value <= 2.0:
            score = 2
        elif metric_value <= 3.5:
            score = 1
        else:
            score = 0
        if interest_coverage is not None and interest_coverage < 2.5:
            score = clamp(score - 1, 0, 3)

    return {
        "name": "Balance-sheet safety",
        "metric_name": metric_name,
        "metric_value": metric_value,
        "score": score,
        "note": "Checks leverage, capital, or runway depending on the sector family.",
    }


def cash_generation_dimension(pack):
    company = pack.get("company", {})
    quality = pack.get("quality_inputs", {})
    model = pack.get("model_summary", {})
    family = sector_family(company)

    if family in {"biotech", "clinical_stage_biotech"}:
        metric_name = "cash_runway_months"
        metric_value = get_num(quality, "cash_runway_months")
        thresholds = (24.0, 18.0, 12.0)
        score = score_from_thresholds(metric_value, thresholds)
    else:
        metric_name = "fcf_to_net_income"
        metric_value = get_num(quality, "fcf_to_net_income")
        if metric_value is None:
            metric_name = "fcf_margin"
            metric_value = get_num(quality, "fcf_margin", get_num(model, "fcf_margin_ltm"))
            thresholds = (0.20, 0.10, 0.02)
        else:
            thresholds = (1.00, 0.80, 0.50)
        score = score_from_thresholds(metric_value, thresholds)

    return {
        "name": "Cash generation",
        "metric_name": metric_name,
        "metric_value": metric_value,
        "score": score,
        "note": "Tests whether accounting earnings convert into usable cash.",
    }


def moat_dimension(pack):
    quality = pack.get("quality_inputs", {})
    moat_types = quality.get("moat_types", []) or []
    explicit_score = quality.get("moat_score")
    if explicit_score is not None:
        score = clamp(int(explicit_score), 0, 3)
    else:
        count = len(moat_types)
        if count >= 2:
            score = 3
        elif count == 1:
            score = 2
        elif quality.get("competitive_advantage_flag") or get_num(quality, "net_revenue_retention", 0.0) >= 1.05:
            score = 1
        else:
            score = 0
    return {
        "name": "Moat / competitive position",
        "metric_name": "moat_types",
        "metric_value": moat_types,
        "score": score,
        "note": "Uses explicit moat tags first, then simple retention or advantage fallbacks.",
    }


def rating_for_total(total_score):
    if total_score >= 10:
        return "A"
    if total_score >= 7:
        return "B"
    if total_score >= 4:
        return "C"
    return "D"


def main():
    parser = argparse.ArgumentParser(
        description="Build a deterministic four-dimension quality overlay from the memo input pack."
    )
    parser.add_argument("--input", required=True, help="Path to memo_input_pack JSON")
    parser.add_argument("--output", default="quality_overlay.json", help="Path to JSON output")
    args = parser.parse_args()

    pack = load_json(args.input)
    dimensions = [
        returns_dimension(pack),
        balance_sheet_dimension(pack),
        cash_generation_dimension(pack),
        moat_dimension(pack),
    ]
    total_score = sum(dimension["score"] for dimension in dimensions)
    rating = rating_for_total(total_score)

    result = {
        "dimensions": dimensions,
        "total_score": total_score,
        "rating": rating,
        "summary": {
            "rating": rating,
            "total_score": total_score,
            "interpretation": (
                "High-quality overlay cross-check."
                if rating in {"A", "B"}
                else "The business may still work, but the quality overlay is not strong."
            ),
        },
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
