# Method Router

Choose valuation methods by economic structure, not by habit.

## Core Routing Questions

1. Is value mainly driven by forward cash flow?
2. Is the asset base itself the main source of value?
3. Are returns constrained by regulation?
4. Are outcomes binary or probability-driven?
5. Does book value approximate earning power?

## Default Method Families

| Company Type | Primary | Secondary |
|---|---|---|
| Software / internet / recurring-growth | DCF | EV/Revenue or comps |
| Semiconductor / industrial cyclicals | Mid-cycle DCF | EV/EBITDA comps |
| Stable industrial / devices / staples | DCF | EV/EBITDA or P/E |
| REIT / property | NAV | AFFO multiple |
| Bank | P/B vs ROE / ROTCE | Residual income |
| Insurance | P/B vs ROE | Embedded value or residual income |
| Utility / regulated asset | DDM or RAB | EV/EBITDA or yield |
| E&P / mining reserves | NAV | EV/EBITDA or P/NAV |
| Pharma with pipeline mix | DCF + asset-level adjustments | comps |
| Clinical biotech | rNPV | cash runway / scenario |
| Conglomerate / mixed businesses | SOTP | consolidated DCF |

## Routing Rules

- Use enterprise-value methods when operations are the core object being valued.
- Use equity-value methods when balance sheet / book value is the proper anchor.
- Use asset-value methods when reserves, property, or regulated asset base dominate.
- Use probability-weighted methods when binary outcomes dominate.

## Mandatory Secondary Method

Every case needs one secondary method, except in rare situations where:

- there is no credible peer set
- the business is singular and asset-specific
- or the user explicitly requests a single-method analysis

Even then, add reverse DCF or implied expectations as the cross-check.

## Peer Set Rules

Document:

- inclusion criteria
- exclusion criteria
- fiscal-period alignment
- one-time adjustment policy
- outlier trimming policy

Do not average peers blindly. Explain why each peer belongs.
