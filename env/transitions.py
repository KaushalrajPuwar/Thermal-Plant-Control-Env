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
import math

from env.state import ThermalPlantState
import utils.constants as C
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
	
	# Compute gap, allowing it to vary around load for balanced control challenge
	# The gap can be positive or negative, creating both "reduce" and "increase" scenarios
	g_gap = regime["G_gap"]
	
	# Clamp stress slightly if excessive to prevent artificial P reduction
	if stress > 0.3:
		stress = clamp(stress * 0.85, S_BOUNDS[0], S_BOUNDS[1])
	
	power = clamp(load + g_gap - P_STRESS_DRAG * stress, P_BOUNDS[0], P_BOUNDS[1])
	
	# Ensure observable gap: |P - L| >= 0.04 so LLM sees clear control objective
	gap_magnitude = abs(power - load)
	if gap_magnitude < 0.04:
		# If gap too small, nudge power away from load in direction determined by seed
		direction = 1.0 if (g_gap >= 0) else -1.0
		power = clamp(load + direction * 0.08, P_BOUNDS[0], P_BOUNDS[1])
	
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



def integration_step(state: ThermalPlantState, action: Dict[str, float]) -> Tuple[ThermalPlantState, float, bool, dict]:
	# 1) Parse & clamp targets
	u_target, f_target = clamp_action_targets(action.get(C.ACTION_U_TARGET, state.U), action.get(C.ACTION_F_TARGET, state.F))
	
	# 2) Actuator Explicit update
	next_u = state.U + C.ACTUATOR_INERTIA_ALPHA * (u_target - state.U)
	next_f = state.F + C.ACTUATOR_INERTIA_ALPHA * (f_target - state.F)
	
	# Clamp actuators immediately
	next_u = clamp(next_u, C.U_BOUNDS[0], C.U_BOUNDS[1])
	next_f = clamp(next_f, C.F_BOUNDS[0], C.F_BOUNDS[1])
	
	delta_u = next_u - state.U
	
	# 3) RK2 Integration for P, T, Pr, S, D
	x = [state.P, state.T, state.Pr, state.S, state.D]
	
	def der(x_vec):
		P, T, Pr, S, D = x_vec
		
		# Power: target tracking for U, minus load drag, minus degradation drag
		dP = C.P_GAIN * (next_u - P) - C.P_LOAD_COEF * (P - state.L) - C.P_DEG_COEF * P * D
		
		# Temperature: dT/dt = a*P^1.1 - b*F^1.05 - c*(T - T_env) - e*D*T
		# T_env is 0.0 effectively
		dT = C.TEMP_POWER_COEF * (P ** C.TEMP_EXP_P if P > 0 else 0) \
			 - C.TEMP_COOL_COEF * (next_f ** C.TEMP_EXP_F if next_f > 0 else 0) \
			 - C.TEMP_ENV_COOL * T - C.TEMP_DEG_COEF * D * T
			 
		# Pressure: dPr/dt = p1*tanh(p2*(T - T_ref)) + p3*P^1.05 - p4*Pr
		dPr = C.PR_T_COEF * math.tanh(C.PR_T_COEF * (T - 0.5)) + C.PR_P_COEF * (P ** 1.05 if P > 0 else 0) - C.PR_DAMP * Pr
		
		# Stress: Accumulate from temperature baseline + control effort
		dS = C.STRESS_T_COEF * max(0.0, T - 0.4) + C.STRESS_U_OSC_COEF * (delta_u ** 2) - C.STRESS_DECAY * S
		
		# Degradation: dD/dt = depends linearly on Stress, natural recovery
		dD = C.DEG_FROM_S_COEF * S - C.DEG_RECOVERY_RATE * D
		
		return [dP, dT, dPr, dS, dD]
		
	if C.INTEGRATOR == "RK2":
		k1 = der(x)
		x_temp = [x[i] + C.DT * k1[i] for i in range(5)]
		k2 = der(x_temp)
		x_next = [x[i] + (C.DT / 2.0) * (k1[i] + k2[i]) for i in range(5)]
	else:
		# Fallback Euler
		k1 = der(x)
		x_next = [x[i] + C.DT * k1[i] for i in range(5)]
		
	# Populate next state
	next_state = ThermalPlantState(
		L=state.L,
		U=next_u,
		F=next_f,
		P=x_next[0],
		T=x_next[1],
		Pr=x_next[2],
		S=x_next[3],
		D=x_next[4]
	)
	
	# Clamp state immediately
	next_state = clamp_state(next_state)
	
	# Done logic and precedence
	catastrophic, error_msg = check_catastrophic(next_state)
	done = catastrophic
	info = {"error": error_msg if catastrophic else None, "invalid_action": False, "invalid_action_penalty": 0.0}
	
	reward = compute_reward(state, next_state, delta_u)
	
	return next_state, reward, done, info


def clamp_state(state: ThermalPlantState) -> ThermalPlantState:
	state.U = clamp(state.U, C.U_BOUNDS[0], C.U_BOUNDS[1])
	state.F = clamp(state.F, C.F_BOUNDS[0], C.F_BOUNDS[1])
	state.P = clamp(state.P, C.P_BOUNDS[0], C.P_BOUNDS[1])
	state.T = clamp(state.T, C.T_BOUNDS[0], C.T_BOUNDS[1])
	state.Pr = clamp(state.Pr, C.PR_BOUNDS[0], C.PR_BOUNDS[1])
	state.S = clamp(state.S, C.S_BOUNDS[0], C.S_BOUNDS[1])
	state.D = clamp(state.D, C.D_BOUNDS[0], C.D_BOUNDS[1])
	return state


def check_catastrophic(state: ThermalPlantState) -> Tuple[bool, str]:
	if state.T > C.FAIL_T + C.HYSTERESIS_MARGIN:
		return True, "Catastrophic failure: Temperature limit exceeded."
	if state.Pr > C.FAIL_PR + C.HYSTERESIS_MARGIN:
		return True, "Catastrophic failure: Pressure limit exceeded."
	if state.S > C.FAIL_S + C.HYSTERESIS_MARGIN:
		return True, "Catastrophic failure: Stress limit exceeded."
	return False, ""


def compute_reward(prev_state: ThermalPlantState, state: ThermalPlantState, delta_u: float) -> float:
	# Tracking reward: smooth linear decay as error increases
	# At error=0: r_track=1.0, at error=0.2: r_track=0.0, at error=0.4: r_track=-1.0
	# This avoids the cliff discontinuity and provides smooth gradient for learning
	tracking_error = abs(state.P - state.L)
	r_track = 1.0 - tracking_error / 0.2  # Linear decay over 0.2 error window
	
	# Safety penalty: only penalize when approaching limits
	safety_violation = max(0.0, state.T - C.SOFT_T) + max(0.0, state.Pr - C.SOFT_PR)
	r_safety = C.SAFETY_PENALTY_COEF * safety_violation
	
	# Stability penalty: penalize excessive control changes
	r_stability = C.OSCILLATION_PENALTY_COEF * (delta_u ** 2)
	
	# Stress penalty: penalize high stress accumulation
	r_stress = C.STRESS_PENALTY_COEF * state.S if state.S > 0.1 else 0.0
	
	# Combine: tracking reward + safety/stress penalty - control oscillation
	reward = C.W_TRACK * r_track - C.W_SAFETY * r_safety - C.W_STABILITY * r_stability - 0.2 * r_stress
	return clamp(reward, -10.0, 10.0)

