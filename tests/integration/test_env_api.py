from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.app import app

# Create a TestClient instance based on your FastAPI app
client = TestClient(app)


def test_root_endpoint():
    """Tests if the root endpoint is available and returns a success message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Thermal Plant Control API is running."}


def test_reset_endpoint_scaffold():
    """
    Tests the basic availability and request/response structure of the /reset endpoint.
    This is a placeholder and does not validate deep environment logic.
    """
    request_body = {"task_id": "task1", "episode_id": 0}
    response = client.post("/reset", json=request_body, headers={"Episode-Override": "test-env"})
    assert response.status_code == 200
    response_data = response.json()
    assert "observation" in response_data
    # As per the current state.py, the observation will be empty until implemented
    # by Teammate A. This test just confirms the key exists.
    assert isinstance(response_data["observation"], dict)

def test_reset_missing_header():
    request_body = {"task_id": "task1", "episode_id": 0}
    response = client.post("/reset", json=request_body)
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden: Missing Episode-Override header for reset."


def test_step_endpoint_scaffold():
    """
    Tests the basic availability and request/response structure of the /step endpoint.
    This is a placeholder for now.
    """
    # First, reset the environment to ensure it's in a valid state to take a step
    client.post("/reset", json={"task_id": "task1", "episode_id": 0}, headers={"Episode-Override": "test-env"})

    # Now, test the step endpoint
    request_body = {"action": {"U_target": 0.5, "F_target": 0.5}}
    response = client.post("/step", json=request_body)
    assert response.status_code == 200
    response_data = response.json()
    assert "observation" in response_data
    assert "reward" in response_data
    assert "done" in response_data
    assert "info" in response_data
    assert "raw_state" in response_data

def test_step_clamping_and_invalid_action():
    client.post("/reset", json={"task_id": "task1", "episode_id": 0}, headers={"Episode-Override": "test-env"})

    request_body = {"action": {"U_target": 1.5, "F_target": -0.5}}
    response = client.post("/step", json=request_body)
    assert response.status_code == 200
    response_data = response.json()
    assert "info" in response_data
    assert response_data["info"].get("invalid_action") is True



def test_state_endpoint_scaffold():
    """
    Tests the basic availability and request/response structure of the /state endpoint.
    """
    # Reset first to initialize a state
    client.post("/reset", json={"task_id": "task1", "episode_id": 0})

    response = client.get("/state")
    assert response.status_code == 200
    response_data = response.json()
    assert "state" in response_data
    assert isinstance(response_data["state"], dict)
