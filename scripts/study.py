"""Run a Leadership Lab study: prepare draws, track them, grade them, analyse them.

    python3 scripts/study.py prepare --study pilot --blocks 5 --seed 2026
    python3 scripts/study.py status  --study pilot [--next 21]
    python3 scripts/study.py grade   --study pilot
    python3 scripts/study.py analyze --study pilot

Design: 7 conditions (6 Goleman styles + control) x 3 situations (execution, exploration,
turnaround) = 21 cells.

prepare  Writes results/<study>/schedule.csv (blocked randomization: every block holds each of the
         21 cells once, in random order), one prompt per draw under draws/<id>/prompt.md, and
         manifest.json with hashes of the briefs and frames. Draw ids are opaque (d001, ...).
status   Lists draws without a reply, in schedule order (run them in that order).
grade    Grades every draw that has draws/<id>/reply.txt -> graded.jsonl and draws.csv.
analyze  Pre-registered tests on draws.csv -> summary.json and summary.md.

Each draw is one fresh Claude Code subagent that reads its prompt.md and saves its own reply.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from leadershiplab import frames as fr  # noqa: E402

SITUATIONS = ["execution", "exploration", "turnaround"]
PRIMARY = "itt_rel_validate"
EQ_MARGIN = 0.02  # equivalence margin for TOST (amendment A1, added before the full study)
SECONDARY = ["valid_rel_validate", "best_rel_validate", "itt_rel_explore", "valid_rate", "constraint_violations",
             "market_attempts", "idea_diversity", "distinct_idea_sets", "features_per_recipe",
             "share_k_extreme", "share_ev_ebitda", "mechanism_words", "share_beating_industry_validate",
             "turnaround_improvement", "turnaround_share_improved"]
# Goleman's "when the style works best", translated into task situations. Each DiD is
# (style - control in X) - (style - control in Y); the predicted sign is negative (lower error in X).
DID_PREDICTIONS = {
    "D1_coercive_turnaround": ("coercive", "turnaround", "exploration"),
    "D2_coaching_turnaround": ("coaching", "turnaround", "exploration"),
    "D3_pacesetting_execution": ("pacesetting", "execution", "exploration"),
    "D4_authoritative_exploration": ("authoritative", "exploration", "execution"),
    "D5_democratic_exploration": ("democratic", "exploration", "execution"),
}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def study_dir(name: str) -> Path:
    """results/<name>; LL_RESULTS overrides the results root (used for dry runs)."""
    return Path(os.environ.get("LL_RESULTS", ROOT / "results")) / name


def read_schedule(d: Path) -> list[dict]:
    with open(d / "schedule.csv") as fh:
        return list(csv.DictReader(fh))


def prepare(a) -> None:
    from leadershiplab import situations as sit
    from leadershiplab import vl
    d = study_dir(a.study)
    if (d / "schedule.csv").exists():
        sys.exit(f"{d} already prepared; never re-randomize a study")
    problems = fr.check_frames(vl.FEATURES, vl.AGGREGATORS, vl.GROUPS)
    if problems:
        sys.exit("frames fail the rules:\n" + "\n".join(problems))
    briefs = {s: sit.brief(s) for s in SITUATIONS}
    cells = [(c, s) for s in SITUATIONS for c in fr.CONDITIONS]
    rng = random.Random(a.seed)
    rows, n = [], 0
    for b in range(1, a.blocks + 1):
        order = cells[:]
        rng.shuffle(order)
        for c, s in order:
            n += 1
            rows.append({"draw_id": f"d{n:03d}", "block": b, "condition": c, "situation": s})
    for r in rows:
        dd = d / "draws" / r["draw_id"]
        dd.mkdir(parents=True)
        (dd / "prompt.md").write_text(fr.build_prompt(r["condition"], briefs[r["situation"]], str(dd / "reply.txt")))
    with open(d / "schedule.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["draw_id", "block", "condition", "situation"])
        w.writeheader()
        w.writerows(rows)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                            text=True).stdout.strip()
    manifest = {
        "study": a.study, "created": datetime.now().isoformat(timespec="seconds"), "seed": a.seed,
        "blocks": a.blocks, "conditions": fr.CONDITIONS, "situations": SITUATIONS, "commit": commit,
        "proposer": a.proposer, "brief_sha": {s: sha(b) for s, b in briefs.items()},
        "turnaround_set_sha": sha(sit.TURNAROUND_SET.read_text()),
        "frame_sha": {c: sha(json.dumps(fr.load_frame(c))) for c in fr.CONDITIONS},
        "frame_words": {c: fr.frame_words(c) for c in fr.CONDITIONS},
    }
    (d / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"prepared {len(rows)} draws in {d}")


def status(a) -> None:
    d = study_dir(a.study)
    rows = read_schedule(d)
    todo = [r for r in rows if not (d / "draws" / r["draw_id"] / "reply.txt").exists()]
    print(f"{len(rows) - len(todo)}/{len(rows)} draws have replies")
    for r in todo[:a.next]:
        print(d / "draws" / r["draw_id"] / "prompt.md")


def grade(a) -> None:
    from leadershiplab.grading import grade_reply
    d = study_dir(a.study)
    graded, flat = [], []
    for r in read_schedule(d):
        p = d / "draws" / r["draw_id"] / "reply.txt"
        if not p.exists():
            continue
        g = grade_reply(r["draw_id"], p.read_text(), r["situation"])
        g.update(condition=r["condition"], block=int(r["block"]))
        graded.append(g)
        flat.append({k: v for k, v in g.items() if k != "proposals"})
        print(f"{r['draw_id']} {r['situation']:11s} graded {g['n_graded']}/6  {PRIMARY} {g[PRIMARY]:.3f}")
    with open(d / "graded.jsonl", "w") as fh:
        for g in graded:
            fh.write(json.dumps(g, default=float) + "\n")
    if flat:
        with open(d / "draws.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(flat[0]))
            w.writeheader()
            w.writerows(flat)
    print(f"graded {len(graded)} draws -> {d / 'draws.csv'}")


def analyze(a) -> None:
    import numpy as np
    from leadershiplab import stats
    d = study_dir(a.study)
    with open(d / "draws.csv") as fh:
        draws = list(csv.DictReader(fh))
    if a.exclude_blocks:
        draws = [x for x in draws if int(x["block"]) not in a.exclude_blocks]

    def num(x):
        return float(x) if x not in ("", "nan", None) else np.nan

    def col(cond, s, var=PRIMARY):
        return [num(x[var]) for x in draws if x["condition"] == cond and x["situation"] == s]

    def mean(v):
        v = np.asarray(v, float)
        return float(np.nanmean(v)) if np.any(~np.isnan(v)) else np.nan

    out = {"study": a.study, "n_draws": len(draws), "primary": PRIMARY, "cells": {}, "tests": {}}
    for s in SITUATIONS:
        out["cells"][s] = {c: {"n": len(col(c, s)), **{v: mean(col(c, s, v)) for v in [PRIMARY] + SECONDARY}}
                           for c in fr.CONDITIONS}
    t = out["tests"]
    # T1 (confirmatory): style effects differ across situations (omnibus interaction)
    y = [num(x[PRIMARY]) for x in draws]
    t["T1_interaction"] = stats.perm_interaction(y, [x["condition"] for x in draws],
                                                 [x["situation"] for x in draws], seed=1)
    # T2 (confirmatory): Goleman's situation-specific predictions, Holm across D1-D5
    dids = {k: stats.perm_did(col(sty, sx), col(fr.CONTROL, sx), col(sty, sy), col(fr.CONTROL, sy), seed=2)
            for k, (sty, sx, sy) in DID_PREDICTIONS.items()}
    adj = stats.holm({k: v["p"] for k, v in dids.items()})
    for k in dids:
        dids[k]["p_holm"] = adj[k]
        dids[k]["predicted_sign"] = "negative"
    t["T2_goleman_dids"] = dids
    # T3: strong situation: style matters less under tight constraints (execution vs exploration)
    t["T3_spread_execution_vs_exploration"] = stats.bootstrap_spread(
        {c: col(c, "execution") for c in fr.CONDITIONS}, {c: col(c, "exploration") for c in fr.CONDITIONS}, seed=3)
    # Within each situation: Goleman contrast and each style vs control (Holm within situation)
    for s in SITUATIONS:
        ws = {"goleman_contrast": stats.perm_contrast({c: col(c, s) for c in fr.STYLES}, fr.POSITIVE,
                                                      fr.NEGATIVE, seed=4)}
        ctrl = col(fr.CONTROL, s)
        vs = {c: stats.perm_diff(col(c, s), ctrl, seed=5) for c in fr.STYLES}
        adj = stats.holm({c: v["p"] for c, v in vs.items()})
        for c in vs:
            vs[c]["p_holm"] = adj[c]
        ws["style_vs_control"] = vs
        ws["spearman_climate"] = stats.spearman([fr.GOLEMAN_CLIMATE[c] for c in fr.STYLES],
                                                [-out["cells"][s][c][PRIMARY] for c in fr.STYLES])
        ws["diversity_contrast"] = stats.perm_contrast({c: col(c, s, "idea_diversity") for c in fr.STYLES},
                                                       fr.POSITIVE, fr.NEGATIVE, seed=6)
        t[f"within_{s}"] = ws
    # E1/E2 (amendment A1): equivalence. 90% bootstrap intervals inside +/-EQ_MARGIN = TOST at 5%.
    e1 = {}
    for s in SITUATIONS:
        for c in fr.STYLES:
            ci = stats.bootstrap_ci(col(c, s), col(fr.CONTROL, s), seed=7, level=0.90)
            e1[f"{c}|{s}"] = {"ci90": ci, "equivalent": stats.equivalent(ci, EQ_MARGIN)}
    t["E1_style_vs_control_equivalence"] = {"margin": EQ_MARGIN, "all_equivalent": all(v["equivalent"] for v in e1.values()),
                                            "cells": e1}
    e2 = {}
    for k, (sty, sx, sy) in DID_PREDICTIONS.items():
        ci = stats.bootstrap_did_ci(col(sty, sx), col(fr.CONTROL, sx), col(sty, sy), col(fr.CONTROL, sy), seed=8)
        e2[k] = {"ci90": ci, "equivalent": stats.equivalent(ci, EQ_MARGIN)}
    t["E2_did_equivalence"] = {"margin": EQ_MARGIN, "all_equivalent": all(v["equivalent"] for v in e2.values()), "dids": e2}
    (d / "summary.json").write_text(json.dumps(out, indent=1, default=float))

    L = [f"# {a.study}: {len(draws)} draws", "", f"Primary outcome: {PRIMARY} (lower is better; 1.0 = industry median)", "",
         "| Condition | " + " | ".join(SITUATIONS) + " |", "|---|" + "---|" * len(SITUATIONS)]
    for c in fr.CONDITIONS:
        L.append(f"| {c} | " + " | ".join(f"{out['cells'][s][c][PRIMARY]:.3f} (n={out['cells'][s][c]['n']})"
                                          for s in SITUATIONS) + " |")
    L += ["", f"T1 interaction: SS {t['T1_interaction']['ss']:.5f}, p = {t['T1_interaction']['p']:.3f}", "",
          "| T2 prediction | DiD | p | p (Holm) |", "|---|---|---|---|"]
    for k, v in t["T2_goleman_dids"].items():
        L.append(f"| {k} | {v['did']:+.4f} | {v['p']:.3f} | {v['p_holm']:.3f} |")
    sp = t["T3_spread_execution_vs_exploration"]
    L += ["", f"T3 spread of condition means: execution {sp['sd_x']:.4f} vs exploration {sp['sd_y']:.4f}, "
              f"95% CI of difference [{sp['ci95'][0]:+.4f}, {sp['ci95'][1]:+.4f}]"]
    e1, e2 = t["E1_style_vs_control_equivalence"], t["E2_did_equivalence"]
    L += ["", f"E1 equivalence, style vs control within +/-{EQ_MARGIN} (90% CI): "
              f"{sum(v['equivalent'] for v in e1['cells'].values())}/{len(e1['cells'])} cells equivalent; "
              f"all equivalent: {e1['all_equivalent']}",
          f"E2 equivalence of D1-D5 within +/-{EQ_MARGIN}: "
          + ", ".join(f"{k.split('_')[0]} [{v['ci90'][0]:+.3f}, {v['ci90'][1]:+.3f}] {'eq' if v['equivalent'] else 'not eq'}"
                      for k, v in e2["dids"].items())]
    for s in SITUATIONS:
        ws = t[f"within_{s}"]
        L += ["", f"## {s}", f"Goleman contrast (positive - negative): {ws['goleman_contrast']['contrast']:+.4f}, "
                             f"p = {ws['goleman_contrast']['p']:.3f}; Spearman with climate {ws['spearman_climate']:+.2f}",
              "", "| Style vs control | diff | p | p (Holm) |", "|---|---|---|---|"]
        for c, v in ws["style_vs_control"].items():
            L.append(f"| {c} | {v['diff']:+.4f} | {v['p']:.3f} | {v['p_holm']:.3f} |")
    (d / "summary.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("cmd", choices=["prepare", "status", "grade", "analyze"])
ap.add_argument("--study", required=True)
ap.add_argument("--blocks", type=int, default=5)
ap.add_argument("--seed", type=int, default=2026)
ap.add_argument("--next", type=int, default=21)
ap.add_argument("--proposer", default="claude-code-subagent (general-purpose, model inherited from session)")
ap.add_argument("--exclude-blocks", type=int, nargs="*", default=[])
a = ap.parse_args()
{"prepare": prepare, "status": status, "grade": grade, "analyze": analyze}[a.cmd](a)
