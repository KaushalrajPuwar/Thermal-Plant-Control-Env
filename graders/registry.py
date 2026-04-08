"""Grader registry mapping task ids to grader callables.

Expose `grader_registry()` which returns a dict mapping task id strings
to functions with signature `grade(trajectory) -> float`.
"""

from __future__ import annotations

from typing import Callable, Dict

from graders import task1_grader, task2_grader, task3_grader, task4_grader


def grader_registry() -> Dict[str, Callable]:
	return {
		"task1": task1_grader.grade,
		"task2": task2_grader.grade,
		"task3": task3_grader.grade,
		"task4": task4_grader.grade,
	}
