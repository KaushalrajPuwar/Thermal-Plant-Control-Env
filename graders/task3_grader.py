"""Task 3 grader: Preemptive constraint management.

Implements specification from context/06_tasks_and_graders.md.
"""

from __future__ import annotations

from ._metrics import (
	compute_TE,
	compute_LS,
	compute_SV,
	compute_EMB,
	compute_failure_flag,
	compute_invalid_count,
	normalize_metrics,
)
import utils.constants as C


def grade(trajectory) -> float:
	te = compute_TE(trajectory)
	ls = compute_LS(trajectory)
	sv = compute_SV(trajectory)
	emb = compute_EMB(trajectory)
	ff = compute_failure_flag(trajectory)
	invalid_count = compute_invalid_count(trajectory)

	norm = normalize_metrics({"TE": te, "LS": ls, "SV": sv})

	score = 1.0
	score -= 0.3 * norm.get("TE", 0.0)
	score -= 0.3 * norm.get("LS", 0.0)
	score -= 0.2 * norm.get("SV", 0.0)
	score += 0.2 * float(emb)
	score -= 0.3 * (1 if ff else 0)

	score -= invalid_count * getattr(C, "INVALID_ACTION_PENALTY", 0.2)

	return float(max(0.0, min(1.0, score)))
