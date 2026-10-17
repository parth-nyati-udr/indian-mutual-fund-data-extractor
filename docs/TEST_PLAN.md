# Test plan

Run `pytest -q`. All offline.

| Test | Fixture | Expected |
|---|---|---|
| `test_extract_and_find_xlsx` | Next.js page with 2 XLSX + 1 PDF | 2 URLs with JSON paths; query strings and upper-case extensions handled |
| `test_keyword_filter_and_pdf_extension` | Same | Keyword filter, alternate extension |
| `test_missing_next_data_raises` | Plain HTML | ValueError |
| `test_fallback_skips_invalid_and_failed_steps` | Shell page, 403 API, valid PDF | Returns PDF; both earlier failures logged |
| `test_fallback_raises_when_all_fail` | Nothing validates | RuntimeError listing attempts |
| `test_parse_holdings_finds_header_drops_totals` (×2) | XLSX with banners, subtotals; % and fraction weights | 3 holdings, weights in % |
| `test_parse_holdings_no_header_raises` | XLSX without header | ValueError |
| `test_as_on_date` (×4) | "30th September, 2026", "31-Aug-2026", "30/09/2026", none | Correct dates / None |
| `test_allocation_parse_and_classify` | Multi-asset text | Net equity 48.3, debt 42.2, gold 9.5, other 0 |

## Manual checks
1. Run against one live AMC disclosures page; confirm XLSX links resolve.
2. Compare parsed top-10 holdings with the factsheet.
