"""Procedural placeholder for the Oystermouth Castle Chapel mesh.

Stands in for the real LiDAR-derived asset so the optimisation pipeline is
exercised end-to-end tonight. Deliberately built to LiDAR-like density
(subdivided to a few hundred thousand triangles) so decimation does real work.

Real-world footprint approximates the chapel: ~10m long, ~6m wide, walls ~5m,
roof ridge ~8m. The scale quality-check references these dimensions.
"""

from __future__ import annotations

import numpy as np
import trimesh

# Reference dimensions (metres) used by quality_checks.check_scale.
REFERENCE_DIMS_M = (10.0, 6.0, 8.0)  # length (x), width (y), ridge height (z)


def _gabled_block(length: float, width: float, wall_h: float, ridge_h: float) -> trimesh.Trimesh:
    """A box nave with a triangular-prism gabled roof, as one watertight mesh."""
    hl, hw = length / 2.0, width / 2.0
    vertices = np.array(
        [
            # floor
            [-hl, -hw, 0.0],
            [hl, -hw, 0.0],
            [hl, hw, 0.0],
            [-hl, hw, 0.0],
            # eaves
            [-hl, -hw, wall_h],
            [hl, -hw, wall_h],
            [hl, hw, wall_h],
            [-hl, hw, wall_h],
            # ridge line
            [-hl, 0.0, ridge_h],
            [hl, 0.0, ridge_h],
        ]
    )
    faces = np.array(
        [
            # floor
            [0, 2, 1], [0, 3, 2],
            # long walls
            [0, 1, 5], [0, 5, 4],
            [2, 3, 7], [2, 7, 6],
            # roof planes
            [4, 5, 9], [4, 9, 8],
            [6, 7, 8], [6, 8, 9],
            # gable ends (wall rectangle + roof triangle)
            [1, 2, 6], [1, 6, 5], [5, 6, 9],
            [3, 0, 4], [3, 4, 7], [7, 4, 8],
        ]
    )
    return trimesh.Trimesh(vertices=vertices, faces=faces, process=True)


def build_placeholder_chapel(target_min_faces: int = 200_000) -> trimesh.Trimesh:
    """Chapel-shaped watertight mesh subdivided to LiDAR-like triangle density."""
    length, width, ridge = REFERENCE_DIMS_M
    mesh = _gabled_block(length=length, width=width, wall_h=5.0, ridge_h=ridge)
    while len(mesh.faces) < target_min_faces:
        mesh = mesh.subdivide()
    # Small vertex jitter so the surface is not perfectly planar — decimators
    # collapse ideal planes to near-zero faces, which a scanned mesh never is.
    rng = np.random.default_rng(seed=42)
    jitter = rng.normal(scale=0.004, size=mesh.vertices.shape)  # ~4mm noise, LiDAR-ish
    mesh = trimesh.Trimesh(vertices=mesh.vertices + jitter, faces=mesh.faces, process=False)
    return mesh
