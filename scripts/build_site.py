"""Build the Leadership Lab site (index.html at the repository root) from the study results.

    python3 scripts/build_site.py

Every number on the site is computed here from results/ (no hand-typed results). The data are
written to site/site_data.json and injected into site/template.html. The root index.html is what
GitHub Pages serves.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from leadershiplab import frames as fr  # noqa: E402

SITUATIONS = ["execution", "exploration", "turnaround"]
PHRASE = {"coercive": "Do what I tell you", "authoritative": "Come with me", "affiliative": "People come first",
          "democratic": "What do you think?", "pacesetting": "Do as I do, now", "coaching": "Try this",
          "control": None}


def r(x, n=4):
    return None if x is None or not np.isfinite(float(x)) else round(float(x), n)


def load_draws(study: str) -> list[dict]:
    with open(ROOT / "results" / study / "draws.csv") as fh:
        return list(csv.DictReader(fh))


def num(x):
    return float(x) if x not in ("", "nan", None) else np.nan


def cell(rows, var, s, c):
    return np.array([num(x[var]) for x in rows if x["situation"] == s and x["condition"] == c], float)


def boot_ci(v, n=4000, seed=0, level=0.95):
    v = v[~np.isnan(v)]
    rng = np.random.default_rng(seed)
    m = [rng.choice(v, len(v)).mean() for _ in range(n)]
    lo, hi = np.quantile(m, [(1 - level) / 2, (1 + level) / 2])
    return [r(lo, 3), r(hi, 3)]


def main() -> None:
    full, pilot = load_draws("full"), load_draws("pilot")
    sf = json.loads((ROOT / "results/full/summary.json").read_text())
    sp = json.loads((ROOT / "results/pilot/summary.json").read_text())
    tf, tp = sf["tests"], sp["tests"]
    manip = json.loads((ROOT / "results/manipulation_check/summary.json").read_text())
    ref = json.loads((ROOT / "results/reference/valuationlab_bare_brief_draws.json").read_text())

    cells = {}
    for s in SITUATIONS:
        cells[s] = {}
        for c in fr.CONDITIONS:
            v = cell(full, "itt_rel_validate", s, c)
            e = {"mean": r(v.mean()), "n": int(len(v)),
                 "words": r(np.nanmean(cell(full, "mechanism_words", s, c)), 1),
                 "words_ci": boot_ci(cell(full, "mechanism_words", s, c), seed=1),
                 "diversity": r(np.nanmean(cell(full, "idea_diversity", s, c)), 3),
                 "diversity_ci": boot_ci(cell(full, "idea_diversity", s, c), seed=2),
                 "features": r(np.nanmean(cell(full, "features_per_recipe", s, c)), 2)}
            if s == "turnaround":
                e["improvement"] = r(np.nanmean(cell(full, "turnaround_improvement", s, c)), 3)
                e["share_improved"] = r(np.nanmean(cell(full, "turnaround_share_improved", s, c)), 3)
            if c != fr.CONTROL:
                vs = tf[f"within_{s}"]["style_vs_control"][c]
                eq = tf["E1_style_vs_control_equivalence"]["cells"][f"{c}|{s}"]
                e.update(diff=r(vs["diff"]), p=r(vs["p"]), p_holm=r(vs["p_holm"]),
                         ci90=[r(x) for x in eq["ci90"]], equivalent=eq["equivalent"])
            cells[s][c] = e

    def dids(t):
        out = {}
        for k, v in t["T2_goleman_dids"].items():
            eq = t["E2_did_equivalence"]["dids"][k]
            out[k] = {"did": r(v["did"]), "p": r(v["p"]), "p_holm": r(v["p_holm"]),
                      "ci90": [r(x) for x in eq["ci90"]], "equivalent": eq["equivalent"]}
        return out

    import importlib.util
    spec = importlib.util.spec_from_file_location("study", ROOT / "scripts" / "study.py")
    study = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(study)  # the CLI only parses arguments under __main__
    DID_PREDICTIONS = study.DID_PREDICTIONS
    sit_means = {s: r(np.mean([num(x["itt_rel_validate"]) for x in full if x["situation"] == s])) for s in SITUATIONS}
    style_span = {s: r(max(cells[s][c]["mean"] for c in fr.CONDITIONS) - min(cells[s][c]["mean"] for c in fr.CONDITIONS))
                  for s in SITUATIONS}
    within_sd = {}
    for s in SITUATIONS:
        res = np.concatenate([cell(full, "itt_rel_validate", s, c) - cell(full, "itt_rel_validate", s, c).mean()
                              for c in fr.CONDITIONS])
        within_sd[s] = r(np.sqrt(np.sum(res ** 2) / (len(res) - len(fr.CONDITIONS))))

    from leadershiplab import vl
    panel = vl.panel()
    per_year = {int(y): int(n) for y, n in panel.groupby("fiscal_year").size().items()}
    val = panel[panel["fiscal_year"].isin(vl.PROTOCOL.validate)]
    panel_info = {
        "per_year": per_year, "firm_years": int(len(panel)), "firms": int(panel["id"].nunique()),
        "years": [min(per_year), max(per_year)], "explore": list(vl.PROTOCOL.explore),
        "validate": list(vl.PROTOCOL.validate), "holdout": list(vl.PROTOCOL.holdout),
        "validation_firm_years": {"EV/EBITDA": int(((val["ebitda"] > 0) & (val["ev"] > 0)).sum()),
                                  "EV/Sales": int(((val["sales"] > 0) & (val["ev"] > 0)).sum())},
        "features": [{"name": f, "note": vl.al.FEATURE_NOTES.get(f, "")} for f in vl.FEATURES],
    }

    data = {
        "generated": date.today().isoformat(),
        "panel": panel_info,
        "counts": {"draws_full": len(full), "draws_pilot": len(pilot), "recipes_full": 6 * len(full),
                   "firm_years": 27693, "blocks_full": max(int(x["block"]) for x in full),
                   "unusable_slots": int(sum(6 - int(x["n_graded"]) for x in full)),
                   "constraint_violations": int(sum(int(x["constraint_violations"]) for x in full)),
                   "market_attempts": int(sum(int(x["market_attempts"]) for x in full))},
        "conditions": fr.CONDITIONS, "styles": fr.STYLES, "situations": SITUATIONS,
        "positive": fr.POSITIVE, "negative": fr.NEGATIVE,
        "climate": fr.GOLEMAN_CLIMATE, "phrase": PHRASE,
        "frames": {c: fr.load_frame(c) for c in fr.CONDITIONS},
        "cells": cells,
        "situation_means": sit_means, "style_span": style_span, "within_sd": within_sd,
        "tests": {
            "T1_p": r(tf["T1_interaction"]["p"], 3),
            "T1_p_pilot": r(tp["T1_interaction"]["p"], 3),
            "T3": {k: (r(v) if not isinstance(v, (list, tuple)) else [r(x) for x in v])
                   for k, v in tf["T3_spread_execution_vs_exploration"].items()},
            "E1_all": tf["E1_style_vs_control_equivalence"]["all_equivalent"],
            "E1_n_eq": sum(v["equivalent"] for v in tf["E1_style_vs_control_equivalence"]["cells"].values()),
            "E2_all": tf["E2_did_equivalence"]["all_equivalent"],
            "margin": tf["E1_style_vs_control_equivalence"]["margin"],
            "diversity_contrast": {s: {"contrast": r(tf[f"within_{s}"]["diversity_contrast"]["contrast"]),
                                       "p": r(tf[f"within_{s}"]["diversity_contrast"]["p"])} for s in SITUATIONS},
        },
        "dids": {"full": dids(tf), "pilot": dids(tp),
                 "spec": {k: {"style": v[0], "x": v[1], "y": v[2]} for k, v in DID_PREDICTIONS.items()}},
        "manipulation": {"correct": sum(f["correct"] for f in manip["frames"]),
                         "total": sum(f["raters"] for f in manip["frames"])},
        "reference": {"mean": r(np.mean([x["itt_rel_validate"] for x in ref])),
                      "sd": r(np.std([x["itt_rel_validate"] for x in ref], ddof=1)), "n": len(ref)},
    }
    (ROOT / "site" / "site_data.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    tpl = (ROOT / "site" / "template.html").read_text()
    out = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    (ROOT / "index.html").write_text(out)
    print(f"wrote index.html ({len(out) // 1024} KB) and site/site_data.json")


if __name__ == "__main__":
    main()
