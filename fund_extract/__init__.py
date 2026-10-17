"""fund-data-extractors: get fund disclosures out of JS-heavy AMC sites, PDFs and XLSX files."""
from .next_data import extract_next_data, find_file_urls
from .fetcher import fetch_with_fallback, FetchResult
from .holdings_xlsx import parse_holdings_xlsx
from .factsheet import find_as_on_date, parse_asset_allocation
from .allocation import classify_multi_asset

__version__ = "1.0.0"
