"""Core thermal plant environment implementation.

This module provides the contract surface for reset(), step(), and state().
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import logging

from env.state import ThermalPlantState
from env.transitions import (
	build_coherent_initial_state,
	integration_step,
)
from utils.constants import (
	ACTION_F_TARGET,
	ACTION_U_TARGET,
	DEFAULT_EPISODE_ID,
	DEFAULT_MAX_STEPS,
	DEFAULT_TASK_ID,
)


class ThermalPlantEnv:
	"""Deterministic thermal plant environment core.

	Determinism assumptions:
	- No random number generation is used in state transitions.
	- Floating-point operations are executed in a fixed order per step.
	- Identical initial state and action sequence produce identical trajectories.

	Step return contract:
	- observation: Dict[str, float] rounded for agent-facing display
		- reward: float
		- done: bool
		- info: Dict[str, Any] with keys: error, step_count, invalid_action
	"""

	def __init__(
		self,
		max_steps: int = DEFAULT_MAX_STEPS,
		task_id: str = DEFAULT_TASK_ID,
		episode_id: int = DEFAULT_EPISODE_ID,
	) -> None:
		self.max_steps = max_steps
		self.task_id = task_id
		self.episode_id = int(episode_id)
		self._state = build_coherent_initial_state(task_id=self.task_id, episode_id=self.episode_id)
		self._step_count = 0

	def reset(self, task_id: Optional[str] = None, episode_id: Optional[int] = None) -> Dict[str, float]:
		"""Reset environment state and return a task-aware initial observation."""
		if task_id is not None:
			self.task_id = task_id
		if episode_id is not None:
			self.episode_id = int(episode_id)

		# Build task-aware startup state. If an unknown task_id is provided,
		# fall back to the default task id and log a warning so validator runs
		# continue (robust behaviour for external callers).
		try:
			self._state = build_coherent_initial_state(task_id=self.task_id, episode_id=self.episode_id)
		except ValueError as exc:
			logging.warning("reset(): unknown task_id '%s' - falling back to default '%s' (%s)", self.task_id, DEFAULT_TASK_ID, exc)
			self.task_id = DEFAULT_TASK_ID
			self._state = build_coherent_initial_state(task_id=self.task_id, episode_id=self.episode_id)
		self._step_count = 0
		return self._state.to_observation()

	def state(self) -> Dict[str, float]:
		"""Return the current full-precision internal state."""
		return self._state.to_dict()

	def step(self, action: Dict[str, Any]) -> Tuple[Dict[str, float], float, bool, Dict[str, Any]]:
		"""Advance one deterministic time step using the action dictionary."""
		invalid_action = False
		error_msg: Optional[str] = None
		
		# Validation
		if not isinstance(action, dict):
			invalid_action = True
			error_msg = "action_not_dict"
			action = {}
		
		try:
			# Just explicitly check if things are castable to float
			if ACTION_U_TARGET in action:
				float(action[ACTION_U_TARGET])
			if ACTION_F_TARGET in action:
				float(action[ACTION_F_TARGET])
		except (ValueError, TypeError):
			invalid_action = True
			error_msg = "invalid_action_payload"
			action = {}

		next_state, reward, done_catastrophic, transition_info = integration_step(self._state, action)
		
		if invalid_action:
			transition_info["invalid_action"] = True
			if not transition_info.get("error"):
				transition_info["error"] = error_msg
		
		self._state = next_state
		self._step_count += 1
		
		done = done_catastrophic or self._step_count >= self.max_steps
		
		info: Dict[str, Any] = {
			"error": transition_info.get("error"),
			"step_count": self._step_count,
			"invalid_action": transition_info.get("invalid_action", False),
			"invalid_action_penalty": transition_info.get("invalid_action_penalty", 0.0)
		}
		return self._state.to_observation(), float(reward), bool(done), info
