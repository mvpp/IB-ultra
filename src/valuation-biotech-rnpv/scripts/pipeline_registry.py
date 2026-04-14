#!/usr/bin/env python3
import argparse
import re

from biotech_common import (
    DEFAULT_STAGE_LAUNCH_LAG,
    DEFAULT_STAGE_POS,
    current_year,
    diluted_shares_total,
    dump_json,
    get_nested,
    get_num,
    load_json,
    normalize_approval_status,
    normalize_stage,
    parse_year,
    safe_div,
    source_tier,
)


def slugify(*parts):
    text = "-".join(str(part or "").strip().lower() for part in parts if part not in (None, ""))
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "asset"


def normalize_source(entry, default_authority=None):
    authority = entry.get("authority") or entry.get("source_type") or default_authority
    return {
        "title": entry.get("title"),
        "authority": authority,
        "source_type": entry.get("source_type") or authority,
        "url": entry.get("url"),
        "date": entry.get("date") or entry.get("as_of") or entry.get("updated_at"),
        "tier": source_tier(authority),
    }


def parse_clinicaltrials_entries(payload):
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("studies"), list):
            rows = []
            for study in payload["studies"]:
                protocol = study.get("protocolSection", {})
                identification = protocol.get("identificationModule", {})
                status = protocol.get("statusModule", {})
                design = protocol.get("designModule", {})
                conditions = protocol.get("conditionsModule", {})
                interventions = protocol.get("armsInterventionsModule", {})
                rows.append(
                    {
                        "asset_id": study.get("asset_id") or study.get("assetId"),
                        "nct_id": identification.get("nctId"),
                        "title": identification.get("briefTitle"),
                        "status": status.get("overallStatus"),
                        "phase": ", ".join(design.get("phases", [])) if design.get("phases") else None,
                        "primary_completion_date": get_nested(status, "primaryCompletionDateStruct", "date"),
                        "completion_date": get_nested(status, "completionDateStruct", "date"),
                        "enrollment": get_nested(design, "enrollmentInfo", "count"),
                        "conditions": conditions.get("conditions"),
                        "interventions": [
                            row.get("name") for row in interventions.get("interventions", []) if row.get("name")
                        ],
                        "url": f"https://clinicaltrials.gov/study/{identification.get('nctId')}"
                        if identification.get("nctId")
                        else None,
                    }
                )
            return rows
        if isinstance(payload.get("trials"), list):
            return payload["trials"]
    return []


def build_trial_index(entries):
    index = {}
    for row in entries:
        asset_id = row.get("asset_id")
        if not asset_id:
            continue
        index.setdefault(asset_id, []).append(row)
    return index


def latest_trial(trials):
    if not trials:
        return None
    def sort_key(row):
        return parse_year(row.get("primary_completion_date")) or parse_year(row.get("completion_date")) or 0
    return max(trials, key=sort_key)


def stage_from_sources(asset, trials, regulatory_updates):
    explicit = asset.get("stage") or asset.get("clinical_stage")
    if explicit:
        return normalize_stage(explicit)
    approved_status = approval_from_sources(asset, regulatory_updates)
    if approved_status == "approved":
        return "approved"
    latest = latest_trial(trials)
    if latest and latest.get("phase"):
        return normalize_stage(latest["phase"])
    return None


def approval_from_sources(asset, regulatory_updates):
    explicit = asset.get("approval_status")
    if explicit:
        return normalize_approval_status(explicit)
    if not regulatory_updates:
        return None
    latest = max(regulatory_updates, key=lambda row: parse_year(row.get("date")) or 0)
    return normalize_approval_status(latest.get("status"))


def normalize_asset_sources(asset, trial_rows, regulatory_rows, literature_rows):
    sources = [normalize_source(row) for row in asset.get("sources", [])]
    for row in trial_rows:
        sources.append(
            normalize_source(
                {
                    "title": row.get("title") or row.get("nct_id"),
                    "authority": "clinicaltrials",
                    "source_type": "clinicaltrials",
                    "url": row.get("url"),
                    "date": row.get("primary_completion_date") or row.get("completion_date"),
                }
            )
        )
    for row in regulatory_rows:
        sources.append(normalize_source(row, default_authority=row.get("authority") or "fda"))
    for row in literature_rows:
        sources.append(normalize_source(row, default_authority=row.get("authority") or row.get("source_type")))
    dedup = []
    seen = set()
    for row in sources:
        key = (row.get("authority"), row.get("url"), row.get("title"))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)
    return sorted(dedup, key=lambda row: (row.get("tier", 99), row.get("date") or ""))


