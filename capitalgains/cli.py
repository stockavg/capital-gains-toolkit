"""Command line front end: python -m capitalgains ..."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal

from .carryover import carryover
from .cost_basis import Lot, realized_gain_fifo, total_gain, weighted_average
from .ltcg import ltcg_bands, ltcg_tax, niit
from .wash_sale import is_replacement, replacement_window


def _lots(spec):
    lots = []
    for part in spec.split(";"):
        shares, price = part.split("@")
        lots.append(Lot(Decimal(shares), Decimal(price)))
    return lots


def main(argv=None):
    p = argparse.ArgumentParser(prog="capitalgains", description="Cost basis, wash sales, LTCG bands, carryover worksheet")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("avg", help="weighted average cost per share")
    a.add_argument("lots", help="semicolon separated list, e.g. '100@50;50@60'")

    f = sub.add_parser("fifo", help="realized gain matching a sale oldest-lot-first")
    f.add_argument("lots")
    f.add_argument("--shares", required=True)
    f.add_argument("--price", required=True)

    w = sub.add_parser("wash", help="is a purchase inside the wash-sale window")
    w.add_argument("--sale", required=True, help="ISO date")
    w.add_argument("--buy", required=True, help="ISO date")

    l = sub.add_parser("ltcg", help="split a long-term gain over the 0/15/20% bands")
    l.add_argument("--gain", required=True)
    l.add_argument("--other", required=True, help="other taxable income")
    l.add_argument("--status", default="single", choices=["single", "mfj", "mfs", "hoh"])
    l.add_argument("--year", type=int, default=2026)

    n = sub.add_parser("niit", help="3.8% net investment income tax")
    n.add_argument("--nii", required=True)
    n.add_argument("--magi", required=True)
    n.add_argument("--status", default="single", choices=["single", "mfj", "mfs", "hoh"])

    c = sub.add_parser("carryover", help="Schedule D capital loss carryover worksheet")
    c.add_argument("--line1", required=True)
    c.add_argument("--line2", required=True)
    c.add_argument("--st-loss", required=True)
    c.add_argument("--st-gain", default="0")
    c.add_argument("--lt-loss", default="0")
    c.add_argument("--lt-gain", default="0")

    args = p.parse_args(argv)

    if args.cmd == "avg":
        r = weighted_average(_lots(args.lots))
        print(json.dumps({"shares": str(r.shares), "total_cost": str(r.total_cost), "average": str(r.average)}))
    elif args.cmd == "fifo":
        m = realized_gain_fifo(_lots(args.lots), args.shares, args.price)
        print(json.dumps([{"shares": str(x.shares), "proceeds": str(x.proceeds), "basis": str(x.basis), "gain": str(x.gain)} for x in m]))
        print("total gain", total_gain(m))
    elif args.cmd == "wash":
        win = replacement_window(args.sale)
        print(json.dumps({"window": [win.start.isoformat(), win.end.isoformat()], "replacement": is_replacement(args.sale, args.buy)}))
    elif args.cmd == "ltcg":
        bands = ltcg_bands(args.gain, args.other, args.status, args.year)
        print(json.dumps([{"rate": str(b.rate), "amount": str(b.amount), "tax": str(b.tax)} for b in bands]))
        print("total tax", ltcg_tax(args.gain, args.other, args.status, args.year))
    elif args.cmd == "niit":
        print(json.dumps({"niit": str(niit(args.nii, args.magi, args.status))}))
    elif args.cmd == "carryover":
        r = carryover(
            income_line1=args.line1,
            allowed_loss_line2=args.line2,
            st_loss_line5=args.st_loss,
            st_gain_line6=args.st_gain,
            lt_loss_line9=args.lt_loss,
            lt_gain_line10=args.lt_gain,
        )
        print(json.dumps({"short_term": str(r.short_term), "long_term": str(r.long_term), "lines": {
            "3": str(r.line3), "4": str(r.line4), "7": str(r.line7), "8": str(r.line8_short_term),
            "11": str(r.line11), "12": str(r.line12), "13": str(r.line13_long_term)}}))


if __name__ == "__main__":
    main()
