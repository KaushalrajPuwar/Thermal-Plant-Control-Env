"""Configuration and base classes for the Thermal Plant Task hierarchy.

This module defines the abstract contract for disturbance injection and 
baseline policy provision, ensuring a consistent interface for the benchmarker.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Any

from env.state import ThermalPlantState


class AgentPolicy(ABC):
    """A deterministic baseline controller for sanity checks and grading."""
    
    @abstractmethod
    def get_action(self, observation: Dict[str, float]) -> Dict[str, float]:
        """Return a deterministic control action based on the state observation."""
        pass


class ThermalPlantTask(ABC):
    """Base class for tasks governing the episodes in the standard benchmark.
    
    Tasks control deterministic disturbances over time and provide metadata
    for graders and OpenEnv integration.
    """

    task_id: str
    name: str
    description: str
    max_steps: int

    @abstractmethod
    def reset(self, episode_id: int) -> None:
        """Reset the task-internal state using the episode ID as a deterministic seed."""
        pass

    @abstractmethod
    def apply_disturbance(self, state: ThermalPlantState, step: int) -> Tuple[Dict[str, float], Optional[Dict[str, Any]]]:
        """Compute relative disturbances for the current step.
        
        Args:
            state: The fully specified current actual state (un-rounded).
            step: The current 1-indexed environment step.
            
        Returns:
            deltas: A dictionary mapping state keys (e.g., 'L', 'D', 'T') to absolute Delta values
                    to add to the current state fields. Amplitudes should be derived relative
                    to the variable domain bounds implicitly.
            event: An optional dictionary describing the event that just occurred for info logging.
        """
        pass

    def is_completed(self, state: ThermalPlantState, step_count: int) -> bool:
        """Check if the task has successfully reached a terminal stabilizing state."""
        return False

    @abstractmethod
    def get_baseline_policy(self) -> AgentPolicy:
        """Return a simple heuristic or rule-based agent capable of surviving the task."""
        pass
