"""Pure transition functions for deterministic thermal plant dynamics.

Update order contract used by env core:
1) clamp action targets
2) actuator inertia (U, F)
3) power (P)
4) degradation (D) used by current-step cooling
5) temperature (T)
6) pressure (Pr)
7) stress (S)
8) clamp state bounds
9) done checks and reward computation
"""

from __future__ import annotations

from typing import Dict, Tuple

from env.state import ThermalPlantState
from utils.constants import (
	COOL_DEG_LOSS,
	D_BOUNDS,
	DEGRADATION_RATE,
	F_BOUNDS,
	FAIL_PR,
	FAIL_S,
	FAIL_T,
	F_INERTIA_PREV,
	F_INERTIA_TARGET,
	F_MARGIN_RELIEF,
	F_POWER_GAIN,
	F_STRESS_GAIN,
	F_TENSION_GAIN,
	F_WEAR_GAIN,
	GAP_DEG_DRAG,
	GAP_TENSION_DRAG,
	INIT_P_U_GAIN,
	INIT_T_BIAS,
	INIT_T_F_GAIN,
	INIT_T_P_GAIN,
	K_COOL_BASE,
	L_BOUNDS,
	OSCILLATION_PENALTY_COEF,
	P_BOUNDS,
	PR_BOUNDS,
	PR_DEG_GAIN,
	PR_MARGIN_PENALTY,
	PR_MIX_COEF,
	PR_POWER_COEF,
	PR_PREV_COEF,
	PR_TENSION_GAIN,
	P_STRESS_DRAG,
	P_PREV_COEF,
	P_U_COEF,
	RECOVER_F_GAIN,
	RECOVER_P_GAIN,
	S_BOUNDS,
	SAFETY_PENALTY_COEF,
	SOFT_PR,
	SOFT_T,
	STRESS_PENALTY_COEF,
	STRESS_RATE,
	T_BOUNDS,
	T_DEG_GAIN,
	T_STRESS_GAIN,
	T_TENSION_GAIN,
	TASK_CODE,
	TASK_STARTUP_PROFILES,
	T_POWER_COEF,
	T_WARNING,
	U_BOUNDS,
	U_INERTIA_PREV,
	U_INERTIA_TARGET,
	U_GAP_GAIN,
	U_MARGIN_RELIEF,
	U_WEAR_GAIN,
)


def clamp(value: float, low: float, high: float) -> float:
	"""Clamp a numeric value to [low, high]."""
	return max(low, min(high, value))


def clamp_action_targets(u_target: float, f_target: float) -> Tuple[float, float]:
	"""Clamp action targets to valid actuator ranges."""
	u = clamp(float(u_target), U_BOUNDS[0], U_BOUNDS[1])
	f = clamp(float(f_target), F_BOUNDS[0], F_BOUNDS[1])
	return u, f


def _xorshift32(seed: int) -> int:
	"""Return the next deterministic 32-bit xorshift state."""
	seed &= 0xFFFFFFFF
	seed ^= (seed << 13) & 0xFFFFFFFF
	seed ^= (seed >> 17) & 0xFFFFFFFF
	seed ^= (seed << 5) & 0xFFFFFFFF
	return seed & 0xFFFFFFFF


def _seed_stream(task_id: str, episode_id: int, count: int = 8) -> Tuple[float, ...]:
	"""Generate deterministic floats in [0, 1] from task and episode identifiers."""
	if task_id not in TASK_CODE:
		raise ValueError(f"Unknown task_id '{task_id}'. Expected one of {tuple(TASK_CODE)}.")

	seed = ((episode_id + 1) * 2654435761 + TASK_CODE[task_id] * 1013904223) & 0xFFFFFFFF
	if seed == 0:
		seed = 0xA511E9B3

	values = []
	for _ in range(count):
		seed = _xorshift32(seed)
		values.append(seed / 4294967295.0)
	return tuple(values)


def _task_profile(task_id: str) -> Dict[str, float]:
	"""Return the regime-map coefficients for a supported task."""
	if task_id not in TASK_STARTUP_PROFILES:
		raise ValueError(f"Unknown task_id '{task_id}'. Expected one of {tuple(TASK_STARTUP_PROFILES)}.")
	return TASK_STARTUP_PROFILES[task_id]


