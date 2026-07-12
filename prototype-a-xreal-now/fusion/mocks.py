"""Mocked GPS-accuracy and visual-confidence feeds.

No live device session is possible in this environment, so these scenarios stand
in for tonight's field data. Each is a deterministic tick sequence shaped after a
failure case named in the spec, and each drives the state machine through the
branch that case is supposed to exercise. Everything downstream of these mocks
(the decision logic, logging, self-learning ingestion) is real code.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .state_machine import SensorSnapshot


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    ticks: tuple[SensorSnapshot, ...]
    lighting: str = "daylight"


def _t(gps=5.0, target=True, vis=0.0, tracking=True, anchor=False) -> SensorSnapshot:
    return SensorSnapshot(
        gps_accuracy_m=gps,
        target_exists_for_cell=target,
        visual_confidence=vis,
        tracking_ok=tracking,
        has_resolved_anchor=anchor,
    )


def clean_fused_lock() -> Scenario:
    """Happy path: GPS settles, recogniser ramps up, fused fine lock holds."""
    ticks = (
        _t(gps=25.0, vis=0.0),          # walking up: coarse fix only
        _t(gps=12.0, vis=0.20),
        _t(gps=6.0, vis=0.55),
        _t(gps=4.0, vis=0.82),          # both above threshold -> FUSED_LOCK
        _t(gps=4.0, vis=0.88, anchor=True),
        _t(gps=3.5, vis=0.90, anchor=True),
    )
    return Scenario("clean_fused_lock", "GPS + visual both good; fused fine lock", ticks)


def urban_canyon() -> Scenario:
    """Spec: 'GPS accuracy is poor (urban canyon, indoors) -> rely on visual'."""
    ticks = (
        _t(gps=45.0, vis=0.10),
        _t(gps=38.0, vis=0.50),
        _t(gps=41.0, vis=0.79),         # visual locks while GPS never does
        _t(gps=44.0, vis=0.84, anchor=True),
    )
    return Scenario("urban_canyon", "GPS poor throughout; visual-only fine lock", ticks)


def poor_lighting_fallback() -> Scenario:
    """Spec: 'visual confidence low (poor lighting...) -> GPS + last anchor, flag re-scan'."""
    ticks = (
        _t(gps=5.0, vis=0.75, anchor=False),   # initial lock earlier in the day
        _t(gps=5.0, vis=0.78, anchor=True),
        _t(gps=6.0, vis=0.40, anchor=True),    # dusk: confidence collapses
        _t(gps=6.0, vis=0.31, anchor=True),    # -> anchor fallback + rescan flag
        _t(gps=6.0, vis=0.28, anchor=True),
    )
    return Scenario("poor_lighting_fallback", "Visual degrades; anchor fallback + rescan flag", ticks, lighting="dusk")


def tracking_loss_relocalization() -> Scenario:
    """Spec: 'tracking lost mid-session -> attempt Spatial Anchor re-localization'."""
    ticks = (
        _t(gps=4.0, vis=0.85, anchor=True),          # fused lock
        _t(gps=4.0, vis=0.85, anchor=True, tracking=False),  # occlusion/fast motion
        _t(gps=4.0, vis=0.0, anchor=True, tracking=False),
        _t(gps=4.0, vis=0.30, anchor=True),          # tracking back, anchor rescues
        _t(gps=4.0, vis=0.81, anchor=True),          # recogniser recovers -> fused again
    )
    return Scenario("tracking_loss_relocalization", "Mid-session tracking loss and recovery", ticks)


def no_target_cell() -> Scenario:
    """Spec: 'no recognition target for the current GPS cell -> explicit no-content'."""
    ticks = (
        _t(gps=8.0, vis=0.0, target=False),
        _t(gps=6.0, vis=0.0, target=False),
    )
    return Scenario("no_target_cell", "Wrong location: clear no-content state", ticks)


def gps_dead_no_anchor() -> Scenario:
    """Worst case: no GPS fix, weak visual, nothing persisted — must keep ACQUIRING, never fake a lock."""
    ticks = (
        _t(gps=math.inf, vis=0.10),
        _t(gps=math.inf, vis=0.35),
        _t(gps=math.inf, vis=0.50),
    )
    return Scenario("gps_dead_no_anchor", "No fix, weak visual, no anchor: stays acquiring", ticks, lighting="overcast")


ALL_SCENARIOS = (
    clean_fused_lock,
    urban_canyon,
    poor_lighting_fallback,
    tracking_loss_relocalization,
    no_target_cell,
    gps_dead_no_anchor,
)
