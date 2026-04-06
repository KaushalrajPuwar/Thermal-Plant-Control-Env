"""Judge-facing stdout helpers with frozen line formats."""

from __future__ import annotations

from typing import Iterable, Optional

from utils.schemas import StepLogRecord


def _sanitize_single_line(value: Optional[str]) -> str:
	"""Collapse arbitrary text into a single-line field-safe string."""
	if value is None or value == "":
		return "null"
	return " ".join(str(value).split())


def _bool_string(value: bool) -> str:
	"""Return the lowercase boolean representation required by the judges."""
	return "true" if value else "false"


def canonical_action_string(u_target: float, f_target: float) -> str:
	"""Return deterministic compact JSON for action logging."""
	return (
		"{"
		f'"U_target":{u_target:.2f},'
		f'"F_target":{f_target:.2f}'
		"}"
	)


def log_start(task: str, env: str, model: str) -> None:
	"""Emit the required episode-start line."""
	print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(record: StepLogRecord) -> None:
	"""Emit the required per-step line."""
	print(
		f"[STEP] step={record.step} action={record.action} reward={record.reward:.2f} "
		f"done={_bool_string(record.done)} error={_sanitize_single_line(record.error)}",
		flush=True,
	)


def log_end(success: bool, steps: int, score: float, rewards: Iterable[float]) -> None:
	"""Emit the required episode-end line."""
	rewards_string = ",".join(f"{reward:.2f}" for reward in rewards)
	print(
		f"[END] success={_bool_string(success)} steps={steps} score={score:.2f} rewards={rewards_string}",
		flush=True,
	)
