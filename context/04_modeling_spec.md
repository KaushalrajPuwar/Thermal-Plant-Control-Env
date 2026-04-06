# MODELING SPECIFICATION (THERMAL PLANT ENVIRONMENT)
Version: 1

---

## PURPOSE

This file defines the **exact modeling logic** for the environment:
- state variables
- transition equations (discrete-time)
- action effects
- constraints
- stability rules

This is the **most critical technical file**. Do not implement environment logic without following this.

---

## DESIGN GOAL

We are NOT building real physics.

We ARE building:
- a stable dynamical system
- with delayed effects
- with causal relationships
- that is interpretable by an LLM
- and produces meaningful behavior

---

## TIME MODEL

- Discrete timestep system
- dt = 1 per step
- Episode length ≈ 8–20 steps

---

## PRECISION POLICY

- Internal simulation state uses full floating-point precision
- Do NOT round values during transitions, reward computation, or grading
- LLM-facing observations should be rounded to 2 decimals
- The raw state and the rounded observation are different views of the same plant

---

## STARTUP STATE POLICY

- Episode startup must be deterministic per `(task_id, episode_id)`
- Do NOT sample each state variable independently
- Build the initial state from a coupled regime map so `P, L, T, Pr, U, F, S, D` are coherent together
- Task routing belongs outside the env core; the task layer or inference layer passes `task_id`
- Startup must be safe and recoverable for the intended task, not arbitrarily random or fixed

---

## STATE VARIABLES

All values MUST be bounded.

### Core variables

P = Power output (0 → 1)
L = Target load (0 → 1)
T = Temperature (0 → 1.5)
Pr = Pressure (0 → 1.5)
U = Control input (0 → 1)
F = Cooling input (0 → 1)
S = Stress (0 → 1.5)
D = Degradation (0 → 1)

---
 
## ACTION SPACE

Action = { U_target, F_target }

Both:
- float in [0,1]
- MUST be clamped

---

## TRANSITION EQUATIONS

### 1. Actuator inertia (smooth movement)

U(t) = 0.8 * U(t-1) + 0.2 * U_target  
F(t) = 0.8 * F(t-1) + 0.2 * F_target  

---

### 2. Power dynamics

P(t) = 0.85 * P(t-1) + 0.15 * U(t)

Interpretation:
- power follows control input with lag

---

### 3. Temperature dynamics

Cooling efficiency decreases at high temperature:

k_cool = 0.5 * (1 - min(1, T(t-1)))

T(t) = T(t-1) + 0.4 * P(t) - k_cool * F(t)

---

### 4. Pressure dynamics

Pr(t) = 0.7 * Pr(t-1) + 0.3 * (T(t) + 0.5 * P(t))

---

### 5. Stress accumulation (Task 3 critical)

T_warning = 0.9

S(t) = S(t-1) + max(0, T(t) - T_warning) * 0.2

---

### 6. Degradation (Task 4)

D(t) = D(t-1) + 0.06 * abs(U_target - U(t-1))

Cooling effectiveness reduced:

k_cool_final = k_cool * (1 - D(t))

---

## CLAMPING RULES

After each update:

- clamp P, U, F to [0,1]
- clamp T, Pr, S to [0,1.5]
- clamp D to [0,1]

---

## FAILURE CONDITIONS

Episode terminates if:

- T > 1.3
- Pr > 1.3
- S > 1.3

---

## REWARD SIGNAL (STEP LEVEL)

reward = 0

### Tracking
reward += 1 - abs(P - L)

### Safety penalty
reward -= max(0, T - 1.0) * 2
reward -= max(0, Pr - 1.0) * 2

### Oscillation penalty
reward -= abs(U(t) - U(t-1)) * 0.2

### Stress penalty
reward -= S(t) * 0.3

---

## IMPORTANT PROPERTIES

### 1. Delayed effects
- stress accumulates slowly
- temperature responds gradually
- delayed effects must still become visible to a 2-decimal observation view within a short horizon

---

### 2. Nonlinearity
- cooling weakens at high T

---

### 3. Trade-offs
- higher power → higher temp/stress
- more cooling → safer but inefficient

---

### 4. Recoverability
- small mistakes are recoverable
- large violations terminate

---

### 5. Observation visibility
- meaningful actions should change at least one displayed state variable within 1–2 steps
- primary feedback variables should usually move by about 0.01–0.05 per step on the rounded observation view

---

## DESIGN CONSTRAINTS

DO NOT:

- add more than 9 variables
- create circular dependencies
- create unbounded growth
- add randomness (unless controlled)

---

## DEBUGGING CHECKLIST

After implementation verify:

- increasing U increases P
- increasing P increases T
- increasing F decreases T
- high T increases S
- high D reduces cooling effectiveness
- rounded observations still show visible state change within 1–2 steps for meaningful actions
- same `(task_id, episode_id, action sequence)` gives the same trajectory

---

## FINAL RULE

If system becomes unstable or unintuitive:
→ simplify coefficients, NOT structure

---

END OF FILE
