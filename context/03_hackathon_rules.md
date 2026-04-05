# HACKATHON RULES, EVALUATION & CONSTRAINTS (DETAILED)
Version: 1

---

## PURPOSE

This file encodes the **true operational rules of the hackathon**, combining:
- official instructions
- inference script behavior
- validator behavior
- implicit constraints discovered during analysis

This is the **single source of truth for compliance**.

---

## CORE REALITY (MOST IMPORTANT)

> This hackathon is NOT about training an RL model.  
> It is about building an environment that can be evaluated by a fixed LLM agent.

---

## WHAT IS ACTUALLY SCORED

### Primary evaluation areas:

1. Environment quality
2. Task design
3. Grader correctness
4. System robustness
5. Reproducibility
6. OpenEnv compliance

---

## WHAT IS NOT SCORED (COMMON MISCONCEPTION)

- Training pipelines
- PPO / RL algorithms
- Model architecture (MLP vs Transformer)
- Convergence performance

---

## PHASE 1 — VALIDATION PIPELINE

Your submission MUST pass all of these:

### 1. HF SPACE CHECK

Validator sends:
POST /reset

Must return:
- HTTP 200

Failure → immediate rejection

---

### 2. DOCKER BUILD

Dockerfile must:
- build successfully
- within time limit (~600s)

Failure → rejection

---

### 3. OPENENV VALIDATION

Command:
openenv validate

Must:
- pass all checks
- detect tasks
- detect graders
- confirm API compliance

Failure → rejection

---

## PHASE 2 — INFERENCE EXECUTION

They run:

python inference.py

This must:

- run end-to-end
- not crash
- produce valid logs
- produce score

---

## REQUIRED STDOUT FORMAT (STRICT)

Must output EXACTLY:

[START]
[STEP]
[END]

NO deviations.

---

### FORMAT DETAILS

#### START
[START] task=<task_name> env=<benchmark> model=<model_name>

#### STEP
[STEP] step=<n> action=<action_str> reward=<float> done=<true|false> error=<msg|null>

#### END
[END] success=<true|false> steps=<n> score=<float> rewards=<r1,r2,...>

---

### RULES

- one START
- one END
- one STEP per step
- no extra prints
- no multiline logs
- booleans must be lowercase
- rewards formatted to 2 decimals

Violation → parsing failure → rejection

---

## LLM REQUIREMENT (CRITICAL)

You MUST:

- use OpenAI client
- use environment variables:
  - API_BASE_URL
  - MODEL_NAME
  - HF_TOKEN

---

## WHAT THIS IMPLIES

You are NOT:

- choosing a model permanently
- hardcoding provider
- controlling evaluation model

---

## WHAT JUDGES DO

They:

- inject their own model endpoint
- inject their own API key
- run your inference.py
- run their own LLM agent later

---

## CRITICAL CONSEQUENCE

Your environment MUST work with:

- unknown model
- unknown behavior
- unknown output format

---

## LLM OUTPUT IS UNTRUSTED INPUT

Assume:

- broken JSON
- extra text
- missing fields
- nonsense strings
- partial answers

---

## MANDATORY DEFENSE

You MUST implement:

- safe parsing
- fallback extraction
- clamping
- default actions
- penalty for invalid outputs

If env.step() crashes → FAIL

---

## STEP LIMITS

Example script uses:
MAX_STEPS = 8

Implication:

- tasks must show signal within 5–10 steps
- long horizon learning is invalid

---

## RUNTIME CONSTRAINTS

- total runtime < ~20 min
- per-step must be fast
- no heavy simulation loops
- no expensive computation

---

## DETERMINISM REQUIREMENT

They check:

- "baseline reproduces"
- "score variance"

Implication:

- same input → same score
- randomness must be controlled

---

## GRADER REQUIREMENTS

Each task must:

- return score ∈ [0,1]
- be deterministic
- vary across policies

If all policies score same → fail

---

## ENVIRONMENT API REQUIREMENT

Must support:

- reset()
- step(action)
- state()

---

## HF SPACE ROLE

HF Space is:

- environment host
- API endpoint provider

NOT:

- training environment
- model host (necessarily)

---

## COMMON FAILURE MODES (AVOID)

### 1. Crashing on bad LLM output
→ instant failure

---

### 2. Incorrect logging format
→ parser failure

---

### 3. Non-deterministic results
→ score rejection

---

### 4. No meaningful grader variation
→ low score

---

### 5. Over-complex environment
→ LLM cannot act → poor evaluation

---

### 6. Too simple environment
→ trivial → low score

---

## TRUE OPTIMIZATION TARGET

You are optimizing:

> "How well a generic LLM can interact with and be evaluated on this environment"

NOT:

> "How optimal a trained policy is"

---

## FINAL CHECKLIST

Before submission ensure:

- inference.py runs fully
- no crashes
- logs correct
- scores in [0,1]
- Docker builds
- HF Space responds
- parser robust
- tasks distinct
- environment deterministic

---

## FINAL RULE

If something improves RL purity but breaks LLM compatibility → DO NOT DO IT.

---

END OF FILE
