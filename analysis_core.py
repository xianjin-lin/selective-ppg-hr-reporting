"""Released analysis core for selective PPG heart-rate reporting. Pure functions on aligned arrays.
Retained sets are fixed on the observed data; the bootstrap re-weights subjects (units) only and never re-ranks."""
import math

import numpy as np

FR = {"AF": 201369 / 289164, "SR": 1986265 / 2072598, "G-T": 3073030 / 3313901, "G-D": 420209 / 477880}
MIMIC_SIGN = {"E1": -1, "E2a": -1, "E2b": -1, "E3": +1}


def k_of(f, n):
    return int(math.floor(f * n + 0.5))


def retained(score, mask, f):
    """Top-k by descending score within mask; ties by ascending flat index (array position). Returns bool array."""
    idx = np.flatnonzero(mask)
    k = k_of(f, len(idx))
    order = np.lexsort((idx, -score[idx]))  # primary: -score, secondary: flat index
    out = np.zeros(len(score), bool)
    out[idx[order[:k]]] = True
    return out


def failure(hr, ref, lim=5.0):
    hr = np.asarray(hr, float)
    return ~np.isfinite(hr) | (np.abs(np.where(np.isfinite(hr), hr, 0.0) - ref) > lim)


class Contrast:
    """Per seed: subject-level vectors (numC, denC, numQ, denQ) and a kind:
    'ratio' -> 100*(numC/denC - numQ/denQ); 'cov' -> 100*(numC - numQ)/denC (denC == denQ); 'count' -> numC - numQ."""

    def __init__(self, cid, endpoint, config, label, kind, per_seed):
        self.cid, self.endpoint, self.config, self.label, self.kind, self.per_seed = cid, endpoint, config, label, kind, per_seed


def seed_stat(kind, nC, dC, nQ, dQ):
    with np.errstate(divide="ignore", invalid="ignore"):
        if kind == "ratio":
            v = 100 * (nC / dC - nQ / dQ)
            return np.where((dC > 0) & (dQ > 0), v, np.nan)
        if kind == "cov":
            return np.where(dC > 0, 100 * (nC - nQ) / dC, np.nan)
        return nC - nQ


def evaluate(contrasts, W):
    """W: weights [B, n_units] (or a single row of ones). Returns theta [B, J] (nan where undefined)."""
    out = np.empty((W.shape[0], len(contrasts)))
    for j, c in enumerate(contrasts):
        vals = [seed_stat(c.kind, W @ nC, W @ dC, W @ nQ, W @ dQ) for (nC, dC, nQ, dQ) in c.per_seed]
        out[:, j] = np.mean(np.vstack(vals), axis=0)  # nan if any seed undefined
    return out


def q_higher(x, q):
    x = np.sort(x)
    return x[min(len(x) - 1, int(math.ceil(q * len(x))) - 1)]


def family(theta_hat, theta_star, members):
    """Protocol 8.3 order of operations; returns per-member results, c, |V_F| and exclusions."""
    J = [j for j in members if np.isfinite(theta_hat[j])]
    excl = {j: "observed-undefined (non-estimable)" for j in members if j not in J}
    und = {j: float(np.mean(~np.isfinite(theta_star[:, j]))) for j in J}
    for j in list(J):
        if und[j] > 0.01:
            excl[j] = f"bootstrap-non-estimable ({und[j]:.4f} undefined)"; J.remove(j)
    for j in list(J):
        d = np.isfinite(theta_star[:, j])
        sd = np.std(theta_star[d, j], ddof=1) if d.sum() > 1 else 0.0
        if sd <= 1e-8 * max(1.0, abs(theta_hat[j])):
            excl[j] = "degenerate (sd ~ 0): point estimate only"; J.remove(j)
    V = np.all(np.isfinite(theta_star[:, J]), axis=1) if J else np.zeros(len(theta_star), bool)
    res = {}
    if J and V.sum() > 1:
        ts = theta_star[V][:, J]
        sd = ts.std(axis=0, ddof=1)
        T = np.max(np.abs(ts - theta_hat[J]) / sd, axis=1)
        c = q_higher(T, 0.95)
        for i, j in enumerate(J):
            res[j] = dict(sd=float(sd[i]), sim_lo=float(theta_hat[j] - c * sd[i]), sim_hi=float(theta_hat[j] + c * sd[i]),
                          marg_lo=float(np.percentile(ts[:, i], 2.5)), marg_hi=float(np.percentile(ts[:, i], 97.5)))
    else:
        c = float("nan")
    return dict(results=res, c=float(c), members_used=J, V_size=int(V.sum()), B=len(theta_star), exclusions=excl, V=V)


def stability(theta_hat, theta_star, fam):
    """Note S1 criteria on halves of the draws, within V_F."""
    J, V = fam["members_used"], fam["V"]
    B = len(theta_star)
    halves = [np.arange(B) < B // 2, np.arange(B) >= B // 2]
    stats = []
    for h in halves:
        ts = theta_star[V & h][:, J]
        sd = ts.std(axis=0, ddof=1)
        T = np.max(np.abs(ts - theta_hat[J]) / sd, axis=1)
        stats.append((q_higher(T, 0.95), sd))
    (c1, s1), (c2, s2) = stats
    rel_c = abs(c1 - c2) / max(c1, c2)
    rel_sd = float(np.max(np.abs(s1 - s2) / np.maximum(s1, s2)))
    sd_full = np.array([fam["results"][j]["sd"] for j in J])
    end = float(np.max(np.abs(c1 * s1 - c2 * s2) / sd_full))  # endpoint difference |theta+-c1 s1 - (theta+-c2 s2)| / sd
    return dict(c_half1=float(c1), c_half2=float(c2), rel_c_diff=float(rel_c), max_rel_sd_diff=rel_sd, max_endpoint_diff_sd=end,
                stable=bool(rel_c <= 0.02 and rel_sd <= 0.05 and end <= 0.10))


def weights(n_units, B, seed=20261016):
    return np.random.default_rng(seed).multinomial(n_units, np.full(n_units, 1.0 / n_units), size=B).astype(np.float64)


def category(endpoint, est, lo, hi):
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "technically undefined"
    sign = MIMIC_SIGN[endpoint]
    if lo > 0 or hi < 0:
        return "MIMIC direction supported" if np.sign(est) == sign else "opposite to MIMIC (not reproduced)"
    return "imprecise: interval includes 0 (point estimate " + ("same direction as MIMIC)" if np.sign(est) == sign else "opposite to MIMIC)")
