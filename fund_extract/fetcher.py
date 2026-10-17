"""Ordered fallback chain for pages that are hard to fetch.

1. Plain GET with a browser User-Agent (verify=False tolerates the broken
   certificate chains some AMC sites serve).
2. The site's hidden JSON API (find it in DevTools > Network > Fetch/XHR).
3. The PDF factsheet from the AMC's main domain.
4. Headless Playwright, last resort (slow, heavy dependency).

Each step's output is checked by a validator, so a 200 response containing
a cookie wall or empty shell doesn't count as success.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import requests
import urllib3

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}


@dataclass
class FetchResult:
    method: str
    content: bytes
    attempts: list[str] = field(default_factory=list)


def _get(url: str) -> bytes:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    r = requests.get(url, headers=UA, timeout=30, verify=False)
    r.raise_for_status()
    return r.content


def _playwright(url: str) -> bytes:
    from playwright.sync_api import sync_playwright  # optional dependency
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        page.goto(url, wait_until="networkidle")
        html = page.content()
        b.close()
    return html.encode()


def fetch_with_fallback(page_url: str, validate: Callable[[bytes], bool],
                        api_url: str | None = None, pdf_url: str | None = None,
                        allow_browser: bool = False, getter: Callable[[str], bytes] = _get) -> FetchResult:
    """Try each source in order; return the first whose content passes `validate`.

    Raises RuntimeError listing every attempt if all fail.
    """
    steps = [("requests", page_url), ("hidden_api", api_url), ("pdf", pdf_url)]
    attempts = []
    for name, url in steps:
        if not url:
            continue
        try:
            content = getter(url)
            if validate(content):
                return FetchResult(name, content, attempts + [f"{name}: ok"])
            attempts.append(f"{name}: fetched but failed validation")
        except Exception as e:  # noqa: BLE001 - record and continue the chain
            attempts.append(f"{name}: {type(e).__name__}: {e}")
    if allow_browser:
        try:
            content = _playwright(page_url)
            if validate(content):
                return FetchResult("playwright", content, attempts + ["playwright: ok"])
            attempts.append("playwright: failed validation")
        except Exception as e:  # noqa: BLE001
            attempts.append(f"playwright: {type(e).__name__}: {e}")
    raise RuntimeError("All fetch methods failed:\n  " + "\n  ".join(attempts))
