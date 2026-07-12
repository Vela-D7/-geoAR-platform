"""Rule tests for self-learning v0: each rule fired by a constructed window,
plus bounds/clamps/hysteresis."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from self_learning.v0 import (
    LOW_DRIFT_M,
    MAX_CUTOFF,
    MIN_CUTOFF,
    MIN_SESSIONS,
    STEP,
    evaluate,
)

CUTOFF = 0.70


def session(conf, outcome="success", drift=0.1):
    return {"visual_confidence": conf, "outcome": outcome, "drift_m": drift, "final_state": None}


def near_miss_fine(n, cutoff=CUTOFF):
    return [session(cutoff - 0.05, outcome="degraded", drift=0.2) for _ in range(n)]


def passed_bad(n, cutoff=CUTOFF):
    return [session(min(1.0, cutoff + 0.05), outcome="failure", drift=1.2) for _ in range(n)]


def healthy(n):
    return [session(0.85, outcome="success", drift=0.1) for _ in range(n)]


def test_holds_below_min_sessions():
    result = evaluate(near_miss_fine(MIN_SESSIONS - 1), CUTOFF)
    assert result.action == "hold"
    assert "need" in result.reason


def test_loosens_on_near_miss_but_fine_pattern():
    result = evaluate(near_miss_fine(6) + healthy(4), CUTOFF)
    assert result.action == "loosen"
    assert result.new_cutoff == round(CUTOFF - STEP, 3)


def test_tightens_on_passed_but_bad_pattern():
    result = evaluate(passed_bad(4) + healthy(6), CUTOFF)
    assert result.action == "tighten"
    assert result.new_cutoff == round(CUTOFF + STEP, 3)


def test_holds_on_healthy_window():
    assert evaluate(healthy(10), CUTOFF).action == "hold"


def test_tighten_wins_over_loosen_when_both_fire():
    result = evaluate(passed_bad(3) + near_miss_fine(7), CUTOFF)
    assert result.action == "tighten"


def test_loosen_clamped_at_min_cutoff():
    result = evaluate(near_miss_fine(10, cutoff=MIN_CUTOFF), MIN_CUTOFF)
    assert result.action == "hold"
    assert "minimum" in result.reason


def test_tighten_clamped_at_max_cutoff():
    result = evaluate(passed_bad(10, cutoff=MAX_CUTOFF), MAX_CUTOFF)
    assert result.action == "hold"
    assert "maximum" in result.reason


def test_high_drift_near_misses_do_not_loosen():
    bad_drift = [session(CUTOFF - 0.05, outcome="degraded", drift=LOW_DRIFT_M + 0.5) for _ in range(8)]
    assert evaluate(bad_drift + healthy(2), CUTOFF).action == "hold"


def test_only_window_n_newest_considered():
    # Newest 10 healthy, older near-misses must be ignored.
    result = evaluate(healthy(10) + near_miss_fine(20), CUTOFF)
    assert result.action == "hold"
