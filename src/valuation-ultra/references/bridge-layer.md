# Bridge Layer

Build this layer before any valuation method. The goal is to transform the 3-statement
model into standardized valuation inputs.

## Required Build

Create `Valuation_Prep` with these sections:

1. `Operating Earnings`
   - Revenue
   - EBIT
   - tax-adjusted EBIT / NOPAT
   - D&A
   - SBC if material

2. `Cash Flow`
   - CFO
   - capex
   - unlevered FCF
   - levered FCF if relevant
   - maintenance vs growth capex if relevant

3. `Reinvestment`
   - change in NWC
   - capex
   - acquisitions / disposals treatment
   - reinvestment rate
   - sales-to-capital or incremental ROIC check

4. `Capital Base`
   - invested capital
   - ROIC
   - incremental ROIC where possible

5. `EV Bridge Inputs`
   - cash
   - restricted cash policy
   - total debt
   - lease liabilities
   - preferreds / hybrids
   - minority interest
   - unconsolidated investments
   - pension deficit / surplus
   - other non-operating assets or liabilities

6. `Share Bridge`
   - basic shares
   - in-the-money options / RSUs
   - convertibles
   - buyback assumptions
   - fully diluted shares

## Adjustment Rules

- Keep GAAP and adjusted views side by side when non-GAAP is used.
- Do not remove SBC without explicit justification.
- Do not treat restructuring, litigation, earnouts, or acquisition costs as automatically
  non-recurring; classify them deliberately.
- If the company is cyclical, create both reported and normalized earnings / cash flow views.
- If acquisitions are frequent, show acquired growth separately from organic growth.

## Output Checks

The bridge is complete only if:

- NOPAT, FCF, invested capital, ROIC, net debt, and diluted shares all reconcile
- every valuation method can reference this tab without re-reading raw filings
- the EV bridge and share bridge are explicit, not buried in notes
