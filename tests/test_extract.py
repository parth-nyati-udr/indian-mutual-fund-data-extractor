import json
from datetime import date
from io import BytesIO

import openpyxl
import pytest

from fund_extract import (classify_multi_asset, extract_next_data, fetch_with_fallback,
                          find_as_on_date, find_file_urls, parse_asset_allocation, parse_holdings_xlsx)


# ---- __NEXT_DATA__ --------------------------------------------------------
def page(payload):
    return f'<html><body><script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script></body></html>'


DISCLOSURES = {"props": {"pageProps": {"sections": [
    {"title": "Monthly Portfolio", "files": [
        {"name": "Flexi Cap Sep-26", "link": "https://cdn.amc.example/portfolio/FlexiCap_Sep2026.xlsx?v=3"},
        {"name": "Mid Cap Sep-26", "link": "https://cdn.amc.example/portfolio/MidCap_Sep2026.XLSX"}]},
    {"title": "Factsheet", "files": [{"link": "https://cdn.amc.example/factsheet.pdf"}]}]}}}


def test_extract_and_find_xlsx():
    urls = find_file_urls(extract_next_data(page(DISCLOSURES)))
    assert len(urls) == 2 and urls[0]["path"].startswith("props/pageProps/sections/0")


def test_keyword_filter_and_pdf_extension():
    tree = extract_next_data(page(DISCLOSURES))
    assert [u["url"] for u in find_file_urls(tree, keyword="midcap")][0].endswith(".XLSX")
    assert len(find_file_urls(tree, extensions=(".pdf",))) == 1


def test_missing_next_data_raises():
    with pytest.raises(ValueError):
        extract_next_data("<html></html>")


# ---- fallback chain -------------------------------------------------------
def test_fallback_skips_invalid_and_failed_steps():
    responses = {"page": b"<html>enable javascript</html>", "api": RuntimeError("403"), "pdf": b"%PDF-1.7 data"}

    def getter(url):
        r = responses[url]
        if isinstance(r, Exception):
            raise r
        return r

    res = fetch_with_fallback("page", validate=lambda c: c.startswith(b"%PDF"),
                              api_url="api", pdf_url="pdf", getter=getter)
    assert res.method == "pdf"
    assert "failed validation" in res.attempts[0] and "403" in res.attempts[1]


def test_fallback_raises_when_all_fail():
    with pytest.raises(RuntimeError, match="All fetch methods failed"):
        fetch_with_fallback("p", validate=lambda c: False, getter=lambda u: b"x")


# ---- holdings XLSX --------------------------------------------------------
def make_xlsx(fraction=False):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["XYZ Mutual Fund"])
    ws.append(["Portfolio as on 30-Sep-2026"])
    ws.append([])
    ws.append(["Name of the Instrument", "ISIN", "Quantity", "% to Net Assets"])
    rows = [("HDFC Bank Ltd", "INE040A01034", 100, 8.5), ("Infosys Ltd", "INE009A01021", 50, 6.25),
            ("Sub Total", None, None, 14.75), ("TREPS", None, None, 2.0), ("Grand Total", None, None, 100)]
    for n, i, q, w in rows:
        ws.append([n, i, q, w / 100 if fraction else w])
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.parametrize("fraction", [False, True])
def test_parse_holdings_finds_header_drops_totals(fraction):
    df = parse_holdings_xlsx(make_xlsx(fraction))
    assert df["instrument"].tolist() == ["HDFC Bank Ltd", "Infosys Ltd", "TREPS"]
    assert df.loc[0, "weight_pct"] == pytest.approx(8.5)


def test_parse_holdings_no_header_raises():
    wb = openpyxl.Workbook(); wb.active.append(["nothing", "here"])
    buf = BytesIO(); wb.save(buf)
    with pytest.raises(ValueError):
        parse_holdings_xlsx(buf.getvalue())


# ---- factsheet text -------------------------------------------------------
@pytest.mark.parametrize("text,expected", [
    ("Factsheet as on 30th September, 2026", date(2026, 9, 30)),
    ("Portfolio As On: 31-Aug-2026", date(2026, 8, 31)),
    ("data as on 30/09/2026", date(2026, 9, 30)),
    ("no date here", None),
])
def test_as_on_date(text, expected):
    assert find_as_on_date(text) == expected


def test_allocation_parse_and_classify():
    text = "Equity 72.4%\nEquity Hedged (Derivatives): -24.1%\nDebt 15.0%\nUnits of Mutual Fund 9.5%\nCash & Equivalents 3.1%"
    alloc = parse_asset_allocation(text)
    assert alloc["Equity"] == 72.4 and len(alloc) == 5
    c = classify_multi_asset(alloc)
    assert c["equity_net"] == pytest.approx(48.3)
    assert c["debt"] == pytest.approx(42.2)      # 15 + 3.1 cash + 24.1 hedge
    assert c["gold_silver"] == 9.5
    assert abs(c["other"]) < 0.01