def _compute_regime_variables(profile: Dict[str, float], samples: Tuple[float, ...]) -> Dict[str, float]:
	"""Map seed samples into a coupled startup regime for the selected task."""
	r1, r2, r3, r4, r5, r6, _, _ = samples
	g_load = clamp(profile["aL"] + profile["sL"] * (2.0 * r1 - 1.0), 0.0, 1.0)
	g_wear = clamp(
		profile["aD"] + profile["sD"] * (0.70 * r2 + 0.20 * r4 + 0.10 * abs(2.0 * r3 - 1.0)),
		0.0,
		1.0,
	)
	g_tension = clamp(
		profile["aT"] + profile["sT"] * (0.45 * r4 + 0.25 * g_load + 0.20 * g_wear + 0.10 * max(0.0, 2.0 * r3 - 1.0)),
		0.0,
		1.0,
	)
	g_margin = clamp(
		profile["aM"] + profile["sM"] * ((2.0 * r5 - 1.0) - 0.35 * g_tension - 0.25 * g_wear + 0.10 * (2.0 * r6 - 1.0)),
		0.0,
		1.0,
	)
	g_gap = (
		profile["gap_scale"] * (2.0 * r3 - 1.0) * (0.35 + 0.65 * g_load)
		- GAP_DEG_DRAG * g_wear
		- GAP_TENSION_DRAG * g_tension
	)
	return {
		"G_load": g_load,
		"G_wear": g_wear,
		"G_tension": g_tension,
		"G_margin": g_margin,
		"G_gap": g_gap,
	}


def _solve_controls(load: float, power: float, degradation: float, stress: float, g_tension: float, g_margin: float, profile: Dict[str, float]) -> Tuple[float, float]:
	"""Solve the inherited startup controls from the coupled operating regime."""
	u = clamp(
		power / INIT_P_U_GAIN
		+ U_WEAR_GAIN * degradation
		+ U_GAP_GAIN * max(0.0, power - load)
		- U_MARGIN_RELIEF * g_margin,
		U_BOUNDS[0],
		U_BOUNDS[1],
	)
	f = clamp(
		profile["f_bias"]
		+ F_POWER_GAIN * power
		+ F_WEAR_GAIN * degradation
		+ F_TENSION_GAIN * g_tension
		+ F_STRESS_GAIN * stress
		- F_MARGIN_RELIEF * g_margin,
		F_BOUNDS[0],
		F_BOUNDS[1],
	)
	return u, f


def _solve_thermal_state(power: float, cooling: float, degradation: float, stress: float, g_tension: float, g_margin: float, profile: Dict[str, float]) -> Tuple[float, float, float]:
	"""Solve effective cooling, temperature, and pressure from the startup regime."""
	cool = cooling * (1.0 - COOL_DEG_LOSS * degradation) * (0.75 + 0.25 * g_margin)
	temperature = clamp(
		INIT_T_BIAS
		+ INIT_T_P_GAIN * power
		- INIT_T_F_GAIN * cool
		+ T_DEG_GAIN * degradation
		+ T_STRESS_GAIN * stress
		+ T_TENSION_GAIN * g_tension
		+ profile["t_task_bias"],
		T_BOUNDS[0],
		T_BOUNDS[1],
	)
	pressure = clamp(
		temperature
		+ PR_POWER_COEF * power
		+ PR_DEG_GAIN * degradation
		+ PR_TENSION_GAIN * g_tension
		+ PR_MARGIN_PENALTY * (1.0 - g_margin),
		PR_BOUNDS[0],
		PR_BOUNDS[1],
	)
	return cool, temperature, pressure


def build_coherent_initial_state(task_id: str, episode_id: int) -> ThermalPlantState:
	"""Build a deterministic, task-aware startup state from a coupled regime map."""
	profile = _task_profile(task_id)
	samples = _seed_stream(task_id=task_id, episode_id=int(episode_id))
	regime = _compute_regime_variables(profile=profile, samples=samples)

	load = clamp(regime["G_load"], L_BOUNDS[0], L_BOUNDS[1])
	degradation = clamp(profile["d_max"] * regime["G_wear"], D_BOUNDS[0], D_BOUNDS[1])
	stress = clamp(
		profile["s_base"] + profile["s_gain"] * max(0.0, regime["G_tension"] - 0.60 * regime["G_margin"]),
		S_BOUNDS[0],
		S_BOUNDS[1],
	)
	power = clamp(load + regime["G_gap"] - P_STRESS_DRAG * stress, P_BOUNDS[0], P_BOUNDS[1])
	control, cooling = _solve_controls(
		load=load,
		power=power,
		degradation=degradation,
		stress=stress,
		g_tension=regime["G_tension"],
		g_margin=regime["G_margin"],
		profile=profile,
	)
	_, temperature, pressure = _solve_thermal_state(
		power=power,
		cooling=cooling,
		degradation=degradation,
		stress=stress,
		g_tension=regime["G_tension"],
		g_margin=regime["G_margin"],
		profile=profile,
	)

	risk = max(0.0, temperature - profile["soft_t_cap"]) + max(0.0, pressure - profile["soft_pr_cap"])
	if risk > 0.0:
		cooling = clamp(cooling + RECOVER_F_GAIN * risk, F_BOUNDS[0], F_BOUNDS[1])
		power = clamp(power - RECOVER_P_GAIN * risk, P_BOUNDS[0], P_BOUNDS[1])
		control, _ = _solve_controls(
			load=load,
			power=power,
			degradation=degradation,
			stress=stress,
			g_tension=regime["G_tension"],
			g_margin=regime["G_margin"],
			profile=profile,
		)
		_, temperature, pressure = _solve_thermal_state(
			power=power,
			cooling=cooling,
			degradation=degradation,
			stress=stress,
			g_tension=regime["G_tension"],
			g_margin=regime["G_margin"],
			profile=profile,
		)

	state = ThermalPlantState(
		P=power,
		L=load,
		T=temperature,
		Pr=pressure,
		U=control,
		F=cooling,
		S=stress,
		D=degradation,
	)
	return clamp_state(state)


