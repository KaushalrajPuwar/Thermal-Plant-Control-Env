import pytest

from env.core import ThermalPlantEnv
from tasks.registry import get_task


@pytest.mark.parametrize("task_id", ["task1", "task2", "task3", "task4"])
def test_task_registry_has_tasks(task_id):
    task = get_task(task_id)
    assert task.task_id == task_id
    assert task.max_steps > 0
    assert task.get_baseline_policy() is not None


def test_task1_baseline():
    env = ThermalPlantEnv(task_id="task1", episode_id=42)
    obs = env.reset()
    assert env.max_steps == 12

    # Task1 applies NO disturbances except constant Load enforcement
    action = env._task.get_baseline_policy().get_action(obs)
    obs, reward, done, info = env.step(action)
    
    assert info.get("task_event") is not None
    assert info["task_event"]["type"] == "constant_load"


def test_task2_periodic_pulses():
    env = ThermalPlantEnv(task_id="task2", episode_id=42)
    obs = env.reset()
    assert env.max_steps == 12
    
    events_seen = 0
    for step in range(1, 13):
        action = env._task.get_baseline_policy().get_action(obs)
        obs, reward, done, info = env.step(action)
        if info.get("task_event"):
            assert info["task_event"]["type"] == "load_step"
            target = info["task_event"]["target_L"]
            if step <= 3:
                assert target == 0.5
            elif step <= 6:
                assert target == 0.8
            else:
                assert target == 0.6
                
        if done:
            break


def test_task3_ramp():
    env = ThermalPlantEnv(task_id="task3", episode_id=42)
    obs = env.reset()
    assert env.max_steps == 12
    
    events_seen = 0
    # Artificially spike T to test stress accumulation
    env._state.T = 0.95
    for _ in range(12):
        action = env._task.get_baseline_policy().get_action(obs)
        obs, reward, done, info = env.step(action)
        if info.get("task_event") is not None:
            events_seen += 1
            
        if done:
            break
            
    assert events_seen > 0, "No events occurred in task3"


def test_task4_thermal_shock():
    env = ThermalPlantEnv(task_id="task4", episode_id=42)
    obs = env.reset()
    assert env.max_steps == 12
    
    events_seen = 0
    for step in range(1, 13):
        action = env._task.get_baseline_policy().get_action(obs)
        obs, reward, done, info = env.step(action)
        if info.get("task_event") is not None:
            if info["task_event"].get("type") == "thermal_fault":
                events_seen += 1
                assert step == 4
            
        if done:
            break
            
    # Should see exactly 1 thermal shock at step 4
    assert events_seen == 1, f"Expected 1 thermal shock, got {events_seen}"
