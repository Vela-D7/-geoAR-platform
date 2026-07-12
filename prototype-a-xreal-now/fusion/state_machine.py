"""Fusion state machine: GPS coarse lock + visual fine lock + Spatial Anchor fallback.

Rules in spec order (docs/geoAR_prototype_A_xreal_now.md, "Localization Decision
Logic"). Keep in lockstep with FusionStateMachine.cs — same states, same rule
order, same threshold names as the shared backend's per-site config.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum


class FusionState(str, Enum):
    ACQUIRING = "ACQUIRING"
    FUSED_LOCK = "FUSED_LOCK"
    VISUAL_ONLY = "VISUAL_ONLY"
    GPS_ANCHOR_FALLBACK = "GPS_ANCHOR_FALLBACK"
    RELOCALIZING = "RELOCALIZING"
    NO_CONTENT = "NO_CONTENT"


LOCKED_STATES = frozenset(
    {FusionState.FUSED_LOCK, FusionState.VISUAL_ONLY, FusionState.GPS_ANCHOR_FALLBACK}
)


@dataclass(frozen=True)
class SensorSnapshot:
    gps_accuracy_m: float = math.inf  # reported accuracy radius; inf = no fix
    target_exists_for_cell: bool = True
    visual_confidence: float = 0.0  # 0..1
    tracking_ok: bool = True
    has_resolved_anchor: bool = False


@dataclass
class FusionThresholds:
    """Per-site config; visual_confidence_min is what the self-learning loop tunes."""

    gps_accuracy_good_m: float = 10.0
    visual_confidence_min: float = 0.70


@dataclass
class StepResult:
    state: FusionState
    flags: list[str] = field(default_factory=list)


class FusionStateMachine:
    def __init__(self, thresholds: FusionThresholds | None = None) -> None:
        self.thresholds = thresholds or FusionThresholds()
        self.state = FusionState.ACQUIRING

    def step(self, s: SensorSnapshot) -> StepResult:
        """Advance one tick. Rule order matters and matches the spec:

        1. No target for this GPS cell     -> NO_CONTENT (explicit, never silent).
        2. Tracking lost mid-session       -> RELOCALIZING (anchor first, not full re-lock).
        3. GPS good AND visual recognised  -> FUSED_LOCK.
        4. GPS poor but visual recognised  -> VISUAL_ONLY.
        5. Visual low, anchor available    -> GPS_ANCHOR_FALLBACK + rescan_recommended.
        6. Otherwise                       -> ACQUIRING.
        """
        result = StepResult(state=FusionState.ACQUIRING)

        if not s.target_exists_for_cell:
            result.state = FusionState.NO_CONTENT
        elif not s.tracking_ok:
            result.state = FusionState.RELOCALIZING
            result.flags.append("tracking_lost")
        else:
            gps_good = s.gps_accuracy_m <= self.thresholds.gps_accuracy_good_m
            visual_ok = s.visual_confidence >= self.thresholds.visual_confidence_min

            if visual_ok:
                result.state = FusionState.FUSED_LOCK if gps_good else FusionState.VISUAL_ONLY
            elif s.has_resolved_anchor:
                result.state = FusionState.GPS_ANCHOR_FALLBACK
                result.flags.append("rescan_recommended")
            # else: stay ACQUIRING

        self.state = result.state
        return result

    @property
    def is_locked(self) -> bool:
        return self.state in LOCKED_STATES
