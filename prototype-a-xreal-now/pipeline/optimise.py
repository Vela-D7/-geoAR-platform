"""Decimation and LOD generation.

Input: any trimesh-loadable mesh (.glb/.gltf/.ply/.obj — the real LiDAR export)
or the procedural placeholder. Output: LOD0/1/2 GLBs + manifest.

Texture bake is a stub tonight: this environment has no Blender. The interface
(`bake_textures`) is defined and called so the pipeline shape is final; the real
implementation is a Blender headless job (see `bake_textures` docstring).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import trimesh

from .placeholder_mesh import build_placeholder_chapel

# Per-tier triangle budgets for XR glasses (see spec: "polygon count against
# XR glasses performance budget"). Conservative for a single hero asset on
# phone-class silicon driving the glasses.
LOD_BUDGETS = {0: 100_000, 1: 25_000, 2: 5_000}


@dataclass
class LodResult:
    tier: int
    faces: int
    vertices: int
    path: str


@dataclass
class PipelineResult:
    input_faces: int
    input_vertices: int
    lods: list[LodResult] = field(default_factory=list)
    texture_bake: str = "stub"  # "stub" until the Blender job exists

    def to_manifest(self) -> dict:
        return {
            "input": {"faces": self.input_faces, "vertices": self.input_vertices},
            "lods": [vars(l) for l in self.lods],
            "texture_bake": self.texture_bake,
            "budgets": LOD_BUDGETS,
        }


def load_input_mesh(path: str | Path | None) -> trimesh.Trimesh:
    """Load the real asset if a path is given, else the placeholder chapel."""
    if path is None:
        return build_placeholder_chapel()
    loaded = trimesh.load(str(path), force="mesh")
    if not isinstance(loaded, trimesh.Trimesh) or len(loaded.faces) == 0:
        raise ValueError(f"{path} did not load as a non-empty triangle mesh")
    return loaded


def clean_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Basic scan cleanup: drop degenerate faces, unreferenced vertices, tiny islands."""
    mesh = mesh.copy()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    # Keep only components with a meaningful share of the geometry (scan debris filter).
    components = mesh.split(only_watertight=False)
    if len(components) > 1:
        biggest = max(len(c.faces) for c in components)
        keep = [c for c in components if len(c.faces) >= 0.01 * biggest]
        mesh = trimesh.util.concatenate(keep)
    return mesh


def decimate_to(mesh: trimesh.Trimesh, target_faces: int) -> trimesh.Trimesh:
    """Quadric decimation to at most target_faces (no-op if already under)."""
    if len(mesh.faces) <= target_faces:
        return mesh.copy()
    simplified = mesh.simplify_quadric_decimation(face_count=target_faces)
    return simplified


def bake_textures(mesh: trimesh.Trimesh) -> str:
    """STUB — texture bake requires the Blender headless workflow.

    Real implementation: export LOD0 to Blender, project source scan textures /
    vertex colours onto a UV-unwrapped low-poly target, bake diffuse + normal
    at 2048px, KTX2-compress. Tracked as a pre-24-July task; the pipeline
    manifest records "stub" until it lands so nothing can silently pretend
    baking happened.
    """
    return "stub"


def run_pipeline(input_path: str | Path | None, out_dir: str | Path) -> PipelineResult:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    mesh = clean_mesh(load_input_mesh(input_path))
    result = PipelineResult(input_faces=len(mesh.faces), input_vertices=len(mesh.vertices))

    for tier, budget in LOD_BUDGETS.items():
        lod = decimate_to(mesh, budget)
        path = out / f"chapel_lod{tier}.glb"
        lod.export(path)
        result.lods.append(
            LodResult(tier=tier, faces=len(lod.faces), vertices=len(lod.vertices), path=str(path))
        )

    result.texture_bake = bake_textures(mesh)

    (out / "manifest.json").write_text(json.dumps(result.to_manifest(), indent=2))
    return result
