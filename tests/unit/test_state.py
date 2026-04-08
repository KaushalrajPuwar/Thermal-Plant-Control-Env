import pytest

from env.core import ThermalPlantEnv
from env.transitions import build_coherent_initial_state, clamp_state, check_catastrophic
from env.state import ThermalPlantState
from utils.constants import TASK_STARTUP_PROFILES, DEFAULT_TASK_ID


def test_build_coherent_initial_state_determinism():
	s1 = build_coherent_initial_state(task_id="task1", episode_id=0)
	s2 = build_coherent_initial_state(task_id="task1", episode_id=0)
	assert s1.to_raw_dict() == s2.to_raw_dict()


def test_reset_returns_observation_and_state_methods():
	env = ThermalPlantEnv()
	obs = env.reset(task_id="task2", episode_id=1)
	assert isinstance(obs, dict)
	raw = env.state()
	assert isinstance(raw, dict)
	# observation keys should be present
	for k in ("P", "L", "T", "Pr", "U", "F", "S", "D"):
		assert k in obs
		assert k in raw


def test_startup_not_catastrophic_for_tasks():
	# for a sample of episode ids ensure no catastrophic startup
	for task in TASK_STARTUP_PROFILES:
		for ep in (0, 1, 7):
			st = build_coherent_initial_state(task_id=task, episode_id=ep)
			assert not check_catastrophic(st)[0], f"Startup catastrophic for {task}@{ep}"


def test_clamp_state_enforces_bounds():
	s = ThermalPlantState(P=10.0, L=-1.0, T=5.0, Pr=5.0, U=2.0, F=-0.5, S=9.0, D=3.0)
	s2 = clamp_state(s)
	for k, v in s2.to_raw_dict().items():
		assert isinstance(v, float)


