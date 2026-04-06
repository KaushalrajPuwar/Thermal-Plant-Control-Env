# VALIDATION & TESTING SPECIFICATION
Version: 1

---

## PURPOSE

Defines:
- how to test the system before submission
- what failure cases to simulate
- how to ensure robustness against LLM behavior
- how to verify grading correctness

This file is CRITICAL to avoid silent failures during judging.

---

## CORE PRINCIPLE

> If you do not test failure cases, they WILL happen in evaluation.

---

## TESTING TIERS

### Tier 1 — Unit Tests (Local)

Test individual components:

- state updates
- transition equations
- clamping behavior
- failure conditions
- grader outputs
- raw-state vs rounded-observation separation
- deterministic startup generation keyed by task_id and episode_id

---

### Tier 2 — Integration Tests

Test:

- inference loop
- parser + env interaction
- full episode run

---

### Tier 3 — Adversarial Tests (MOST IMPORTANT)

Simulate bad LLM outputs.

---

## REQUIRED TEST CASES

### 1. Valid Output

Input:
{"U_target": 0.6, "F_target": 0.3}

Expected:
- parsed correctly
- normal step execution

---

### 2. Missing JSON braces

Input:
"U_target": 0.6, "F_target": 0.3

Expected:
- fallback parser works
- no crash

---

### 3. Extra text

Input:
"I think best is {"U_target":0.7,"F_target":0.2}"

Expected:
- extraction works
- correct values used

---

### 4. Completely invalid text

Input:
"hello world"

Expected:
- fallback action used
- penalty applied
- no crash

---

### 5. Out-of-range values

Input:
{"U_target": 5, "F_target": -2}

Expected:
- values clamped to [0,1]

---

### 6. Partial output

Input:
{"U_target": 0.5}

Expected:
- missing F handled
- fallback or default used

---

### 7. Empty output

Input:
""

Expected:
- fallback action
- penalty
- no crash

---

## ENVIRONMENT TESTS

### 1. Stability

- run 20+ episodes
- ensure no NaN or explosion
- ensure startup states are non-catastrophic across episode_id sweeps

---

### 2. Monotonic behavior

Verify:

- increasing U increases P
- increasing P increases T
- increasing F reduces T

Also verify:
- meaningful actions change at least one rounded observation value within 1–2 steps

---

### 3. Failure triggers

Force:

- T > threshold
- Pr > threshold

Ensure:
- episode ends correctly

---

## GRADER TESTS

### Must verify:

- score ∈ [0,1]
- deterministic output
- different trajectories → different scores
- grader uses raw internal values, not rounded display observations

---

### Test cases:

- random policy → low score
- heuristic → medium score
- stable control → higher score

---

## INFERENCE TESTS

### Must verify:

- logs match EXACT format
- no extra prints
- [START], [STEP], [END] present

---

### Run:

python inference.py

Check:
- no exceptions
- proper termination

---

## DETERMINISM TEST

Run same setup twice:

Expected:
- identical scores
- identical logs (except timestamps if any)
- identical startup state for the same `(task_id, episode_id)`
- different startup state when `episode_id` changes within the same task

---

## VISIBILITY TEST

For each task:

- apply a meaningful control change
- verify rounded observation changes are visible within 1–2 steps for primary variables `P`, `T`, and `Pr`
- verify `S` and `D` are not permanently flat under conditions where they should be accumulating

---

## ROUNDING SAFETY TEST

Compare:
- raw internal trajectory
- rounded observation trajectory

Ensure:
- internal values retain full precision
- rounded observations remain readable
- rounded observations do not hide causal impact for multiple consecutive steps under meaningful actions

---

## DOCKER TEST

Run:

docker build .

Then run container:

Expected:
- inference works
- no missing dependencies

---

## HF SPACE TEST

After deployment:

Test:

POST /reset

Expected:
- HTTP 200

---

## FULL PIPELINE TEST

Simulate judge flow:

1. run inference.py
2. verify logs
3. verify score
4. verify no crash

---

## FAILURE CRITERIA

Submission FAILS if:

- any crash occurs
- logs malformed
- parser fails
- score missing
- nondeterministic outputs

---

## DEBUGGING STRATEGY

If failure occurs:

1. isolate parser
2. isolate environment
3. test with fixed actions
4. reduce complexity
5. re-run minimal case

---

## FINAL CHECKLIST

Before submission ensure:

- parser handles ALL bad inputs
- environment never crashes
- inference always completes
- grader always returns valid score
- logs exactly match spec

---

## FINAL RULE

If you did not explicitly test a failure case → assume it will fail in judging.

---

END OF FILE