def main():
    parser = argparse.ArgumentParser(
        description="Build a source-traceable biotech pipeline registry from company, trial, and regulatory inputs."
    )
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument("--output", default="pipeline_registry.json", help="Path to JSON output")
    args = parser.parse_args()

    payload = load_json(args.input)
    assets = payload.get("pipeline_assets") or payload.get("assets") or []
    valuation_year = int(payload.get("valuation_year") or current_year())
    balance_sheet = payload.get("balance_sheet", {})
    cash_flow = payload.get("cash_flow", {})
    share_bridge = payload.get("share_bridge", {})
    market = payload.get("market", {})

    trial_entries = parse_clinicaltrials_entries(payload.get("trial_registry") or payload.get("clinicaltrials"))
    trial_index = build_trial_index(trial_entries)
    regulatory_index = build_trial_index(payload.get("regulatory_updates", []))
    literature_index = build_trial_index(payload.get("literature_updates", []))

    diluted_shares = (
        get_num(share_bridge, "diluted_shares")
        if share_bridge.get("diluted_shares") is not None
        else diluted_shares_total(share_bridge)
    )
    basic_shares = get_num(share_bridge, "basic_shares", diluted_shares)

    cash = get_num(balance_sheet, "cash")
    marketable_securities = get_num(balance_sheet, "marketable_securities")
    debt = get_num(balance_sheet, "debt")
    other_assets = get_num(balance_sheet, "other_assets")
    other_liabilities = get_num(balance_sheet, "other_liabilities")
    liquidity = cash + marketable_securities

    annual_cash_burn = (
        get_num(cash_flow, "annual_cash_burn")
        if cash_flow.get("annual_cash_burn") is not None
        else max(
            0.0,
            -get_num(cash_flow, "operating_cash_flow_ltm") + get_num(cash_flow, "capex_ltm"),
        )
    )
    quarterly_cash_burn = (
        get_num(cash_flow, "quarterly_cash_burn")
        if cash_flow.get("quarterly_cash_burn") is not None
        else safe_div(annual_cash_burn, 4.0, 0.0)
    )
    runway_months = safe_div(liquidity, safe_div(annual_cash_burn, 12.0, None))

    processed_assets = []
    source_counts = {}
    assets_with_company_source = 0
    assets_with_trial_source = 0
    assets_with_regulatory_source = 0

    for raw_asset in assets:
        asset_id = raw_asset.get("asset_id") or slugify(raw_asset.get("name"), raw_asset.get("indication"))
        trials = trial_index.get(asset_id, [])
        regulatory_updates = regulatory_index.get(asset_id, [])
        literature_updates = literature_index.get(asset_id, [])
        latest = latest_trial(trials)

        stage = stage_from_sources(raw_asset, trials, regulatory_updates)
        approval_status = approval_from_sources(raw_asset, regulatory_updates)
        if approval_status == "approved":
            stage = "approved"

        probability = raw_asset.get("probability_of_success")
        probability_source = "explicit"
        if probability is None:
            probability = DEFAULT_STAGE_POS.get(stage, 0.10)
            probability_source = "stage_default"

        launch_year = raw_asset.get("expected_launch_year") or raw_asset.get("launch_year")
        launch_year_source = "explicit"
        if launch_year is None:
            lag = DEFAULT_STAGE_LAUNCH_LAG.get(stage, 4)
            launch_year = valuation_year + lag
            launch_year_source = "stage_default"
        launch_year = int(launch_year)

        next_catalyst_year = parse_year(raw_asset.get("next_readout_date")) or parse_year(
            raw_asset.get("next_catalyst_date")
        )
        if next_catalyst_year is None:
            next_catalyst_year = parse_year(latest.get("primary_completion_date")) if latest else None
        if next_catalyst_year is None and stage not in {"approved", None}:
            next_catalyst_year = max(valuation_year, launch_year - 1)

        sources = normalize_asset_sources(raw_asset, trials, regulatory_updates, literature_updates)
        source_authorities = {str(row.get("authority", "")).lower() for row in sources}
        has_company_source = bool(source_authorities & {"company_sec", "company_ir", "company_pr", "sec"})
        has_trial_source = "clinicaltrials" in source_authorities
        has_regulatory_source = bool(source_authorities & {"fda", "ema"})
        if has_company_source:
            assets_with_company_source += 1
        if has_trial_source:
            assets_with_trial_source += 1
        if has_regulatory_source:
            assets_with_regulatory_source += 1
        for row in sources:
            authority = row.get("authority") or "unknown"
            source_counts[authority] = source_counts.get(authority, 0) + 1

        source_confidence = 1
        if has_company_source and (has_trial_source or has_regulatory_source):
            source_confidence = 3
        elif has_company_source or has_trial_source or has_regulatory_source:
            source_confidence = 2

        processed_assets.append(
            {
                "asset_id": asset_id,
                "name": raw_asset.get("name"),
                "indication": raw_asset.get("indication"),
                "modality": raw_asset.get("modality"),
                "economics_type": raw_asset.get("economics_type", "owned"),
                "ownership_pct": float(raw_asset.get("ownership_pct", 1.0) or 1.0),
                "royalty_rate": get_num(raw_asset, "royalty_rate"),
                "stage": stage,
                "approval_status": approval_status,
                "probability_of_success": float(probability),
                "probability_source": probability_source,
                "expected_launch_year": launch_year,
                "launch_year_source": launch_year_source,
                "next_value_inflection_year": next_catalyst_year,
                "patent_expiry_year": parse_year(raw_asset.get("patent_expiry_year")),
                "peak_sales": get_num(raw_asset, "peak_sales"),
                "current_sales": get_num(raw_asset, "current_sales"),
                "operating_margin": get_num(raw_asset, "operating_margin", 0.65),
                "tax_rate": get_num(raw_asset, "tax_rate", 0.21),
                "discount_rate": get_num(raw_asset, "discount_rate", 0.125),
                "remaining_rnd_cost": get_num(raw_asset, "remaining_rnd_cost"),
                "milestone_costs": get_num(raw_asset, "milestone_costs"),
                "milestone_schedule": raw_asset.get("milestone_schedule", []),
                "commercial_years": int(raw_asset.get("commercial_years", 10) or 10),
                "ramp_years": int(raw_asset.get("ramp_years", 5) or 5),
                "sales_curve": raw_asset.get("sales_curve", []),
                "trial_ids": raw_asset.get("trial_ids") or [row.get("nct_id") for row in trials if row.get("nct_id")],
                "latest_trial_status": latest.get("status") if latest else None,
                "latest_trial_phase": latest.get("phase") if latest else None,
                "latest_primary_completion_date": latest.get("primary_completion_date") if latest else None,
                "source_confidence": source_confidence,
                "source_flags": {
                    "has_company_source": has_company_source,
                    "has_trial_source": has_trial_source,
                    "has_regulatory_source": has_regulatory_source,
                },
                "sources": sources,
            }
        )

    result = {
        "company": payload.get("company", {}),
        "valuation_year": valuation_year,
        "assets": processed_assets,
        "balance_sheet_bridge": {
            **balance_sheet,
            "cash": cash,
            "marketable_securities": marketable_securities,
            "liquidity": liquidity,
            "debt": debt,
            "other_assets": other_assets,
            "other_liabilities": other_liabilities,
            "net_cash": liquidity - debt,
        },
        "cash_flow_bridge": {
            **cash_flow,
            "annual_cash_burn": annual_cash_burn,
            "quarterly_cash_burn": quarterly_cash_burn,
            "runway_months": runway_months,
        },
        "share_bridge": {
            **share_bridge,
            "basic_shares": basic_shares,
            "diluted_shares": diluted_shares,
        },
        "source_registry": {
            "asset_count": len(processed_assets),
            "assets_with_company_source": assets_with_company_source,
            "assets_with_trial_source": assets_with_trial_source,
            "assets_with_regulatory_source": assets_with_regulatory_source,
            "source_counts": source_counts,
        },
        "market": market,
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
