import pytest
import io
import contextlib
import re

import inference
from env.core import ThermalPlantEnv
from utils.constants import TASK_CODE

@pytest.fixture
def mock_inference_env_tasks(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "fake_token")
    monkeypatch.setenv("MODEL_NAME", "fake_model")
    monkeypatch.setenv("API_BASE_URL", "http://fake.api")
    monkeypatch.setenv("THERMAL_PLANT_EPISODE_ID", "42")
    yield monkeypatch


@pytest.mark.parametrize("task_id", ["task1", "task2", "task3", "task4"])
def test_inference_runs_full_episode_for_each_task(mock_inference_env_tasks, task_id):
    mock_inference_env_tasks.setenv("THERMAL_PLANT_TASK", task_id)
    
    # We will hook inference so it just runs the task's baseline policy instead of calling a model
    env = ThermalPlantEnv(task_id=task_id, episode_id=42)
    policy = env._task.get_baseline_policy()

    def mock_get_model_response(client, task_description, step, observation, last_reward, history):
        action = policy.get_action(observation)
        # convert back to valid string
        return f"{action['U_target']:.2f} {action['F_target']:.2f}"
    
    mock_inference_env_tasks.setattr(inference, "get_model_response", mock_get_model_response)

    stdout_capture = io.StringIO()
    with contextlib.redirect_stdout(stdout_capture):
        inference.main()
        
    output = stdout_capture.getvalue()
    lines = output.strip().split("\n")
    
    assert lines[0].startswith(f"[START] task={task_id} env=thermal-plant-control")
    assert lines[-1].startswith("[END] success=")
    
    step_lines = [line for line in lines if line.startswith("[STEP]")]
    max_steps = env.max_steps
    assert len(step_lines) <= max_steps
