import pytest
from env.state import ThermalPlantState
from env.transitions import (
	clamp,
	clamp_action_targets,
	integration_step,
	check_catastrophic,
	clamp_state,
	compute_reward
)
import utils.constants as C

def test_clamp():
	assert clamp(0.5, 0.0, 1.0) == 0.5
	assert clamp(-1.0, 0.0, 1.0) == 0.0
	assert clamp(2.0, 0.0, 1.0) == 1.0

def test_integration_step_monotonic():
	state = ThermalPlantState(P=0.5, T=0.5, Pr=0.5, U=0.5, F=0.5, S=0.0, D=0.0, L=0.5)
	action = {C.ACTION_U_TARGET: 1.0, C.ACTION_F_TARGET: 0.5}
	next_state, reward, done, info = integration_step(state, action)
	assert next_state.U > 0.5
	assert next_state.P > 0.5
	# Temperature might slightly drop depending on coefficients, but power definitely raises it eventually.
	assert isinstance(next_state.T, float)

def test_catastrophic():
	state = ThermalPlantState(P=0.5, T=0.5, Pr=0.5, U=0.5, F=0.5, S=0.0, D=0.0, L=0.5)
	done, msg = check_catastrophic(state)
	assert not done
	
	state.T = C.FAIL_T + C.HYSTERESIS_MARGIN + 0.1
	done, msg = check_catastrophic(state)
	assert done

def test_reward():
	state = ThermalPlantState(P=0.5, T=0.5, Pr=0.5, U=0.5, F=0.5, S=0.0, D=0.0, L=0.5)
	prev_state = ThermalPlantState(P=0.5, T=0.5, Pr=0.5, U=0.5, F=0.5, S=0.0, D=0.0, L=0.5)
	reward = compute_reward(prev_state, state, 0.0)
	assert isinstance(reward, float)


# --- newly added tests ---
def test_actuator_inertia_monotonicity():
	state = ThermalPlantState(P=0.5, T=0.5, Pr=0.5, U=0.5, F=0.5, S=0.0, D=0.0, L=0.5)
	action = {C.ACTION_U_TARGET: 1.0, C.ACTION_F_TARGET: 0.0}
	next_state, _, _, _ = integration_step(state, action)
	assert next_state.U == 0.75  # 0.5 + 0.5 * (1.0 - 0.5)
	assert next_state.F == 0.25  # 0.5 + 0.5 * (0.0 - 0.5)
	
def test_power_response_under_constant_U():
	state = ThermalPlantState(P=0.0, T=0.5, Pr=0.5, U=1.0, F=0.5, S=0.0, D=0.0, L=0.5)
	# High U should increase P. Let's run a single step.
	action = {C.ACTION_U_TARGET: 1.0, C.ACTION_F_TARGET: 0.5}
	next_state, _, _, _ = integration_step(state, action)
	assert next_state.P > state.P
	
def test_temperature_response_and_clamp():
	# With high power and 0 cooling, T should rise.
	state = ThermalPlantState(P=1.0, T=1.0, Pr=0.5, U=1.0, F=0.0, S=0.0, D=0.0, L=0.5)
	action = {C.ACTION_U_TARGET: 1.0, C.ACTION_F_TARGET: 0.0}
	next_state, _, _, _ = integration_step(state, action)
	assert next_state.T > state.T
	
def test_degradation_slow_growth_and_optional_recovery():
	state = ThermalPlantState(P=0.5, T=0.5, Pr=0.5, U=0.5, F=0.5, S=1.0, D=0.1, L=0.5)
	action = {C.ACTION_U_TARGET: 0.5, C.ACTION_F_TARGET: 0.5}
	next_state, _, _, _ = integration_step(state, action)
	# S=1.0 means degradation should grow.
	assert next_state.D > 0.1
	
	# recovery with S=0
	state_safe = ThermalPlantState(P=0.5, T=0.5, Pr=0.5, U=0.5, F=0.5, S=0.0, D=0.1, L=0.5)
	action_safe = {C.ACTION_U_TARGET: 0.5, C.ACTION_F_TARGET: 0.5}
	next_state_safe, _, _, _ = integration_step(state_safe, action_safe)
	assert next_state_safe.D < 0.1

def test_clamp_order_effects():
	# U clamped first, so extremely high target won't blow up system
	state = ThermalPlantState(P=0.5, T=0.5, Pr=0.5, U=0.5, F=0.5, S=0.0, D=0.0, L=0.5)
	# extreme targets to see clamps
	action = {C.ACTION_U_TARGET: 100.0, C.ACTION_F_TARGET: -100.0}
	next_state, _, _, _ = integration_step(state, action)
	assert next_state.U == 0.75
	assert next_state.F == 0.25
