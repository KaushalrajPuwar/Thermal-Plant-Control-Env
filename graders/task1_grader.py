"""Task 1 grader: Stable baseline operation.

Grader implements the formula from context/06_tasks_and_graders.md and
returns a float in [0,1].
"""

from __future__ import annotations

from ._metrics import (
	compute_TE,
	compute_SV,
	compute_OC,
	compute_failure_flag,
	compute_invalid_count,
	normalize_metrics,
)
import utils.constants as C


def grade(trajectory) -> float:
	"""Compute Task 1 score from trajectory and return a float in [0,1]."""
	te = compute_TE(trajectory)
	sv = compute_SV(trajectory)
	oc = compute_OC(trajectory)
	ff = compute_failure_flag(trajectory)
	invalid_count = compute_invalid_count(trajectory)

	norm = normalize_metrics({"TE": te, "SV": sv, "OC": oc})

	score = 1.0
	score -= 0.5 * norm.get("TE", 0.0)
	score -= 0.2 * norm.get("SV", 0.0)
	score -= 0.2 * norm.get("OC", 0.0)
	score -= 0.3 * (1 if ff else 0)

	# Apply per-invalid-step penalty
	score -= invalid_count * getattr(C, "INVALID_ACTION_PENALTY", 0.2)

	# Clamp strictly within (0.01, 0.99) — so 2-decimal output never shows 0.00 or 1.00
	return round(float(max(0.01, min(0.99, score))), 2)
