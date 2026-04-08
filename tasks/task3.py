"""Task 3: Preemptive Constraint Management.

L_t = moderately high constant (0.7).
Stress accumulates when T > 0.9. Agent must reduce risk BEFORE visible failure.
"""

from typing import Dict, Optional, Tuple, Any

from env.state import ThermalPlantState
from tasks.config import ThermalPlantTask, AgentPolicy
from utils.constants import L_BOUNDS, TASK_CODE

class RampPolicy(AgentPolicy):
    """Proportional tracker."""
    
    def get_action(self, observation: Dict[str, float]) -> Dict[str, float]:
        # Track power to load proportionally
        u_target = min(observation["U"] + 0.4 * (observation["L"] - observation["P"]), 1.0)
        u_target = max(u_target, 0.0)
        
        f_target = max(0.4, 0.8 * observation["T"])
        # Preemptively keep T < 0.9 by sharply increasing cooling when safely near the threshold
        if observation["T"] > 0.85:
            f_target = 0.95
            u_target = max(0.0, u_target - 0.2)
            
        return {"U_target": u_target, "F_target": f_target}


class Task3(ThermalPlantTask):
    task_id = "task3"
    name = "Preemptive Constraint Management"
    description = "Manage moderately high load (0.7) and prevent stress accumulation by keeping Temperature below 0.9 under restricted coolant conditions."
    max_steps = 12

    def reset(self, episode_id: int) -> None:
        self._seed = int(episode_id)

    def apply_disturbance(self, state: ThermalPlantState, step: int) -> Tuple[Dict[str, float], Optional[Dict[str, Any]]]:
        deltas: Dict[str, float] = {}
        event: Dict[str, Any] = {"type": "constraint_management"}

        target_L = 0.7
        if abs(state.L - target_L) > 1e-5:
            deltas["L"] = target_L - state.L

        # Exogenous heat: acts as a coolant deficiency.
        # Max cooling (F=1.0) is no longer strong enough to overcome both this and P=0.7.
        deltas["T"] = 0.045

        # Stress accumulates when T > 0.9
        if state.T > 0.9:
            deltas["S"] = 0.05 # Additive stress accumulation per step
            event["stress_warning"] = True

        return deltas, event

    def is_completed(self, state: ThermalPlantState, step_count: int) -> bool:
        # End task if stable and constraints are well managed.
        error = abs(state.P - 0.7)
        return error <= 0.02 and state.T < 0.85 and step_count >= 3

    def get_baseline_policy(self) -> AgentPolicy:
        return RampPolicy()
