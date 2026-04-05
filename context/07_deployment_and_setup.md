# DEPLOYMENT & SETUP SPECIFICATION
Version: 1

---

## PURPOSE

Defines:
- how to run locally
- how to configure API access
- how to build Docker
- how to deploy to Hugging Face Spaces
- how submission environment differs from local

This file prevents infra-related failures.

---

## CORE PRINCIPLE

> Your code must run in TWO environments:
1. Local development (your machine)
2. Judge environment (HF Space + injected API)

These environments are NOT identical.

---

## ENVIRONMENT VARIABLES (MANDATORY)

Your system must rely on:

- API_BASE_URL
- MODEL_NAME
- HF_TOKEN

Optional:
- IMAGE_NAME (if using Docker image loading)

---

## LOCAL DEVELOPMENT SETUP

### Option 1 — OpenRouter

Set:

API_BASE_URL=https://openrouter.ai/api/v1  
MODEL_NAME=meta-llama/llama-3-8b-instruct  
HF_TOKEN=<your_openrouter_key>

---

### Option 2 — Together AI

API_BASE_URL=https://api.together.xyz/v1  
MODEL_NAME=meta-llama/Llama-3-8b-instruct  
HF_TOKEN=<your_together_key>

---

### Option 3 — Hugging Face Router

API_BASE_URL=https://router.huggingface.co/v1  
MODEL_NAME=<hf_model>  
HF_TOKEN=<hf_token>

---

## IMPORTANT RULE

Do NOT hardcode any API.

Always use:

os.getenv("API_BASE_URL")  
os.getenv("MODEL_NAME")  
os.getenv("HF_TOKEN")

---

## RUNNING LOCALLY

Steps:

1. Set environment variables
2. Run:

python inference.py

3. Verify:
- no crash
- logs correct
- score generated

---

## DOCKER REQUIREMENTS

Your repo must contain:

Dockerfile

---

### Dockerfile must:

- install dependencies
- copy project
- expose environment correctly
- run environment server

---

### Example structure:

FROM python:3.10

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

CMD ["python", "inference.py"]

---

## DOCKER BUILD TEST

Run:

docker build .

Must:
- complete successfully
- no missing dependencies
- no runtime errors

---

## HUGGING FACE SPACE DEPLOYMENT

### Space type:

- Docker
- OpenEnv tagged

---

### Must expose endpoints:

- /reset
- /step
- /state

---

### Validation check:

POST https://your-space.hf.space/reset

Must return 200

---

## SUBMISSION ENVIRONMENT DIFFERENCE

### Locally:
- You control API
- You control model
- You control runtime

---

### Judges:
- Inject API_BASE_URL
- Inject MODEL_NAME
- Inject HF_TOKEN
- May use different model

---

## CRITICAL IMPLICATION

Your system must:

- NOT depend on a specific model
- NOT assume output format
- NOT assume behavior

---

## HF SPACE ROLE

HF Space is:

- environment host
- HTTP interface provider

NOT:

- guaranteed model host
- training environment

---

## NETWORK REQUIREMENTS

- outbound API calls must work
- no local-only dependencies
- no localhost assumptions

---

## TIME LIMITS

- build < ~10 minutes
- execution < ~20 minutes total

---

## COMMON DEPLOYMENT FAILURES

### 1. Hardcoded API key
→ fails in judge env

---

### 2. Missing env variables
→ inference fails

---

### 3. Docker build errors
→ immediate rejection

---

### 4. HF Space not responding
→ fails validation

---

### 5. Wrong endpoints
→ OpenEnv validate fails

---

## PRE-SUBMISSION CHECKLIST

Before submission:

- docker build works
- inference.py runs locally
- env variables used correctly
- no hardcoded keys
- HF Space deployed
- /reset responds
- openenv validate passes

---

## FINAL RULE

If it only works locally → it is a failed submission.

---

END OF FILE
