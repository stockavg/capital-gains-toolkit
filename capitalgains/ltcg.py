"""Long-term capital gains: stacking a gain through the 0 / 15 / 20% bands,
and the 3.8% net investment income tax that sits on top of them.

Thresholds ship in data/federal-ltcg-bands-2026.csv and
data/niit-thresholds.csv, each with the page it came from.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from decimal import Decimal

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

STATUS = {
    "single": "single",
    "mfj": "married filing jointly",
    "mfs": "married filing separately",
    "hoh": "head of household",
}


def _load_bands(year: int = 2026):
    with open(os.path.join(DATA, f"federal-ltcg-bands-{year}.csv"), newline="", encoding="utf-8-sig") as fh:
        return {r["status_key"]: (Decimal(r["zero_ends_at"]), Decimal(r["fifteen_ends_at"])) for r in csv.DictReader(fh)}


def _load_niit():
    with open(os.path.join(DATA, "niit-thresholds.csv"), newline="", encoding="utf-8-sig") as fh:
        return {r["status_key"]: Decimal(r["threshold"]) for r in csv.DictReader(fh)}


@dataclass(frozen=True)
class Band:
    rate: Decimal
    amount: Decimal

    @property
    def tax(self) -> Decimal:
        return (self.amount * self.rate).quantize(Decimal("0.01"))


def ltcg_bands(gain, other_taxable_income, status="single", year=2026):
    """Split a long-term gain over the 0/15/20% bands.

    The gain is stacked on top of other taxable income, so a gain only reaches
    the 0% band when there is room left below the first threshold.
    """
    gain = Decimal(str(gain))
    other = Decimal(str(other_taxable_income))
    if gain < 0:
        raise ValueError("gain must not be negative; a loss is handled by the carryover worksheet")
    zero_end, fifteen_end = _load_bands(year)[status]
    start, end = other, other + gain
    out = []
    for rate, lo, hi in (
        (Decimal("0.00"), Decimal("0"), zero_end),
        (Decimal("0.15"), zero_end, fifteen_end),
        (Decimal("0.20"), fifteen_end, None),
    ):
        if hi is None:
            amount = max(Decimal("0"), end - max(start, lo))
        else:
            amount = max(Decimal("0"), min(end, hi) - max(start, lo))
        if amount > 0:
            out.append(Band(rate, amount))
    return out


def ltcg_tax(gain, other_taxable_income, status="single", year=2026) -> Decimal:
    return sum((b.tax for b in ltcg_bands(gain, other_taxable_income, status, year)), Decimal("0.00"))


def niit(net_investment_income, magi, status="single") -> Decimal:
    """3.8% on the lesser of net investment income or MAGI above the threshold."""
    nii = Decimal(str(net_investment_income))
    magi = Decimal(str(magi))
    threshold = _load_niit()[status]
    excess = max(Decimal("0"), magi - threshold)
    return (min(nii, excess) * Decimal("0.038")).quantize(Decimal("0.01"))
