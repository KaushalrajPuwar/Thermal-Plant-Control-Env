# DESIGN CONSTRAINTS & PITFALLS
Version: 1

---

## PURPOSE

This file encodes:
- all known conceptual traps
- mistakes other teams will make
- mistakes we almost made
- rules to prevent architecture drift

This is a guardrail file. Follow it strictly.

---

## CORE PRINCIPLE

> Most failures will NOT be due to code bugs.  
> They will be due to WRONG DESIGN DECISIONS.

---

## SECTION 1 — RL vs LLM CONFUSION

### WRONG THINKING

- “Agent will learn over episodes”
- “Reward will update policy”
- “We should optimize convergence”

### REALITY

- LLM does NOT learn
- No weight updates
- No policy improvement

---

### CORRECT MODEL

- adaptation happens within ONE episode
- via prompt + reward feedback
- not via training

---

## RULE

Design for:
→ short-term adaptation

NOT:
→ long-term learning

---

## SECTION 2 — TOO MANY CONTROLS

### WRONG

Adding:
- pressure valves
- fuel mix
- turbine speed
- etc.

---

### WHY THIS FAILS

- LLM cannot coordinate many dimensions
- action space becomes noisy
- evaluation signal weakens

---

### CORRECT

Use:
- 2 continuous controls
- optional 1 discrete

Let environment create complexity.

---

## SECTION 3 — TOO MUCH REALISM

### WRONG

- accurate thermodynamics
- detailed physical modeling

---

### WHY THIS FAILS

- hard to debug
- unstable
- not needed for scoring

---

### CORRECT

Use:
- simplified but causal system
- stable equations
- clear relationships

---

## SECTION 4 — TOO SIMPLE (TOY PROBLEM)

### WRONG

- direct mapping state → action
- no delay
- no trade-off

---

### WHY THIS FAILS

- LLM solves instantly
- no differentiation in scores

---

### CORRECT

Include:
- delayed effects
- trade-offs
- accumulation (stress)

---

## SECTION 5 — EARLY TERMINATION

### WRONG

Terminate on small mistake.

---

### WHY THIS FAILS

- LLM cannot recover
- no adaptation possible
- all scores collapse

---

### CORRECT

- allow recovery
- terminate only on catastrophic failure

---

## SECTION 6 — BAD PARSER DESIGN

### WRONG

- loose regex
- assuming valid JSON
- crashing on parse

---

### WHY THIS FAILS

- LLM output is messy
- validation will break

---

### CORRECT

- strict parse → fallback → clamp → default

---

## SECTION 7 — OVERCOMPLEX REWARD

### WRONG

- too many terms
- conflicting objectives

---

### WHY THIS FAILS

- LLM cannot optimize multi-objective well

---

### CORRECT

- few interpretable components
- clear penalties and rewards

---

## SECTION 8 — NON-DETERMINISM

### WRONG

- randomness in environment
- random seeds not fixed

---

### WHY THIS FAILS

- reproducibility checks fail

---

### CORRECT

- deterministic transitions
- fixed seeds

---

## SECTION 8.5 — BAD PRECISION POLICY

### WRONG

- exposing raw float repr values to the LLM
- rounding internal state every step
- using rounded display values for grading

---

### WHY THIS FAILS

- noisy prompts make the state harder to read
- repeated rounding can flatten gradual dynamics
- grader sensitivity drops if it uses display values instead of raw internals

---

### CORRECT

- keep internal simulation full precision
- expose rounded observations to the LLM
- keep graders on raw internal values

---

## SECTION 8.6 — INVISIBLE DYNAMICS

### WRONG

- state changes smaller than display resolution for many consecutive steps
- delayed effects that never become visible during the episode

---

### WHY THIS FAILS

- LLM cannot observe causality
- actions look disconnected from consequences
- benchmark becomes unfair or uninformative

---

### CORRECT

- meaningful actions change at least one displayed state variable within 1–2 steps
- stress and degradation remain gradual but become visible within the episode horizon

---

## SECTION 9 — INFRA NEGLECT

### WRONG

- focusing only on env logic
- ignoring Docker / HF Space

---

### WHY THIS FAILS

- submission rejected before evaluation

---

### CORRECT

- test full pipeline early
- treat infra as first-class

---

## SECTION 10 — IGNORING JUDGE AGENT

### WRONG

- tuning for your own model

---

### WHY THIS FAILS

- judges use different LLM

---

### CORRECT

- assume unknown agent
- design robust interface

---

## SECTION 11 — ARCHITECTURE DRIFT

### WRONG

- changing structure mid-way
- adding ad-hoc components

---

### WHY THIS FAILS

- breaks consistency
- increases bugs

---

### CORRECT

- follow architecture.txt strictly
- update spec BEFORE code changes

---

## SECTION 12 — OVERFITTING TO EDGE CASES

### WRONG

- overengineering rare cases

---

### WHY THIS FAILS

- wastes time
- increases complexity

---

### CORRECT

- focus on core loop
- handle main failure modes

---

## FINAL RULES

1. Simplicity > complexity  
2. Robustness > realism  
3. Determinism > randomness  
4. Clarity > cleverness  
5. Evaluation compatibility > ML purity  

---

## FINAL CHECK

If unsure:

Ask:
→ “Will a generic LLM handle this reliably?”

If answer is NO → redesign.

---

END OF FILE
