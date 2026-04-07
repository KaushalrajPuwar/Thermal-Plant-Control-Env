"""Core thermal plant environment implementation.

This module provides the contract surface for reset(), step(), and state().
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import logging

from env.state import ThermalPlantState
from env.transitions import (
	build_coherent_initial_state,
	clamp_action_targets,
	clamp_state,
	compute_reward,
	is_catastrophic,
	update_actuators,
	update_degradation,
	update_power,
	update_pressure,
	update_stress,
	update_temperature,
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
		prev_state = ThermalPlantState(**self._state.to_raw_dict())
		invalid_action = False
		error_msg: Optional[str] = None

		try:
			raw_u_target = action.get(ACTION_U_TARGET, prev_state.U)
			raw_f_target = action.get(ACTION_F_TARGET, prev_state.F)
			u_target, f_target = clamp_action_targets(raw_u_target, raw_f_target)
		except Exception:
			invalid_action = True
			error_msg = "invalid_action_payload"
			u_target, f_target = prev_state.U, prev_state.F

		# Transition order is explicit and deterministic.
		new_u, new_f = update_actuators(prev_state.U, prev_state.F, u_target, f_target)
		new_p = update_power(prev_state.P, new_u)
		new_d = update_degradation(prev_state.D, u_target, prev_state.U)
		new_t = update_temperature(prev_state.T, new_p, new_f, new_d)
		new_pr = update_pressure(prev_state.Pr, new_t, new_p)
		new_s = update_stress(prev_state.S, new_t)

		self._state = ThermalPlantState(
			P=new_p,
			L=prev_state.L,
			T=new_t,
			Pr=new_pr,
			U=new_u,
			F=new_f,
			S=new_s,
			D=new_d,
		)
		self._state = clamp_state(self._state)
		self._step_count += 1

		reward = compute_reward(self._state, prev_u=prev_state.U)
		done = is_catastrophic(self._state) or self._step_count >= self.max_steps

		info: Dict[str, Any] = {
			"error": error_msg,
			"step_count": self._step_count,
			"invalid_action": invalid_action,
		}
		return self._state.to_observation(), float(reward), bool(done), info
