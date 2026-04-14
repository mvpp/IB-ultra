#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path

from dotenv import dotenv_values
from sec_edgar_downloader import Downloader


def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{proc.stderr.strip()}")
    return proc.stdout


def run_json(cmd):
    return json.loads(run(cmd))


def list_filing_texts(base_dir: Path, ticker: str):
    ticker_dir = base_dir / "sec-edgar-filings" / ticker.upper()
    return sorted(ticker_dir.glob("**/full-submission.txt"))


def main():
    parser = argparse.ArgumentParser(description="Download SEC filings and seed a NotebookLM notebook.")
    parser.add_argument("--ticker", required=True, help="SEC ticker, e.g. COHR")
    parser.add_argument("--download-dir", default="sec_filings", help="Download directory")
    parser.add_argument("--env-file", default=str(Path.home() / "Programs" / ".env"), help="Env file holding SEC_EDGAR_EMAIL")
    parser.add_argument("--company-name", default="skill-bootstrap", help="EDGAR company name for downloader")
    parser.add_argument("--notebook-id", help="Reuse an existing NotebookLM notebook")
    parser.add_argument("--notebook-title", help="Notebook title if creating a new notebook")
    parser.add_argument("--tenk-limit", type=int, default=2)
    parser.add_argument("--tenq-limit", type=int, default=4)
    parser.add_argument("--eightk-limit", type=int, default=4)
    args = parser.parse_args()

    env = dotenv_values(args.env_file)
    email = env.get("SEC_EDGAR_EMAIL")
    if not email:
        raise SystemExit(f"SEC_EDGAR_EMAIL missing in {args.env_file}")

    download_dir = Path(args.download_dir).expanduser().resolve()
    download_dir.mkdir(parents=True, exist_ok=True)

    downloader = Downloader(
        company_name=args.company_name,
        email_address=email,
        download_folder=str(download_dir),
    )
    downloader.get("10-K", args.ticker, limit=args.tenk_limit)
    downloader.get("10-Q", args.ticker, limit=args.tenq_limit)
    downloader.get("8-K", args.ticker, limit=args.eightk_limit)

    notebook_id = args.notebook_id
    if not notebook_id:
        title = args.notebook_title or f"{args.ticker.upper()} SEC Filings"
        created = run_json(["notebooklm", "create", title, "--json"])
        notebook_id = created["notebook"]["id"]

    run(["notebooklm", "use", notebook_id])

    source_ids = []
    for filing_path in list_filing_texts(download_dir, args.ticker):
        added = run_json(["notebooklm", "source", "add", str(filing_path), "-n", notebook_id, "--json"])
        source_ids.append(added["source"]["id"])

    for source_id in source_ids:
        run(["notebooklm", "source", "wait", source_id, "-n", notebook_id])

    summary = {
        "ticker": args.ticker.upper(),
        "notebook_id": notebook_id,
        "download_dir": str(download_dir),
        "uploaded_sources": source_ids,
        "filing_texts": [str(p) for p in list_filing_texts(download_dir, args.ticker)],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
