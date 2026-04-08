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

DEV_RESET_HEADER = os.getenv("DEV_RESET_HEADER", "Episode-Override")

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
    dev_token = http_request.headers.get(DEV_RESET_HEADER.lower())
    if not dev_token:
        raise HTTPException(status_code=403, detail=f"Forbidden: Missing {DEV_RESET_HEADER} header for reset.")

    try:
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
        invalid_flag = False
        
        # Clamp inputs and check validity
        for k in ("U_target", "F_target"):
            val = action_dict[k]
            if val < 0.0 or val > 1.0:
                invalid_flag = True
                action_dict[k] = max(0.0, min(1.0, val))

        observation, reward, done, info = env_interface.step(action_dict)
        
        if invalid_flag:
            info["invalid_action"] = True
            
        raw_state = env_interface.get_state()
        return StepResponse(
            observation=observation,
            raw_state=raw_state,
            reward=reward,
            done=done,
            info=info
        )
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

def main():
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

