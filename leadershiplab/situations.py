"""Three task situations, each a version of the ValuationLab proposer brief.

Goleman (2000) argues that the best style depends on the situation. Situations for people mix two
things: the structure of the task and the state of the people. An AI agent has no morale or
grievances, so the situations here vary only the task's structure, objectively and with the same
grader:

  execution     A tightly specified task. Six recipes under exact constraints; the analyst only
                chooses an industry level, two features and k. Success is mostly about compliance
                and precision ("strong situation").
  exploration   The unchanged ValuationLab memoryless brief: open search for new recipes.
  turnaround    Six earlier recipes, all worse than the industry median on the exploration years,
                with their scores. The analyst must revise each one. A fixed set, the same in every
                condition, drawn once by a seeded rule (see freeze_turnaround_set).

Within a situation every condition gets the identical brief; only the manager's frame differs.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from . import vl

ROOT = Path(__file__).resolve().parents[1]
SITUATIONS = ["execution", "exploration", "turnaround"]
TURNAROUND_SET = ROOT / "prompts" / "situations" / "turnaround_set.json"
ANCHOR = "Each proposal needs:"

# ---------------------------------------------------------------- execution constraints

EXEC_RULES = {
    "per_multiple": 3,
    "k_range": (5, 15),
    "agg": "median",
    "min_peers": 5,
    "fallback": [[{"same": "industry_l2"}], []],
}

EXECUTION_BLOCK = """CONSTRAINTS (every recipe must satisfy all of them; a recipe that breaks any constraint is
discarded and scored as if no recipe had been delivered)
  C1. Exactly 3 recipes use EV/EBITDA and exactly 3 use EV/Sales.
  C2. "filters" holds exactly one screen, and it is {"same": GROUP} (no bands).
  C3. "rank" holds exactly 2 features, each with weight 1.
  C4. "k" is an integer from 5 to 15.
  C5. "agg" is "median".
  C6. "min_peers" is 5.
  C7. "fallback" is exactly [[{"same": "industry_l2"}], []].
  C8. Within each multiple, no two recipes use the same pair of rank features.

