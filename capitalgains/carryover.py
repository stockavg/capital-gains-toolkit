"""The Schedule D Capital Loss Carryover Worksheet, as arithmetic.

The worksheet has 13 printed lines. Field references move with the tax year,
so the line *numbers* below are the worksheet's own; the figures you pass in
are the four amounts it asks for from the prior year's return.

Sign convention: losses are passed as positive amounts, gains as positive
amounts. The function applies the printed additions and subtractions.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


def _d(x) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


@dataclass(frozen=True)
class Carryover:
    line3: Decimal
    line4: Decimal
    line7: Decimal
    line8_short_term: Decimal
    line11: Decimal
    line12: Decimal
    line13_long_term: Decimal

    @property
    def short_term(self) -> Decimal:
        return self.line8_short_term

    @property
    def long_term(self) -> Decimal:
        return self.line13_long_term


def carryover(
    *,
    income_line1,
    allowed_loss_line2,
    st_loss_line5,
    st_gain_line6=0,
    lt_loss_line9=0,
    lt_gain_line10=0,
) -> Carryover:
    """Run the 13-line worksheet.

    income_line1        prior-year Form 1040, line 15 (taxable income)
    allowed_loss_line2  prior-year Schedule D, line 21, the loss actually deducted
    st_loss_line5       prior-year Schedule D, line 7 (short-term loss, positive)
    st_gain_line6       prior-year Schedule D, line 15 (long-term gain, positive)
    lt_loss_line9       prior-year Schedule D, line 15 (long-term loss, positive)
    lt_gain_line10      prior-year Schedule D, line 7 (short-term gain, positive)

    When line 3 comes out at zero or less the printed form has you enter -0-
    and skip to line 9, which leaves the short-term loss on line 5 untouched;
    that branch is implemented here and is called out in the README, because
    it is the one place where a reading of the instructions, rather than the
    plain arithmetic, decides the answer.
    """
    l1 = _d(income_line1)
    l2 = _d(allowed_loss_line2)
    l5 = _d(st_loss_line5)
    l6 = _d(st_gain_line6)
    l9 = _d(lt_loss_line9)
    l10 = _d(lt_gain_line10)

    if l2 < 0 or l5 < 0 or l6 < 0 or l9 < 0 or l10 < 0:
        raise ValueError("pass losses and gains as positive amounts")

    l3 = max(Decimal("0"), l1 + l2)
    if l3 == 0:
        short = l5
        return Carryover(l3, Decimal("0"), l6, short, Decimal("0"), l10, max(Decimal("0"), l9 - l10))

    l4 = min(l2, l3)
    l7 = l4 + l6
    l8 = max(Decimal("0"), l5 - l7)
    l11 = max(Decimal("0"), l4 - l5)
    l12 = l10 + l11
    l13 = max(Decimal("0"), l9 - l12)
    return Carryover(l3, l4, l7, l8, l11, l12, l13)
