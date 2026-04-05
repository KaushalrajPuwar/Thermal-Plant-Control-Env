# ARCHITECTURE & REPOSITORY SPECIFICATION
Version: 1

---

## PURPOSE

Defines the **exact system architecture, repository layout, and component boundaries**.

This file is authoritative. Do NOT deviate without updating this file.

---

## CORE PRINCIPLE

> One environment. One system. Four tasks. One inference pipeline.

No forks. No parallel implementations.

---

## HIGH-LEVEL ARCHITECTURE

```
LLM (via OpenAI client)
        ↓
inference.py (agent loop + parsing)
        ↓
OpenEnv Interface
        ↓
Environment Core (state + transitions)
        ↓
Task Layer (configurations)
        ↓
Grader Layer (final scoring)
```

---

## COMPONENT BREAKDOWN

### 1. inference.py (MANDATORY ENTRYPOINT)

Responsibilities:

- Build prompt from state
- Call LLM via OpenAI-compatible client
- Parse output → action
- Call env.step()
- Log EXACT format:
  - [START]
  - [STEP]
  - [END]
- Handle ALL errors
- Never crash

---

### 2. Environment Core

Responsibilities:

- Hold full state
- Apply transitions
- Clamp values
- Return:
  - observation
  - reward
  - done
  - info

Must be:
- deterministic
- bounded
- debuggable

---

### 3. Task Layer

Responsibilities:

- Define:
  - load patterns
  - thresholds
  - coefficients
- Switch behavior per task

NO duplication of environment logic.

---

### 4. Grader Layer

Responsibilities:

- Take full trajectory
- Compute normalized score ∈ [0,1]
- Deterministic

---

### 5. Parser (CRITICAL COMPONENT)

Location: inside inference.py or utils/

Responsibilities:

- Attempt JSON parse
- Fallback to regex extraction
- Clamp values
- Fallback to previous action
- Apply penalty

Must NEVER throw.

---

## DATA FLOW

### Step cycle

1. state → prompt
2. prompt → LLM
3. LLM → raw text
4. parser → action
5. env.step(action)
6. reward + next state
7. log output

---

## HARD RULES

### DO NOT:

- Add new top-level folders arbitrarily
- Duplicate logic across tasks
- Embed logic in inference.py (except agent loop)
- Make environment depend on inference logic
- Add hidden global state

---

### ALWAYS:

- Keep environment pure
- Keep parsing isolated
- Keep grading separate
- Keep transitions explicit

---

## STATE DESIGN RULE

Each variable must satisfy:

- single responsibility
- clear cause-effect
- bounded range

---

## ACTION DESIGN RULE

- max 2 continuous controls
- optional 1 discrete
- always clamp [0,1]

---

## FAILURE HANDLING

Environment must:

- NEVER crash on invalid action
- apply penalty
- continue episode unless catastrophic

---

## DETERMINISM

- fixed seeds
- no random noise unless controlled
- identical inputs → identical outputs

---

## FINAL CHECK

If removing a component:
- does system still run end-to-end?
- does inference.py still work?
- does grading still produce meaningful score?

If NO → do not remove.

---

END OF FILE