def update_actuators(prev_u: float, prev_f: float, u_target: float, f_target: float) -> Tuple[float, float]:
	"""Apply actuator inertia to smooth changes in control inputs."""
	u = U_INERTIA_PREV * prev_u + U_INERTIA_TARGET * u_target
	f = F_INERTIA_PREV * prev_f + F_INERTIA_TARGET * f_target
	return u, f


def update_power(prev_p: float, u: float) -> float:
	"""Update power with lagged response to control input."""
	return P_PREV_COEF * prev_p + P_U_COEF * u


def compute_cooling_coeff(prev_t: float, degradation: float) -> float:
	"""Compute cooling coefficient with temperature and current-step degradation."""
	k_cool = K_COOL_BASE * (1.0 - min(1.0, prev_t))
	return k_cool * (1.0 - degradation)


def update_temperature(prev_t: float, p: float, f: float, degradation: float) -> float:
	"""Update temperature from power heating and cooling flow.

	Uses current-step degradation D(t) for cooling effectiveness.
	"""
	k_cool_final = compute_cooling_coeff(prev_t=prev_t, degradation=degradation)
	return prev_t + T_POWER_COEF * p - k_cool_final * f


def update_pressure(prev_pr: float, t: float, p: float) -> float:
	"""Update pressure from coupled temperature and power dynamics."""
	return PR_PREV_COEF * prev_pr + PR_MIX_COEF * (t + PR_POWER_COEF * p)


def update_stress(prev_s: float, t: float) -> float:
	"""Accumulate stress only when temperature exceeds warning threshold."""
	return prev_s + max(0.0, t - T_WARNING) * STRESS_RATE


def update_degradation(prev_d: float, u_target: float, prev_u: float) -> float:
	"""Accumulate degradation from aggressive control target shifts."""
	return prev_d + DEGRADATION_RATE * abs(u_target - prev_u)


def clamp_state(state: ThermalPlantState) -> ThermalPlantState:
	"""Clamp all state values to their configured bounds."""
	state.P = clamp(state.P, P_BOUNDS[0], P_BOUNDS[1])
	state.L = clamp(state.L, L_BOUNDS[0], L_BOUNDS[1])
	state.U = clamp(state.U, U_BOUNDS[0], U_BOUNDS[1])
	state.F = clamp(state.F, F_BOUNDS[0], F_BOUNDS[1])
	state.T = clamp(state.T, T_BOUNDS[0], T_BOUNDS[1])
	state.Pr = clamp(state.Pr, PR_BOUNDS[0], PR_BOUNDS[1])
	state.S = clamp(state.S, S_BOUNDS[0], S_BOUNDS[1])
	state.D = clamp(state.D, D_BOUNDS[0], D_BOUNDS[1])
	return state


def is_catastrophic(state: ThermalPlantState) -> bool:
	"""Return True if any hard safety limit is breached."""
	return state.T > FAIL_T or state.Pr > FAIL_PR or state.S > FAIL_S


def compute_reward(state: ThermalPlantState, prev_u: float) -> float:
	"""Compute step reward from tracking, safety, smoothness, and stress."""
	reward = 0.0
	reward += 1.0 - abs(state.P - state.L)
	reward -= max(0.0, state.T - SOFT_T) * SAFETY_PENALTY_COEF
	reward -= max(0.0, state.Pr - SOFT_PR) * SAFETY_PENALTY_COEF
	reward -= abs(state.U - prev_u) * OSCILLATION_PENALTY_COEF
	reward -= state.S * STRESS_PENALTY_COEF
	return reward
