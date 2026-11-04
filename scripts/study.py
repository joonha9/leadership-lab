"""Run a Leadership Lab study: prepare draws, track them, grade them, analyse them.

    python3 scripts/study.py prepare --study pilot --blocks 10 --seed 2026
    python3 scripts/study.py status  --study pilot [--next 7]
    python3 scripts/study.py grade   --study pilot
    python3 scripts/study.py analyze --study pilot

prepare  Writes results/<study>/schedule.csv (blocked randomization: every block holds each
         condition once, in random order), one prompt per draw under draws/<id>/prompt.md, and
         manifest.json with hashes of the brief and frames. Draw ids are opaque (d001, d002, ...),
         so nothing a subagent sees reveals its condition.
status   Lists draws without a reply, in schedule order (run them in that order).
grade    Grades every draw that has draws/<id>/reply.txt -> graded.jsonl and draws.csv.
analyze  Pre-registered tests on draws.csv -> summary.json and summary.md.

Each draw is one fresh Claude Code subagent given prompt.md verbatim; it saves its own reply.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from leadershiplab import frames as fr  # noqa: E402

PRIMARY = "itt_rel_validate"
SECONDARY = ["valid_rel_validate", "best_rel_validate", "itt_rel_explore", "valid_rate", "market_attempts",
             "idea_diversity", "distinct_idea_sets", "features_per_recipe", "share_k_extreme",
             "share_ev_ebitda", "mechanism_words", "share_beating_industry_validate"]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def study_dir(name: str) -> Path:
    return ROOT / "results" / name


def read_schedule(d: Path) -> list[dict]:
    with open(d / "schedule.csv") as fh:
        return list(csv.DictReader(fh))


def prepare(a) -> None:
    from leadershiplab import vl
    d = study_dir(a.study)
    if (d / "schedule.csv").exists():
        sys.exit(f"{d} already prepared; never re-randomize a study")
    problems = fr.check_frames(vl.FEATURES, vl.AGGREGATORS, vl.GROUPS)
    if problems:
        sys.exit("frames fail the rules:\n" + "\n".join(problems))
    rng = random.Random(a.seed)
    rows, n = [], 0
    for b in range(1, a.blocks + 1):
        order = fr.CONDITIONS[:]
        rng.shuffle(order)
        for c in order:
            n += 1
            rows.append({"draw_id": f"d{n:03d}", "block": b, "condition": c})
    brief = vl.task_brief()
    for r in rows:
        dd = d / "draws" / r["draw_id"]
        dd.mkdir(parents=True)
        (dd / "prompt.md").write_text(fr.build_prompt(r["condition"], brief, str(dd / "reply.txt")))
    with open(d / "schedule.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["draw_id", "block", "condition"])
        w.writeheader()
        w.writerows(rows)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                            text=True).stdout.strip()
    manifest = {
        "study": a.study, "created": datetime.now().isoformat(timespec="seconds"), "seed": a.seed,
        "blocks": a.blocks, "conditions": fr.CONDITIONS, "commit": commit,
        "proposer": a.proposer, "brief_sha": sha(brief),
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
    rows = read_schedule(d)
    graded, flat = [], []
    for r in rows:
        p = d / "draws" / r["draw_id"] / "reply.txt"
        if not p.exists():
            continue
        g = grade_reply(r["draw_id"], p.read_text())
        g.update(condition=r["condition"], block=int(r["block"]))
        graded.append(g)
        flat.append({k: v for k, v in g.items() if k != "proposals"})
        print(f"{r['draw_id']} graded {g['n_graded']}/6  itt_rel_validate {g['itt_rel_validate']:.3f}")
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

    def col(cond, var):
        return [float(x[var]) if x[var] not in ("", "nan") else np.nan for x in draws if x["condition"] == cond]

    def mean(v):
        v = np.asarray(v, float)
        return float(np.nanmean(v)) if np.any(~np.isnan(v)) else np.nan

    out = {"study": a.study, "n_draws": len(draws), "primary": PRIMARY, "by_condition": {}, "tests": {}}
    for c in fr.CONDITIONS:
        out["by_condition"][c] = {"n": len(col(c, PRIMARY)),
                                  **{v: mean(col(c, v)) for v in [PRIMARY] + SECONDARY}}
    # H1: Goleman contrast (positive-climate styles vs negative-climate styles), primary outcome
    vals = {c: col(c, PRIMARY) for c in fr.STYLES}
    out["tests"]["H1_goleman_contrast"] = stats.perm_contrast(vals, fr.POSITIVE, fr.NEGATIVE, seed=1)
    # H2: each style vs control, Holm-adjusted
    ctrl = col(fr.CONTROL, PRIMARY)
    h2 = {s: stats.perm_diff(col(s, PRIMARY), ctrl, seed=2) for s in fr.STYLES}
    adj = stats.holm({s: r["p"] for s, r in h2.items()})
    for s in fr.STYLES:
        h2[s]["p_holm"] = adj[s]
        h2[s]["ci95"] = stats.bootstrap_ci(col(s, PRIMARY), ctrl, seed=3)
    out["tests"]["H2_style_vs_control"] = h2
    # H3: rank agreement with Goleman's climate ranking (descriptive; n = 6 styles)
    acc = [-out["by_condition"][s][PRIMARY] for s in fr.STYLES]  # higher = better
    out["tests"]["H3_spearman_climate"] = stats.spearman([fr.GOLEMAN_CLIMATE[s] for s in fr.STYLES], acc)
    # H4: idea diversity, same contrast
    vals = {c: col(c, "idea_diversity") for c in fr.STYLES}
    out["tests"]["H4_diversity_contrast"] = stats.perm_contrast(vals, fr.POSITIVE, fr.NEGATIVE, seed=4)
    out["tests"]["H4_diversity_vs_control"] = {
        s: stats.perm_diff(col(s, "idea_diversity"), col(fr.CONTROL, "idea_diversity"), seed=5) for s in fr.STYLES}
    (d / "summary.json").write_text(json.dumps(out, indent=1, default=float))

    lines = [f"# {a.study}: {len(draws)} draws", "",
             "| Condition | n | ITT rel. error (validation) | valid-only | best | valid rate | diversity |",
             "|---|---|---|---|---|---|---|"]
    for c, r in out["by_condition"].items():
        lines.append(f"| {c} | {r['n']} | {r[PRIMARY]:.3f} | {r['valid_rel_validate']:.3f} | "
                     f"{r['best_rel_validate']:.3f} | {r['valid_rate']:.2f} | {r['idea_diversity']:.3f} |")
    t = out["tests"]
    lines += ["", f"H1 contrast (positive - negative styles): {t['H1_goleman_contrast']['contrast']:+.4f}, "
                  f"p = {t['H1_goleman_contrast']['p']:.3f}",
              "", "| Style vs control | diff | 95% CI | p | p (Holm) |", "|---|---|---|---|---|"]
    for s, r in t["H2_style_vs_control"].items():
        lines.append(f"| {s} | {r['diff']:+.4f} | [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] | {r['p']:.3f} | {r['p_holm']:.3f} |")
    lines += ["", f"H3 Spearman (Goleman climate vs accuracy): {t['H3_spearman_climate']:+.2f}",
              f"H4 diversity contrast: {t['H4_diversity_contrast']['contrast']:+.4f}, p = {t['H4_diversity_contrast']['p']:.3f}"]
    (d / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("cmd", choices=["prepare", "status", "grade", "analyze"])
ap.add_argument("--study", required=True)
ap.add_argument("--blocks", type=int, default=10)
ap.add_argument("--seed", type=int, default=2026)
ap.add_argument("--next", type=int, default=7)
ap.add_argument("--proposer", default="claude-code-subagent (general-purpose, model inherited from session)")
ap.add_argument("--exclude-blocks", type=int, nargs="*", default=[])
a = ap.parse_args()
{"prepare": prepare, "status": status, "grade": grade, "analyze": analyze}[a.cmd](a)
