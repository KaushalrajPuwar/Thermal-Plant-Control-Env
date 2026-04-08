"""Robust action parsing for untrusted LLM outputs."""

from __future__ import annotations

import json
import re
import os
from typing import Any, Mapping, Optional

from utils.schemas import ParsedAction
from utils.constants import PARSER_DEFAULT_U, PARSER_DEFAULT_F, INVALID_ACTION_PENALTY

INVALID_OUTPUT_PENALTY = -INVALID_ACTION_PENALTY

_NUMBER_PATTERN = r"-?(?:\d+(?:\.\d*)?|\.\d+)"
_U_TARGET_PATTERN = re.compile(r'(?i)["\']?u_target["\']?(?:\s*[:=]\s*|\s+)(' + _NUMBER_PATTERN + r')')
_F_TARGET_PATTERN = re.compile(r'(?i)["\']?f_target["\']?(?:\s*[:=]\s*|\s+)(' + _NUMBER_PATTERN + r')')
_PAIR_PATTERN = re.compile(r'^\s*(' + _NUMBER_PATTERN + r')[\s,;]+(' + _NUMBER_PATTERN + r')\s*$')


def _clamp_unit_interval(value: Any, *, fallback: float) -> float:
    """Coerce to float and clamp to [0.0, 1.0]."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        numeric_value = fallback
    return max(0.0, min(1.0, numeric_value))


def _from_mapping(payload: Mapping[str, Any], raw_text: str) -> ParsedAction:
    """Parse the expected JSON payload from a mapping."""
    # Find keys ignoring case
    u_key = next((k for k in payload.keys() if k.lower() == "u_target"), "U_target")
    f_key = next((k for k in payload.keys() if k.lower() == "f_target"), "F_target")
    
    if u_key not in payload or f_key not in payload:
        missing = []
        if u_key not in payload:
            missing.append("U_target")
        if f_key not in payload:
            missing.append("F_target")
        raise ValueError(f"missing required keys: {', '.join(missing)}")

    return ParsedAction(
        u_target=_clamp_unit_interval(payload[u_key], fallback=PARSER_DEFAULT_U),
        f_target=_clamp_unit_interval(payload[f_key], fallback=PARSER_DEFAULT_F),
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
        u_target=_clamp_unit_interval(u_match.group(1), fallback=PARSER_DEFAULT_U),
        f_target=_clamp_unit_interval(f_match.group(1), fallback=PARSER_DEFAULT_F),
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
		"U_target": PARSER_DEFAULT_U,
		"F_target": PARSER_DEFAULT_F,
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

	# Always try to match the compact "value value" pair format as a valid
	# alternative to JSON, since the system prompt may be tuned for pair output.
	pair_match = _PAIR_PATTERN.match(text)
	if pair_match:
		u_val = _clamp_unit_interval(pair_match.group(1), fallback=PARSER_DEFAULT_U)
		f_val = _clamp_unit_interval(pair_match.group(2), fallback=PARSER_DEFAULT_F)
		return ParsedAction(
			u_target=u_val,
			f_target=f_val,
			source="fallback",
			used_fallback=False,
			invalid_output=False,
			penalty_applied=0.0,
			raw_text=text,
			parse_error=None,
		)

	if previous_valid_action is not None:
		return ParsedAction(
			u_target=_clamp_unit_interval(previous_valid_action.get("U_target"), fallback=PARSER_DEFAULT_U),
			f_target=_clamp_unit_interval(previous_valid_action.get("F_target"), fallback=PARSER_DEFAULT_F),
			source="previous_valid",
			used_fallback=True,
			invalid_output=True,
			penalty_applied=INVALID_OUTPUT_PENALTY,
			raw_text=text,
			parse_error=f"{json_error_message}; {fallback_error_message}",
		)

	return ParsedAction(
		u_target=_clamp_unit_interval(fallback_default.get("U_target"), fallback=PARSER_DEFAULT_U),
		f_target=_clamp_unit_interval(fallback_default.get("F_target"), fallback=PARSER_DEFAULT_F),
		source="default",
		used_fallback=True,
		invalid_output=True,
		penalty_applied=INVALID_OUTPUT_PENALTY,
		raw_text=text,
		parse_error=f"{json_error_message}; {fallback_error_message}",
	)

