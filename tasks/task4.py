"""Task 4: Fault Recovery with Degradation.

L=0.6 mostly. Disturbance at t=4: T spike (+0.3).
Degradation reduces cooling effectiveness over time.
"""

from typing import Dict, Optional, Tuple, Any

from env.state import ThermalPlantState
from tasks.config import ThermalPlantTask, AgentPolicy
from utils.constants import T_BOUNDS, PR_BOUNDS, TASK_CODE

class ShockPolicy(AgentPolicy):
    """Heavy cooling strategy."""
    
    def get_action(self, observation: Dict[str, float]) -> Dict[str, float]:
        # Track power to load cautiously
        u_target = min(observation["U"] + 0.2 * (observation["L"] - observation["P"]), 0.8)
        
        # Heavy cooling
        f_target = 0.6
        if observation["T"] > 0.8 or observation["Pr"] > 0.8:
            f_target = 1.0
            u_target = 0.0 # Emergency shutdown
            
        return {"U_target": max(0.0, u_target), "F_target": f_target}


class Task4(ThermalPlantTask):
    task_id = "task4"
    name = "Fault Recovery with Degradation"
    description = "Recover from a major thermal spike at step 4 while managing ongoing system degradation."
    max_steps = 12

    def reset(self, episode_id: int) -> None:
        self._seed = int(episode_id)

    def apply_disturbance(self, state: ThermalPlantState, step: int) -> Tuple[Dict[str, float], Optional[Dict[str, Any]]]:
        deltas = {}
        event = {"type": "constant_load"}

        target_L = 0.6
        if abs(state.L - target_L) > 1e-5:
            deltas["L"] = target_L - state.L

        if step == 4:
            deltas["T"] = 0.5
            event = {"type": "thermal_fault", "T_delta": deltas["T"]}
            
        # Ongoing degradation to simulate reduced cooling effectiveness
        deltas["D"] = 0.02

        return deltas, event

    def is_completed(self, state: ThermalPlantState, step_count: int) -> bool:
        # Task 4 has a major fault at step 4.
        # Don't end early before the fault has been processed and stabilized.
        if step_count < 6:
            return False
        return abs(state.P - 0.6) <= 0.02 and state.T < 0.8 and state.Pr < 0.8

    def get_baseline_policy(self) -> AgentPolicy:
        return ShockPolicy()
