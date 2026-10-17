"""Turn a multi-asset / balanced-advantage fund's disclosed allocation into
economic exposure.

Rules:
- Use NET equity: gross equity minus derivative hedges.
- The hedged portion behaves like debt (arbitrage carry), so count it as debt.
- 'Units of Mutual Fund' lines in these funds are usually gold/silver ETFs.
"""
from __future__ import annotations


def _find(alloc: dict[str, float], *keys) -> float:
    tot = 0.0
    for label, v in alloc.items():
        if any(k in label.lower() for k in keys):
            tot += v
    return tot


def classify_multi_asset(alloc: dict[str, float]) -> dict[str, float]:
    """Map disclosed lines to {equity_net, debt, gold_silver, other}, summing to ~100.

    Hedge lines may be disclosed negative or positive; magnitude is used.
    """
    hedge = abs(_find(alloc, "hedge", "derivative", "futures", "arbitrage"))
    gross_eq = sum(v for k, v in alloc.items()
                   if "equity" in k.lower() and not any(h in k.lower() for h in ("hedge", "derivative")))
    debt = _find(alloc, "debt", "bond", "g-sec", "gsec", "treasury", "money market", "cash", "tbill", "t-bill", "reverse repo", "treps")
    gold = _find(alloc, "units of mutual fund", "gold", "silver", "commodit")
    out = {"equity_net": round(gross_eq - hedge, 2), "debt": round(debt + hedge, 2), "gold_silver": round(gold, 2)}
    out["other"] = round(100 - sum(out.values()), 2)
    return out
