"""Run a scenario through the state machine and emit a schema-v1 session log.

Python twin of FieldTestLogger.cs: same aggregation rules (best confidence, best
GPS accuracy, time to first locked state, outcome from terminal state), same
output schema. Tick rate is fixed at 4 Hz to convert tick index -> seconds,
matching the Unity controller's default.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone

from .mocks import Scenario
from .state_machine import LOCKED_STATES, FusionState, FusionStateMachine, FusionThresholds

TICK_SECONDS = 0.25  # 4 Hz, matching GeoFusionController.ticksPerSecond
GPS_NO_FIX_SENTINEL = 999.0  # schema wants a number; matches FieldTestLogger.cs


def run_session(
    scenario: Scenario,
    site_id: str = "oystermouth-chapel",
    thresholds: FusionThresholds | None = None,
    source: str = "synthetic",
    started_at: datetime | None = None,
) -> dict:
    machine = FusionStateMachine(thresholds)
    started = started_at or datetime.now(timezone.utc)

    best_conf = 0.0
    best_gps = math.inf
    time_to_lock = None
    relock_attempts = 0
    flags: set[str] = set()
    prev_state = machine.state

    for i, snapshot in enumerate(scenario.ticks):
        result = machine.step(snapshot)
        best_conf = max(best_conf, snapshot.visual_confidence)
        best_gps = min(best_gps, snapshot.gps_accuracy_m)
        flags.update(result.flags)
        if result.state in LOCKED_STATES and time_to_lock is None:
            time_to_lock = (i + 1) * TICK_SECONDS
        if result.state == FusionState.RELOCALIZING and prev_state != FusionState.RELOCALIZING:
            relock_attempts += 1
        prev_state = result.state

    duration = len(scenario.ticks) * TICK_SECONDS
    final = machine.state
    outcome = (
        "success" if final in (FusionState.FUSED_LOCK, FusionState.VISUAL_ONLY)
        else "degraded" if final == FusionState.GPS_ANCHOR_FALLBACK
        else "failure"
    )

    return {
        "schema_version": 1,
        "session_id": uuid.uuid4().hex,
        "site_id": site_id,
        "device_profile": "xreal_current_sdk",
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ended_at": (started + timedelta(seconds=duration)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gps_accuracy_m": GPS_NO_FIX_SENTINEL if math.isinf(best_gps) else round(best_gps, 3),
        "visual_confidence": round(best_conf, 3),
        "time_to_lock_s": round(time_to_lock if time_to_lock is not None else duration, 3),
        "drift_m": 0.0,  # no anchor pose stream in scenario replay; measured on device
        "lighting": scenario.lighting,
        "time_of_day_local": started.strftime("%H:%M"),
        "final_state": final.value,
        "outcome": outcome,
        "relock_attempts": relock_attempts,
        "flags": sorted(flags),
        "source": source,
        "notes": f"scenario={scenario.name}: {scenario.description}",
    }
