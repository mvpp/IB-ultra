# SEC + NotebookLM Bootstrap

Use this reference when the target company is a US SEC filer and the environment has:

- `SEC_EDGAR_EMAIL` available in an env file such as `~/Programs/.env`
- `notebooklm-py` installed and authenticated

## Default Policy

For US-listed / SEC-reporting companies, this fork should prefer:

1. Download `10-K`, `10-Q`, and earnings-relevant `8-K` filings from EDGAR
2. Create a dedicated NotebookLM notebook for the ticker
3. Upload the downloaded filing texts into that notebook
4. Run the structured extraction prompts from NotebookLM
5. Use web only as a cross-check or to fill non-filing guidance gaps

Do not default to Yahoo / Sina / web snippets when SEC + NotebookLM is available.

## Dependencies

```bash
pip install openpyxl yfinance pandas python-dotenv sec-edgar-downloader
pip install "notebooklm-py[browser]"
python -m playwright install chromium
```

## One-Time NotebookLM Auth

```bash
notebooklm login
notebooklm status --paths
```

Expected auth path:

```text
~/.notebooklm/storage_state.json
```

## Bootstrap Script

Use the bundled bootstrap script instead of rewriting the EDGAR + NotebookLM upload flow:

```bash
python scripts/sec_nlm_bootstrap.py --ticker COHR
```

This script:

- reads `SEC_EDGAR_EMAIL`
- downloads recent `10-K`, `10-Q`, and `8-K` filings
- creates a new NotebookLM notebook unless one is provided
- uploads each filing text to NotebookLM
- waits for indexing to complete

Key options:

```bash
python scripts/sec_nlm_bootstrap.py --ticker COHR --notebook-title "COHR SEC Filings"
python scripts/sec_nlm_bootstrap.py --ticker COHR --notebook-id <ID>
python scripts/sec_nlm_bootstrap.py --ticker COHR --env-file ~/Programs/.env
```

## Extraction Script

After the notebook is ready:

```bash
python scripts/nlm_extract_company_pack.py --notebook-id <NOTEBOOK_ID>
```

This writes a JSON file containing:

- income statement extraction
- balance sheet extraction
- cash flow / capital structure / demand driver extraction
- customer concentration extraction
- guidance / demand commentary check

## Merge Rule

When SEC + NotebookLM is available:

- SEC + NotebookLM = primary source
- Excel upload = secondary cross-check / speed layer
- Web = tertiary cross-check / non-filing supplement

If NotebookLM does not find an explicit guidance figure in the uploaded SEC set, label it as
`not found in uploaded SEC set` and keep any external IR guidance separate from filing-only assumptions.
