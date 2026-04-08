# Grader Implementation Details

The thermal plant environment evaluates external LLM agents using deterministic graders implemented in `graders/task*_grader.py`.

## Core Principles
- **Deterministic**: Graders rely only on mathematical computations over `trajectory.steps[].raw_state` (full precision) and not on rounded observations.
- **Normalization**: Computed metrics are mapped to a normalized range `[0,1]` using linear clamping. The default metric scale is `0.5`, defined in `utils/constants.py` under the dictionary `METRIC_NORM_SCALES`.
- **Score constraints**: All final scores are bounded algebraically and strictly clamped to `[0,1]` via `max(0.0, min(1.0, score))`.

## Shared Metrics (`graders/_metrics.py`)
All graders share deterministic extraction functions:
- **TE** (Tracking Error): `(1/N) * sum(|P - L|)`
- **OS** (Overshoot): `max(0, P - L)` over all steps
- **SV** (Safety Violations): `(1/N) * sum(max(0, T - 1.0) + max(0, Pr - 1.0))`
- **OC** (Oscillation): `(1/(N-1)) * sum(|U_t - U_{t-1}|)`
- **SL** (Stress Level): `(1/N) * sum(S)`
- **Failure Flag (FF)**: `1` if trajectory ended due to a catastrophic state violation of temperature, pressure, or stress, else `0`
- **Invalid Output Penalty**: Graders subtract `INVALID_ACTION_PENALTY` (default `0.2`) from the computed task score for *each step* where the LLM's payload was unparseable. 

## Special Operations
- Task 4 (Fault Recovery) computes **RT**, the Recovery Time. This defines the step index when the control tracks within bounds again (`|P - L| < 0.1` and `T < 1.0`). If recovery fails completely, it returns `N`. 
RT is normalized directly as `Clamp(RT / N)` instead of using the generic `0.5` scaling value.

## Debugging and Diagnostics
The `inference.py` runner includes an optional debug mode. Call inference with `DEBUG=1` to print un-rounded raw values, actual metric outputs, and penalty flags to `stderr`. 
```bash
DEBUG=1 python inference.py
```
This data is printed only to `stderr` and never `stdout`, protecting the `[START]/[STEP]/[END]` requirement established by the framework specification.
