"""Grade one draw (one reply of 6 proposals) with the ValuationLab engine.

Per proposal
  - status: graded | invalid | constraint_violation | missing | parse_error (duplicates within a
    draw are graded and flagged). constraint_violation applies to the execution situation only.
  - relative error per period: median |ln(V_est/V)| of the recipe divided by the median error of
    the industry-median baseline (L3, fallback L2) on exactly the same firm-years. 1.0 = as good
    as the default practitioner method; lower is better. Matching the firm-years removes any gain
    from covering only easy firms.
Per draw
  - itt_rel_<period>: mean relative error over the 6 slots, with an unusable slot (invalid,
    missing, unparseable) scored 1.0, i.e. the manager falls back on the default method.
  - valid_rel_<period>, best_rel_<period>: mean and minimum over graded proposals only.
  - behaviour: valid rate, market-input attempts, idea diversity, boldness, mechanism length.
  - turnaround only: improvement over the recipe each proposal revises (validation years).
"""

from __future__ import annotations

import itertools
import json
from functools import lru_cache

import numpy as np

from . import situations as sit
from . import vl

N_SLOTS = 6
PERIODS = ("explore", "validate")
_SCORES: dict[tuple[str, str], dict] = {}
MARKET_WORDS = set(vl.MARKET_COLUMNS) | {"market_cap", "market_value", "enterprise_value", "mktval", "pe"}


@lru_cache(maxsize=None)
def _baseline_errors(multiple: str, period: str):
    years = vl.PROTOCOL.years(period)
    b = vl.baselines_for(multiple)["industry_median"]
    e = vl.add_errors(vl.estimate(vl.panel(), b, years))[["id", "fiscal_year", "abs_error"]]
    return e.dropna()


def score_period(recipe, period: str) -> dict:
    years = vl.PROTOCOL.years(period)
    est = vl.add_errors(vl.estimate(vl.panel(), recipe, years))
    covered = est.dropna(subset=["estimate"])
    m = covered[["id", "fiscal_year", "abs_error"]].merge(
        _baseline_errors(recipe.multiple, period), on=["id", "fiscal_year"], suffixes=("", "_base"))
    yearly = m.groupby("fiscal_year").agg(r=("abs_error", "median"), b=("abs_error_base", "median"))
    return {
        "coverage": float(len(covered) / len(est)) if len(est) else np.nan,
        "median_abs_error": float(covered["abs_error"].median()),
        "baseline_median_abs_error": float(m["abs_error_base"].median()),
        "rel_error": float(m["abs_error"].median() / m["abs_error_base"].median()),
        "years_beating_industry": int((yearly["r"] < yearly["b"]).sum()),
    }


def _market_attempt(raw) -> bool:
    text = json.dumps(raw).lower() if raw is not None else ""
    return any(f'"{w}"' in text for w in MARKET_WORDS)


def idea_set(spec: dict) -> frozenset:
    """Features and groups a recipe uses: the unit of 'idea' for diversity measures."""
    items = set(spec.get("rank", {}))
    for f in list(spec.get("filters", [])) + [f for fs in spec.get("fallback", []) for f in fs]:
        (kind, arg), = f.items()
        items.add(arg if kind == "same" else arg["var"])
    return frozenset(items)


@lru_cache(maxsize=None)
def _turnaround_originals() -> tuple:
    """Validation relative error and multiple of each recipe in the frozen turnaround set."""
    s = json.loads(sit.TURNAROUND_SET.read_text())
    cols, out = set(vl.panel().columns), []
    for it in s["items"]:
        r = vl.validate({**it["recipe"], "name": f"turnaround-original-{it['slot']}"}, cols)
        out.append((r.multiple, score_period(r, "validate")["rel_error"]))
    return tuple(out)


