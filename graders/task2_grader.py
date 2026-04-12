"""Task 2 grader: Load following.

Formula from context/06_tasks_and_graders.md. Returns a float in [0,1].
"""

from __future__ import annotations

from ._metrics import (
	compute_TE,
	compute_OS,
	compute_LP,
	compute_SV,
	compute_failure_flag,
	compute_invalid_count,
	normalize_metrics,
)
import utils.constants as C


def grade(trajectory) -> float:
	te = compute_TE(trajectory)
	os_ = compute_OS(trajectory)
	lp = compute_LP(trajectory)
	sv = compute_SV(trajectory)
	ff = compute_failure_flag(trajectory)
	invalid_count = compute_invalid_count(trajectory)

	norm = normalize_metrics({"TE": te, "OS": os_, "LP": lp, "SV": sv})

	score = 1.0
	score -= 0.4 * norm.get("TE", 0.0)
	score -= 0.2 * norm.get("OS", 0.0)
	score -= 0.2 * norm.get("LP", 0.0)
	score -= 0.2 * norm.get("SV", 0.0)
	score -= 0.3 * (1 if ff else 0)

	score -= invalid_count * getattr(C, "INVALID_ACTION_PENALTY", 0.2)

	# Clamp strictly within (0.01, 0.99) — so 2-decimal output never shows 0.00 or 1.00
	return round(float(max(0.01, min(0.99, score))), 2)
