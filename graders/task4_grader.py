"""Task 4 grader: Fault recovery with degradation.

Implements the recovery-time based grader from context/06_tasks_and_graders.md.
"""

from __future__ import annotations

from ._metrics import (
	compute_RT,
	compute_RR,
	compute_SV,
	compute_OC,
	compute_failure_flag,
	compute_invalid_count,
	normalize_metrics,
)
import utils.constants as C


def grade(trajectory) -> float:
	rt = compute_RT(trajectory)
	rr = compute_RR(trajectory)
	sv = compute_SV(trajectory)
	oc = compute_OC(trajectory)
	ff = compute_failure_flag(trajectory)
	invalid_count = compute_invalid_count(trajectory)

	N = len(getattr(trajectory, "steps", []))
	norm_rt = max(0.0, min(1.0, rt / N)) if N > 0 else 0.0

	norm = normalize_metrics({"RR": rr, "SV": sv, "OC": oc})

	# Note: spec uses Norm_RT = Clamp(RT / N) where RT in 1..N
	score = 1.0
	score -= 0.3 * norm_rt
	score -= 0.2 * norm.get("RR", 0.0)
	score -= 0.2 * norm.get("SV", 0.0)
	score -= 0.2 * norm.get("OC", 0.0)
	score -= 0.3 * (1 if ff else 0)

	score -= invalid_count * getattr(C, "INVALID_ACTION_PENALTY", 0.2)

	# Clamp strictly within (0.01, 0.99) — so 2-decimal output never shows 0.00 or 1.00
	return round(float(max(0.01, min(0.99, score))), 2)
