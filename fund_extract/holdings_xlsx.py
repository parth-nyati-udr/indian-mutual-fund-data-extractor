"""Parse AMC monthly portfolio disclosure XLSX files.

These files have banner rows, merged cells and footers. Locate the real
header row by its column names instead of assuming a fixed row number.
"""
from __future__ import annotations

from io import BytesIO

import pandas as pd

NAME_COLS = ("name of the instrument", "name of instrument", "company name", "security name")
WEIGHT_COLS = ("% to net assets", "% to nav", "% of net assets", "% to aum")


def _match(cell, options) -> bool:
    return isinstance(cell, str) and any(o in " ".join(cell.lower().split()) for o in options)


def parse_holdings_xlsx(data: bytes | str, sheet: int | str = 0) -> pd.DataFrame:
    """Return holdings as DataFrame[instrument, weight_pct, ...other columns].

    Drops subtotal/total rows and blank lines. Weight is converted to percent
    (0.052 fractions become 5.2) when the column is clearly fractional.
    """
    src = BytesIO(data) if isinstance(data, bytes) else data
    raw = pd.read_excel(src, sheet_name=sheet, header=None, engine="openpyxl")
    header_row = next((i for i, row in raw.iterrows()
                       if any(_match(c, NAME_COLS) for c in row) and any(_match(c, WEIGHT_COLS) for c in row)), None)
    if header_row is None:
        raise ValueError("Could not find a header row with instrument name and % to net assets.")
    df = raw.iloc[header_row + 1:].copy()
    df.columns = [str(c).strip() for c in raw.iloc[header_row]]
    name_col = next(c for c in df.columns if _match(c, NAME_COLS))
    wt_col = next(c for c in df.columns if _match(c, WEIGHT_COLS))
    df = df.rename(columns={name_col: "instrument", wt_col: "weight_pct"})
    df["weight_pct"] = pd.to_numeric(df["weight_pct"], errors="coerce")
    df = df[df["instrument"].notna() & df["weight_pct"].notna()]
    df = df[~df["instrument"].astype(str).str.lower().str.contains(r"\b(?:sub ?total|grand total|total)\b")]
    if df["weight_pct"].sum() <= 1.5:  # stored as fractions
        df["weight_pct"] = df["weight_pct"] * 100
    return df.reset_index(drop=True)
