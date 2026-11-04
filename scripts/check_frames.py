"""Check the frames against the pre-registered rules (length band, no task information).

    python3 scripts/check_frames.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from leadershiplab import frames as fr  # noqa: E402
from leadershiplab import vl  # noqa: E402

for c in fr.CONDITIONS:
    print(f"{c:14s} {fr.frame_words(c):4d} words")
problems = fr.check_frames(vl.FEATURES, vl.AGGREGATORS, vl.GROUPS)
print("\n".join(problems) if problems else "all frames pass")
sys.exit(1 if problems else 0)
