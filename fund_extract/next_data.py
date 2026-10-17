"""Next.js sites ship their page data as JSON in <script id="__NEXT_DATA__">.

Instead of rendering the JS, read that JSON and walk it for the links you
need (e.g. monthly portfolio XLSX files on an AMC disclosures page).
"""
from __future__ import annotations

import json
import re
from typing import Iterator

_NEXT = re.compile(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def extract_next_data(html: str) -> dict:
    """Return the parsed __NEXT_DATA__ JSON; ValueError if absent."""
    m = _NEXT.search(html)
    if not m:
        raise ValueError("No __NEXT_DATA__ block (not a Next.js page, or content is client-fetched).")
    return json.loads(m.group(1))


def _walk(node, path=()) -> Iterator[tuple[tuple, object]]:
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, path + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, path + (i,))
    else:
        yield path, node


def find_file_urls(tree: dict, extensions=(".xlsx", ".xls"), keyword: str | None = None) -> list[dict]:
    """All string values ending in `extensions` (query strings allowed).

    Returns [{'url', 'path'}] where path is the JSON location, which helps
    when the same page lists several fund families. Optional case-insensitive
    `keyword` filter on the URL.
    """
    out, seen = [], set()
    for path, val in _walk(tree):
        if not isinstance(val, str):
            continue
        base = val.split("?")[0].lower()
        if base.endswith(tuple(e.lower() for e in extensions)) and val not in seen:
            if keyword and keyword.lower() not in val.lower():
                continue
            seen.add(val)
            out.append({"url": val, "path": "/".join(map(str, path))})
    return out
