"""Access to the ValuationLab task, grader and data.

ValuationLab (https://github.com/joonha9/Valuation_Lab) is a sibling checkout. Its location is
read from the VALUATION_LAB environment variable, or defaults to ../valuation-lab next to this
repository. The licensed FactSet data stays inside that checkout and is never copied here.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VL_ROOT = Path(os.environ.get("VALUATION_LAB", ROOT.parent / "valuation-lab")).resolve()

if not (VL_ROOT / "valuationlab").is_dir():
    raise ImportError(f"ValuationLab not found at {VL_ROOT}; set VALUATION_LAB to its checkout")
sys.path.insert(0, str(VL_ROOT))

from valuationlab import agentloop as al  # noqa: E402
from valuationlab.baselines import baselines_for  # noqa: E402
from valuationlab.data import load_panel  # noqa: E402
from valuationlab.grader import Protocol, add_errors, estimate  # noqa: E402
from valuationlab.panel import FEATURES, MARKET_COLUMNS  # noqa: E402
from valuationlab.recipe import AGGREGATORS, RecipeError, validate  # noqa: E402

PROTOCOL = Protocol(explore=(2016, 2017, 2018, 2019), validate=(2020, 2021, 2022, 2023),
                    holdout=(2024, 2025))
MULTIPLES = al.MULTIPLES_IN_SCOPE
GROUPS = al.GROUPS_IN_DATA


@lru_cache(maxsize=1)
def panel():
    return load_panel(VL_ROOT)


def task_brief() -> str:
    """The ValuationLab memoryless proposer brief: the task block shared by every condition."""
    return al.memoryless_prompt(panel(), PROTOCOL, 6)


__all__ = ["AGGREGATORS", "FEATURES", "GROUPS", "MARKET_COLUMNS", "MULTIPLES", "PROTOCOL", "RecipeError",
           "VL_ROOT", "add_errors", "al", "baselines_for", "estimate", "panel", "task_brief", "validate"]
