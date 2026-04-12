"""Task 2: Load Following.

This 'Intermediate' tier task evaluates the agent's agility in responding 
to external load transients. The system undergoes two significant step 
changes (to 0.8 and then to 0.6), testing the ability to minimise overshoot 
and settling time.
"""

from typing import Dict, Optional, Tuple, Any

from env.state import ThermalPlantState
from tasks.config import ThermalPlantTask, AgentPolicy
from utils.constants import L_BOUNDS, D_BOUNDS, TASK_CODE

class PeriodicPolicy(AgentPolicy):
    """Tracker with low-bandwidth sampling and inadequate cooling."""
    
    def __init__(self):
        self._step = 0
        self._last_u = 0.5
        self._last_f = 0.5

    def get_action(self, observation: Dict[str, float]) -> Dict[str, float]:
        """
        Baseline policy for Load Following.
        
        Simulates a discrete, low-frequency controller typical of 
        legacy industrial PLC systems with 0.5Hz update internal cycles.
        """
        self._step += 1
        if self._step % 2 == 1:
            # Steady-state tracking with aggressive proportional gain
            u_target = min(max(observation["U"] + 2.5 * (observation["L"] - observation["P"]), 0.1), 0.9)
            f_target = 0.5
            if observation["T"] > 0.8:
                # High-damping cooling constraint to prevent actuator wear
                f_target = 0.25 
                u_target -= 0.05
            self._last_u = u_target
            self._last_f = f_target
            
        return {"U_target": max(0.0, self._last_u), "F_target": self._last_f}


class Task2(ThermalPlantTask):
    task_id = "task2"
    name = "Load Following"
    description = "Track step changes in required load (0.5 -> 0.8 -> 0.6) with minimal lag and overshoot."
    max_steps = 12

    def reset(self, episode_id: int) -> None:
        self._seed = episode_id

    def apply_disturbance(self, state: ThermalPlantState, step: int) -> Tuple[Dict[str, float], Optional[Dict[str, Any]]]:
        deltas = {}
        
        if step <= 3:
            target_L = 0.5
        elif step <= 6:
            target_L = 0.8
        else:
            target_L = 0.6
            
        if abs(state.L - target_L) > 1e-5:
            deltas["L"] = target_L - state.L
            
        event = {"type": "load_step", "target_L": target_L}
        return deltas, event

    def is_completed(self, state: ThermalPlantState, step_count: int) -> bool:
        # Task 2 has a final load step change at step 7.
        # So we only allow early completion after the final change has stabilized.
        if step_count < 8:
            return False
        return abs(state.P - 0.6) <= 0.02

    def get_baseline_policy(self) -> AgentPolicy:
        return PeriodicPolicy()
