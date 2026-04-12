"""Task 1 grader: Stable baseline operation.

This grader calculates the performance score for the 'Stable State' challenge. 
It prioritise tracking accuracy (TE) while penalising safety excursions (SV) 
and control oscillations (OC).
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
	"""
	Compute the Task 1 score from a complete episode trajectory.
	
	The scoring logic uses 'Sigma-Standardisation' to normalise physical 
	observables into a weighted penalty sum. The final score is rounded 
	and clamped to ensure a consistent 2-decimal presentation.
	"""
	te = compute_TE(trajectory)
	sv = compute_SV(trajectory)
	oc = compute_OC(trajectory)
	ff = compute_failure_flag(trajectory)
	invalid_count = compute_invalid_count(trajectory)

	norm = normalize_metrics({"TE": te, "SV": sv, "OC": oc})

	# Start from perfect credit and decrement based on weighted violations
	score = 1.0
	score -= 0.5 * norm.get("TE", 0.0) # Tracking Error weight
	score -= 0.4 * norm.get("SV", 0.0) # Safety Violation weight
	score -= 0.2 * norm.get("OC", 0.0) # Oscillation Count weight
	score -= 0.3 * (1 if ff else 0)   # Failure Flag penalty

	# Apply per-invalid-step penalty for malformed parsing results
	score -= invalid_count * getattr(C, "INVALID_ACTION_PENALTY", 0.2)

	# Clamp strictly within (0.01, 0.99) to provide a fair but strict boundary
	return round(float(max(0.01, min(0.99, score))), 2)
