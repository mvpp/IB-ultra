#!/usr/bin/env python3
import argparse
from datetime import date

from memo_common import dump_json, iso_days_until, load_json


def evaluate_driver(item):
    current = item.get("current")
    base = item.get("base")
    bull = item.get("bull")
    bear = item.get("bear")
    direction = str(item.get("direction", "higher_better")).lower()

    if current is None:
        status = "missing"
    elif direction == "lower_better":
        if bull is not None and current <= bull:
            status = "outperform"
        elif base is not None and current <= base:
            status = "on_track"
        elif bear is not None and current <= bear:
            status = "watch"
        else:
            status = "breach"
    else:
        if bull is not None and current >= bull:
            status = "outperform"
        elif base is not None and current >= base:
            status = "on_track"
        elif bear is not None and current >= bear:
            status = "watch"
        else:
            status = "breach"

    return {
        **item,
        "status": status,
        "green_trigger": base,
        "red_trigger": bear,
    }


def evaluate_risk(item):
    current = item.get("current")
    warning = item.get("warning")
    breach = item.get("breach")
    direction = str(item.get("direction", "lower_better")).lower()

    if current is None:
        status = "missing"
    elif direction == "higher_better":
        if breach is not None and current < breach:
            status = "red"
        elif warning is not None and current < warning:
            status = "yellow"
        else:
            status = "green"
    else:
        if breach is not None and current > breach:
            status = "red"
        elif warning is not None and current > warning:
            status = "yellow"
        else:
            status = "green"

    return {**item, "status": status}


def evaluate_catalyst(item, today):
    days_until = iso_days_until(item.get("date"), today=today)
    if days_until is None:
        status = "undated"
    elif days_until < 0:
        status = "past"
    elif days_until <= 30:
        status = "near_term"
    elif days_until <= 90:
        status = "medium_term"
    else:
        status = "longer_term"
    return {**item, "days_until": days_until, "status": status}


def overall_status(drivers, risks):
    statuses = [item["status"] for item in drivers + risks]
    if "breach" in statuses or "red" in statuses:
        return "red"
    if "watch" in statuses or "yellow" in statuses:
        return "yellow"
    return "green"


def main():
    parser = argparse.ArgumentParser(
        description="Build a monitoring dashboard from memo monitoring inputs."
    )
    parser.add_argument("--input", required=True, help="Path to memo_input_pack JSON")
    parser.add_argument("--output", default="monitoring_dashboard.json", help="Path to JSON output")
    args = parser.parse_args()

    pack = load_json(args.input)
    monitoring_inputs = pack.get("monitoring_inputs", {})
    today = date.today()

    drivers = [evaluate_driver(item) for item in monitoring_inputs.get("drivers", [])]
    risks = [evaluate_risk(item) for item in monitoring_inputs.get("risks", [])]
    catalysts = [evaluate_catalyst(item, today) for item in monitoring_inputs.get("catalysts", [])]

    result = {
        "drivers": drivers,
        "risks": risks,
        "catalysts": catalysts,
        "overall_status": overall_status(drivers, risks),
    }
    dump_json(args.output, result)
    print(args.output)


if __name__ == "__main__":
    main()
