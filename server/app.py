from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from env.api import (
    ActionRequest,
    ResetResponse,
    StateResponse,
    StepRequest,
    StepResponse,
)
from env.interface import ConcreteOpenEnvInterface
from tasks.registry import normalize_task_id
from utils.constants import DEFAULT_EXTERNAL_EPISODE_ID

# Initialize the FastAPI application
app = FastAPI(
    title="Thermal Plant Control Environment",
    description="An OpenEnv-compliant environment for a thermal plant control hackathon.",
    version="1.0.0",
)

# Create a singleton instance of our environment interface
env_interface = ConcreteOpenEnvInterface()


@app.post("/reset", response_model=ResetResponse)
async def reset_endpoint(http_request: Request):
    """
    Resets the environment. Accepts optional task_id/episode_id in body,
    defaults to task1 with the standard episode if not provided.
    """
    try:
        try:
            body = await http_request.json()
        except Exception:
            body = {}

        task_id = normalize_task_id(body.get("task_id", "task1") or "task1")
        episode_id = body.get("episode_id", None)
        if episode_id is None:
            episode_id = DEFAULT_EXTERNAL_EPISODE_ID
        else:
            episode_id = int(episode_id)

        observation = env_interface.reset(task_id=task_id, episode_id=episode_id)
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

        # Round reward to 2 decimals for judge-facing output
        reward = round(float(reward), 2)
            
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


@app.get("/health")
def health():
    """Health check endpoint declared in openenv.yaml."""
    return {"status": "healthy"}


@app.get("/")
def root():
    """Root endpoint to confirm the API is running."""
    return JSONResponse(content={"message": "Thermal Plant Control API is running."})

def main():
    import uvicorn

    port = int(os.getenv("PORT", os.getenv("API_PORT", "7860")))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()

