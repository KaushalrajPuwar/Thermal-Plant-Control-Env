import math
from utils.schemas import EpisodeTrajectory
from graders.task1_grader import grade as grade_t1
from graders.task4_grader import grade as grade_t4
from graders._metrics import compute_RT, compute_TE

def test_empty_trajectory():
    traj = EpisodeTrajectory(task="task1", benchmark="test", model="tester")
    score = grade_t1(traj)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    
def test_task4_never_recovered():
    traj = EpisodeTrajectory(task="task4", benchmark="test", model="tester")
    from tests.unit.test_graders import _make_step
    # P is 0.5, L is 0.7, diff = 0.2 >= 0.1 -> never recovered
    traj.steps.append(_make_step(1, {"P": 0.5, "L": 0.7, "T": 0.5, "Pr": 0.5, "U": 0.5, "F": 0.5, "S": 0}))
    traj.steps.append(_make_step(2, {"P": 0.5, "L": 0.7, "T": 0.5, "Pr": 0.5, "U": 0.5, "F": 0.5, "S": 0}))
    
    rt = compute_RT(traj)
    assert math.isclose(rt, 2.0)
    score = grade_t4(traj)
    # Norm_RT should be 1.0 (2 / 2), penalty = 0.3 * 1.0 = 0.3
    # other penalties 0
    assert score <= 0.7
