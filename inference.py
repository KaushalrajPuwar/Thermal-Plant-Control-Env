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
from tasks.registry import get_task
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
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.3-70B-Instruct")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
TASK_NAME = os.getenv("THERMAL_PLANT_TASK", C.DEFAULT_TASK_ID)
EPISODE_ID = int(os.getenv("THERMAL_PLANT_EPISODE_ID", str(C.DEFAULT_EPISODE_ID)))
DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")


SYSTEM_PROMPT = textwrap.dedent(
	"""
	You are controlling a thermal plant benchmark.
	Your objective is to track the required load (L) with your power output (P) while keeping temperature (T) and pressure (Pr) safely below 1.0 to avoid stress (S).
	
	State Variables (Inputs):
	P : Current Power output (track this to L)
	L : Required Load
	T : Temperature (keep safely below 1.0)
	Pr: Pressure (keep safely below 1.0)
	S : System Stress
	D : Plant Degradation
	U : Current Control Valve position (inertia-delayed power target)
	F : Current Cooling Valve position (inertia-delayed cooling target)

	Action Space (Your Outputs):
	- U_target: Desired power level [0, 1]. Drives the power valve U.
	- F_target: Desired cooling level [0, 1]. Drives the cooling valve F.

	Note that your target controls (U_target, F_target) are subject to physical lag. They slowly move the actual valves (U, F) towards your targets. Anticipate delayed responses and system inertia.
	
	Return ONLY a compact numeric pair separated by a space representing your chosen `U_target` and `F_target` (e.g. "0.60 0.50"). Do not output JSON, explanations, or prose.
	"""
).strip()


def _format_observation(observation: Dict[str, float]) -> str:
    """Render the rounded observation view for the model prompt."""
    return ", ".join(f"{key}={value:.2f}" for key, value in observation.items())


def build_user_prompt(
    task_description: str,
    step: int,
    observation: Dict[str, float],
    last_reward: float,
    history: List[str],
) -> str:
	"""Build the user prompt using only rounded observation values."""
	history_block = "\n".join(history[-4:]) if history else "None"
	return textwrap.dedent(
		f"""
		Task Objective: {task_description}

		Step: {step}
		Observation: {_format_observation(observation)}
		Last reward: {last_reward:.2f}
		Recent history:
		{history_block}
		"""
	).strip()


def get_model_response(
    client: OpenAI,
    task_description: str,
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
				{"role": "user", "content": build_user_prompt(task_description, step, observation, last_reward, history)},
			],
			temperature=TEMPERATURE,
			max_tokens=MAX_TOKENS,
		)
		return (completion.choices[0].message.content or "").strip()
	except Exception as exc:
		if DEBUG:
			print(f"[DEBUG] model call exception: {exc}", file=sys.stderr, flush=True)
		return ""


def compute_normalized_score(rewards: List[float], max_steps: int) -> float:
	"""Convert collected step rewards into a normalized score in [0, 1]."""
	if not rewards:
		return 0.0
	positive_reward = sum(max(0.0, reward) for reward in rewards)
	return min(max(positive_reward / float(max_steps), 0.0), 1.0)


def determine_termination_reason(loop_error: Optional[str], done: bool, steps_taken: int, max_steps: int) -> str:
	"""Return a stable end-of-episode reason."""
	if loop_error:
		return "exception"
	if done:
		return "env_done"
	if steps_taken >= max_steps:
		return "max_steps"
	return "stopped"


def main() -> None:
	"""Run a full deterministic inference episode and always emit end logs."""
	model_name_for_logs = MODEL_NAME or "unset"
	env = ConcreteOpenEnvInterface()
	client: Optional[OpenAI] = None
	last_valid_action: Optional[Dict[str, float]] = None
	observation = env.reset(task_id=TASK_NAME, episode_id=EPISODE_ID)
	max_steps = getattr(env._env, "max_steps", 12) if hasattr(env, "_env") else 12
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
		task_obj = get_task(TASK_NAME)
		task_description = getattr(task_obj, "description", "Optimal Thermal Plant Control")
	except Exception:
		task_description = "Optimal Thermal Plant Control"

	try:
		if HF_TOKEN and MODEL_NAME and API_BASE_URL:
			client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
		if DEBUG and client is None:
			print(
				f"[DEBUG] OpenAI client configured? HF_TOKEN={bool(HF_TOKEN)} MODEL_NAME={bool(MODEL_NAME)} API_BASE_URL={bool(API_BASE_URL)}",
				file=sys.stderr,
				flush=True,
			)

		for step in range(1, max_steps + 1):
			raw_response = ""
			if client is not None:
				raw_response = get_model_response(
					client=client,
					task_description=task_description,
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
		score = compute_normalized_score(rewards, max_steps)
		# If grader registry is available, prefer grader-computed score (deterministic, uses raw internals)
		try:
			from graders.registry import grader_registry
			registry = grader_registry()
			grader_fn = registry.get(TASK_NAME)
			if grader_fn is not None:
				# grader functions return float score in [0,1]
				try:
					gscore = float(grader_fn(trajectory))
					# clamp defensively
					score = max(0.0, min(1.0, gscore))
					if DEBUG:
						from graders._metrics import compute_TE, compute_OS, compute_SV, compute_OC, compute_SL, compute_LP, compute_LS, compute_EMB, compute_RT, compute_RR, compute_failure_flag, compute_invalid_count
						print(
							f"[DEBUG] Grader Metrics: TE={compute_TE(trajectory):.3f} OS={compute_OS(trajectory):.3f} "
							f"SV={compute_SV(trajectory):.3f} OC={compute_OC(trajectory):.3f} SL={compute_SL(trajectory):.3f} "
							f"FF={compute_failure_flag(trajectory)} Invalids={compute_invalid_count(trajectory)}",
							file=sys.stderr, flush=True
						)
				except Exception as e:
					# Ignore grader errors and fall back to reward-based score
					if DEBUG:
						print(f"[DEBUG] Grader exception: {e}", file=sys.stderr, flush=True)
		except Exception:
			# missing registry or other import error -> keep reward-based score
			pass
		success = score >= SUCCESS_SCORE_THRESHOLD
		termination_reason = determine_termination_reason(loop_error=loop_error, done=done, steps_taken=steps_taken, max_steps=max_steps)
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
	if HF_TOKEN is None:
		raise ValueError("HF_TOKEN environment variable is required")
	main()
