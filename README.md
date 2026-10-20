# capital-gains-toolkit

Cost basis, wash-sale windows, long-term capital gains bands and the Schedule D capital loss carryover worksheet, as plain Python with no dependencies.

Built because the same handful of arithmetic comes up every time someone sells shares: what the position cost per share, which lot the sale came out of, whether the repurchase 20 days later kills the loss, how much of the gain reaches the 0% band, and what is left to carry into next year. Each of those is a small, checkable sum — so here they are as functions with tests rather than another spreadsheet.

## Install

```bash
git clone https://github.com/stockavg/capital-gains-toolkit.git
cd capital-gains-toolkit
python -m unittest discover -s tests   # 12 tests, no third-party packages
```

Python 3.10 or newer.

## What is in it

| Module | What it does |
| --- | --- |
| `capitalgains.cost_basis` | Weighted average cost per share; FIFO and specific-identification matching of a sale against lots |
| `capitalgains.wash_sale` | The 61-day replacement window (30 days either side) and a simplified disallowed-loss figure |
| `capitalgains.ltcg` | Splits a long-term gain over the 0 / 15 / 20% bands, then the 3.8% net investment income tax |
| `capitalgains.carryover` | The 13 lines of the Schedule D capital loss carryover worksheet, as arithmetic |

Money is carried as `Decimal` and rounded **down** to the cent, never up, so a printed figure is never larger than the true one.

## Command line

```bash
$ python -m capitalgains.cli avg "100@50;50@60"
{"shares": "150", "total_cost": "8000.00", "average": "53.3333"}
```

Two purchases, 100 shares at 50.00 and 50 at 60.00. The average is 8,000.00 / 150, not the mean of 50 and 60.

```bash
$ python -m capitalgains.cli fifo "100@50;50@60" --shares 120 --price 58.20
[{"shares": "100", "proceeds": "5820.00", "basis": "5000.00", "gain": "820.00"},
 {"shares": "20",  "proceeds": "1164.00", "basis": "1200.00", "gain": "-36.00"}]
total gain 784.00
```

Selling 120 shares out of those two lots: 100 come from the first lot, 20 from the second, and the second match is a loss.

```bash
$ python -m capitalgains.cli ltcg --gain 20000 --other 40000 --status single
[{"rate": "0.00", "amount": "9450", "tax": "0.00"},
 {"rate": "0.15", "amount": "10550", "tax": "1582.50"}]
total tax 1582.50
```

A 20,000.00 gain stacked on 40,000.00 of other taxable income fills the 0% band to its 49,450 edge first, so only the remainder is taxed at 15%.

```bash
$ python -m capitalgains.cli niit --nii 20000 --magi 210000
{"niit": "380.00"}
$ python -m capitalgains.cli wash --sale 2026-03-15 --buy 2026-04-10
{"window": ["2026-02-13", "2026-04-14"], "replacement": true}
$ python -m capitalgains.cli carryover --line1 97000 --line2 3000 --st-loss 8000
{"short_term": "5000", "long_term": "0", "lines": {"3": "100000", "4": "3000", ...}}
```

An 8,000.00 short-term loss in a year that could only deduct 3,000.00 against other income leaves 5,000.00 carrying forward.

## Data, and where each figure comes from

| File | Contents | Source |
| --- | --- | --- |
| `data/federal-ltcg-bands-2026.csv` | Where the 0% band ends and the 15% band ends, by filing status, for 2026 | IRS Revenue Procedure 2025-32, https://www.irs.gov/pub/irs-drop/rp-25-32.pdf |
| `data/niit-thresholds.csv` | The modified-AGI thresholds for the 3.8% surtax, by filing status | IRS, Net Investment Income Tax, https://www.irs.gov/individuals/net-investment-income-tax |
| `data/schedule-d-carryover-worksheet.csv` | The 13 printed lines of the carryover worksheet, in order | Schedule D instructions, Capital Loss Carryover Worksheet |

Every row carries its source in a `source` column, so a number can be traced without trusting this repository.

## Limits, stated plainly

- **The thresholds are 2026 figures.** Inflation adjustments are reissued every year; the loaders take a year argument and will fail loudly rather than return a stale table.
- **Line numbers on the carryover worksheet move between tax years.** The figures you pass are the four amounts the worksheet asks for, not this repository's guess at your form.
- **One branch of the worksheet is a reading, not plain arithmetic.** When line 3 comes out at zero or less, the printed instructions have you enter -0- and skip to line 9; this implementation therefore leaves the short-term loss on line 5 untouched. That is the one place to check against the form for the year you are filing.
- **Wash-sale basis allocation is not modelled.** `disallowed_loss` gives the share of a loss a replacement purchase disallows. Real filings spread that amount across the replacement lots and adjust their basis; do that allocation yourself or with your broker's figures.
- **Not tax advice.** This is arithmetic with citations. Which lot you sold, which rate applies and what your broker reports are all yours to confirm.

## Licence

MIT. Use it, fork it, take the tests apart.

The same arithmetic in the browser, with the working printed line by line, is at https://stockavg.com/ .
