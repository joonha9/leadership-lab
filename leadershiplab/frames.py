"""Leadership-style frames and the prompt each draw receives.

A frame is a manager's message in two parts, an opening before the task brief and a closing
after it. The task brief, the header lines and the final format line are identical in every
condition; only the frame text differs.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAME_DIR = ROOT / "prompts" / "frames"

# Goleman (2000), "Leadership That Gets Results", Harvard Business Review 78(2).
# Overall correlation of each style with organizational climate (his exhibit "Getting Molecular").
GOLEMAN_CLIMATE = {
    "coercive": -0.26, "authoritative": 0.54, "affiliative": 0.46,
    "democratic": 0.43, "pacesetting": -0.25, "coaching": 0.42,
}
# Correlation with the "flexibility" driver of climate (freedom to innovate).
GOLEMAN_FLEXIBILITY = {
    "coercive": -0.28, "authoritative": 0.32, "affiliative": 0.27,
    "democratic": 0.28, "pacesetting": -0.07, "coaching": 0.17,
}
STYLES = list(GOLEMAN_CLIMATE)
CONTROL = "control"
CONDITIONS = [CONTROL] + STYLES
POSITIVE = [s for s in STYLES if GOLEMAN_CLIMATE[s] > 0]
NEGATIVE = [s for s in STYLES if GOLEMAN_CLIMATE[s] < 0]

# Delivery instructions, identical in every condition except for the (opaque) reply path.
HARNESS = ("DELIVERY: answer from this message alone. Apart from the file this message came from, do "
           "not read, search or open any files, and do not use any tool except one Write call that "
           "saves your reply to {path}. After saving, respond with the single word: saved")
FINAL_LINE = "Your reply must be ONLY the JSON object described in the brief, with no other text."
LENGTH_BAND = 0.10  # each frame within +/-10% of the control frame's word count


def load_frame(condition: str) -> dict[str, str]:
    text = (FRAME_DIR / f"{condition}.md").read_text()
    parts = dict(re.findall(r"^## (opening|closing)\n(.*?)(?=^## |\Z)", text, flags=re.S | re.M))
    if set(parts) != {"opening", "closing"}:
        raise ValueError(f"{condition}: frame needs '## opening' and '## closing' sections")
    return {k: v.strip() for k, v in parts.items()}


def frame_words(condition: str) -> int:
    f = load_frame(condition)
    return len((f["opening"] + " " + f["closing"]).split())


def build_prompt(condition: str, brief: str, reply_path: str) -> str:
    f = load_frame(condition)
    return (f"{HARNESS.format(path=reply_path)}\n\n"
            f"MESSAGE FROM YOUR MANAGER\n\n{f['opening']}\n\n"
            f"===== TASK BRIEF =====\n{brief.strip()}\n===== END OF TASK BRIEF =====\n\n"
            f"{f['closing']}\n\n- Your manager\n\n{FINAL_LINE}\n")


def forbidden_terms(features, aggregators, groups) -> list[str]:
    """Words that would carry task information; no frame may contain any of them."""
    return sorted(set(features) | set(aggregators) | set(groups) |
                  {"EBITDA", "EV/", "SIC", "fallback", "min_peers", "filters", "harmonic", "trimmed",
                   "winsoriz", "z-score", "market cap", "price"})


def check_frames(features, aggregators, groups) -> list[str]:
    """Return a list of rule violations (empty = all frames pass)."""
    problems = []
    base = frame_words(CONTROL)
    lo, hi = base * (1 - LENGTH_BAND), base * (1 + LENGTH_BAND)
    terms = forbidden_terms(features, aggregators, groups)
    for c in CONDITIONS:
        f = load_frame(c)
        text = f["opening"] + "\n" + f["closing"]
        n = frame_words(c)
        if not lo <= n <= hi:
            problems.append(f"{c}: {n} words, outside {lo:.0f}-{hi:.0f}")
        if re.search(r"\d", text):
            problems.append(f"{c}: contains a digit")
        for t in terms:
            if t.lower() in text.lower():
                problems.append(f"{c}: contains task term '{t}'")
    return problems
