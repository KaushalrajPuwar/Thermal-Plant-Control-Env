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
	"""
	Canonical representation of the thermal plant's internal state.
	
	This dataclass provides a centralised contract for the system variables 
	shared across the physics core, the API boundary, and the evaluation graders.
	
	Operational Bounds & Units:
	- P, L, U, F, D: Normalised units in [0, 1].
	- T, Pr, S: Normalised units in [0, 1.5] (Safety threshold at 1.0).
	
	Note: U (Control) and F (Cooling) in this state represent the *actual* 
	physical positions of the valves, subject to inertia, as opposed to the 
	*target* positions requested by the agent.
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
