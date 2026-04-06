"""Robust action parsing for untrusted LLM outputs."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping, Optional

from utils.schemas import ParsedAction

INVALID_OUTPUT_PENALTY = -1.0
DEFAULT_U_TARGET = 0.5
DEFAULT_F_TARGET = 0.5

_NUMBER_PATTERN = r"-?(?:\d+(?:\.\d*)?|\.\d+)"
_U_TARGET_PATTERN = re.compile(r'"U_target"\s*:\s*(' + _NUMBER_PATTERN + r")")
_F_TARGET_PATTERN = re.compile(r'"F_target"\s*:\s*(' + _NUMBER_PATTERN + r")")


def _clamp_unit_interval(value: Any, *, fallback: float) -> float:
	"""Coerce to float and clamp to [0.0, 1.0]."""
	try:
		numeric_value = float(value)
	except (TypeError, ValueError):
		numeric_value = fallback
	return max(0.0, min(1.0, numeric_value))


def _from_mapping(payload: Mapping[str, Any], raw_text: str) -> ParsedAction:
	"""Parse the expected JSON payload from a mapping."""
	if "U_target" not in payload or "F_target" not in payload:
		missing = []
		if "U_target" not in payload:
			missing.append("U_target")
		if "F_target" not in payload:
			missing.append("F_target")
		raise ValueError(f"missing required keys: {', '.join(missing)}")

	return ParsedAction(
		u_target=_clamp_unit_interval(payload["U_target"], fallback=DEFAULT_U_TARGET),
		f_target=_clamp_unit_interval(payload["F_target"], fallback=DEFAULT_F_TARGET),
		source="json",
		used_fallback=False,
		invalid_output=False,
		penalty_applied=0.0,
		raw_text=raw_text,
		parse_error=None,
	)


def _anchored_extract(raw_text: str) -> ParsedAction:
	"""Extract targets from anchored key/value pairs embedded in free text."""
	u_match = _U_TARGET_PATTERN.search(raw_text)
	f_match = _F_TARGET_PATTERN.search(raw_text)
	if not u_match or not f_match:
		raise ValueError("anchored extraction failed")

	return ParsedAction(
		u_target=_clamp_unit_interval(u_match.group(1), fallback=DEFAULT_U_TARGET),
		f_target=_clamp_unit_interval(f_match.group(1), fallback=DEFAULT_F_TARGET),
		source="fallback",
		used_fallback=True,
		invalid_output=True,
		penalty_applied=INVALID_OUTPUT_PENALTY,
		raw_text=raw_text,
		parse_error="strict_json_failed",
	)


def parse_llm_action(
	raw_text: Optional[str],
	previous_valid_action: Optional[Mapping[str, float]] = None,
	default_action: Optional[Mapping[str, float]] = None,
) -> ParsedAction:
	"""Parse untrusted model output into a canonical action without raising."""
	text = (raw_text or "").strip()
	fallback_default = default_action or {
		"U_target": DEFAULT_U_TARGET,
		"F_target": DEFAULT_F_TARGET,
	}

	try:
		payload = json.loads(text)
		if not isinstance(payload, Mapping):
			raise ValueError("json payload is not an object")
		return _from_mapping(payload, text)
	except Exception as json_error:
		json_error_message = str(json_error)

	try:
		return _anchored_extract(text)
	except Exception as fallback_error:
		fallback_error_message = str(fallback_error)

	if previous_valid_action is not None:
		return ParsedAction(
			u_target=_clamp_unit_interval(previous_valid_action.get("U_target"), fallback=DEFAULT_U_TARGET),
			f_target=_clamp_unit_interval(previous_valid_action.get("F_target"), fallback=DEFAULT_F_TARGET),
			source="previous_valid",
			used_fallback=True,
			invalid_output=True,
			penalty_applied=INVALID_OUTPUT_PENALTY,
			raw_text=text,
			parse_error=f"{json_error_message}; {fallback_error_message}",
		)

	return ParsedAction(
		u_target=_clamp_unit_interval(fallback_default.get("U_target"), fallback=DEFAULT_U_TARGET),
		f_target=_clamp_unit_interval(fallback_default.get("F_target"), fallback=DEFAULT_F_TARGET),
		source="default",
		used_fallback=True,
		invalid_output=True,
		penalty_applied=INVALID_OUTPUT_PENALTY,
		raw_text=text,
		parse_error=f"{json_error_message}; {fallback_error_message}",
	)

