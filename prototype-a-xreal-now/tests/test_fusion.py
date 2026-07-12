"""One test per spec decision rule, plus trajectory tests for every mock scenario
and schema validation of the emitted session logs."""

import json
import math
from pathlib import Path

import jsonschema
import pytest

from fusion import mocks
from fusion.session import run_session
from fusion.state_machine import (
    FusionState,
    FusionStateMachine,
    FusionThresholds,
    SensorSnapshot,
)

SCHEMA = json.loads(
    (Path(__file__).parents[2] / "shared-infrastructure/schemas/field_test_log.schema.json").read_text()
)


def snap(**kw):
    defaults = dict(gps_accuracy_m=5.0, target_exists_for_cell=True,
                    visual_confidence=0.0, tracking_ok=True, has_resolved_anchor=False)
    defaults.update(kw)
    return SensorSnapshot(**defaults)


class TestDecisionRules:
    """Each test maps 1:1 to a bullet in the spec's Localization Decision Logic."""

    def test_gps_good_and_visual_recognised_gives_fused_lock(self):
        m = FusionStateMachine()
        assert m.step(snap(gps_accuracy_m=4.0, visual_confidence=0.85)).state == FusionState.FUSED_LOCK

    def test_gps_poor_with_visual_gives_visual_only(self):
        m = FusionStateMachine()
        assert m.step(snap(gps_accuracy_m=40.0, visual_confidence=0.85)).state == FusionState.VISUAL_ONLY

    def test_low_visual_with_anchor_falls_back_and_flags_rescan(self):
        m = FusionStateMachine()
        result = m.step(snap(visual_confidence=0.30, has_resolved_anchor=True))
        assert result.state == FusionState.GPS_ANCHOR_FALLBACK
        assert "rescan_recommended" in result.flags

    def test_tracking_loss_goes_to_relocalizing_before_full_relock(self):
        m = FusionStateMachine()
        m.step(snap(visual_confidence=0.85))  # locked first
        result = m.step(snap(visual_confidence=0.85, tracking_ok=False))
        assert result.state == FusionState.RELOCALIZING
        assert "tracking_lost" in result.flags

    def test_no_target_for_cell_is_explicit_no_content(self):
        m = FusionStateMachine()
        # Even with perfect sensors: wrong cell must never render content.
        result = m.step(snap(visual_confidence=0.99, target_exists_for_cell=False))
        assert result.state == FusionState.NO_CONTENT

    def test_nothing_usable_stays_acquiring_never_fakes_a_lock(self):
        m = FusionStateMachine()
        result = m.step(snap(gps_accuracy_m=math.inf, visual_confidence=0.50))
        assert result.state == FusionState.ACQUIRING
        assert not m.is_locked

    def test_no_target_beats_tracking_loss_in_rule_order(self):
        m = FusionStateMachine()
        result = m.step(snap(target_exists_for_cell=False, tracking_ok=False))
        assert result.state == FusionState.NO_CONTENT

    def test_thresholds_are_configurable_per_site(self):
        strict = FusionStateMachine(FusionThresholds(visual_confidence_min=0.90))
        assert strict.step(snap(visual_confidence=0.85)).state == FusionState.ACQUIRING
        loose = FusionStateMachine(FusionThresholds(visual_confidence_min=0.50))
        assert loose.step(snap(visual_confidence=0.55)).state == FusionState.FUSED_LOCK


class TestScenarioTrajectories:
    def run(self, factory):
        scenario = factory()
        m = FusionStateMachine()
        return scenario, [m.step(t).state for t in scenario.ticks]

    def test_clean_fused_lock_ends_fused(self):
        _, states = self.run(mocks.clean_fused_lock)
        assert states[-1] == FusionState.FUSED_LOCK
        assert states[0] == FusionState.ACQUIRING  # doesn't lock instantly

    def test_urban_canyon_never_fuses_but_locks_visually(self):
        _, states = self.run(mocks.urban_canyon)
        assert FusionState.FUSED_LOCK not in states
        assert states[-1] == FusionState.VISUAL_ONLY

    def test_poor_lighting_degrades_to_anchor_fallback(self):
        _, states = self.run(mocks.poor_lighting_fallback)
        assert states[1] == FusionState.FUSED_LOCK      # locked while light was good
        assert states[-1] == FusionState.GPS_ANCHOR_FALLBACK

    def test_tracking_loss_recovers_via_anchor_then_refuses(self):
        _, states = self.run(mocks.tracking_loss_relocalization)
        assert FusionState.RELOCALIZING in states
        assert states[-1] == FusionState.FUSED_LOCK     # full recovery

    def test_no_target_cell_reports_no_content_every_tick(self):
        _, states = self.run(mocks.no_target_cell)
        assert set(states) == {FusionState.NO_CONTENT}

    def test_dead_sensors_stay_acquiring(self):
        _, states = self.run(mocks.gps_dead_no_anchor)
        assert set(states) == {FusionState.ACQUIRING}


class TestSessionLogs:
    @pytest.mark.parametrize("factory", mocks.ALL_SCENARIOS, ids=lambda f: f.__name__)
    def test_every_scenario_log_validates_against_shared_schema(self, factory):
        record = run_session(factory())
        jsonschema.validate(record, SCHEMA)

    def test_synthetic_provenance_is_never_field(self):
        record = run_session(mocks.clean_fused_lock())
        assert record["source"] == "synthetic"

    def test_outcomes_match_terminal_states(self):
        assert run_session(mocks.clean_fused_lock())["outcome"] == "success"
        assert run_session(mocks.poor_lighting_fallback())["outcome"] == "degraded"
        assert run_session(mocks.no_target_cell())["outcome"] == "failure"
