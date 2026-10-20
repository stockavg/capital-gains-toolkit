"""Capital gains arithmetic in plain Python.

Modules
-------
cost_basis  weighted average cost, FIFO and specific-identification matching
wash_sale   the 61-day replacement window and a simplified disallowed loss
ltcg        0/15/20% band stacking and the 3.8% net investment income tax
carryover   the 13-line Schedule D capital loss carryover worksheet
"""

from .carryover import Carryover, carryover
from .cost_basis import AverageCost, Lot, Match, realized_gain_fifo, realized_gain_specific_id, weighted_average
from .ltcg import Band, ltcg_bands, ltcg_tax, niit
from .wash_sale import Window, disallowed_loss, is_replacement, replacement_window

__all__ = [
    "Band",
    "AverageCost",
    "Carryover",
    "Lot",
    "Match",
    "Window",
    "carryover",
    "disallowed_loss",
    "is_replacement",
    "ltcg_bands",
    "ltcg_tax",
    "niit",
    "realized_gain_fifo",
    "realized_gain_specific_id",
    "replacement_window",
    "weighted_average",
]

__version__ = "0.1.0"
