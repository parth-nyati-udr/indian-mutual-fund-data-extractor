# Scope

## The ask
Reliably pull mutual fund holdings and allocation data from AMC websites that resist simple scraping, and convert disclosures into economically meaningful exposure for portfolio look-through.

## In scope
- Next.js pages with `__NEXT_DATA__`.
- A generic four-step fetch fallback with validation.
- AMC monthly portfolio XLSX parsing.
- Factsheet text: as-on date and allocation lines.
- Multi-asset / balanced-advantage exposure classification.

## Out of scope
- Site-specific crawlers for every AMC (the building blocks are generic).
- OCR of scanned PDFs.
- Authenticated sources (CAS, broker logins).
- NAV and returns (see `mf-analytics`).

## Assumptions
- Disclosure XLSX files contain a header with an instrument-name column and a "% to net assets" column.
- In multi-asset funds, "Units of Mutual Fund" are gold/silver ETFs; verify per fund.

## Success criteria
- Offline tests pass on realistic fixtures.
- Failures are explicit (a list of what each fetch step returned), never silent.
