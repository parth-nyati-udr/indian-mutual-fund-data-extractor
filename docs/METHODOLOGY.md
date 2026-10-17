# Methodology

## 1. `__NEXT_DATA__`
Next.js server-renders page props into `<script id="__NEXT_DATA__">`. Parsing that JSON returns the same data the browser would render, without executing JavaScript. The walker returns every matching URL with its JSON path, which disambiguates fund families on one page. This approach was used to recover monthly portfolio XLSX links from a large AMC's disclosures page.

## 2. Fetch fallback order
1. `requests` + browser User-Agent (`verify=False` for broken cert chains).
2. Hidden JSON API, found in DevTools → Network → Fetch/XHR.
3. PDF factsheet from the AMC's main domain (parse with pdfplumber).
4. Headless Playwright, last because it is slow and heavy.

Every step's output goes through a caller-supplied `validate()`. A 200 response containing "enable JavaScript" is a failure, not a success.

## 3. Holdings XLSX
Scan rows for one containing both an instrument-name column and a weight column, then use it as the header. Drop rows labelled Sub Total / Total / Grand Total and blanks. If weights sum to ≤ 1.5 they are fractions, so multiply by 100.

## 4. Always check "as on"
Factsheet links are often updated late. Parse the as-on date and compare it with what you expected before using the numbers.

## 5. Multi-asset exposure
| Disclosed line | Treated as |
|---|---|
| Equity (gross) − hedged/derivatives | Net equity |
| Hedged / derivatives | Debt (arbitrage carry) |
| Debt, G-sec, T-bill, TREPS, cash | Debt |
| Units of Mutual Fund, gold, silver | Gold/silver |
