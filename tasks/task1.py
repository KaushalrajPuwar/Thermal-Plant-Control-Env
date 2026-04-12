"""Task 1: Stable Baseline Operation.

Maintain P close to L while staying safe and smooth. Constant load pattern L_t = 0.6.
"""

from typing import Dict, Optional, Tuple, Any

from env.state import ThermalPlantState
from tasks.config import ThermalPlantTask, AgentPolicy
from utils.constants import U_BOUNDS, F_BOUNDS, P_BOUNDS, L_BOUNDS, T_BOUNDS, PR_BOUNDS

class BaselinePolicy(AgentPolicy):
    """A simple rule-based tracker."""
    
    def get_action(self, observation: Dict[str, float]) -> Dict[str, float]:
        # Track power to load
        u_target = observation["L"]
        if observation["P"] < observation["L"] - 0.05:
            u_target = min(0.9, observation["U"] + 0.1)
        elif observation["P"] > observation["L"] + 0.05:
            u_target = max(0.1, observation["U"] - 0.1)
            
        # Heavy cooling if temp/pressure gets hot
        f_target = 0.4
        if observation["T"] > 0.85 or observation["Pr"] > 0.85:
            f_target = 0.8
            u_target = max(0.1, u_target - 0.2)
            
        return {"U_target": u_target, "F_target": f_target}


class Task1(ThermalPlantTask):
    task_id = "task1"
    name = "Stable Baseline Operation"
    description = "Maintain power close to the given constant load requirement while staying safe and smooth."
    max_steps = 12

    def reset(self, episode_id: int) -> None:
        self._seed = episode_id
        self._target_L = None

    def apply_disturbance(self, state: ThermalPlantState, step: int) -> Tuple[Dict[str, float], Optional[Dict[str, Any]]]:
        deltas = {}
        # L_t is constant for the episode, set by the initial coherent state
        if getattr(self, "_target_L", None) is None:
            self._target_L = state.L
            
        target_L = self._target_L
        if abs(state.L - target_L) > 1e-5:
            deltas["L"] = target_L - state.L
        return deltas, {"type": "constant_load", "target_L": target_L}

    def is_completed(self, state: ThermalPlantState, step_count: int) -> bool:
        # User requested early stop when P=L.
        tracking_error = abs(state.P - state.L)
        # End task immediately if error is very small (converged to load target)
        return tracking_error <= 0.02 and step_count >= 3

    def get_baseline_policy(self) -> AgentPolicy:
        return BaselinePolicy()
