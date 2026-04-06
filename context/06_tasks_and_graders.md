# TASKS & GRADERS SPECIFICATION
Version: 1

---

## PURPOSE

Defines:
- exact task behavior
- demand/load patterns
- task-specific mechanics
- grader formulas (deterministic, normalized)

This file is authoritative for scoring.

---

## GLOBAL CONVENTIONS

- Episode length: N steps (default 8–12)
- State variables from modeling_spec apply
- Rewards are step-level (unnormalized)
- Graders compute final score in [0,1]
- All graders must be deterministic
- Task selection logic passes `task_id` and `episode_id` into the env so startup state is reproducible and task-aware
- Graders use raw internal trajectory values, not rounded LLM-facing observations

---

## SHARED METRICS (computed over trajectory)

All symbols below refer to raw internal state values collected from the trajectory.

Let:
- P_t = power at step t
- L_t = load at step t
- T_t = temperature at step t
- Pr_t = pressure at step t
- S_t = stress at step t
- U_t = control input
- F_t = cooling input

Define:

1) Tracking Error (TE)
TE = (1/N) * Σ |P_t - L_t|

2) Overshoot (OS)
OS = max_t max(0, P_t - L_t)

3) Safety Violation (SV)
SV = (1/N) * Σ [ max(0, T_t - 1.0) + max(0, Pr_t - 1.0) ]

4) Oscillation (OC)
OC = (1/(N-1)) * Σ |U_t - U_{t-1}|

5) Stress Level (SL)
SL = (1/N) * Σ S_t

6) Failure Flag (FF)
FF = 1 if any termination due to T, Pr, or S breach else 0

---

## NORMALIZATION HELPERS

Clamp(x) = min(max(x, 0), 1)

Norm_TE = Clamp(TE / 0.5)
Norm_OS = Clamp(OS / 0.5)
Norm_SV = Clamp(SV / 0.5)
Norm_OC = Clamp(OC / 0.5)
Norm_SL = Clamp(SL / 0.5)

FailurePenalty = 1 if FF == 1 else 0

---

## TASK 1 — STABLE BASELINE OPERATION

### Load Pattern
L_t = constant (e.g., 0.6)

### Objective
Maintain P close to L while staying safe and smooth.

Startup expectation:
- starts in a stable, low-wear operating regime with readable but safe dynamics

### Grader

Score_T1 = 1
    - 0.5 * Norm_TE
    - 0.2 * Norm_SV
    - 0.2 * Norm_OC
    - 0.3 * FailurePenalty

Score_T1 = Clamp(Score_T1)

---

## TASK 2 — LOAD FOLLOWING

### Load Pattern
Step changes:
- t=1..3: L=0.5
- t=4..6: L=0.8
- t=7..N: L=0.6

### Objective
Track changing load with minimal lag and overshoot.

Startup expectation:
- starts in a lower-load, safe regime aligned with the early task phase, not in a stressed startup

### Additional Metric

Lag Penalty (LP):
LP = (1/N) * Σ max(0, |P_t - L_t| - 0.1)

Norm_LP = Clamp(LP / 0.5)

### Grader

Score_T2 = 1
    - 0.4 * Norm_TE
    - 0.2 * Norm_OS
    - 0.2 * Norm_LP
    - 0.2 * Norm_SV
    - 0.3 * FailurePenalty

Score_T2 = Clamp(Score_T2)

---

## TASK 3 — PREEMPTIVE CONSTRAINT MANAGEMENT

### Load Pattern
L_t = moderately high constant (e.g., 0.7)

### Special Mechanic
Stress accumulates when T > T_warning (0.9)

Agent must reduce risk BEFORE visible failure.

Startup expectation:
- starts mildly strained but recoverable so the LLM can see emerging risk before catastrophic failure

### Additional Metrics

Late Stress (LS):
LS = (1/N) * Σ max(0, S_t - 0.5)

Norm_LS = Clamp(LS / 0.5)

Early Mitigation Bonus (EMB):
Count steps where:
- S_t < 0.5 AND T_t < 1.0
EMB = count / N

### Grader

Score_T3 = 1
    - 0.3 * Norm_TE
    - 0.3 * Norm_LS
    - 0.2 * Norm_SV
    + 0.2 * EMB
    - 0.3 * FailurePenalty

Score_T3 = Clamp(Score_T3)

---

## TASK 4 — FAULT RECOVERY WITH DEGRADATION

### Load Pattern
- t=1..3: L=0.6
- t=4: disturbance → T spike (inject +0.3)
- t=5..N: L=0.6

### Special Mechanic
Degradation reduces cooling effectiveness over time.

Startup expectation:
- starts with visibly higher inherited degradation than other tasks while still remaining recoverable before the disturbance

### Additional Metrics

Recovery Time (RT):
First step where:
- |P_t - L_t| < 0.1 AND T_t < 1.0

If never recovered:
RT = N

Norm_RT = Clamp(RT / N)

Residual Risk (RR):
RR = (1/N) * Σ max(0, T_t - 1.0)

Norm_RR = Clamp(RR / 0.5)

### Grader

Score_T4 = 1
    - 0.3 * Norm_RT
    - 0.2 * Norm_RR
    - 0.2 * Norm_SV
    - 0.2 * Norm_OC
    - 0.3 * FailurePenalty

Score_T4 = Clamp(Score_T4)

---

## FINAL RULES

- All scores must be ∈ [0,1]
- All metrics deterministic
- Different policies must yield different scores
- Failure must significantly reduce score but not always zero it
- Do not compute grader metrics from rounded prompt/display values

---

## VALIDATION CHECK

Before submission ensure:

- Random policy scores low
- Heuristic policy scores medium
- LLM baseline produces non-zero, variable scores

---

END OF FILE
