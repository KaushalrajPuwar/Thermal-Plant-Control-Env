---
title: Thermal Plant Control
emoji: 🏭
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
app_file: server/app.py
pinned: false
tags:
  - openenv
  - reinforcement-learning
---

# 🏭 Thermal Plant Control Environment (OpenEnv)

[![OpenEnv](https://img.shields.io/badge/OpenEnv-v1.0-blue?style=for-the-badge)](https://github.com/meta-pytorch/OpenEnv)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue?style=for-the-badge)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](https://opensource.org/licenses/Apache-2.0)
[![Hugging Face Space](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue?style=for-the-badge)](https://huggingface.co/spaces/kaushalrajpuwar/thermal-plant-control)

> **Evaluating LLM Reasoning in Safety-Critical Cyber-Physical Systems.**

---

## ⚡ Problem Statement: Industrial Grid Resilience

In a modern electrical grid, **Thermal Power Plants** (Coal, Natural Gas, or Nuclear Steam Turbines) provide the critical "Base Load" that keeps the grid stable. However, as demand fluctuates or renewable supply (wind/solar) suddenly drops, these massive physical systems must scale their output rapidly without exceeding safety-critical thermal limits.

This environment simulates a **High-Fidelity Steam Turbine Cycle**. An LLM agent acts as the Lead Plant Controller, managing the balance between fuel input and cooling flux. A single mistake—such as failing to anticipate thermal inertia during a load spike—can lead to **Steam Vessel Over-pressurisation** or **Catastrophic Core Failure**, resulting in a grid-wide blackout.

---

## 📖 Overview

The **Thermal Plant Control Environment** is a deterministic OpenEnv benchmark designed to evaluate agentic reasoning in complex industrial loops. It enforces strict physical consistency across sequential episodes, measuring an agent's ability to navigate non-linear system responses, actuator lag, and cumulative hardware degradation.

This environment is fully compliant with the **OpenEnv** specification, providing a standardized platform for testing LLMs on multi-step optimization and preemptive safety management.

### 🧩 Benchmark Sensitivity & Precision
Unlike discrete logic puzzles, this environment measures **Control Resolution**. 
- **Thermal Inertia:** Heat doesn't dissipate instantly; models must "cool ahead" to prevent spikes.
- **Actuator Lag:** Inputs are smoothed by a 0.5-alpha delay. Reactive models will oscillate; reasoning models will anticipate.
- **Coupled Variables:** Changing fuel input affects temperature AND pressure simultaneously, requiring multi-variable optimization.

---

## 🛠️ System Dynamics

### 🧪 Plant Schematic (Topology)
The system is modeled as a **2nd-order coupled thermal-hydraulic loop**. Energy balance ($\dot{Q}_{net} = \alpha U - \beta F$) drives the core temperature ($T$), which induces non-linear pressure transients ($P$) and cumulative hardware stress ($S$).

```mermaid
graph LR
    subgraph "Actuation"
        U[Fuel/Power]
        F[Coolating Flux]
    end
    
    subgraph "Core Physics"
        Core((Thermal Core))
    end
    
    subgraph "State Vector"
        T[Temperature T]
        Pr[Pressure P]
        S[Stress S]
    end

    U --> |"+Q_in (Fuel)"| Core
    F --> |"-Q_out (Coolant)"| Core
    Core --> |"dT/dt"| T
    T --> |"dP/dt"| Pr
    Pr --> |"d S/dt"| S
    S -.-> |"Degradation D"| F
    
    L((Load L)) -.-> |"Disturbance"| Core
```

### 🔍 Observation Space

| Variable | Symbol | Description | Safety Limit |
| :--- | :--- | :--- | :--- |
| **Power Output** | `P` | Current electrical generation tracking the required load. | N/A |
| **Required Load** | `L` | Dynamic target for power production. | N/A |
| **Temperature** | `T` | Thermal state. Crossing **1.0** triggers safety penalties. | < 1.0 |
| **Pressure** | `Pr` | Internal vessel pressure. Crossing **1.0** triggers penalties. | < 1.0 |
| **System Stress** | `S` | Instantaneous mechanical strain from heat/pressure. | < 1.3 |
| **Degradation** | `D` | Cumulative wear. Reduces cooling efficiency by up to 60%. | N/A |
| **Control Valve** | `U` | Actual position of the fuel/power actuator (with inertia). | [0, 1] |
| **Cooling Valve** | `F` | Actual position of the coolant actuator (with inertia). | [0, 1] |

### ⚡ Action Space

The agent must output a JSON object containing exactly two continuous values `[0.0, 1.0]`:

```json
{
  "U_target": 0.65,
  "F_target": 0.45
}
```

> [!NOTE]
> **Actuator Inertia:** The system implements a 0.5 alpha smoothing. Your target input does not jump the valve instantly; the system exponentially approaches your target over multiple steps. Anticipation is key.

### 📐 Reward Logic & Mathematics

The environment utilizes a **Composite Physical Reward Function** that penalizes both deviations from the target and breaches of structural safety. The per-step reward $r_t$ is defined as:

$$r_t = 1.0 - (w_{te} \cdot TE_{norm} + w_{sv} \cdot SV_{norm} + w_{oc} \cdot OC_{norm})$$

| Component | Metric | Weight | Purpose |
| :--- | :--- | :---: | :--- |
| **TE** | Tracking Error | **0.50** | Precision in matching the required grid load. |
| **SV** | Safety Violation | **0.40** | Magnitude of Temperature/Pressure excursions. |
| **OC** | Oscillation | **0.10** | Actuator fatigue caused by erratic valve changes. |

**Catastrophic Failure:** If Temperature ($T$), Pressure ($Pr$), or Stress ($S$) exceed the hard **1.5x failure limit**, the environment triggers an immediate `done=true` with a **-5.0 Terminal Penalty**.

---

## 🏆 Standalone Benchmark Tasks

The challenge scales through four distinct operational regimes. Every task is deterministic and reproducible.

### 🟢 Task 1: Stable Baseline Operation
Establishes the agent's ability to maintain equilibrium in a "Cold-Start" or "Steady-State" regime.
| Operational Profile | Objective | Critical Observation |
| :--- | :--- | :--- |
| **Static Demand** | Maintain zero-error tracking. | Stability of Power output `P`. |
| **Zero Disturbance** | Verify actuator lag compensation. | Valve position `U` vs `L`. |

### 🟡 Task 2: Load Following
Simulates a grid-level demand spike requiring rapid power scaling.
| Operational Profile | Objective | Critical Observation |
| :--- | :--- | :--- |
| **Instant Step-Change** | Transition power output to new setpoints. | Overshoot (`OS`) management. |
| **Dynamic Scaling** | Minimize settling time during transients. | Tracking Error (`TE`) recovery. |

### 🟠 Task 3: Preemptive Constraint Management
A high-pressure scenario where the agent spawns into a system near its thermal limit.
| Operational Profile | Objective | Critical Observation |
| :--- | :--- | :--- |
| **Near-Critical Spawn** | Immediate heat mitigation (Emergency Cooling). | Temperature `T` safety buffer. |
| **Boundary Control** | Prevent stress leakage at high pressures. | Stress accumulation `S`. |

### 🔴 Task 4: Fault Recovery with Degradation
The ultimate stress test. Simultaneous hardware failure and external thermal shock.
| Operational Profile | Objective | Critical Observation |
| :--- | :--- | :--- |
| **Athermal Shock** | Recover from sudden energy injection. | Pressure rate-of-change. |
| **Hardware Wear** | Manage degraded coolant efficiency (D=0.6). | Valve saturation limits. |

---

## 📊 Performance & Discriminative Power

We compare high-frontier models against a hardcoded **Rule-Based Baseline** to measure the reasoning "delta." 

| Task ID | **Heuristic Baseline** | **Llama-3.3-70B** | Improvement |
| :--- | :---: | :---: | :---: |
| `task1` | 0.95 | **0.95** | --- |
| `task2` | 0.77 | **0.84** | **+9%** |
| `task3` | 0.57 | **0.75** | **+31%** |
| `task4` | 0.48 | **0.74** | **+54%** |

> [!NOTE]
> **The Success Reversal:** Note that while rule-based logic is sufficient for steady-state tracking (Task 1), it lacks the 'Predictive Intuition' required for high-stress recovery. The **9%-54% improvement** of the LLM over the baseline validates this repository as a true test of **Physical Reasoning** rather than simple instruction following.
>
> High-frontier models like Llama-3.3-70B demonstrate significant resilience in Task 4, with performance remaining remarkably consistent with the Hard-tier baseline.

> [!IMPORTANT]
> **Anti-Coasting Fix:** We have strictly defined the evaluation window to begin **ONLY after** the disturbance injection. Models can not inflate their scores with early "stable" steps.

### 🧠 The AI Agent: In-Context Reinforcement Learning

Unlike traditional controllers, the LLM agent operates as an **In-Context RL Learner**. It leverages the high-resolution state history provided in the `OpenEnv` observation loop to refine its control strategy across the episode.

- **Non-Linear Reasoning:** The agent must internalize the "Actuator Lag" and "Thermal Inertia" from previous steps to time its cooling flux *before* a spike occurs.
- **Strategic Buffering:** In Task 3, models demonstrate the ability to sacrifice tracking precision (TE) in exchange for maintaining a "Safety Buffer" (SV) near the thermal boundaries.
- **Feedback Sensitivity:** By observing the `reward` signal provided at each step, the model identifies the "Sensitivity" of the specific plant instance and adapts its Gain ($K_p$) on-the-fly.

---

## 🚀 Getting Started

### 1️⃣ Installation

Clone the repository and install the lightweight requirements:

```bash
git clone https://huggingface.co/spaces/kaushalrajpuwar/thermal-plant-control
cd thermal-plant-control
pip install -r requirements.txt
```

### 2️⃣ Environment Configuration

Create a `.env` file or export your tokens:

```bash
export HF_TOKEN="your_token_here"
export MODEL_NAME="meta-llama/Llama-3.3-70B-Instruct"
export API_BASE_URL="https://router.huggingface.co/v1"
```

### 3️⃣ Running Inference

Execute the full 4-task sequential evaluation:

```bash
python inference.py
```

### 4️⃣ Local Docker Validation

To mirror the Exact Hugging Face production environment locally:

```bash
docker build -t thermal-plant:latest .
docker run -p 7860:7860 thermal-plant:latest
```

---

## 🤝 The Team

*   [**KaushalrajPuwar**](https://github.com/KaushalrajPuwar)
*   [**freakun0025**](https://github.com/freakun0025)
*   [**nikunj169**](https://github.com/nikunj169)

---

> [!TIP]
> **Check the Graders:** View the deterministic grading formulas in `graders/_metrics.py` to understand exactly how TE (Tracking Error), SV (Safety Violation), OC (Oscillation), and all other internal metrics impact your final leaderboard standing.