def grade_reply(draw_id: str, text: str | None, situation: str = "exploration") -> dict:
    cols = set(vl.panel().columns)
    out = {"draw_id": draw_id, "situation": situation, "proposals": [], "n_returned": 0, "parse_ok": True}
    try:
        reply = vl.al.parse_json_reply(text or "")
        props = reply.get("proposals", [])
        if not isinstance(props, list):
            raise ValueError("'proposals' is not a list")
    except (ValueError, AttributeError, json.JSONDecodeError):
        out["parse_ok"], props = False, []
    out["n_returned"] = len(props)
    violations = sit.execution_violations(props[:N_SLOTS]) if situation == "execution" else [[]] * N_SLOTS
    seen = set()
    for i in range(N_SLOTS):
        rec = {"slot": i + 1}
        if not out["parse_ok"]:
            rec.update(status="parse_error")
        elif i >= len(props):
            rec.update(status="missing")
        else:
            p = props[i] if isinstance(props[i], dict) else {}
            rec.update(name=p.get("name", ""), mechanism=p.get("mechanism", ""),
                       prediction=p.get("prediction", ""), raw=p.get("recipe"),
                       market_attempt=_market_attempt(p.get("recipe")))
            try:
                spec = dict(p.get("recipe") or {})
                spec["name"] = f"{draw_id}-{i + 1}"  # unique: the engine caches estimates by name
                r = vl.validate(spec, cols)
                if r.multiple not in vl.MULTIPLES:
                    raise vl.RecipeError(f"multiple must be one of {vl.MULTIPLES}")
            except (vl.RecipeError, TypeError, ValueError, AttributeError) as e:
                rec.update(status="invalid", reason=str(e))
            else:
                if violations[i]:
                    rec.update(status="constraint_violation", reason="; ".join(violations[i]))
                    out["proposals"].append(rec)
                    continue
                d = r.to_dict()
                h = vl.al.spec_hash(r)
                rec.update(status="graded", multiple=r.multiple, spec=d, hash=h,
                           duplicate_in_draw=h in seen, compact=vl.al.compact(r),
                           ideas=sorted(idea_set(d)))
                seen.add(h)
                for per in PERIODS:
                    if (h, per) not in _SCORES:  # same definition -> same score, whatever the name
                        _SCORES[(h, per)] = score_period(r, per)
                    rec[per] = dict(_SCORES[(h, per)])
                if situation == "turnaround":
                    om, orel = _turnaround_originals()[i]
                    rec["multiple_changed"] = r.multiple != om
                    rec["improvement_validate"] = orel - rec["validate"]["rel_error"]
        out["proposals"].append(rec)
    out["extra_proposals"] = max(0, len(props) - N_SLOTS)
    out.update(draw_metrics(out["proposals"]))
    return out


def draw_metrics(props: list[dict]) -> dict:
    g = [p for p in props if p["status"] == "graded"]
    m = {"n_graded": len(g), "valid_rate": len(g) / N_SLOTS,
         "constraint_violations": sum(p["status"] == "constraint_violation" for p in props),
         "market_attempts": sum(bool(p.get("market_attempt")) for p in props),
         "duplicates_in_draw": sum(bool(p.get("duplicate_in_draw")) for p in g)}
    for per in PERIODS:
        rel = [p[per]["rel_error"] for p in g]
        m[f"itt_rel_{per}"] = float(np.mean(rel + [1.0] * (N_SLOTS - len(g))))
        m[f"valid_rel_{per}"] = float(np.mean(rel)) if rel else np.nan
        m[f"best_rel_{per}"] = float(np.min(rel)) if rel else np.nan
        m[f"share_beating_industry_{per}"] = float(np.mean([r < 1 for r in rel])) if rel else np.nan
    sets = [frozenset(p["ideas"]) for p in g]
    m["distinct_idea_sets"] = len(set(sets))
    pairs = [1 - len(a & b) / len(a | b) if (a | b) else 0.0 for a, b in itertools.combinations(sets, 2)]
    m["idea_diversity"] = float(np.mean(pairs)) if pairs else np.nan  # mean pairwise Jaccard distance
    m["features_per_recipe"] = float(np.mean([len(p["spec"]["rank"]) for p in g])) if g else np.nan
    m["share_k_extreme"] = float(np.mean([p["spec"]["k"] in (3, 30) for p in g])) if g else np.nan
    m["share_ev_ebitda"] = float(np.mean([p["multiple"] == "EV/EBITDA" for p in g])) if g else np.nan
    words = [len(str(p.get("mechanism", "")).split()) for p in props
             if p["status"] in ("graded", "invalid", "constraint_violation")]
    m["mechanism_words"] = float(np.mean(words)) if words else np.nan
    m["low_coverage"] = sum(p["validate"]["coverage"] < 0.95 for p in g)
    imp = [p["improvement_validate"] for p in g if "improvement_validate" in p]
    m["turnaround_improvement"] = float(np.mean(imp)) if imp else np.nan
    m["turnaround_share_improved"] = float(np.mean([x > 0 for x in imp])) if imp else np.nan
    m["turnaround_multiple_changed"] = sum(bool(p.get("multiple_changed")) for p in g)
    return m
