"""Central task discovery and instantiation."""

from typing import Dict, Type, Optional

from tasks.config import ThermalPlantTask
from tasks.task1 import Task1
from tasks.task2 import Task2
from tasks.task3 import Task3
from tasks.task4 import Task4


_TASK_CLASSES: Dict[str, Type[ThermalPlantTask]] = {
    "task1": Task1,
    "task2": Task2,
    "task3": Task3,
    "task4": Task4,
}


def get_task(task_id: str) -> ThermalPlantTask:
    """Instantiate and return the canonical task."""
    cls = _TASK_CLASSES.get(task_id)
    if not cls:
        raise ValueError(f"Unknown task_id '{task_id}'. Expected one of {list(_TASK_CLASSES.keys())}")
    return cls()


def task_registry() -> Dict[str, dict]:
    """Expose registry metadata required by OpenEnv validation."""
    return {
        task_id: {
            "name": getattr(cls, "name", task_id),
            "description": getattr(cls, "description", ""),
            "max_steps": getattr(cls, "max_steps", None),
        }
        for task_id, cls in _TASK_CLASSES.items()
    }
