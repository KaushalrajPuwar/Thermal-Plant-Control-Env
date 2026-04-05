# INFERENCE & LLM INTERACTION SPECIFICATION
Version: 1

---

## PURPOSE

Defines:
- how inference.py must behave
- how LLM is used
- how prompts are structured
- how outputs are parsed
- how failures are handled

This file is CRITICAL for passing validation and evaluation.

---

## CORE PRINCIPLE

> LLM OUTPUT IS UNTRUSTED INPUT

Never assume:
- valid JSON
- correct format
- correct values

---

## INFERENCE LOOP (MANDATORY)

For each episode:

1. reset environment
2. loop for N steps:
   - build prompt
   - call LLM
   - parse output → action
   - env.step(action)
   - log [STEP]
3. compute score
4. log [END]

---

## LLM CLIENT REQUIREMENT

Must use:

OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY
)

Environment variables:
- API_BASE_URL
- MODEL_NAME
- HF_TOKEN

---

## PROMPT STRUCTURE

System prompt must:

- define role clearly
- define action format STRICTLY
- forbid extra text

Example:

"You are controlling a thermal plant.
Return ONLY JSON:
{"U_target": float, "F_target": float}
No explanation."

---

User prompt must include:

- current step
- key state variables
- last reward
- short history (last 3–4 steps)

---

## ACTION FORMAT (STRICT TARGET)

Expected ideal output:

{"U_target": 0.5, "F_target": 0.3}

BUT DO NOT RELY ON THIS.

---

## PARSER DESIGN (MANDATORY)

### Step 1 — Try JSON

try:
    json.loads(text)

---

### Step 2 — Anchored extraction

Use regex:

"U_target": number
"F_target": number

DO NOT use generic number extraction.

---

### Step 3 — Clamp

U = min(max(U, 0), 1)
F = min(max(F, 0), 1)

---

### Step 4 — Fallback

If parsing fails:
- reuse last valid action
- OR default (0.5, 0.5)

---

### Step 5 — Penalty

If fallback used:
- apply strong negative reward

---

## WHAT NOT TO DO

❌ Do not use loose regex capturing all numbers  
❌ Do not trust model format  
❌ Do not crash on parse failure  
❌ Do not silently ignore errors  

---

## ERROR HANDLING

Use:

except Exception:

NOT:

except:

---

## LOGGING (STRICT)

Every step must print:

[STEP] step=... action=... reward=... done=... error=...

---

## ACTION STRING

Must log EXACT raw action string returned by LLM.

---

## TEMPERATURE SETTINGS

Use:

temperature = 0.0–0.3

Reason:
- reduce randomness
- improve determinism

---

## MAX TOKENS

Keep low (~100–150)

Reason:
- faster inference
- less hallucination

---

## HISTORY WINDOW

Include last 3–5 steps max.

Too long → noise  
Too short → no adaptation  

---

## FAILURE SAFETY

Even if:

- model fails
- parsing fails
- env errors

You MUST:

- continue execution
- always log [END]

---

## SUCCESS CONDITION

success = score >= threshold (e.g., 0.1)

---

## DETERMINISM STRATEGY

- fixed prompts
- low temperature
- no randomness in env

---

## FINAL RULE

If inference.py crashes → entire submission fails.

Treat this file as production-critical.

---

END OF FILE
