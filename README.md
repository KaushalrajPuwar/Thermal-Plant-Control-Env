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

[![OpenEnv](https://img.shields.io/badge/OpenEnv-v1.0-blue.svg)](https://github.com/meta-pytorch/OpenEnv)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Hugging Face Space](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/kaushalrajpuwar/thermal-plant-control)

> **Evaluating LLM Reasoning in Safety-Critical Cyber-Physical Systems.**

---

## 📖 Overview

The **Thermal Plant Control Environment** is a high-fidelity, deterministic simulation designed to test the limits of agentic reasoning in industrial automation. Agents must manage a simulated power plant, balancing energy production (**Power Output**) against strict physical constraints (**Temperature**, **Pressure**, and **Mechanical Stress**) under the influence of delayed actuator responses and long-term hardware degradation.

This environment is fully compliant with the **Meta PyTorch OpenEnv** specification and serves as a benchmark for evaluating LLMs on multi-step optimization, disturbance rejection, and preemptive safety management.

---

## 🛠️ System Dynamics

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

---

## 🏆 Benchmark Tasks & Difficulty Tiers

We provide a sequence of tasks that transition from simple tracking to high-pressure emergency recovery.

| Task ID | Tier | Name | Challenge |
| :--- | :--- | :--- | :--- |
| `task1` | 🟢 **Easy** | **Stable Baseline** | Perfect tracking of a constant load with minimal fluctuation. |
| `task2` | 🟡 **Medium** | **Load Following** | Handling sharp step-changes in demand (0.5 → 0.8 → 0.6). |
| `task3` | 🟠 **Hard** | **Preemptive Management** | Spawns at 0.95+ Temp. Requires instant cooling to prevent stress leakage. |
| `task4` | 🔴 **Extra Hard** | **Fault Recovery** | Recovers from a +0.5 sudden thermal blast while fighting high degradation. |

---

## 📊 Baseline Performance (Llama-3.3-70B)

Based on the latest environment tuning (v1.1), the current state-of-the-art results for our internal benchmark are:

- **Global Success Threshold:** `0.70` (Score $\ge$ 0.70 required for ✅)
- **Task 1 Score:** `0.95`
- **Task 2 Score:** `0.84`
- **Task 3 Score:** `0.75`
- **Task 4 Score:** `0.74`

*Note: High-frontier models like Llama-3.3-70B demonstrate significant resilience in Task 4, with performance remaining remarkably consistent with the Hard-tier baseline.*

> [!IMPORTANT]
> **Anti-Coasting Fix:** We have recently plugged the "Lazy Completion" loopholes. Task 4 now strictly measures recovery only **after** the thermal shock occurs, preventing models from getting free points for early safety.

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

High-performance control systems optimized by:

*   [**KaushalrajPuwar**](https://github.com/KaushalrajPuwar)
*   [**freakun0025**](https://github.com/freakun0025)
*   [**nikunj169**](https://github.com/nikunj169)

---

> [!TIP]
> **Check the Graders:** View the deterministic grading formulas in `graders/_metrics.py` to understand exactly how TE (Tracking Error), SV (Safety Violation), OC (Oscillation), and all other internal metrics impact your final leaderboard standing.
