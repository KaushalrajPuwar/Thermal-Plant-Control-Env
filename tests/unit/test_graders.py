import math

from utils.schemas import EpisodeTrajectory, TrajectoryStep, ParsedAction

from graders.task1_grader import grade as grade_t1
from graders.task2_grader import grade as grade_t2
from graders.task3_grader import grade as grade_t3
from graders.task4_grader import grade as grade_t4


def _make_parsed_action(u=0.5, f=0.5, invalid=False):
    return ParsedAction(
        u_target=float(u),
        f_target=float(f),
        source="json",
        used_fallback=False,
        invalid_output=invalid,
        penalty_applied=0.0,
        raw_text="",
        parse_error=None,
    )


def _make_step(idx: int, raw_state: dict, invalid=False, done=False, error=None):
    pa = _make_parsed_action(u=raw_state.get("U", 0.5), f=raw_state.get("F", 0.5), invalid=invalid)
    return TrajectoryStep(
        step=idx,
        raw_llm_text="",
        parsed_action=pa,
        canonical_action={"U_target": pa.u_target, "F_target": pa.f_target},
        observation={k: float(v) for k, v in raw_state.items()},
        raw_state={k: float(v) for k, v in raw_state.items()},
        reward=0.0,
        done=done,
        error=error,
        env_invalid_action=invalid,
        invalid_penalty_applied=0.0,
    )


def test_task1_basic_deterministic_and_range():
    traj = EpisodeTrajectory(task="task1", benchmark="test", model="tester")
    # Two-step simple trajectory
    s1 = {"P": 0.6, "L": 0.5, "T": 0.5, "Pr": 0.5, "U": 0.5, "F": 0.5, "S": 0.1}
    s2 = {"P": 0.5, "L": 0.7, "T": 0.4, "Pr": 0.3, "U": 0.4, "F": 0.4, "S": 0.2}
    traj.steps.append(_make_step(1, s1))
    traj.steps.append(_make_step(2, s2))

    score1 = grade_t1(traj)
    score2 = grade_t1(traj)
    assert isinstance(score1, float)
    assert 0.0 <= score1 <= 1.0
    assert math.isclose(score1, score2, rel_tol=1e-9)


def test_invalid_penalty_reduces_score():
    traj = EpisodeTrajectory(task="task1", benchmark="test", model="tester")
    s = {"P": 0.6, "L": 0.5, "T": 0.5, "Pr": 0.5, "U": 0.5, "F": 0.5, "S": 0.1}
    traj.steps.append(_make_step(1, s, invalid=False))
    traj.steps.append(_make_step(2, s, invalid=False))
    base = grade_t1(traj)

    traj2 = EpisodeTrajectory(task="task1", benchmark="test", model="tester")
    traj2.steps.append(_make_step(1, s, invalid=True))
    traj2.steps.append(_make_step(2, s, invalid=False))
    penalized = grade_t1(traj2)

    assert penalized <= base


def test_task2_and_task3_and_task4_basic_ranges():
    # Build a short trajectory that is safe
    traj = EpisodeTrajectory(task="task2", benchmark="test", model="tester")
    for i in range(4):
        s = {"P": 0.6, "L": 0.6 + 0.0 * i, "T": 0.5, "Pr": 0.5, "U": 0.5, "F": 0.5, "S": 0.05}
        traj.steps.append(_make_step(i + 1, s))

    assert 0.0 <= grade_t2(traj) <= 1.0
    assert 0.0 <= grade_t3(traj) <= 1.0
    assert 0.0 <= grade_t4(traj) <= 1.0
