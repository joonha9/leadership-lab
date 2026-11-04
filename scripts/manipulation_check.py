"""Manipulation check: can a blind rater tell which Goleman style each frame expresses?

    python3 scripts/manipulation_check.py write --raters 3     # one prompt per rater, shuffled order
    python3 scripts/manipulation_check.py score                # read replies, print the confusion

Each rater sees short descriptions of the six styles plus a 'none' option, and the seven frames
(six styles and the control) under neutral letters, in a different random order per rater.
Raters are fresh Claude Code subagents. A frame passes if a majority of raters label it correctly.
"""

from __future__ import annotations

import argparse
import json
import random
import string
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from leadershiplab import frames as fr  # noqa: E402

OUT = ROOT / "results" / "manipulation_check"
DESCRIPTIONS = {
    "coercive": "Demands immediate compliance; top-down orders, threats, no room for the employee's views.",
    "authoritative": "Mobilizes people toward a vision; explains where the work is going and why it matters, "
                     "then leaves the means to the employee.",
    "affiliative": "Puts people first; builds emotional bonds and harmony through warmth, praise and reassurance.",
    "democratic": "Forges consensus through participation; asks for the employee's ideas and gives them a say.",
    "pacesetting": "Sets very high standards and models them; expects speed and self-direction, gives little "
                   "guidance, and takes over when work falls short.",
    "coaching": "Develops people for the future; links the task to the employee's growth and tolerates "
                "short-term failure for the sake of learning.",
    "none": "No recognizable leadership style; neutral or purely administrative.",
}


def write(n: int, seed: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    key = {}
    labels = list(DESCRIPTIONS)
    for r in range(1, n + 1):
        order = fr.CONDITIONS[:]
        rng.shuffle(order)
        letters = dict(zip(string.ascii_uppercase, order))
        key[f"rater{r}"] = letters
        desc = "\n".join(f"  - {k}: {v}" for k, v in DESCRIPTIONS.items())
        msgs = "\n\n".join(
            f"MESSAGE {L}\n{fr.load_frame(c)['opening']}\n[... task description omitted ...]\n{fr.load_frame(c)['closing']}"
            for L, c in letters.items())
        path = OUT / f"rater{r}_reply.json"
        prompt = f"""DELIVERY: answer from this message alone. Apart from the file this message came from, do not read, search or open any files, and do not use any tool except one Write call that saves your reply to {path}. After saving, respond with the single word: saved

You are an organizational-behaviour researcher. Below are {len(letters)} messages a manager sent to an
analyst before a task. The task description in the middle is the same for all messages and is omitted.
Classify the leadership style each message expresses, using exactly one of these labels:

{desc}

Use each label as often as it fits; labels may repeat or go unused.

{msgs}

Your reply must be ONLY this JSON, no other text:
{{"ratings": [{{"message": "A", "label": "...", "confidence": 1-5, "reason": "one sentence"}}, ...]}}
"""
        (OUT / f"rater{r}_prompt.md").write_text(prompt)
        print(OUT / f"rater{r}_prompt.md")
    (OUT / "key.json").write_text(json.dumps({"labels": labels, "key": key}, indent=1))


def score() -> None:
    key = json.loads((OUT / "key.json").read_text())["key"]
    votes: dict[str, Counter] = {c: Counter() for c in fr.CONDITIONS}
    for rater, letters in key.items():
        p = OUT / f"{rater}_reply.json"
        if not p.exists():
            print("missing", p.name)
            continue
        for x in json.loads(p.read_text())["ratings"]:
            votes[letters[x["message"]]][x["label"]] += 1
    rows, ok_all = [], True
    for c, v in votes.items():
        target = "none" if c == fr.CONTROL else c
        n = sum(v.values())
        ok = n > 0 and v[target] > n / 2
        ok_all &= ok
        rows.append({"frame": c, "correct": v[target], "raters": n, "pass": ok, "votes": dict(v)})
        print(f"{c:14s} {v[target]}/{n} {'PASS' if ok else 'FAIL'}  {dict(v)}")
    (OUT / "summary.json").write_text(json.dumps({"all_pass": ok_all, "frames": rows}, indent=1))
    print("all frames pass" if ok_all else "some frames fail: revise before freezing")


ap = argparse.ArgumentParser()
ap.add_argument("cmd", choices=["write", "score"])
ap.add_argument("--raters", type=int, default=3)
ap.add_argument("--seed", type=int, default=2000)
a = ap.parse_args()
write(a.raters, a.seed) if a.cmd == "write" else score()
