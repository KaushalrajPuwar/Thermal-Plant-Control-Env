from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

from env.core import ThermalPlantEnv


class OpenEnvInterface(ABC):
    """
    Abstract base class defining the contract for an OpenEnv-compliant interface.
    This ensures that the API layer can interact with any environment that
    adheres to this standard structure.
    """

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Returns the full, unrounded internal state of the environment."""
        raise NotImplementedError

    @abstractmethod
    def reset(self, task_id: str, episode_id: int) -> Dict[str, float]:
        """Resets the environment to a new initial state for a given task and episode."""
        raise NotImplementedError

    @abstractmethod
    def step(self, action: Dict[str, float]) -> Tuple[Dict[str, float], float, bool, Dict[str, Any]]:
        """
        Executes one time step in the environment.

        Args:
            action: A dictionary containing the agent's action.

        Returns:
            A tuple containing:
            - observation (Dict[str, float]): The agent's observation of the current environment state.
            - reward (float): The amount of reward returned after the previous action.
            - done (bool): Whether the episode has ended.
            - info (Dict[str, Any]): Contains auxiliary diagnostic information.
        """
        raise NotImplementedError


class ConcreteOpenEnvInterface(OpenEnvInterface):
    """
    Concrete implementation of the OpenEnvInterface.

    This class holds a singleton instance of the core environment and maps the
    interface methods to the actual environment's methods, acting as a
    decoupling layer between the API and the environment logic.
    """

    _instance: "ConcreteOpenEnvInterface" | None = None
    _env: ThermalPlantEnv | None = None

    def __new__(cls) -> "ConcreteOpenEnvInterface":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._env = ThermalPlantEnv()
        return cls._instance

    def get_state(self) -> Dict[str, Any]:
        """Returns the full, unrounded internal state from the core environment."""
        if self._env is None:
            raise RuntimeError("Environment not initialized.")
        return self._env.state()

    def reset(self, task_id: str, episode_id: int) -> Dict[str, float]:
        """Resets the core environment and returns the initial observation."""
        if self._env is None:
            raise RuntimeError("Environment not initialized.")
        return self._env.reset(task_id=task_id, episode_id=episode_id)

    def step(self, action: Dict[str, float]) -> Tuple[Dict[str, float], float, bool, Dict[str, Any]]:
        """Performs a step in the core environment."""
        if self._env is None:
            raise RuntimeError("Environment not initialized.")
        return self._env.step(action)
