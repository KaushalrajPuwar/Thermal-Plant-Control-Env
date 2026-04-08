"""Shared constants for the thermal plant environment."""

from __future__ import annotations

from typing import Dict, Tuple

# Canonical action keys.
ACTION_U_TARGET = "U_target"
ACTION_F_TARGET = "F_target"

# Canonical observation/state keys.
STATE_KEYS = ("P", "L", "T", "Pr", "U", "F", "S", "D")

# Variable bounds.
BOUND_01: Tuple[float, float] = (0.0, 1.0)
BOUND_015: Tuple[float, float] = (0.0, 1.5)

P_BOUNDS: Tuple[float, float] = BOUND_01
L_BOUNDS: Tuple[float, float] = BOUND_01
U_BOUNDS: Tuple[float, float] = BOUND_01
F_BOUNDS: Tuple[float, float] = BOUND_01
D_BOUNDS: Tuple[float, float] = BOUND_01

T_BOUNDS: Tuple[float, float] = BOUND_015
PR_BOUNDS: Tuple[float, float] = BOUND_015
S_BOUNDS: Tuple[float, float] = BOUND_015

# Deterministic default initialization for the state dataclass.
DEFAULT_P = 0.4
DEFAULT_L = 0.6
DEFAULT_T = 0.6
DEFAULT_PR = 0.6
DEFAULT_U = 0.5
DEFAULT_F = 0.5
DEFAULT_S = 0.0
DEFAULT_D = 0.0

DEFAULT_STATE: Dict[str, float] = {
	"P": DEFAULT_P,
	"L": DEFAULT_L,
	"T": DEFAULT_T,
	"Pr": DEFAULT_PR,
	"U": DEFAULT_U,
	"F": DEFAULT_F,
	"S": DEFAULT_S,
	"D": DEFAULT_D,
}

# Episode controls.
# Tasks dictate default episode lengths. Max steps are defined in the specific Task subclasses.
DEFAULT_TASK_ID = "task1"
DEFAULT_EPISODE_ID = 43
OBSERVATION_DECIMALS = 2

# External evaluator episode policy
# External (evaluator/public) calls will use this fixed episode id unless
# a valid developer token is supplied via the `X-DEV-TOKEN` header.
DEFAULT_EXTERNAL_EPISODE_ID = 143
EXTERNAL_EPISODE_DISPLAY_WIDTH = 3

# Name of the environment variable that holds the developer reset token.
# When set locally by developers, requests including the matching
# `X-DEV-TOKEN` header are allowed to override episode ids.
DEV_RESET_TOKEN_ENV = "DEV_RESET_TOKEN"

# Regime-map task identifiers.
TASK_CODE: Dict[str, int] = {
	"task1": 1,
	"task2": 2,
	"task3": 3,
	"task4": 4,
}

# Startup solver coefficients shared across tasks.
GAP_DEG_DRAG = 0.10
GAP_TENSION_DRAG = 0.05
P_STRESS_DRAG = 0.02

U_WEAR_GAIN = 0.08
U_GAP_GAIN = 0.06
U_MARGIN_RELIEF = 0.04

F_POWER_GAIN = 0.55
F_WEAR_GAIN = 0.30
F_TENSION_GAIN = 0.18
F_STRESS_GAIN = 0.10
F_MARGIN_RELIEF = 0.06

COOL_DEG_LOSS = 0.60

T_DEG_GAIN = 0.20
T_STRESS_GAIN = 0.15
T_TENSION_GAIN = 0.12

PR_DEG_GAIN = 0.10
PR_TENSION_GAIN = 0.08
PR_MARGIN_PENALTY = 0.06

RECOVER_F_GAIN = 0.70
RECOVER_P_GAIN = 0.25

# Coefficients used by the coupled startup solver.
INIT_P_U_GAIN = 0.90
INIT_T_BIAS = 0.35
INIT_T_P_GAIN = 0.45
INIT_T_F_GAIN = 0.30

