import sys
import os
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from capitalgains import (  # noqa: E402
    Lot,
    carryover,
    disallowed_loss,
    is_replacement,
    ltcg_bands,
    ltcg_tax,
    niit,
    realized_gain_fifo,
    replacement_window,
    weighted_average,
)


class TestCostBasis(unittest.TestCase):
    def test_weighted_average_is_not_the_mean_of_prices(self):
        r = weighted_average([Lot(100, 50), Lot(50, 60)])
        self.assertEqual(r.shares, Decimal("150"))
        self.assertEqual(r.total_cost, Decimal("8000.00"))
        self.assertEqual(r.average, Decimal("53.3333"))

    def test_fifo_matches_oldest_lot_first(self):
        lots = [Lot(100, 50), Lot(50, 60)]
        m = realized_gain_fifo(lots, 120, 58.20)
        self.assertEqual([x.shares for x in m], [Decimal("100"), Decimal("20")])
        self.assertEqual(sum(x.basis for x in m), Decimal("6200.00"))
        self.assertEqual(sum(x.gain for x in m), Decimal("784.00"))

    def test_fifo_refuses_to_oversell(self):
        with self.assertRaises(ValueError):
            realized_gain_fifo([Lot(10, 5)], 11, 6)


class TestWashSale(unittest.TestCase):
    def test_window_is_61_days(self):
        w = replacement_window("2026-03-15")
        self.assertEqual(w.start.isoformat(), "2026-02-13")
        self.assertEqual(w.end.isoformat(), "2026-04-14")

    def test_boundaries_are_inside(self):
        self.assertTrue(is_replacement("2026-03-15", "2026-02-13"))
        self.assertTrue(is_replacement("2026-03-15", "2026-04-14"))
        self.assertFalse(is_replacement("2026-03-15", "2026-02-12"))
        self.assertFalse(is_replacement("2026-03-15", "2026-04-15"))

    def test_partial_replacement(self):
        self.assertEqual(disallowed_loss(1000, 100, 40), Decimal("400.00"))
        self.assertEqual(disallowed_loss(1000, 100, 0), Decimal("0.00"))
        self.assertEqual(disallowed_loss(1000, 100, 150), Decimal("1000.00"))


class TestLtcg(unittest.TestCase):
    def test_gain_entirely_in_fifteen_percent_band(self):
        bands = ltcg_bands(20000, 190000, "single")
        self.assertEqual(len(bands), 1)
        self.assertEqual(bands[0].rate, Decimal("0.15"))
        self.assertEqual(ltcg_tax(20000, 190000, "single"), Decimal("3000.00"))

    def test_gain_straddles_zero_band(self):
        # single: 0% ends at 49,450, so 40,000 of other income leaves 9,450 of room
        bands = ltcg_bands(20000, 40000, "single")
        self.assertEqual(bands[0].rate, Decimal("0.00"))
        self.assertEqual(bands[0].amount, Decimal("9450"))
        self.assertEqual(bands[1].amount, Decimal("10550"))
        self.assertEqual(ltcg_tax(20000, 40000, "single"), Decimal("1582.50"))

    def test_niit_only_on_the_excess(self):
        self.assertEqual(niit(20000, 210000, "single"), Decimal("380.00"))
        self.assertEqual(niit(20000, 150000, "single"), Decimal("0.00"))


class TestCarryover(unittest.TestCase):
    def test_8000_loss_leaves_5000_carrying(self):
        r = carryover(income_line1=97000, allowed_loss_line2=3000, st_loss_line5=8000)
        self.assertEqual(r.line3, Decimal("100000"))
        self.assertEqual(r.short_term, Decimal("5000"))
        self.assertEqual(r.long_term, Decimal("0"))

    def test_no_loss_no_carryover(self):
        r = carryover(income_line1=120000, allowed_loss_line2=0, st_loss_line5=0)
        self.assertEqual(r.short_term, Decimal("0"))
        self.assertEqual(r.long_term, Decimal("0"))

    def test_long_term_loss_reduced_by_short_term_gain(self):
        r = carryover(income_line1=90000, allowed_loss_line2=3000, st_loss_line5=0,
                      st_gain_line6=0, lt_loss_line9=10000, lt_gain_line10=4000)
        self.assertEqual(r.line7, Decimal("3000"))
        self.assertEqual(r.line11, Decimal("3000"))
        self.assertEqual(r.line12, Decimal("7000"))
        self.assertEqual(r.long_term, Decimal("3000"))


if __name__ == "__main__":
    unittest.main()
