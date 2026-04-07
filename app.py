from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
import os
from fastapi.responses import JSONResponse

from env.api import (
    ActionRequest,
    ResetRequest,
    ResetResponse,
    StateResponse,
    StepRequest,
    StepResponse,
)
from env.interface import ConcreteOpenEnvInterface
from utils.constants import DEFAULT_EXTERNAL_EPISODE_ID, DEV_RESET_TOKEN_ENV, DEFAULT_EPISODE_ID

# Initialize the FastAPI application
app = FastAPI(
    title="Thermal Plant Control Environment",
    description="An OpenEnv-compliant environment for a thermal plant control hackathon.",
    version="1.0.0",
)

# Create a singleton instance of our environment interface
env_interface = ConcreteOpenEnvInterface()


@app.post("/reset", response_model=ResetResponse)
def reset_endpoint(body: ResetRequest, http_request: Request):
    """
    Resets the environment to a new initial state based on the provided
    task and episode ID. This is the starting point for any new episode.
    """
    try:
        # Inspect developer token header (case-insensitive)
        dev_token = http_request.headers.get("x-dev-token") or http_request.headers.get("X-DEV-TOKEN")
        env_token = os.getenv(DEV_RESET_TOKEN_ENV)

        if dev_token and env_token and dev_token == env_token:
            # Developer-authorized request: honor provided episode_id if present
            # If developer didn't provide an episode id, fall back to the
            # canonical developer default from `utils.constants`.
            episode_id = body.episode_id if body.episode_id is not None else DEFAULT_EPISODE_ID
        else:
            # Public evaluator: always use the fixed external episode id
            episode_id = DEFAULT_EXTERNAL_EPISODE_ID

        observation = env_interface.reset(task_id=body.task_id, episode_id=episode_id)
        return ResetResponse(observation=observation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset environment: {e}")


@app.post("/step", response_model=StepResponse)
def step_endpoint(request: StepRequest):
    """
    Executes one time step within the environment using the provided action.
    """
    try:
        action_dict = request.action.model_dump()
        observation, reward, done, info = env_interface.step(action_dict)
        return StepResponse(observation=observation, reward=reward, done=done, info=info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute step: {e}")


@app.get("/state", response_model=StateResponse)
def state_endpoint():
    """
    Retrieves the complete, unrounded internal state of the environment.
    This is useful for debugging and grading.
    """
    try:
        state = env_interface.get_state()
        return StateResponse(state=state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get state: {e}")


@app.get("/")
def root():
    """Root endpoint to confirm the API is running."""
    return JSONResponse(content={"message": "Thermal Plant Control API is running."})
