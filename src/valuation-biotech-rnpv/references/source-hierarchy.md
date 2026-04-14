# Pipeline Source Hierarchy

Use primary sources only for pipeline facts whenever possible.

## Recommended Hierarchy

1. Company official disclosures for asset ownership, economics, and management framing:

- SEC EDGAR filings like `10-K`, `10-Q`, `20-F`, `6-K`, and `8-K`
- official pipeline pages
- official investor presentations and earnings decks

2. Official trial registries for stage, status, enrollment, and dates:

- [ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/about-api)
- [ClinicalTrials.gov Study Data Structure](https://clinicaltrials.gov/data-api/about-api/study-data-structure)

3. Official regulatory databases for approval and filing status:

- [Drugs@FDA](https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-database)
- [Purple Book Search](https://purplebooksearch.fda.gov/)
- [EMA Medicines Finder](https://www.ema.europa.eu/en/medicines)
- [EMA Download Medicine Data](https://www.ema.europa.eu/en/medicines/download-medicine-data)

4. Official literature and abstract sources for readouts:

- [NCBI PubMed / E-utilities](https://www.ncbi.xyz/books/NBK25499/)
- official abstract pages from AACR, ASCO, ESMO, SITC, and other relevant congresses

## How To Use Sources In This Pack

- Asset existence, ownership, and partner economics:
  default to company SEC and official IR materials.
- Trial phase, status, and completion dates:
  default to ClinicalTrials.gov when available.
- Approval, filing, or withdrawal status:
  default to FDA / EMA databases.
- Efficacy and safety claims:
  prefer peer-reviewed publications or official conference abstracts over summaries.

## What This Pack Treats As Assumptions

The following should be explicit model inputs, not scraped "facts":

- probability of success
- peak sales
- launch timing when not officially guided
- operating margin and royalty economics beyond what is disclosed
- discount rate

## Provenance Rule

Each asset in `pipeline_registry.json` should carry:

- source type
- authority
- URL or citation
- date
- whether the source is company, trial registry, regulatory, or literature
