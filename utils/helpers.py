"""General-purpose helper functions for serialization and consistency."""

from __future__ import annotations


def format_reward(reward: float) -> str:
    """Consistently format reward values for logging and display."""
    return f"{reward:.2f}"


def format_action_value(value: float) -> str:
    """Consistently format action target values."""
    return f"{value:.2f}"