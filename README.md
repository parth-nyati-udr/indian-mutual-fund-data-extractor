# Indian Mutual Fund Data Extractor

Mutual fund disclosures are public but awkward to get at: JavaScript-rendered AMC sites, XLSX files with banner rows and merged cells, and PDF factsheets that are sometimes a month stale. This package turns them into clean tables.

| Module | Problem it solves |
|---|---|
| `next_data` | Next.js pages hide links inside `__NEXT_DATA__` JSON. Read the JSON instead of rendering JavaScript. |
| `fetcher` | Ordered fallback: plain GET → hidden JSON API → PDF → headless browser, with validation at each step. |
| `holdings_xlsx` | Finds the real header row in a portfolio disclosure, drops subtotals, normalises weights. |
| `factsheet` | Extracts the "as on" date and asset-allocation lines from factsheet text. |
| `allocation` | Converts a multi-asset fund's disclosure to economic exposure (net equity, hedge as debt, MF units as gold/silver). |

## Install
```bash
pip install -e ".[dev,pdf]"          # add [browser] + `playwright install chromium` for step 4
```

## Example
```python
import requests
from fund_extract import extract_next_data, find_file_urls, parse_holdings_xlsx

html = requests.get("<AMC disclosures page>", headers={"User-Agent": "Mozilla/5.0"}).text
links = find_file_urls(extract_next_data(html), keyword="flexi")
holdings = parse_holdings_xlsx(requests.get(links[0]["url"]).content)
```

## Layout
```
fund_extract/  next_data.py  fetcher.py  holdings_xlsx.py  factsheet.py  allocation.py
tests/         13 offline tests with HTML, XLSX and text fixtures
docs/          SCOPE.md, METHODOLOGY.md, TEST_PLAN.md
```

## Responsible use
Fetches public disclosure documents only. Respect each site's terms and rate limits. `verify=False` exists for sites with broken certificate chains; don't use it for anything carrying credentials.

## License
MIT
