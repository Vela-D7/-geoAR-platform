"""Self-learning loop v0: rule-based visual-confidence threshold adjustment.

This is v0 by design — a transparent, bounded, reversible rule set over the last
N sessions per site. It is NOT a trained model; a learned classifier over
lighting/pose features is a post-MVP milestone (see shared infrastructure doc).

Rules (evaluated on the last N sessions of a site, newest first):

  LOOSEN  — sessions are being rejected by the cutoff (confidence lands in the
            band just below it) yet their anchor-fallback outcome was degraded
            with LOW drift, i.e. the render was actually fine. If enough recent
            sessions fit that pattern, lower the cutoff one step: we are turning
            away locks that would have worked.

  TIGHTEN — sessions that PASSED the cutoff ended in failure or high drift,
            i.e. the cutoff is admitting bad locks. Raise it one step.

  HOLD    — anything else, including "not enough data" (< MIN_SESSIONS).

Every change is one bounded STEP, clamped to [MIN_CUTOFF, MAX_CUTOFF], and
written as a new threshold version (append-only) so any adjustment can be
rolled back by re-issuing a previous version.
"""

from __future__ import annotations

from dataclasses import dataclass

WINDOW_N = 10          # sessions considered
MIN_SESSIONS = 6       # below this: HOLD (avoid reacting to noise)
STEP = 0.05            # one bounded adjustment per cycle
MIN_CUTOFF, MAX_CUTOFF = 0.40, 0.90
NEAR_MISS_BAND = 0.15  # "just below cutoff" band width
LOW_DRIFT_M = 0.5      # drift under this = render was acceptable
LOOSEN_TRIGGER = 0.5   # fraction of window that must be near-miss-but-fine
TIGHTEN_TRIGGER = 0.3  # fraction of window that must be passed-but-bad


@dataclass
class Adjustment:
    action: str  # "loosen" | "tighten" | "hold"
    old_cutoff: float
    new_cutoff: float
    reason: str
    evidence: dict


def evaluate(sessions: list[dict], current_cutoff: float) -> Adjustment:
    """sessions: field-test records (dicts with visual_confidence, outcome,
    drift_m, final_state), newest first; only the newest WINDOW_N are used."""
    window = sessions[:WINDOW_N]
    hold = lambda reason, **ev: Adjustment("hold", current_cutoff, current_cutoff, reason, ev)  # noqa: E731

    if len(window) < MIN_SESSIONS:
        return hold(f"only {len(window)} sessions in window; need {MIN_SESSIONS}", window=len(window))

    near_miss_but_fine = [
        s for s in window
        if current_cutoff - NEAR_MISS_BAND <= s["visual_confidence"] < current_cutoff
        and s["outcome"] == "degraded"
        and s["drift_m"] <= LOW_DRIFT_M
    ]
    passed_but_bad = [
        s for s in window
        if s["visual_confidence"] >= current_cutoff
        and (s["outcome"] == "failure" or s["drift_m"] > LOW_DRIFT_M)
    ]

    evidence = {
        "window": len(window),
        "near_miss_but_fine": len(near_miss_but_fine),
        "passed_but_bad": len(passed_but_bad),
        "cutoff": current_cutoff,
    }

    # Tighten wins ties: admitting bad locks is worse than rejecting good ones.
    if len(passed_but_bad) / len(window) >= TIGHTEN_TRIGGER:
        new = min(MAX_CUTOFF, round(current_cutoff + STEP, 3))
        if new != current_cutoff:
            return Adjustment(
                "tighten", current_cutoff, new,
                f"{len(passed_but_bad)}/{len(window)} recent sessions passed the cutoff but "
                f"failed or drifted >{LOW_DRIFT_M}m — cutoff admits bad locks",
                evidence,
            )
        return hold("tighten indicated but cutoff already at maximum", **evidence)

    if len(near_miss_but_fine) / len(window) >= LOOSEN_TRIGGER:
        new = max(MIN_CUTOFF, round(current_cutoff - STEP, 3))
        if new != current_cutoff:
            return Adjustment(
                "loosen", current_cutoff, new,
                f"{len(near_miss_but_fine)}/{len(window)} recent sessions landed just below the "
                f"cutoff yet rendered acceptably via fallback (drift <={LOW_DRIFT_M}m) — "
                "cutoff rejects locks that would have worked",
                evidence,
            )
        return hold("loosen indicated but cutoff already at minimum", **evidence)

    return hold("recent sessions consistent with current cutoff", **evidence)
