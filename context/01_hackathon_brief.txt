THERMAL PLANT HACKATHON HANDOFF BRIEF
Version: 1
Status: Active context handoff for a coding agent

PURPOSE

This file is the first part of a multi-file handoff package for a coding agent. The goal is to transfer the current project state, constraints, hackathon requirements, and execution rules with enough precision that a new agent can continue without architectural drift.

This project is for a hackathon built around OpenEnv-style environments and LLM-driven baseline inference. The environment is the product; the model is only the agent used to test the environment. Do not optimize for model training. Optimize for environment robustness, evaluation compatibility, and judge-visible behavior.

CURRENT PROJECT DIRECTION

We are building a thermal plant control benchmark, not a physics simulator.

The benchmark should feel like a real control problem:
- dynamic load changes
- safety constraints
- delayed consequences
- gradual degradation
- meaningful trade-offs
- deterministic grading
- LLM-compatible operation

The system must remain small enough to finish in a hackathon, but rich enough to avoid “toy problem” criticism.

Do not pivot to a different domain unless the current plan becomes impossible to implement cleanly. The current chosen domain is thermal plant control.

WHAT THE HACKATHON IS ACTUALLY EVALUATING

The hackathon is not mainly evaluating a trained RL agent.

It is evaluating:
- whether the environment is valid and runnable
- whether the environment is OpenEnv-compliant
- whether Docker builds successfully
- whether the Hugging Face Space is live and reachable
- whether the baseline inference script runs and produces the required logs
- whether task graders return meaningful normalized scores
- whether an external standardized LLM agent can interact with the environment successfully
- whether the environment is stable, deterministic, and robust under unknown agent outputs

The environment must work with a non-learning LLM baseline. This is a requirement, not a side note.

IMPORTANT HACKATHON WORKFLOW

There are two separate execution paths:

1) Phase 1 / validation path
- The submission is checked for structural correctness.
- The validator pings the HF Space.
- Docker is built.
- openenv validate is run.
- inference.py is executed.
- The inference script must print exactly the required log format.
- The script must complete and produce a final normalized score.

2) Phase 2 / agentic evaluation path
- A standard LLM agent is run against the environment.
- The environment is not replaced; the judge agent interacts with the environment through the required API.
- The judge agent may output messy, partial, or malformed text.
- The environment and inference pipeline must be robust to this.
- They are not integrating into our codebase; they are calling our environment through the interface.

SUBMISSION INTERFACE REQUIREMENTS

The submission requires:
- inference.py at repository root
- OpenAI-client-based LLM calls using environment variables
- OpenEnv environment code with reset(), step(), and state()
- Docker support
- Hugging Face Space deployment
- task graders returning scores in [0,1]
- logs in a strict format

The official sample inference script and validator strongly imply these requirements:
- API_BASE_URL
- MODEL_NAME
- HF_TOKEN
- possibly LOCAL_IMAGE_NAME if using from_docker_image()
- OpenAI client is required for LLM calls
- stdout logging format must be exact
- one [START] line
- one [STEP] line per step
- one [END] line always, even on exception
- scores must be normalized to [0,1]

Do not alter the required logging structure unless a later file explicitly says otherwise.

INPUT / OUTPUT / MODEL OBSERVATIONS

The model backend is not fixed by us. For local development we may choose OpenRouter, Together, Hugging Face Inference Endpoints, or another OpenAI-compatible provider. For submission, the judges inject their own model endpoint and credentials through environment variables.

Important:
- use the OpenAI client interface
- do not hardcode a provider
- do not assume OpenAI’s own servers
- do not assume one specific model
- do not rely on model-specific behavior
- do not assume the model will produce valid JSON

The environment must accept unknown LLM behavior.

CRITICAL ROBUSTNESS REQUIREMENTS

The inference pipeline must not crash on malformed outputs.

The model may return:
- incomplete JSON
- free text
- extra commentary
- wrong numeric ranges
- missing fields
- partial structured output
- prompt-ignored answers

The system must handle that by:
- trying strict JSON parse first
- using anchored fallback extraction for required keys
- clamping numeric values to allowed ranges
- reusing the previous valid action on parse failure
- applying a large negative penalty for invalid output
- never throwing a hard exception because the model was messy

Never use bare except. Use except Exception only.

Never let a malformed LLM output terminate the evaluation run.

PROJECT GOAL: WHAT THE ENVIRONMENT SHOULD FEEL LIKE

The environment should feel like:
- a controlled, meaningful system
- a benchmark with progressive difficulty
- a sequence of state-action-reward transitions
- a safe but nontrivial operational task
- something a general LLM can interact with step by step

It should not feel like:
- a full engineering simulator
- a physics paper
- a toy grid world
- a trivial direct-mapping puzzle
- a brittle prompt demo

THERMAL PLANT DESIGN INTENT

We are intentionally not building a full-scale physical plant.

We are building a compact benchmark with:
- causal coupling
- delayed effects
- nonlinear behavior near failure
- degradation
- recoverable mistakes
- task progression
- visible improvement over steps

The environment must be legible to an LLM and also meaningful to a human judge.

DO NOT DRIFT TO THE FOLLOWING FAIL MODES

1. Do not add too many controls.
2. Do not add many hidden subsystems.
3. Do not make the action space too wide.
4. Do not add physics realism that cannot be debugged.
5. Do not make Task 3 or Task 4 impossible for a general LLM.
6. Do not remove delayed effects.
7. Do not remove degradation.
8. Do not remove determinism.
9. Do not remove grader normalization.
10. Do not let the code depend on a perfect agent.

CURRENT HIGH-LEVEL SHAPE OF THE BENCHMARK

The benchmark should have:
- one shared environment
- four tasks
- one causal state system
- bounded action space
- deterministic transitions
- an LLM-compatible inference pipeline
- one grader per task
- a README that explains the environment simply
- a Space that demonstrates the system clearly

The environment is the thing to optimize. The model is only the test agent.

WHAT THE AGENT SHOULD EXPERIENCE

The LLM agent should experience:
- a readable current state
- a small number of clear controls
- rewards that help it adjust within the episode
- penalties when it acts badly
- enough steps to show adaptation
- recovery opportunities for non-catastrophic mistakes
- a meaningful but not impossible challenge

We do not want the agent to “solve everything at once.” We want it to visibly improve behavior over the trajectory.

WHAT TO KEEP IN MIND WHILE CODING

- Keep outputs deterministic.
- Keep action parsing robust.
- Keep state transitions bounded.
- Keep the grading clear.
- Keep the environment simple enough to inspect.
- Keep the LLM prompt concise and unambiguous.
- Keep the repository structure stable.
- Keep the validation path as the first priority.
- Keep the evaluation path compatible with judge infrastructure.

NEXT FILES THAT SHOULD FOLLOW THIS ONE

The next files should cover:
- architecture and repo layout
- exact hackathon rules and evaluation assumptions
- modeling equations and task definitions
- inference.py and LLM parsing rules
- progress.md editing rules
- build/deployment instructions
- debugging and validation checklist

OPERATING PRINCIPLE

If a choice improves model-training purity but makes the environment harder for the judge LLM to run, do not choose it.

If a choice improves realism but reduces determinism or robustness, do not choose it.

If a choice adds complexity without improving score visibility, do not choose it.

The submission should be easy to run, easy to validate, and hard to break.
