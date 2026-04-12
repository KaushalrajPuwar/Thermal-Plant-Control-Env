"""Deterministic evaluation of heuristic baseline policies.

This script runs the rule-based AgentPolicies defined in each task to 
establish a 'Control Floor' for the benchmark.
"""

import sys
import os
from typing import List

# Ensure we can import from the root
sys.path.append(os.getcwd())

from env.interface import ConcreteOpenEnvInterface
from tasks.registry import get_task
from graders.registry import grader_registry
from utils.schemas import EpisodeTrajectory, TrajectoryStep, TrajectorySummary

def run_baseline_eval():
    env = ConcreteOpenEnvInterface()
    task_ids = ["task1", "task2", "task3", "task4"]
    episode_id = 42  # Standard evaluation seed
    
    # Get the graders map
    graders = grader_registry()
    
    print(f"| Task | Success | Steps | Score | Description |")
    print(f"| :--- | :--- | :--- | :--- | :--- |")
    
    for task_id in task_ids:
        task = get_task(task_id)
        policy = task.get_baseline_policy()
        grader = graders.get(task_id)
        
        # Capture trajectory for the grader
        obs = env.reset(task_id=task_id, episode_id=episode_id)
        steps: List[TrajectoryStep] = []
        done = False
        step_count = 0
        
        while not done and step_count < task.max_steps:
            step_count += 1
            action_dict = policy.get_action(obs)
            
            # Use the internal step logic (mirroring inference.py but with policy)
            obs, reward, done, info = env.step(action_dict)
            raw_state = env.get_state()
            
            # Record for grading
            # (Note: Minimal mock of TrajectoryStep for the grader's consumed fields)
            t_step = TrajectoryStep(
                step=step_count,
                raw_llm_text="BASELINE_POLICY",
                parsed_action=None, # Not used by current graders
                canonical_action=action_dict,
                observation=obs,
                raw_state=raw_state,
                reward=reward,
                done=done,
                error=None,
                env_invalid_action=False,
                invalid_penalty_applied=0.0
            )
            steps.append(t_step)
            
            # obs is updated via the unpack above
            # done is updated via the unpack above
            
        # Grade the episode
        # The grader wants an EpisodeTrajectory
        trajectory = EpisodeTrajectory(
            task=task_id,
            benchmark="thermal-plant-control",
            model="Heuristic-Baseline",
            steps=steps
        )
        score = grader(trajectory)
        success = score >= 0.85 # Standard threshold
        
        success_str = "✅" if success else "❌"
        print(f"| {task_id} | {success_str} | {step_count} | {score:.2f} | {task.name} |")

if __name__ == "__main__":
    run_baseline_eval()
