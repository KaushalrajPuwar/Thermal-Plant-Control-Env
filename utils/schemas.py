"""Structured contracts for inference parsing, logging, and trajectory capture."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional


ActionSource = Literal["json", "fallback", "previous_valid", "default"]


@dataclass(frozen=True)
class ParsedAction:
    """Canonical parser result consumed by the inference loop."""

    u_target: float
    f_target: float
    source: ActionSource
    used_fallback: bool
    invalid_output: bool
    penalty_applied: float
    raw_text: str
    parse_error: Optional[str] = None

    def to_action_dict(self) -> Dict[str, float]:
        """Return the env-ready action payload."""
        return {
            "U_target": self.u_target,
            "F_target": self.f_target,
        }


@dataclass(frozen=True)
class StepLogRecord:
    """Single stdout step log payload."""

    step: int
    action: str
    reward: float
    done: bool
    error: Optional[str]


@dataclass(frozen=True)
class TrajectoryStep:
    """Detailed step record for graders and downstream reporting."""

    step: int
    raw_llm_text: str
    parsed_action: ParsedAction
    canonical_action: Dict[str, float]
    observation: Dict[str, float]
    raw_state: Dict[str, float]
    reward: float
    done: bool
    error: Optional[str]
    env_invalid_action: bool
    invalid_penalty_applied: float


@dataclass(frozen=True)
class TrajectorySummary:
    """Episode-level summary for graders and reporting."""

    task: str
    benchmark: str
    model: str
    total_steps: int
    rewards: List[float]
    success: bool
    final_score: float
    termination_reason: str


@dataclass
class EpisodeTrajectory:
    """Complete episode artifact captured during inference."""

    task: str
    benchmark: str
    model: str
    steps: List[TrajectoryStep] = field(default_factory=list)
    summary: Optional[TrajectorySummary] = None

