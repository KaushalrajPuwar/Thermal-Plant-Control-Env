from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Request Models
# =============================================================================
class ResetRequest(BaseModel):
    """Request body for the /reset endpoint.

    Note: `episode_id` is accepted in the body for compatibility, but the
    server will only honor it when a valid developer token is provided.
    External evaluators should POST only `task_id` and will be served a
    fixed external episode id.
    """

    task_id: str = Field(..., description="The ID of the task to run, e.g., 'task1'.")
    episode_id: Optional[int] = Field(None, description="Optional episode id; honored only for developer callers with X-DEV-TOKEN.")


class ActionRequest(BaseModel):
    """Defines the structure for a single action provided to the /step endpoint."""

    U_target: float = Field(..., ge=0.0, le=1.0, description="Control for power generation actuator.")
    F_target: float = Field(..., ge=0.0, le=1.0, description="Control for coolant flow actuator.")


class StepRequest(BaseModel):
    """Request body for the /step endpoint."""

    action: ActionRequest = Field(..., description="The action to be taken in the environment.")


# =============================================================================
# Response Models
# =============================================================================
class StepResponse(BaseModel):
    """Response body for the /step endpoint, mirroring gym.Env.step output."""

    observation: Dict[str, float] = Field(..., description="The agent's observation of the environment.")
    reward: float = Field(..., description="The reward returned after the previous action.")
    done: bool = Field(..., description="Whether the episode has ended.")
    info: Dict[str, Any] = Field(..., description="Auxiliary diagnostic information.")


class StateResponse(BaseModel):
    """Response body for the /state endpoint."""

    state: Dict[str, Any] = Field(..., description="The full, unrounded internal state of the environment.")


class ResetResponse(BaseModel):
    """Response body for the /reset endpoint."""

    observation: Dict[str, float] = Field(..., description="The initial observation of the environment.")
