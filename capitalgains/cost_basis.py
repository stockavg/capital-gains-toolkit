"""Cost basis arithmetic: weighted average, FIFO, and specific identification.

All money is handled with Decimal and rounded *down* to the cent (never up),
which is the convention the calculators on stockavg.com use.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Iterable, Sequence

CENT = Decimal("0.01")
SHARE_DP = Decimal("0.0001")


def _d(x) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


def money(x) -> Decimal:
    """Round a money amount down to two decimals."""
    return _d(x).quantize(CENT, rounding=ROUND_DOWN)


def per_share(x) -> Decimal:
    """Round a per-share price down to four decimals."""
    return _d(x).quantize(SHARE_DP, rounding=ROUND_DOWN)


@dataclass(frozen=True)
class Lot:
    shares: Decimal
    price: Decimal
    date: str | None = None  # ISO date, optional
    fee: Decimal = Decimal("0")

    @property
    def cost(self) -> Decimal:
        return _d(self.shares) * _d(self.price) + _d(self.fee)


@dataclass(frozen=True)
class AverageCost:
    shares: Decimal
    total_cost: Decimal
    average: Decimal


def weighted_average(lots: Iterable[Lot]) -> AverageCost:
    """Weighted average cost per share: total cost / total shares.

    This is the figure stockavg.com prints for a position built from several
    purchases. It is not an average of the prices.
    """
    lots = list(lots)
    if not lots:
        raise ValueError("no lots")
    shares = sum((_d(l.shares) for l in lots), Decimal("0"))
    if shares <= 0:
        raise ValueError("shares must be positive")
    cost = sum((l.cost for l in lots), Decimal("0"))
    return AverageCost(shares, money(cost), per_share(cost / shares))


@dataclass(frozen=True)
class Match:
    lot: Lot
    shares: Decimal
    proceeds: Decimal
    basis: Decimal

    @property
    def gain(self) -> Decimal:
        return money(self.proceeds - self.basis)


def realized_gain_fifo(lots: Sequence[Lot], shares_sold, sale_price, fee=Decimal("0")):
    """Match a sale against the oldest lots first (FIFO) and return the matches."""
    remaining = _d(shares_sold)
    if remaining <= 0:
        raise ValueError("shares_sold must be positive")
    price = _d(sale_price)
    matches: list[Match] = []
    for lot in lots:
        if remaining <= 0:
            break
        take = min(_d(lot.shares), remaining)
        if take <= 0:
            continue
        matches.append(
            Match(
                lot=lot,
                shares=take,
                proceeds=money(take * price),
                basis=money(take * _d(lot.price)),
            )
        )
        remaining -= take
    if remaining > 0:
        raise ValueError("not enough shares in the lots to cover the sale")
    return matches


def realized_gain_specific_id(lots: Sequence[Lot], shares_sold, sale_price, lot_indices=()):
    """Match a sale against named lots, in the order given."""
    price = _d(sale_price)
    matches: list[Match] = []
    remaining = _d(shares_sold)
    for i in lot_indices:
        lot = lots[i]
        take = min(_d(lot.shares), remaining)
        if take <= 0:
            continue
        matches.append(
            Match(lot=lot, shares=take, proceeds=money(take * price), basis=money(take * _d(lot.price)))
        )
        remaining -= take
    if remaining > 0:
        raise ValueError("the named lots do not hold enough shares")
    return matches


def total_gain(matches: Iterable[Match]) -> Decimal:
    return money(sum((m.gain for m in matches), Decimal("0")))
