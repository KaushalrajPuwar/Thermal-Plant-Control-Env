# 🔧 Thermal Plant Control Benchmark

A compact reinforcement learning environment for **controlling a thermal power unit under constraints**, designed for evaluating agent behavior in systems with **delayed dynamics, safety limits, and coupled variables**.

---

## 📌 Overview

This project implements a **control benchmark** where an agent operates a simplified thermal plant.

The goal is to:

* Track a target power output
* Maintain safe operating conditions
* Avoid instability and failure

The environment is structured to reflect **real-world control trade-offs** without requiring full physical simulation.

---

## 🎯 Why this exists

Modern LLM-based agents can interact with environments but **do not learn through weight updates during evaluation**.

This benchmark explores:

> How well a general-purpose agent can **adapt its behavior within a short interaction loop** using feedback from a dynamic system.

---

## ⚙️ Environment Summary

The system models a thermal unit with:

* **Production control (U)** — controls power output
* **Cooling control (F)** — regulates temperature
* **Coupled dynamics** — actions affect multiple variables
* **Delayed effects** — consequences unfold over time
* **Safety constraints** — violations lead to penalties or failure

---

## 🧠 Observable State

At each step, the agent receives:

* Power output
* Target load
* Temperature
* Pressure
* Thermal stress
* System degradation

These variables evolve deterministically based on agent actions.

---

## 🎮 Action Space

The agent outputs:

```json
{
  "U_target": float,   // production control [0, 1]
  "F_target": float    // cooling control [0, 1]
}
```

Actions represent **target positions**, not instantaneous changes.
The system transitions gradually due to actuator dynamics.

---

## 🔁 Interaction Loop

Each episode follows:

1. Agent observes state
2. Agent outputs action
3. Environment updates system
4. Reward is computed
5. Repeat until termination

Episodes are short (≈8–10 steps) and deterministic.

---

## 📉 Reward Design

The reward reflects:

* Tracking accuracy (meeting target load)
* Safety (temperature, pressure limits)
* Stability (avoiding oscillations)
* Efficiency (avoiding excessive control effort)

Rewards are dense and computed at every step.

---

## 🧪 Tasks

The environment supports multiple difficulty levels:

1. **Stable Operation**
   Maintain a constant target safely

2. **Load Following**
   Adapt to changing demand

3. **Constraint Anticipation**
   Manage delayed risk before failure

4. **Fault Recovery**
   Recover under degraded system conditions

---

## 🧩 Key Characteristics

* Deterministic dynamics
* Coupled state variables
* Delayed and nonlinear effects
* Short-horizon decision making
* Interpretable reward structure

---

## 🚀 Running the Environment

### Requirements

* Python 3.10+
* Docker
* `openenv-core`

---

### Validate locally

```bash
pip install openenv-core
openenv validate
```

---

### Run inference

```bash
python inference.py
```

---

## 🤖 Agent Interface

The environment is designed to be used with LLM-based agents via:

* OpenAI-compatible client
* Hugging Face router / API providers

The agent receives structured state and must output valid actions.

---

## 🧱 Repository Structure

```
env/            # core environment logic
tasks/          # task configurations
graders/        # scoring functions
models/         # data structures
inference.py    # evaluation script (required)
openenv.yaml    # environment specification
Dockerfile      # container setup
```

---

## 🧪 Evaluation

Each run produces:

* Step-by-step rewards
* Final normalized score ∈ [0, 1]
* Deterministic results

Evaluation is based on **agent behavior within a single episode**, not training performance.

---

## 🌐 Deployment

The environment is deployable via:

* Hugging Face Spaces
* Docker container

A `/reset` endpoint is exposed for validation.

---

## ⚠️ Notes

* No persistent memory across episodes
* No model training required
* Designed for **interaction-based evaluation**, not learning curves

---

<!--## 📄 License

To be added.

--- -->

## 👥 Team

 * [KaushalrajPuwar (Kaushalraj Puwar)](https://github.com/KaushalrajPuwar)
 * [freakun0025 (Kunal Mittal)](https://github.com/freakun0025)
 * [nikunj169 (Nikunj Mahajan)](https://github.com/nikunj169)

---

## 🔜 Future Improvements

* Enhanced visualization
* Additional task variants
* More complex degradation dynamics

---

## 🧠 Summary

This project provides a **minimal but meaningful control benchmark**:

> A system where intelligent behavior must emerge through interaction with delayed, constrained dynamics.

---
