"""Metric extraction helpers for graders.

Functions accept an `EpisodeTrajectory` (utils.schemas.EpisodeTrajectory) and compute
the canonical raw metrics described in context/06_tasks_and_graders.md.
"""

from typing import Dict, List, Any
import math

import utils.constants as C


def _safe_get(raw: Dict[str, Any], key: str) -> float:
    try:
        return float(raw.get(key, 0.0))
    except Exception:
        return 0.0


def _extract(trajectory) -> Dict[str, List[float]]:
    P = []
    L = []
    T = []
    Pr = []
    U = []
    F = []
    S = []
    for step in getattr(trajectory, "steps", []):
        raw = getattr(step, "raw_state", {}) or {}
        P.append(_safe_get(raw, "P"))
        L.append(_safe_get(raw, "L"))
        T.append(_safe_get(raw, "T"))
        Pr.append(_safe_get(raw, "Pr"))
        U.append(_safe_get(raw, "U"))
        F.append(_safe_get(raw, "F"))
        S.append(_safe_get(raw, "S"))
    return {"P": P, "L": L, "T": T, "Pr": Pr, "U": U, "F": F, "S": S, "N": len(P)}


def compute_TE(trajectory) -> float:
    s = _extract(trajectory)
    N = s["N"]
    if N == 0:
        return 0.0
    return float(sum(abs(p - l) for p, l in zip(s["P"], s["L"])) / N)


def compute_OS(trajectory) -> float:
    s = _extract(trajectory)
    if s["N"] == 0:
        return 0.0
    diffs = [p - l for p, l in zip(s["P"], s["L"])]
    return float(max(0.0, max(diffs)))


def compute_SV(trajectory) -> float:
    s = _extract(trajectory)
    N = s["N"]
    if N == 0:
        return 0.0
    total = 0.0
    for t, pr in zip(s["T"], s["Pr"]):
        total += max(0.0, t - 1.0) + max(0.0, pr - 1.0)
    return float(total / N)


def compute_OC(trajectory) -> float:
    s = _extract(trajectory)
    N = s["N"]
    if N <= 1:
        return 0.0
    diffs = [abs(u1 - u0) for u0, u1 in zip(s["U"][:-1], s["U"][1:])]
    return float(sum(diffs) / max(1, (N - 1)))


def compute_SL(trajectory) -> float:
    s = _extract(trajectory)
    N = s["N"]
    if N == 0:
        return 0.0
    return float(sum(s["S"]) / N)


def compute_LP(trajectory) -> float:
    s = _extract(trajectory)
    N = s["N"]
    if N == 0:
        return 0.0
    return float(sum(max(0.0, abs(p - l) - 0.1) for p, l in zip(s["P"], s["L"])) / N)


def compute_LS(trajectory) -> float:
    s = _extract(trajectory)
    N = s["N"]
    if N == 0:
        return 0.0
    return float(sum(max(0.0, st - 0.5) for st in s["S"]) / N)


def compute_EMB(trajectory) -> float:
    s = _extract(trajectory)
    N = s["N"]
    if N == 0:
        return 0.0
    count = sum(1 for st, t in zip(s["S"], s["T"]) if st < 0.5 and t < 1.0)
    return float(count / N)


def compute_RT(trajectory) -> float:
    s = _extract(trajectory)
    N = s["N"]
    if N == 0:
        return 0.0
    for idx, (p, l, t) in enumerate(zip(s["P"], s["L"], s["T"])):
        if abs(p - l) < 0.1 and t < 1.0:
            return float(idx + 1)
    return float(N)


def compute_RR(trajectory) -> float:
    s = _extract(trajectory)
    N = s["N"]
    if N == 0:
        return 0.0
    return float(sum(max(0.0, t - 1.0) for t in s["T"]) / N)


def compute_failure_flag(trajectory) -> int:
    # FF = 1 if any termination due to catastrophic T/Pr/S breach else 0
    for step in getattr(trajectory, "steps", []):
        err = getattr(step, "error", None)
        if err and isinstance(err, str) and "Catastrophic" in err:
            return 1
        raw = getattr(step, "raw_state", {}) or {}
        if getattr(step, "done", False):
            if _safe_get(raw, "T") > C.FAIL_T or _safe_get(raw, "Pr") > C.FAIL_PR or _safe_get(raw, "S") > C.FAIL_S:
                return 1
    return 0


def compute_invalid_count(trajectory) -> int:
    count = 0
    for step in getattr(trajectory, "steps", []):
        if getattr(step, "env_invalid_action", False):
            count += 1
            continue
        parsed = getattr(step, "parsed_action", None)
        if parsed and getattr(parsed, "invalid_output", False):
            count += 1
    return count


def normalize_metrics(metrics: Dict[str, float], scales: Dict[str, float] = None) -> Dict[str, float]:
    if scales is None:
        scales = getattr(C, "METRIC_NORM_SCALES", {}) or {}
    normalized: Dict[str, float] = {}
    for k, v in metrics.items():
        scale = float(scales.get(k, 0.5)) if scales else 0.5
        if scale <= 0:
            normalized[k] = 0.0
        else:
            normalized[k] = float(max(0.0, min(1.0, v / scale)))
    return normalized
