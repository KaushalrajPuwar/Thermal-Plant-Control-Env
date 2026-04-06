from __future__ import annotations

from fastapi import FastAPI, HTTPException
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

# Initialize the FastAPI application
app = FastAPI(
    title="Thermal Plant Control Environment",
    description="An OpenEnv-compliant environment for a thermal plant control hackathon.",
    version="1.0.0",
)

# Create a singleton instance of our environment interface
env_interface = ConcreteOpenEnvInterface()


@app.post("/reset", response_model=ResetResponse)
def reset_endpoint(request: ResetRequest):
    """
    Resets the environment to a new initial state based on the provided
    task and episode ID. This is the starting point for any new episode.
    """
    try:
        observation = env_interface.reset(task_id=request.task_id, episode_id=request.episode_id)
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
