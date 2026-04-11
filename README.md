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
---

# Thermal Plant Control Environment (OpenEnv)

## Environment Overview and Motivation
The **Thermal Plant Control Environment** is a deterministic, OpenEnv-compliant simulation designed to represent the real-world complexities of industrial power generation. Managing a thermal power plant requires carefully balancing the required energy load with system safety limits. High power generation increases temperature and pressure, which accelerates system degradation and stress. 

The motivation behind this environment is to evaluate the ability of Large Language Models (LLMs) to perform continuous, multi-step optimization and safety-critical control under delayed actuator responses (inertia).

## Action and Observation Spaces

### Observation Space (State Variables)
The environment provides the following continuous state variables at each step:
- **`P` (Power Output)**: The current production levels.
- **`L` (Required Load)**: The target production level the system must track.
- **`T` (Temperature)**: Must be kept safely below 1.0 to avoid catastrophic stress.
- **`Pr` (Pressure)**: Must be kept safely below 1.0.
- **`S` (System Stress)**: Accumulated stress from operating near or above thermal limits.
- **`D` (Plant Degradation)**: Long-term mechanical wear based on stress.
- **`U` (Control Valve)**: Current valve position (subject to inertia).
- **`F` (Cooling Valve)**: Current cooling position (subject to inertia).

### Action Space
The agent must return exactly two continuous values in the range `[0.0, 1.0]` at each step:
- **`U_target`**: The desired power valve level.
- **`F_target`**: The desired cooling valve level.

*Note: Actuators suffer from physical lag. Targets slowly pull the actual `U` and `F` values over time.*

## Task Descriptions and Difficulty Levels
This benchmark features 4 predefined tasks with programmatic, deterministic graders mapping scores from `0.0` to `1.0`.

| Task ID | Difficulty | Objective |
|---|---|---|
| **`task1`** | **Easy**   | **Base Load Tracking:** Track a steady, consistent required load (`L`) while keeping temperature stable. |
| **`task2`** | **Medium** | **Variable Load Tracking:** Adapt to periodic diurnal shifts in required load without spiking system pressure. |
| **`task3`** | **Hard**   | **Aggressive Load Steps:** Respond to sudden, massive spikes in load (`L`), requiring anticipatory cooling (`F`) to prevent stress limits from triggering failure. |
| **`task4`** | **Extreme**| **Disturbance Rejection:** Maintain stability during internal degradation and external equipment degradation fluctuations. |

## Setup and Usage Instructions

### Running via Docker (Local Validation)
```bash
# Build the image
docker build -t thermal-plant-control:latest .

# Run the container
docker run -p 7860:7860 thermal-plant-control:latest
```

The container listens on port `7860`. The helper script in [scripts/run_local.sh](scripts/run_local.sh) uses the same default mapping.

### Running Inference Baseline
Ensure you have your environment variables configured locally or via `.env`:
```bash
export HF_TOKEN="your_huggingface_token"
export MODEL_NAME="meta-llama/Llama-3.3-70B-Instruct"
export API_BASE_URL="https://router.huggingface.co/v1"

# Run the agent inference logic
python inference.py
```

## Baseline Performance Scores
Baseline testing via the deterministic heuristic smoke harness reveals the following baseline scores (normalized `[0.0, 1.0]`):
- **task1**: ~0.94
- **task2**: ~0.83
- **task3**: ~0.76
- **task4**: ~0.65

*The environment is fully OpenEnv-compliant, deployed on Hugging Face Spaces, and strictly containerized.*

## Team Magneto's Cheetos

 * [KaushalrajPuwar (Kaushalraj Puwar)](https://github.com/KaushalrajPuwar)
 * [freakun0025 (Kunal Mittal)](https://github.com/freakun0025)
 * [nikunj169 (Nikunj Mahajan)](https://github.com/nikunj169)
