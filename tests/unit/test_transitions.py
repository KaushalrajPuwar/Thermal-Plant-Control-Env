from env.transitions import (
	update_actuators,
	update_power,
	update_temperature,
	update_degradation,
	compute_cooling_coeff,
)
from utils.constants import (
	U_INERTIA_TARGET,
	U_INERTIA_PREV,
	F_INERTIA_PREV,
	F_INERTIA_TARGET,
	DEGRADATION_RATE,
	K_COOL_BASE,
)


def test_actuator_inertia():
	prev_u = 0.0
	prev_f = 0.0
	u_target = 1.0
	f_target = 1.0
	u, f = update_actuators(prev_u, prev_f, u_target, f_target)
	assert abs(u - U_INERTIA_TARGET) < 1e-6
	assert abs(f - (F_INERTIA_PREV * prev_f + F_INERTIA_TARGET * f_target)) < 1e-6


def test_power_response():
	prev_p = 0.2
	u = 0.7
	p = update_power(prev_p, u)
	assert isinstance(p, float)


def test_degradation_increases_with_violations():
	prev_d = 0.1
	prev_u = 0.2
	u_target = 0.8
	new_d = update_degradation(prev_d, u_target, prev_u)
	assert new_d >= prev_d


def test_cooling_coeff_behavior():
	prev_t = 0.2
	degradation = 0.1
	k = compute_cooling_coeff(prev_t, degradation)
	assert k <= K_COOL_BASE
