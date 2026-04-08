"""Hackathon inference entrypoint with frozen parser and logging contracts."""

from __future__ import annotations

import os
import textwrap
from typing import Dict, List, Optional
import sys

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

from env.interface import ConcreteOpenEnvInterface
from utils import constants as C
from utils.logging_utils import canonical_action_string, log_end, log_start, log_step
from utils.parser import parse_llm_action
from utils.schemas import EpisodeTrajectory, StepLogRecord, TrajectoryStep, TrajectorySummary

BENCHMARK = "thermal-plant-control"

TEMPERATURE = 0.2
MAX_TOKENS = 120
SUCCESS_SCORE_THRESHOLD = 0.10
DEFAULT_ACTION = {
    "U_target": C.PARSER_DEFAULT_U,
    "F_target": C.PARSER_DEFAULT_F,
}

# These will be injected by the judge's infrastructure
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME")
API_BASE_URL = os.getenv("API_BASE_URL")
TASK_NAME = os.getenv("THERMAL_PLANT_TASK", C.DEFAULT_TASK_ID)
EPISODE_ID = int(os.getenv("THERMAL_PLANT_EPISODE_ID", str(C.DEFAULT_EPISODE_ID)))
DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

SYSTEM_PROMPT = textwrap.dedent(
	"""
	You are controlling a thermal plant benchmark. 
	Return ONLY a compact numeric pair separated by a space representing your chosen `U_target` and `F_target` (e.g. "0.60 0.50").
	Both targets must be strictly in the range [0, 1]. Do not output JSON, explanations, or prose.
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
	except Exception as exc:
		if DEBUG:
			print(f"[DEBUG] model call exception: {exc}", file=sys.stderr, flush=True)
		return ""


def compute_normalized_score(rewards: List[float]) -> float:
	"""Convert collected step rewards into a normalized score in [0, 1]."""
	if not rewards:
		return 0.0
	positive_reward = sum(max(0.0, reward) for reward in rewards)
	return min(max(positive_reward / float(C.DEFAULT_MAX_STEPS), 0.0), 1.0)


def determine_termination_reason(loop_error: Optional[str], done: bool, steps_taken: int) -> str:
	"""Return a stable end-of-episode reason."""
	if loop_error:
		return "exception"
	if done:
		return "env_done"
	if steps_taken >= C.DEFAULT_MAX_STEPS:
		return "max_steps"
	return "stopped"


def main() -> None:
	"""Run a full deterministic inference episode and always emit end logs."""
	model_name_for_logs = MODEL_NAME or "unset"
	env = ConcreteOpenEnvInterface(max_steps=C.DEFAULT_MAX_STEPS)
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
		if DEBUG and client is None:
			print(
				f"[DEBUG] OpenAI client configured? HF_TOKEN={bool(HF_TOKEN)} MODEL_NAME={bool(MODEL_NAME)} API_BASE_URL={bool(API_BASE_URL)}",
				file=sys.stderr,
				flush=True,
			)

		for step in range(1, C.DEFAULT_MAX_STEPS + 1):
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

			if DEBUG:
				print(file=sys.stderr)
				print(
					f"[DEBUG] step={step} prompt_observation={_format_observation(observation)}",
					file=sys.stderr,
					flush=True,
				)
				print(
					f"[DEBUG] raw_llm_text={raw_response!r}",
					file=sys.stderr,
					flush=True,
				)
				print(
					f"[DEBUG] parsed_action=u={parsed_action.u_target:.2f}, f={parsed_action.f_target:.2f}, "
					f"source={parsed_action.source} invalid={str(parsed_action.invalid_output).lower()} "
					f"penalty={parsed_action.penalty_applied:.2f}",
					file=sys.stderr,
					flush=True,
				)
			observation, env_reward, done, info = env.step(canonical_action)
			total_reward = env_reward + parsed_action.penalty_applied
			error = info.get("error")

			if DEBUG:
				print(
					f"[DEBUG] step={step} post_observation={_format_observation(observation)} "
					f"raw_state={env.get_state()} env_reward={env_reward:.2f} total_reward={total_reward:.2f} done={done} info={info}",
					file=sys.stderr,
					flush=True,
				)
				print(file=sys.stderr)

			# Judge-facing stdout uses the canonical parsed/clamped action string.
			action_string = canonical_action_string(
				u_target=canonical_action["U_target"],
				f_target=canonical_action["F_target"],
			)
			
			step_error = error
			if parsed_action.invalid_output and C.INCLUDE_PARSE_ERROR_IN_STEP:
				parse_err_msg = parsed_action.parse_error or "invalid_llm_output"
				if step_error:
					step_error = f"parse:{parse_err_msg} | env:{step_error}"
				else:
					step_error = f"parse:{parse_err_msg}"

			log_step(
				StepLogRecord(
					step=step,
					action=action_string,
					reward=total_reward,
					done=done,
					error=step_error,
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
			# Only treat the canonical action as "last valid" when the parser
			# indicated the model output was valid. This prevents default/fallback
			# actions from becoming the previous_valid_action used by the parser
			# on subsequent steps.
			if not parsed_action.invalid_output:
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
