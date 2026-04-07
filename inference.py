"""Hackathon inference entrypoint with frozen parser and logging contracts."""

from __future__ import annotations

import os
import textwrap
from typing import Dict, List, Optional

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

from env.interface import ConcreteOpenEnvInterface
from utils.constants import DEFAULT_TASK_ID
from utils.logging_utils import canonical_action_string, log_end, log_start, log_step
from utils.parser import DEFAULT_F_TARGET, DEFAULT_U_TARGET, parse_llm_action
from utils.schemas import EpisodeTrajectory, StepLogRecord, TrajectoryStep, TrajectorySummary

BENCHMARK = "thermal-plant-control"
MAX_STEPS = 8
TEMPERATURE = 0.1
MAX_TOKENS = 120
SUCCESS_SCORE_THRESHOLD = 0.10
DEFAULT_ACTION = {
    "U_target": DEFAULT_U_TARGET,
    "F_target": DEFAULT_F_TARGET,
}

# These will be injected by the judge's infrastructure
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME")
API_BASE_URL = os.getenv("API_BASE_URL")

# These are for local execution and can be configured
TASK_NAME = os.getenv("THERMAL_PLANT_TASK", DEFAULT_TASK_ID)
EPISODE_ID = int(os.getenv("THERMAL_PLANT_EPISODE_ID", "0"))

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are controlling a thermal plant benchmark.
    Return ONLY compact JSON with exactly these keys:
    {"U_target": 0.50, "F_target": 0.50}
    Do not include markdown, explanation, prose, or extra keys.
    Both values must be numeric targets in the range [0, 1].
    """
).strip()


def _format_observation(observation: Dict[str, float]) -> str:
    """Render the rounded observation view for the model prompt."""
    return ", ".join(f"{key}={value:.2f}" for key, value in observation.items())


def build_user_prompt(
    step: int,
    observation: Dict[str, float],
    last_reward: float,
    history: List[str],
) -> str:
    """Build the user prompt using only rounded observation values."""
    history_block = "\n".join(history[-4:]) if history else "None"
    return textwrap.dedent(
        f"""
        Step: {step}
        Observation: {_format_observation(observation)}
        Last reward: {last_reward:.2f}
        Recent history:
        {history_block}
        Return ONLY JSON for the next action.
        """
    ).strip()


def get_model_response(
    client: OpenAI,
    step: int,
    observation: Dict[str, float],
    last_reward: float,
    history: List[str],
) -> str:
    """Request the next action from the configured model."""
    # In Phase 1, we can return a mock response.
    # The real implementation will be done in Phase 2.
    # return '{"U_target": 0.5, "F_target": 0.5}'
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(step, observation, last_reward, history)},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return (completion.choices[0].message.content or "").strip()
    except Exception:
        # On any exception, return an empty string to trigger parser fallbacks.
        return ""


def compute_normalized_score(rewards: List[float]) -> float:
    """Convert collected step rewards into a normalized score in [0, 1]."""
    # This is a placeholder; the real grader logic will be more complex.
    if not rewards:
        return 0.0
    # Example: score is the fraction of non-negative reward steps.
    positive_reward_steps = sum(1 for r in rewards if r >= 0)
    return float(positive_reward_steps) / float(MAX_STEPS)


def determine_termination_reason(loop_error: Optional[str], done: bool, steps_taken: int) -> str:
    """Return a stable end-of-episode reason."""
    if loop_error:
        return "exception"
    if done:
        return "env_done"
    if steps_taken >= MAX_STEPS:
        return "max_steps"
    return "stopped"


def main() -> None:
    """Run a full deterministic inference episode and always emit end logs."""
    model_name_for_logs = MODEL_NAME or "unset"
    env = ConcreteOpenEnvInterface(max_steps=MAX_STEPS)
    client: Optional[OpenAI] = None
    last_valid_action: Optional[Dict[str, float]] = None
    observation = env.reset(task_id=TASK_NAME, episode_id=EPISODE_ID)
    history: List[str] = []
    rewards: List[float] = []
    score = 0.0
    success = False
    steps_taken = 0
    done = False
    last_reward = 0.0
    loop_error: Optional[str] = None
    trajectory = EpisodeTrajectory(task=TASK_NAME, benchmark=BENCHMARK, model=model_name_for_logs)

    log_start(task=TASK_NAME, env=BENCHMARK, model=model_name_for_logs)

    try:
        # Initialize the OpenAI client only if all credentials are provided
        if HF_TOKEN and MODEL_NAME and API_BASE_URL:
            client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

        for step in range(1, MAX_STEPS + 1):
            raw_response = ""
            if client is not None:
                # In Phase 1, this will likely use a mock or fail gracefully.
                # In Phase 2, this makes a real API call.
                raw_response = get_model_response(
                    client=client,
                    step=step,
                    observation=observation,
                    last_reward=last_reward,
                    history=history,
                )
            else:
                # If no client, use a mock action to test the loop structure
                raw_response = '{"U_target": 0.51, "F_target": 0.49}'

            parsed_action = parse_llm_action(
                raw_text=raw_response,
                previous_valid_action=last_valid_action,
                default_action=DEFAULT_ACTION,
            )
            canonical_action = parsed_action.to_action_dict()

            # The environment step is called with the parsed action.
            # In Phase 1, the env has skeleton logic.
            observation, env_reward, done, info = env.step(canonical_action)
            total_reward = env_reward + parsed_action.penalty_applied
            error = info.get("error")

            action_string = canonical_action_string(
                u_target=canonical_action["U_target"],
                f_target=canonical_action["F_target"],
            )
            log_step(
                StepLogRecord(
                    step=step,
                    action=action_string,
                    reward=total_reward,
                    done=done,
                    error=error,
                )
            )

            trajectory.steps.append(
                TrajectoryStep(
                    step=step,
                    raw_llm_text=raw_response,
                    parsed_action=parsed_action,
                    canonical_action=canonical_action,
                    observation=dict(observation),
                    raw_state=env.get_state(),
                    reward=total_reward,
                    done=done,
                    error=error,
                    env_invalid_action=bool(info.get("invalid_action", False)),
                    invalid_penalty_applied=parsed_action.penalty_applied,
                )
            )

            rewards.append(total_reward)
            steps_taken = step
            last_reward = total_reward
            if not parsed_action.invalid_output:
                last_valid_action = canonical_action

            history.append(
                f"step={step} action={action_string} reward={total_reward:.2f} "
                f"source={parsed_action.source} invalid={str(parsed_action.invalid_output).lower()}"
            )

            if done:
                break
    except Exception as exc:
        # Catch any exception during the loop to ensure logs are always written.
        loop_error = str(exc)
    finally:
        # The finally block ensures that the end log is always emitted.
        score = compute_normalized_score(rewards)
        success = score >= SUCCESS_SCORE_THRESHOLD
        termination_reason = determine_termination_reason(loop_error=loop_error, done=done, steps_taken=steps_taken)
        trajectory.summary = TrajectorySummary(
            task=TASK_NAME,
            benchmark=BENCHMARK,
            model=model_name_for_logs,
            total_steps=steps_taken,
            rewards=list(rewards),
            success=success,
            final_score=score,
            termination_reason=termination_reason,
        )
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    main()
