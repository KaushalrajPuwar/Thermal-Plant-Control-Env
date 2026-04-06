"""Hackathon inference entrypoint with frozen parser and logging contracts."""

from __future__ import annotations

import os
import textwrap
from typing import Dict, List, Optional

from openai import OpenAI

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

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME")
API_BASE_URL = os.getenv("API_BASE_URL")
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
		return ""


def compute_normalized_score(rewards: List[float]) -> float:
	"""Convert collected step rewards into a normalized score in [0, 1]."""
	if not rewards:
		return 0.0
	positive_reward = sum(max(0.0, reward) for reward in rewards)
	return min(max(positive_reward / float(MAX_STEPS), 0.0), 1.0)


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
		if HF_TOKEN and MODEL_NAME and API_BASE_URL:
			client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

		for step in range(1, MAX_STEPS + 1):
			raw_response = ""
			if client is not None:
				raw_response = get_model_response(
					client=client,
					step=step,
					observation=observation,
					last_reward=last_reward,
					history=history,
				)

			parsed_action = parse_llm_action(
				raw_text=raw_response,
				previous_valid_action=last_valid_action,
				default_action=DEFAULT_ACTION,
			)
			canonical_action = parsed_action.to_action_dict()
			observation, env_reward, done, info = env.step(canonical_action)
			total_reward = env_reward + parsed_action.penalty_applied
			error = info.get("error")

			# Judge-facing stdout uses the canonical parsed/clamped action string.
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
			last_valid_action = canonical_action
			history.append(
				f"step={step} action={action_string} reward={total_reward:.2f} "
				f"source={parsed_action.source} invalid={str(parsed_action.invalid_output).lower()}"
			)

			if done:
				break
	except Exception as exc:
		loop_error = str(exc)
	finally:
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
