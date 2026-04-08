import pytest
import os
import io
import contextlib
from unittest.mock import patch, MagicMock
from utils.constants import DEFAULT_TASK_ID
from typing import Dict, List, Optional
import re

import inference

# A predictable sequence of LLM responses to test the robustness of the inference loop
MOCK_RESPONSES = [
    '{"U_target": 0.40, "F_target": 0.60}', # 1. Valid JSON
    '0.45 0.55',                            # 2. Valid Pair format
    '0.45, 0.55',                           # 3. Valid Pair format (comma)
    'Hello world',                          # 4. Invalid fallback
    '{"U_target": 1.5, "F_target": -0.5}',  # 5. Out of bounds (parser clamps)
]

def mock_get_model_response(
    client: MagicMock,
    step: int,
    observation: Dict[str, float],
    last_reward: float,
    history: List[str],
) -> str:
    # 0-indexed step from 1-indexed step argument
    idx = (step - 1) % len(MOCK_RESPONSES)
    return MOCK_RESPONSES[idx]

@pytest.fixture
def mock_inference_env(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "fake_token")
    monkeypatch.setenv("MODEL_NAME", "fake_model")
    monkeypatch.setenv("API_BASE_URL", "http://fake.api")
    monkeypatch.setenv("THERMAL_PLANT_EPISODE_ID", "1")
    monkeypatch.setattr(inference.C, "DEFAULT_MAX_STEPS", 5) # Short episode
    yield

def test_inference_main_prints_exact_stdout_format(mock_inference_env, monkeypatch):
    # Hijack the model call
    monkeypatch.setattr(inference, "get_model_response", mock_get_model_response)

    stdout_capture = io.StringIO()
    with contextlib.redirect_stdout(stdout_capture):
        inference.main()
        
    output = stdout_capture.getvalue()
    lines = output.strip().split("\n")
    
    # Needs at least START, END, and one STEP
    assert len(lines) >= 3
    
    assert lines[0].startswith("[START] task=")
    assert lines[-1].startswith("[END] success=")
    
    step_pattern = re.compile(
        r'^\[STEP\] step=\d+ action=\{"U_target":\d+\.\d{2},"F_target":\d+\.\d{2}\} '
        r'reward=-?\d+\.\d{2} done=(true|false) error=(null|.+)$'
    )
    
    step_count = 0
    for line in lines[1:-1]:
        # Filter debug lines if they slipped through to stdout (they shouldn't; inference prints to stderr for debug)
        if line.startswith("[STEP]"):
            assert step_pattern.match(line) is not None, f"Invalid STEP format: {line}"
            step_count += 1
            
            # Step 4 is 'Hello world', which triggers a parser fallback error
            if "step=4" in line:
                assert "error=parse" in line

    assert step_count == 5, f"Expected exactly 5 steps, got {step_count}"
