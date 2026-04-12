"""Canonical logging utilities for judge-vetted stdout communication.

This module implements the strict logging contract required by the external 
evaluation portal. Any modification to these line formats may result in 
parsing failures during the autograding phase.
"""

from __future__ import annotations

from typing import Iterable, Optional

from utils.helpers import format_action_value, format_reward
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
        f'"U_target":{format_action_value(u_target)},'
        f'"F_target":{format_action_value(f_target)}'
        "}"
    )


def log_start(task: str, env: str, model: str) -> None:
    """
    Emit the required [START] delimiter following the OpenEnv specification.
    """
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(record: StepLogRecord) -> None:
    """Emit the required per-step line."""
    print(
        f"[STEP] step={record.step} action={record.action} reward={format_reward(record.reward)} "
        f"done={_bool_string(record.done)} error={_sanitize_single_line(record.error)}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: Iterable[float]) -> None:
    """
    Emit the required [END] delimiter, providing a comma-separated credit 
    assignment sequence for final score calculation.
    """
    rewards_string = ",".join(format_reward(reward) for reward in rewards)
    print(
        f"[END] success={_bool_string(success)} steps={steps} score={format_reward(score)} rewards={rewards_string}",
        flush=True,
    )

