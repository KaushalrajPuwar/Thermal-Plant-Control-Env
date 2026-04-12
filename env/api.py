from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Request Models
# =============================================================================
class ResetRequest(BaseModel):
    """
    Schema for the /reset endpoint payload.
    
    This model allows for dynamic task switching and episode selection, which 
    facilitates the sequential evaluation of multiple behaviours within a 
    single environment process.
    """
    task_id: Optional[str] = Field("task1", description="The canonical ID of the control task (e.g., 'task1').")
    episode_id: Optional[int] = Field(None, description="Optional integer seed for deterministic state initialisation.")


class ActionRequest(BaseModel):
    """Defines the structure for a single action provided to the /step endpoint."""

    U_target: float = Field(..., description="Normalised target position [0, 1] for the power generation valve.")
    F_target: float = Field(..., description="Normalised target position [0, 1] for the coolant flow valve.")


class StepRequest(BaseModel):
    """Request body for the /step endpoint."""

    action: ActionRequest = Field(..., description="The action to be taken in the environment.")


# =============================================================================
# Response Models
# =============================================================================
class StepResponse(BaseModel):
    """
    Comprehensive response for transitions, mirroring the standard Gym/OpenEnv contract.
    
    Includes canonical observations for agent consumption along with high-fidelity 
    raw state data for autograding and diagnostics.
    """

    observation: Dict[str, float] = Field(..., description="The agent's observation of the environment.")
    raw_state: Optional[Dict[str, Any]] = Field(None, description="The full internal state of the environment.")
    reward: float = Field(..., description="The reward returned after the previous action.")
    done: bool = Field(..., description="Whether the episode has ended.")
    info: Dict[str, Any] = Field(..., description="Auxiliary diagnostic information.")


class StateResponse(BaseModel):
    """Response body for the /state endpoint."""

    state: Dict[str, Any] = Field(..., description="The full, unrounded internal state of the environment.")


class ResetResponse(BaseModel):
    """Response body for the /reset endpoint."""

    observation: Dict[str, float] = Field(..., description="The initial observation of the environment.")
