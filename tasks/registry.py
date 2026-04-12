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


def normalize_task_id(raw: str) -> str:
    """Normalize task_id so '1', 'task1', 'Task1' all resolve to 'task1'."""
    raw = raw.strip().lower()
    if raw in _TASK_CLASSES:
        return raw
    # Try prefixing with "task" for bare numeric IDs like "1", "2"
    candidate = f"task{raw}"
    if candidate in _TASK_CLASSES:
        return candidate
    return raw  # return as-is; will raise in get_task


def get_task(task_id: str) -> ThermalPlantTask:
    """Instantiate and return the canonical task."""
    task_id = normalize_task_id(task_id)
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
