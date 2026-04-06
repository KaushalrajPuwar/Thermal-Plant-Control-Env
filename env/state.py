"""Canonical state contract for the thermal plant environment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from utils.constants import (
	DEFAULT_D,
	DEFAULT_F,
	DEFAULT_L,
	DEFAULT_P,
	DEFAULT_PR,
	DEFAULT_S,
	DEFAULT_T,
	DEFAULT_U,
	OBSERVATION_DECIMALS,
)


@dataclass
class ThermalPlantState:
	"""Canonical environment state shared across core, API, and tests.

	Bounds:
	- P, L, U, F, D in [0, 1]
	- T, Pr, S in [0, 1.5]

	U and F are inherited internal plant conditions at episode start.
	The agent still controls runtime targets through U_target and F_target.
	"""

	P: float = DEFAULT_P
	L: float = DEFAULT_L
	T: float = DEFAULT_T
	Pr: float = DEFAULT_PR
	U: float = DEFAULT_U
	F: float = DEFAULT_F
	S: float = DEFAULT_S
	D: float = DEFAULT_D

	def to_raw_dict(self) -> Dict[str, float]:
		"""Return the full-precision internal state."""
		return {
			"P": self.P,
			"L": self.L,
			"T": self.T,
			"Pr": self.Pr,
			"U": self.U,
			"F": self.F,
			"S": self.S,
			"D": self.D,
		}

	def to_observation(self) -> Dict[str, float]:
		"""Return the rounded observation view intended for agent-facing display."""
		return {
			key: round(value, OBSERVATION_DECIMALS)
			for key, value in self.to_raw_dict().items()
		}

	def to_dict(self) -> Dict[str, float]:
		"""Return the full state as a plain dictionary."""
		return self.to_raw_dict()
