#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


PROMPTS = {
    "income_statement": (
        "Using only the uploaded SEC filings, provide a compact table for the last 3 fiscal years "
        "and latest reported quarters with: revenue, gross profit, R&D, SG&A, operating income, "
        "interest expense, pretax income, net income, net income attributable to the company, "
        "net income attributable to noncontrolling interests, and any explicitly stated next-quarter "
        "revenue guidance if present in the uploaded SEC set. Keep it concise and include citations."
    ),
    "balance_sheet": (
        "Using only the uploaded SEC filings, provide a compact table for the last 3 fiscal year ends "
        "and latest reported quarter with: cash, restricted cash if separately disclosed, accounts receivable, "
        "inventory, prepaid and other current assets, PP&E net, goodwill, intangibles net, current debt, "
        "long-term debt, other accrued liabilities, other non-current liabilities, total stockholders' equity, "
        "and noncontrolling interests. Keep it concise and include citations."
    ),
    "cashflow_drivers": (
        "Using only the uploaded SEC filings, summarize operating cash flow, capex, investing cash flow, "
        "financing cash flow, debt paydown or refinancing actions, major asset sale proceeds, and management's "
        "descriptions of key end-market or segment demand drivers. Keep it concise and include citations."
    ),
    "customer_concentration": (
        "Using only the uploaded SEC filings, what exact customer concentration disclosures does the company make "
        "for the last 3 fiscal years? Give the percentages and context concisely, with citations."
    ),
    "guidance_check": (
        "Using only the uploaded SEC filings, does any uploaded 10-K, 10-Q, or 8-K contain explicit next-quarter "
        "revenue guidance or qualitative demand commentary that should affect assumptions? Summarize exactly what "
        "is present, otherwise say not found in uploaded SEC set. Include citations."
    ),
}


def run_json(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{proc.stderr.strip()}")
    return json.loads(proc.stdout)


def main():
    parser = argparse.ArgumentParser(description="Run a standard NotebookLM extraction pack for a company notebook.")
    parser.add_argument("--notebook-id", required=True)
    parser.add_argument("--output", default="nlm_results.json")
    args = parser.parse_args()

    output = {}
    for key, prompt in PROMPTS.items():
        output[key] = run_json(["notebooklm", "ask", "-n", args.notebook_id, prompt, "--json"])

    output_path = Path(args.output).expanduser().resolve()
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
