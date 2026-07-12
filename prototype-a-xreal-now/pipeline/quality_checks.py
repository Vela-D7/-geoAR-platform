"""Mandatory quality checks from the spec, as machine-readable pass/fail records.

Covered here (runnable on any mesh, tonight):
  - polygon count per LOD tier vs XR budget
  - LOD tiers strictly decreasing
  - scale accuracy vs a known reference measurement
  - basic integrity (non-empty, finite vertices)

Deferred to on-device / capture-time (documented, not silently skipped):
  - scan coverage/overlap, point density, capture drift  -> capture app job
  - draw calls, thermal, battery                          -> Unity profiling on device
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import trimesh

from .optimise import LOD_BUDGETS, PipelineResult
from .placeholder_mesh import REFERENCE_DIMS_M

SCALE_TOLERANCE = 0.05  # ±5% against the surveyed reference dimension


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


def check_integrity(mesh: trimesh.Trimesh) -> Check:
    ok = len(mesh.faces) > 0 and bool(np.isfinite(mesh.vertices).all())
    return Check("integrity", ok, f"faces={len(mesh.faces)}, finite_vertices={ok}")


def check_scale(mesh: trimesh.Trimesh, reference_dims_m: tuple[float, float, float] = REFERENCE_DIMS_M) -> Check:
    """Compare bounding-box extents to surveyed reference dimensions (sorted, axis-order-free)."""
    extents = np.sort(mesh.extents)
    reference = np.sort(np.asarray(reference_dims_m, dtype=float))
    rel_err = np.abs(extents - reference) / reference
    ok = bool((rel_err <= SCALE_TOLERANCE).all())
    return Check(
        "scale_vs_reference",
        ok,
        f"extents={extents.round(3).tolist()}m vs reference={reference.tolist()}m, "
        f"max_rel_err={rel_err.max():.3%} (tolerance {SCALE_TOLERANCE:.0%})",
    )


def check_lod_budgets(result: PipelineResult) -> list[Check]:
    checks = []
    for lod in result.lods:
        budget = LOD_BUDGETS[lod.tier]
        checks.append(
            Check(
                f"lod{lod.tier}_budget",
                lod.faces <= budget,
                f"{lod.faces} faces vs budget {budget}",
            )
        )
    counts = [l.faces for l in sorted(result.lods, key=lambda l: l.tier)]
    checks.append(
        Check(
            "lod_tiers_decreasing",
            all(a > b for a, b in zip(counts, counts[1:])),
            f"face counts by tier: {counts}",
        )
    )
    return checks


def run_all(mesh: trimesh.Trimesh, result: PipelineResult) -> dict:
    checks = [check_integrity(mesh), check_scale(mesh), *check_lod_budgets(result)]
    return {
        "passed": all(c.passed for c in checks),
        "checks": [vars(c) for c in checks],
        "deferred_to_device": [
            "scan_coverage_overlap", "point_density", "capture_drift",
            "draw_calls", "thermal", "battery",
        ],
    }
