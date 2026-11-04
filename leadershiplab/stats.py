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
