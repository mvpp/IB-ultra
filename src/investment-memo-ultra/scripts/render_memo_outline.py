#!/usr/bin/env python3
import argparse
from pathlib import Path

from memo_common import load_json


def fmt_money(value):
    if value is None:
        return "n/a"
    return f"${value:,.2f}"


def fmt_pct(value):
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def main():
    parser = argparse.ArgumentParser(
        description="Render a markdown investment-memo outline from memo artifacts."
    )
    parser.add_argument("--memo-pack", required=True, help="Path to memo_input_pack JSON")
    parser.add_argument("--quality", required=True, help="Path to quality_overlay JSON")
    parser.add_argument("--variant", required=True, help="Path to variant_view_frame JSON")
    parser.add_argument("--decision", required=True, help="Path to decision_framework JSON")
    parser.add_argument("--monitoring", required=True, help="Path to monitoring_dashboard JSON")
    parser.add_argument("--output", default="investment_memo_outline.md", help="Path to markdown output")
    args = parser.parse_args()

    memo_pack = load_json(args.memo_pack)
    quality = load_json(args.quality)
    variant = load_json(args.variant)
    decision = load_json(args.decision)
    monitoring = load_json(args.monitoring)

    company = memo_pack.get("company", {})
    summary = memo_pack.get("summary", {})
    valuation = memo_pack.get("valuation", {})
    model_summary = memo_pack.get("model_summary", {})

    quality_rows = "\n".join(
        f"| {row['name']} | {row['score']} | {row['metric_name']} | {row['metric_value']} |"
        for row in quality.get("dimensions", [])
    ) or "| [Fill] | [Fill] | [Fill] | [Fill] |"

    driver_rows = "\n".join(
        f"| {row.get('name')} | {row.get('current')} | {row.get('base')} | {row.get('status')} |"
        for row in monitoring.get("drivers", [])
    ) or "| [Driver] | [Current] | [Base] | [Status] |"
    risk_rows = "\n".join(
        f"| {row.get('name')} | {row.get('current')} | {row.get('warning')} | {row.get('breach')} | {row.get('status')} |"
        for row in monitoring.get("risks", [])
    ) or "| [Risk] | [Current] | [Warning] | [Breach] | [Status] |"
    catalyst_rows = "\n".join(
        f"| {row.get('name')} | {row.get('date')} | {row.get('days_until')} | {row.get('status')} |"
        for row in monitoring.get("catalysts", [])
    ) or "| [Catalyst] | [Date] | [Days] | [Status] |"

    scenario_rows = "\n".join(
        f"| {row.get('name')} | {fmt_money(row.get('value_per_share'))} | {fmt_pct(row.get('probability'))} |"
        for row in valuation.get("scenarios", [])
    ) or "| [Scenario] | [Value/share] | [Probability] |"

    markdown = f"""# ${company.get('ticker', '[TICKER]')}: [One-sentence variant thesis]

## Executive Summary
- Company: {company.get('name', '[Company]')}
- Current price: {fmt_money(summary.get('current_price'))}
- Weighted target price: {fmt_money(summary.get('weighted_target_price'))}
- Expected value: {fmt_money(summary.get('expected_value_per_share'))}
- Upside vs. current: {fmt_pct(summary.get('upside_pct'))}
- Downside vs. bear: {fmt_pct(summary.get('downside_pct'))}
- Primary / secondary methods: {summary.get('primary_method', '[Primary]')} / {summary.get('secondary_method', '[Secondary]')}
- Action zone: {decision.get('zone', '[Zone]')}
- Quality rating: {quality.get('rating', '[Rating]')} ({quality.get('total_score', '[Score]')}/12)

[Write 2-3 paragraphs that lead with the action and the core reason.]

## Key Forces
1. [Key force 1]
2. [Key force 2]
3. [Key force 3 or remove]

## Business & Earnings Deep Dive
- Revenue growth snapshot: {fmt_pct(summary.get('revenue_growth_forecast'))}
- LTM gross margin: {fmt_pct(model_summary.get('gross_margin_ltm'))}
- LTM EBIT margin: {fmt_pct(model_summary.get('ebit_margin_ltm'))}
- LTM FCF margin: {fmt_pct(model_summary.get('fcf_margin_ltm'))}
- Net debt / EBITDA: {model_summary.get('net_debt_to_ebitda', 'n/a')}
- Interest coverage: {model_summary.get('interest_coverage', 'n/a')}

[Explain the business, the earnings setup, and the key operational debates.]

## Valuation Summary
| Item | Value |
| --- | --- |
| Current price | {fmt_money(summary.get('current_price'))} |
| Weighted target price | {fmt_money(summary.get('weighted_target_price'))} |
| Expected value | {fmt_money(summary.get('expected_value_per_share'))} |
| Bull target | {fmt_money(summary.get('bull_target_price'))} |
| Base target | {fmt_money(summary.get('base_target_price'))} |
| Bear target | {fmt_money(summary.get('bear_target_price'))} |
| Upside | {fmt_pct(summary.get('upside_pct'))} |
| Risk / reward | {decision.get('risk_reward_ratio', 'n/a')} |

| Scenario | Value / Share | Probability |
| --- | --- | --- |
{scenario_rows}

## Variant View
| Dimension | Market-implied | Underwritten | Gap |
| --- | --- | --- | --- |
| Revenue growth | {fmt_pct(variant.get('market_implied_growth'))} | {fmt_pct(variant.get('underwritten_growth'))} | {fmt_pct(summary.get('growth_gap_pct'))} |
| Margin | {fmt_pct(variant.get('market_implied_margin'))} | {fmt_pct(variant.get('underwritten_margin'))} | {fmt_pct(summary.get('margin_gap_pct'))} |
| ROIC | {fmt_pct(variant.get('market_implied_roic'))} | {fmt_pct(variant.get('underwritten_roic'))} | {fmt_pct(summary.get('roic_gap_pct'))} |

[Write the market view, our view, why the market is wrong, and what would falsify the thesis.]

## Quality Overlay
| Dimension | Score | Metric | Value |
| --- | --- | --- | --- |
{quality_rows}

Interpretation: {quality.get('summary', {}).get('interpretation', '[Interpretation]')}

## Risks & Pre-Mortem
- [Risk 1]
- [Risk 2]
- [Risk 3]
- [What failure would look like]
- [Which indicator would warn us first]

## Catalysts & Monitoring
### Drivers
| Driver | Current | Base | Status |
| --- | --- | --- | --- |
{driver_rows}

### Risks
| Risk | Current | Warning | Breach | Status |
| --- | --- | --- | --- | --- |
{risk_rows}

### Catalysts
| Catalyst | Date | Days Until | Status |
| --- | --- | --- | --- |
{catalyst_rows}

## Decision Framework
| Item | Value |
| --- | --- |
| Required return hurdle | {fmt_pct(decision.get('required_return'))} |
| Action price | {fmt_money(decision.get('action_price'))} |
| Trim price | {fmt_money(decision.get('trim_price'))} |
| Expected return | {fmt_pct(decision.get('expected_return_pct'))} |
| Conviction | {decision.get('conviction', '[Conviction]')} |
| Zone | {decision.get('zone', '[Zone]')} |
| Position-size band | {decision.get('size_band', '[Band]')} |
| Pacing | {decision.get('pacing', '[Pacing]')} |

## Evidence Sources
- Model artifacts: [List]
- Valuation artifacts: [List]
- Primary external sources: [List]
- Opinion sources: [List]

## Open Questions
- [Question 1]
- [Question 2]
"""

    Path(args.output).write_text(markdown, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
