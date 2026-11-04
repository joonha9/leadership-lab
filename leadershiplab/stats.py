"""Permutation tests on draw-level outcomes (the draw is the unit of analysis)."""

from __future__ import annotations

import numpy as np


def perm_diff(a, b, n_perm: int = 20000, seed: int = 0) -> dict:
    """Two-sided permutation test for a difference in means (a - b)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    obs = a.mean() - b.mean()
    pool = np.concatenate([a, b])
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        hits += abs(pool[:len(a)].mean() - pool[len(a):].mean()) >= abs(obs) - 1e-12
    return {"diff": float(obs), "p": (hits + 1) / (n_perm + 1), "n_a": len(a), "n_b": len(b)}


def perm_contrast(values: dict[str, list[float]], plus: list[str], minus: list[str],
                  n_perm: int = 20000, seed: int = 0) -> dict:
    """Mean of the `plus` group means minus mean of the `minus` group means.

    Labels are shuffled across draws of all groups in plus + minus (group sizes kept), so each
    group counts equally whatever its number of draws.
    """
    groups = plus + minus
    vals = {g: np.asarray(values[g], float)[~np.isnan(np.asarray(values[g], float))] for g in groups}
    sizes = [len(vals[g]) for g in groups]
    pool = np.concatenate([vals[g] for g in groups])

    def stat(arr):
        means, i = [], 0
        for s in sizes:
            means.append(arr[i:i + s].mean())
            i += s
        k = len(plus)
        return float(np.mean(means[:k]) - np.mean(means[k:]))

    obs = stat(pool)
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        hits += abs(stat(pool)) >= abs(obs) - 1e-12
    return {"contrast": obs, "p": (hits + 1) / (n_perm + 1)}


def holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjusted p-values."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def spearman(x, y) -> float:
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    return float(np.corrcoef(rx, ry)[0, 1])


def bootstrap_ci(a, b, n_boot: int = 10000, seed: int = 0, level: float = 0.95) -> tuple[float, float]:
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    rng = np.random.default_rng(seed)
    d = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(n_boot)]
    lo, hi = np.quantile(d, [(1 - level) / 2, (1 + level) / 2])
    return float(lo), float(hi)


# ---------------------------------------------------------------- two-factor design (style x situation)

def _clean(v):
    v = np.asarray(v, float)
    return v[~np.isnan(v)]


def perm_did(s_x, c_x, s_y, c_y, n_perm: int = 20000, seed: int = 0) -> dict:
    """Difference in differences: (style - control in situation X) - (style - control in Y).

    Null: within each situation, style and control labels are exchangeable.
    """
    s_x, c_x, s_y, c_y = map(_clean, (s_x, c_x, s_y, c_y))
    obs = (s_x.mean() - c_x.mean()) - (s_y.mean() - c_y.mean())
    px, py = np.concatenate([s_x, c_x]), np.concatenate([s_y, c_y])
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(px)
        rng.shuffle(py)
        d = (px[:len(s_x)].mean() - px[len(s_x):].mean()) - (py[:len(s_y)].mean() - py[len(s_y):].mean())
        hits += abs(d) >= abs(obs) - 1e-12
    return {"did": float(obs), "p": (hits + 1) / (n_perm + 1)}


def _cell_table(y, a, b):
    A, B = sorted(set(a)), sorted(set(b))
    M = np.array([[y[(a == i) & (b == j)].mean() for j in B] for i in A])
    return M


def _interaction_ss(y, a, b):
    M = _cell_table(y, a, b)
    R = M - M.mean(axis=1, keepdims=True) - M.mean(axis=0, keepdims=True) + M.mean()
    return float((R ** 2).sum())


def perm_interaction(y, a, b, n_perm: int = 5000, seed: int = 0) -> dict:
    """Omnibus test that factor a's effects differ across levels of factor b.

    Statistic: sum of squared interaction residuals of the cell-mean table. Null distribution by
    permuting residuals of the additive (main-effects) model (ter Braak), which keeps both main
    effects and removes only the interaction.
    """
    y, a, b = np.asarray(y, float), np.asarray(a), np.asarray(b)
    ok = ~np.isnan(y)
    y, a, b = y[ok], a[ok], b[ok]
    obs = _interaction_ss(y, a, b)
    A, B = sorted(set(a)), sorted(set(b))
    M = _cell_table(y, a, b)
    add = M.mean(axis=1, keepdims=True) + M.mean(axis=0, keepdims=True) - M.mean()
    ia = np.array([A.index(x) for x in a])
    ib = np.array([B.index(x) for x in b])
    fit = add[ia, ib]
    res = y - fit
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n_perm):
        hits += _interaction_ss(fit + rng.permutation(res), a, b) >= obs - 1e-12
    return {"ss": obs, "p": (hits + 1) / (n_perm + 1)}


def bootstrap_spread(groups_x: dict, groups_y: dict, n_boot: int = 5000, seed: int = 0) -> dict:
    """Is the spread of condition means (SD across conditions) smaller in situation X than in Y?

    Statistic: SD_x - SD_y. Draws are resampled within each cell. Reports a 95% interval and the
    bootstrap share of SD_x - SD_y >= 0 (a one-sided p-value for "X smaller"). With equal cell
    sizes and similar noise, the upward bias that noise adds to each SD is similar in X and Y.
    """
    def sd(groups):
        return float(np.std([v.mean() for v in groups.values()], ddof=1))

    gx = {k: _clean(v) for k, v in groups_x.items()}
    gy = {k: _clean(v) for k, v in groups_y.items()}
    rng = np.random.default_rng(seed)
    boot = np.array([sd({k: rng.choice(v, len(v)) for k, v in gx.items()}) -
                     sd({k: rng.choice(v, len(v)) for k, v in gy.items()}) for _ in range(n_boot)])
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return {"sd_x": sd(gx), "sd_y": sd(gy), "diff": sd(gx) - sd(gy), "ci95": (float(lo), float(hi)),
            "p_one_sided_x_smaller": float((np.sum(boot >= 0) + 1) / (n_boot + 1))}