"""


def execution_violations(props: list[dict]) -> list[list[str]]:
    """Constraint violations for each proposal (list per slot; empty = compliant)."""
    out, count, pairs = [], {m: 0 for m in vl.MULTIPLES}, {m: set() for m in vl.MULTIPLES}
    lo, hi = EXEC_RULES["k_range"]
    for p in props:
        r = (p or {}).get("recipe") if isinstance(p, dict) else None
        v = []
        if not isinstance(r, dict):
            out.append(["no recipe object"])
            continue
        m = r.get("multiple")
        if m in count:
            count[m] += 1
            if count[m] > EXEC_RULES["per_multiple"]:
                v.append(f"C1: more than {EXEC_RULES['per_multiple']} {m} recipes")
        f = r.get("filters", [])
        if not (isinstance(f, list) and len(f) == 1 and isinstance(f[0], dict) and set(f[0]) == {"same"}):
            v.append("C2: filters must be exactly one 'same' screen")
        rank = r.get("rank", {})
        if not (isinstance(rank, dict) and len(rank) == 2 and all(w == 1 for w in rank.values())):
            v.append("C3: rank must hold exactly 2 features with weight 1")
        k = r.get("k")
        if not (isinstance(k, int) and not isinstance(k, bool) and lo <= k <= hi):
            v.append(f"C4: k must be an integer {lo}-{hi}")
        if r.get("agg", "median") != EXEC_RULES["agg"]:
            v.append("C5: agg must be median")
        if r.get("min_peers", 3) != EXEC_RULES["min_peers"]:
            v.append("C6: min_peers must be 5")
        if r.get("fallback", []) != EXEC_RULES["fallback"]:
            v.append("C7: fallback must be [[{same: industry_l2}], []]")
        if isinstance(rank, dict) and m in pairs:
            key = frozenset(rank)
            if key in pairs[m]:
                v.append("C8: repeats a rank-feature pair within the multiple")
            pairs[m].add(key)
        out.append(v)
    return out


# ---------------------------------------------------------------- turnaround set

def freeze_turnaround_set(seed: int = 4242, per_multiple: int = 3) -> dict:
    """Draw the fixed set of failed recipes once, by a rule stated before any draw.

    Pool: every distinct graded recipe in the ValuationLab archives (agent and random) with
    exploration coverage >= 95% that did worse than the industry median on exploration years.
    Draw `per_multiple` per multiple with a fixed seed, then re-grade each on exploration years
    so the scores shown to the analyst come from the current grader.
    """
    if TURNAROUND_SET.exists():
        raise FileExistsError(f"{TURNAROUND_SET} is frozen; delete it by hand only before any draw")
    pool, seen = {m: [] for m in vl.MULTIPLES}, set()
    for f in sorted((vl.VL_ROOT / "results" / "agent_runs").glob("*/archive_*.jsonl")):
        for line in f.read_text().splitlines():
            r = json.loads(line) if line.strip() else {}
            e = r.get("explore")
            if not e:
                continue
            spec = {k: v for k, v in r["spec"].items() if k != "name"}
            h = json.dumps(spec, sort_keys=True)
            if h in seen or e["coverage"] < 0.95 or e.get("gain_vs_industry_median", 0) >= 0:
                continue
            seen.add(h)
            pool[spec["multiple"]].append(spec)
    rng = random.Random(seed)
    chosen = []
    for m in vl.MULTIPLES:
        chosen += rng.sample(sorted(pool[m], key=lambda s: json.dumps(s, sort_keys=True)), per_multiple)
    rng.shuffle(chosen)
    cols, years = set(vl.panel().columns), vl.PROTOCOL.years("explore")
    items = []
    for i, spec in enumerate(chosen, 1):
        r = vl.validate({**spec, "name": f"turnaround-{i}"}, cols)
        card = vl.al.grade_period(vl.panel(), r, years)
        items.append({"slot": i, "recipe": {k: v for k, v in r.to_dict().items() if k != "name"},
                      "explore_median_abs_error": card["median_abs_error"],
                      "explore_coverage": card["coverage"],
                      "years_beating_industry_median": card["years_beating_industry_median"]})
    out = {"seed": seed, "rule": freeze_turnaround_set.__doc__.strip().splitlines()[0],
           "pool_sizes": {m: len(v) for m, v in pool.items()}, "items": items}
    TURNAROUND_SET.parent.mkdir(parents=True, exist_ok=True)
    TURNAROUND_SET.write_text(json.dumps(out, indent=1))
    return out


def turnaround_block() -> str:
    s = json.loads(TURNAROUND_SET.read_text())
    lines = [json.dumps(it["recipe"]) + "\n      exploration median error "
             f"{it['explore_median_abs_error']:.3f}, coverage {it['explore_coverage']:.1%}, "
             f"beat the industry median in {it['years_beating_industry_median']} of 4 years"
             for it in s["items"]]
    body = "\n".join(f"  Recipe {i}: {t}" for i, t in enumerate(lines, 1))
    return f"""PREVIOUS ROUND
The six recipes below were proposed earlier for this task and graded on the exploration years.
Each one did worse than the industry-median baseline for its multiple (see BASELINES). Your 6
proposals are revisions of them: proposal 1 revises Recipe 1, proposal 2 revises Recipe 2, and so
on, keeping the same multiple. A revision may change any other field.

{body}

"""


# ---------------------------------------------------------------- briefs

def brief(situation: str) -> str:
    base = vl.task_brief()
    if situation == "exploration":
        return base
    if base.count(ANCHOR) != 1:
        raise ValueError("unexpected brief layout")
    if situation == "execution":
        # The reply-format example must not contradict the constraints (it shows min_peers 3 and
        # a free fallback); only its placeholder values change.
        old = '"k": 8, "agg": "median", "min_peers": 3, "fallback": [...]'
        new = '"k": 8, "agg": "median", "min_peers": 5, "fallback": [[{"same": "industry_l2"}], []]'
        if base.count(old) != 1:
            raise ValueError("unexpected reply-format example")
        return base.replace(old, new).replace(ANCHOR, EXECUTION_BLOCK + ANCHOR)
    return base.replace(ANCHOR, turnaround_block() + ANCHOR)