# Task regime maps.
TASK_STARTUP_PROFILES: Dict[str, Dict[str, float]] = {
	"task1": {
		"aL": 0.60,
		"sL": 0.00, # Fixed load start to match constant task target
		"aD": 0.02,
		"sD": 0.03,
		"aT": 0.08,
		"sT": 0.06,
		"aM": 0.88,
		"sM": 0.06,
		"gap_scale": 0.22,
		"d_max": 0.08,
		"s_base": 0.05,
		"s_gain": 0.08,
		"f_bias": 0.20,
		"t_task_bias": -0.08,
		"soft_t_cap": 0.82,
		"soft_pr_cap": 0.86,
	},
	"task2": {
		"aL": 0.50, # Set to exact step 1 load sequence baseline
		"sL": 0.00,
		"aD": 0.04,
		"sD": 0.04,
		"aT": 0.14,
		"sT": 0.10,
		"aM": 0.78,
		"sM": 0.08,
		"gap_scale": 0.16,
		"d_max": 0.10,
		"s_base": 0.03,
		"s_gain": 0.12,
		"f_bias": 0.22,
		"t_task_bias": -0.04,
		"soft_t_cap": 0.84,
		"soft_pr_cap": 0.88,
	},
	"task3": {
		"aL": 0.70,
		"sL": 0.00,
		"aD": 0.08,
		"sD": 0.06,
		"aT": 0.72,
		"sT": 0.12,
		"aM": 0.60,
		"sM": 0.08,
		"gap_scale": 0.05, # Reduce gap further, so power is already high and generating heat
		"d_max": 0.18,
		"s_base": 0.20,
		"s_gain": 0.18,
		"f_bias": 0.12,
		"t_task_bias": 0.35, # Extra direct heat
		"soft_t_cap": 1.05,  # Prevent environment from rescuing the initial state
		"soft_pr_cap": 1.10,
	},
	"task4": {
		"aL": 0.60,
		"sL": 0.00,
		"aD": 0.18,
		"sD": 0.08,
		"aT": 0.22,
		"sT": 0.10,
		"aM": 0.68,
		"sM": 0.08,
		"gap_scale": 0.14,
		"d_max": 0.32,
		"s_base": 0.05,
		"s_gain": 0.14,
		"f_bias": 0.32,
		"t_task_bias": 0.02,
		"soft_t_cap": 0.85,
		"soft_pr_cap": 0.89,
	},
}

# Transition coefficients from modeling spec.
U_INERTIA_PREV = 0.8
U_INERTIA_TARGET = 0.2

F_INERTIA_PREV = 0.8
F_INERTIA_TARGET = 0.2

P_PREV_COEF = 0.85
P_U_COEF = 0.15

K_COOL_BASE = 0.5
T_POWER_COEF = 0.4

PR_PREV_COEF = 0.7
PR_MIX_COEF = 0.3
PR_POWER_COEF = 0.5

T_WARNING = 0.9
# Keep stress accumulation visible on a 2-decimal dashboard within a short horizon.
STRESS_RATE = 0.2

# Keep degradation visible under meaningful control changes within 1-2 steps.
DEGRADATION_RATE = 0.06

# Failure thresholds.
FAIL_T = 1.3
FAIL_PR = 1.3
FAIL_S = 1.3

# Reward coefficients.
SAFETY_PENALTY_COEF = 2.0
OSCILLATION_PENALTY_COEF = 0.2
STRESS_PENALTY_COEF = 0.3

# Safety soft thresholds for reward penalties.
SOFT_T = 1.0
SOFT_PR = 1.0

# --- Newly Added Phase 2 Constants ---
ACTUATOR_INERTIA_ALPHA = 0.5
INTEGRATOR = "RK2"
DT = 1.0
HYSTERESIS_MARGIN = 0.02

# Power dynamics coefficients
P_GAIN = 0.8
P_LOAD_COEF = 0.3
P_DEG_COEF = 0.6

# Temperature dynamics coefficients
TEMP_POWER_COEF = 0.04
TEMP_EXP_P = 1.1
TEMP_COOL_COEF = 0.06
TEMP_EXP_F = 1.05
TEMP_ENV_COOL = 0.01
TEMP_DEG_COEF = 0.05

# Pressure dynamics coefficients
PR_T_COEF = 0.2
PR_P_COEF = 0.05
PR_DAMP = 0.1

# Stress dynamics coefficients - amplified for visibility
STRESS_T_COEF = 0.08
STRESS_U_OSC_COEF = 0.5
STRESS_DECAY = 0.04

# Degradation dynamics coefficients - amplified for visibility
DEG_FROM_S_COEF = 0.05
DEG_BETA = 1.0  # Linear dependence
DEG_RECOVERY_RATE = 0.01

# Reward weights
W_TRACK = 1.0
W_SAFETY = 2.0
W_STABILITY = 0.5
W_EFF = 0.1

# Parser defaults and UI toggles
PARSER_DEFAULT_U = 0.5
PARSER_DEFAULT_F = 0.5
INCLUDE_PARSE_ERROR_IN_STEP = True

# Grader normalization scales and penalties
METRIC_NORM_SCALES = {
	"TE": 0.5,
	"OS": 0.5,
	"SV": 0.5,
	"OC": 0.5,
	"SL": 0.5,
	"LP": 0.5,
	"LS": 0.5,
	"RR": 0.5,
}

INVALID_ACTION_PENALTY = 0.2
NONFINITE_HANDLING = "clamp"



