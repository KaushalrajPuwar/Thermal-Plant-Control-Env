"""Adversarial tests to ensure inference script robustly handles malformed LLM outputs."""

import pytest
import os
import sys
from unittest.mock import patch

import inference
from inference import BENCHMARK
from utils.constants import DEFAULT_TASK_ID

@pytest.fixture
def mock_env_vars():
    with patch.dict(os.environ, {
        "HF_TOKEN": "mock_token",
        "MODEL_NAME": "mock_model",
        "API_BASE_URL": "http://mock.endpoint"
    }):
        yield

def test_inference_main_with_malformed_outputs(capsys, monkeypatch, mock_env_vars):
    # Mock settings to create a short run
    import tasks.task2
    monkeypatch.setattr(tasks.task2.Task2, "max_steps", 4)
    monkeypatch.setattr(inference.C, "INCLUDE_PARSE_ERROR_IN_STEP", True)
    
    # We will simulate exactly 4 steps of LLM responses:
    # 1. Valid JSON.
    # 2. Messy text with anchored extraction.
    # 3. A pair value.
    # 4. Total gibberish fallback.
    mock_responses = [
        '{"U_target": 0.4, "F_target": 0.6}',
        'The answer is u_target=0.5, f_target=0.7 right here',
        '0.5, 0.8',
        'completely malformed nonsense'
    ]
    
    def fake_get_model_response(client, step, observation, last_reward, history):
        # step is 1-indexed
        return mock_responses[step - 1]
        
    monkeypatch.setattr(inference, "get_model_response", fake_get_model_response)
    
    # Run main
    inference.main()
    
    captured = capsys.readouterr()
    output_lines = [line.strip() for line in captured.out.splitlines() if line.strip()]
    
    # Assert Start
    assert output_lines[0].startswith("[START]")
    assert "task=" in output_lines[0]
    
    # Assert End
    assert output_lines[-1].startswith("[END]")
    assert "score=" in output_lines[-1]
    
    # Count steps
    step_lines = [line for line in output_lines if line.startswith("[STEP]")]
    assert len(step_lines) == 4
    
    # Step 1
    assert "action={\"U_target\":0.40,\"F_target\":0.60}" in step_lines[0]
    assert "error=null" in step_lines[0]
    
    # Step 2
    assert "action={\"U_target\":0.50,\"F_target\":0.70}" in step_lines[1]
    assert "parse:" in step_lines[1] # Because of the penalty and parser error log
    
    # Step 3
    assert "action={\"U_target\":0.50,\"F_target\":0.80}" in step_lines[2]
    assert "error=null" in step_lines[2]
    
    # Step 4
    assert "action={\"U_target\":0.50,\"F_target\":0.80}" in step_lines[3] # Previous valid action reused
    assert "parse:" in step_lines[3]
