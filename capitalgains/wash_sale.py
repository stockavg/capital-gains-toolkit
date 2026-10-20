"""Wash-sale window arithmetic.

The wash-sale rule (IRC 1091, IRS Publication 550) disallows a loss when
substantially identical securities are bought within 30 days before or after
the sale. Counting both ends, that is a 61-day window around the sale.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

WINDOW_DAYS = 30


def parse(d: str) -> date:
    return date.fromisoformat(d)


@dataclass(frozen=True)
class Window:
    sale: date
    start: date
    end: date

    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end


def replacement_window(sale_date: str | date) -> Window:
    """The 61-day window: 30 days before the sale through 30 days after it."""
    s = parse(sale_date) if isinstance(sale_date, str) else sale_date
    return Window(sale=s, start=s - timedelta(days=WINDOW_DAYS), end=s + timedelta(days=WINDOW_DAYS))


def is_replacement(sale_date, buy_date) -> bool:
    """True when a purchase falls inside the wash-sale window of the sale."""
    b = parse(buy_date) if isinstance(buy_date, str) else buy_date
    return replacement_window(sale_date).contains(b)


def disallowed_loss(loss, sold_shares, replacement_shares) -> Decimal:
    """Share of a loss disallowed by a replacement purchase.

    Simplified, and deliberately so: the loss disallowed cannot exceed the
    loss on the sale, and it cannot exceed the share of the position that was
    actually replaced. Real filings allocate the disallowed amount to the
    replacement lots and adjust their basis; that allocation is not modelled
    here.
    """
    loss = Decimal(str(loss))
    sold = Decimal(str(sold_shares))
    repl = Decimal(str(replacement_shares))
    if sold <= 0:
        raise ValueError("sold_shares must be positive")
    if repl <= 0:
        return Decimal("0.00")
    fraction = min(Decimal("1"), repl / sold)
    return (loss * fraction).quantize(Decimal("0.01"))
