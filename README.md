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

[![OpenEnv](https://img.shields.io/badge/OpenEnv-v1.0-blue.svg?style=for-the-badge)](https://github.com/meta-pytorch/OpenEnv)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge)](https://opensource.org/licenses/Apache-2.0)
[![Hugging Face Space](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue?style=for-the-badge)](https://huggingface.co/spaces/kaushalrajpuwar/thermal-plant-control)

> **Testing how AI models handle high-stakes physical systems.**

---

## 📖 Overview

The **Thermal Plant Control Environment** is an accurate and consistent simulation designed to test how well AI can manage industrial systems. You must balance power production against real physical limits (**Temperature**, **Pressure**, and **Stress**) while dealing with slow control valves and long-term equipment wear.
 
 This environment follows the **Meta PyTorch OpenEnv** rules and tests if AI can plan ahead and keep the system safe during sudden changes.

### 🧩 Why this is hard
 This isn't a simple logic puzzle. To win, the AI must understand:
 - **Heat Delay:** Heat doesn't disappear instantly; you must start cooling *before* the temperature spikes.
 - **Valve Lag:** Controls are slow. If you just react to what you see, the system will shake and become unstable.
 - **Everything is connected:** Changing the fuel level affects temperature and pressure at the same time.

---

## 🛠️ System Dynamics

### 🧪 How the parts are connected
 Heat and cooling determine the core temperature, which then affects the internal pressure and system wear.
 
 ```mermaid
 graph LR
     subgraph "Controls"
         U[Fuel/Power]
         F[Cooling Flow]
     end
     
     subgraph "Plant Core"
         Core((Steam Core))
     end
     
     subgraph "Current State"
         T[Temperature]
         Pr[Pressure]
         S[Wear Stress]
     end
 
     U --> Core
     F --> Core
     Core --> T
     T --> Pr
     Pr --> S
     S -.-> |"Damage"| F
     
     L((Power Demand)) -.-> Core
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

---

## 🏆 Standalone Benchmark Tasks

The challenge scales through four distinct operational regimes. Every task is deterministic and reproducible.

### 🟢 Task 1: Steady Operation
 Can the AI keep the plant stable when nothing is changing?
 | Task Setting | Target | What to watch for |
 | :--- | :--- | :--- |
 | **Constant Demand** | Keep power steady. | Stable power output. |
 | **No Surprises** | Deal with slow valves. | Position matching. |
 
 ### 🟡 Task 2: Changing Demand
 Can the AI handle sudden spikes in power requirements?
 | Task Setting | Target | What to watch for |
 | :--- | :--- | :--- |
 | **Sudden Load Jump** | Move power to new levels. | Avoid overshooting the target. |
 | **Scaling Up/Down** | Settle quickly. | Smooth transitions. |
 
 ### 🟠 Task 3: Hot-Start Emergency
 Can the AI save a system that is already over-heating?
 | Task Setting | Target | What to watch for |
 | :--- | :--- | :--- |
 | **Over-Heat Spawn** | Cool it down immediately. | Temperature safety limit. |
 | **Pressure Control** | Prevent equipment damage. | Mechanical stress levels. |
 
 ### 🔴 Task 4: Equipment Failure & Shock
 The ultimate test: a sudden heat wave hits while the cooling system is broken.
 | Task Setting | Target | What to watch for |
 | :--- | :--- | :--- |
 | **Heat Wave** | Survive a massive temperature jump. | Pressure limits. |
 | **Broken Cooling** | Manage with weak equipment. | Valve limits. |

---

## 📊 AI vs Human-Written Rules
 
 We compare advanced AI models against standard math-based rules (the Baseline).
 
 | Task ID | **Baseline Rules** | **Llama-3.3-70B** | Improvement |
 | :--- | :---: | :---: | :---: |
 | `task1` | 0.95 | **0.95** | --- |
 | `task2` | 0.77 | **0.84** | **+9%** |
 | `task3` | 0.57 | **0.75** | **+31%** |
 | `task4` | 0.48 | **0.74** | **+54%** |
 
 > [!TIP]
 > **Why the AI wins:** Simple rules can handle easy tasks (Task 1), but they fail when things get complicated. The AI is **9% to 54% better** in the hard tasks because it can **think ahead** and stay safe under pressure.
 
 **Observation:** While standard rules work for steady operation, they fail during emergencies. The AI identifies the need for maximum cooling long before a simple script would react.

> [!IMPORTANT]
> **Anti-Coasting Fix:** We have strictly defined the evaluation window to begin **ONLY after** the disturbance injection. Models can no longer inflate their scores with early "stable" steps.

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
