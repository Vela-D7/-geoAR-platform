"""Optimisation pipeline: LOD budgets, tier ordering, scale check, GLB round-trip."""

import numpy as np
import pytest
import trimesh

from pipeline import optimise, quality_checks
from pipeline.placeholder_mesh import REFERENCE_DIMS_M, build_placeholder_chapel


@pytest.fixture(scope="module")
def chapel():
    # Smaller target than production keeps the suite fast; still forces real decimation.
    return build_placeholder_chapel(target_min_faces=60_000)


@pytest.fixture(scope="module")
def result(chapel, tmp_path_factory):
    out = tmp_path_factory.mktemp("lods")
    # Feed the prebuilt mesh through the same path run_pipeline uses.
    mesh = optimise.clean_mesh(chapel)
    res = optimise.PipelineResult(input_faces=len(mesh.faces), input_vertices=len(mesh.vertices))
    for tier, budget in optimise.LOD_BUDGETS.items():
        lod = optimise.decimate_to(mesh, budget)
        path = out / f"lod{tier}.glb"
        lod.export(path)
        res.lods.append(optimise.LodResult(tier, len(lod.faces), len(lod.vertices), str(path)))
    return res


def test_placeholder_is_dense_enough_to_exercise_decimation(chapel):
    assert len(chapel.faces) >= 60_000


def test_all_lods_within_budget(result):
    for lod in result.lods:
        assert lod.faces <= optimise.LOD_BUDGETS[lod.tier], f"LOD{lod.tier} over budget"


def test_lod_tiers_strictly_decreasing(result):
    counts = [l.faces for l in sorted(result.lods, key=lambda l: l.tier)]
    assert all(a > b for a, b in zip(counts, counts[1:]))


def test_glb_round_trip(result):
    for lod in result.lods:
        loaded = trimesh.load(lod.path, force="mesh")
        assert len(loaded.faces) == lod.faces


def test_scale_check_passes_on_reference_mesh(chapel):
    assert quality_checks.check_scale(chapel).passed


def test_scale_check_fails_on_wrongly_scaled_mesh(chapel):
    shrunk = chapel.copy()
    shrunk.apply_scale(0.5)  # e.g. unit error in export
    assert not quality_checks.check_scale(shrunk).passed


def test_reference_dims_match_placeholder_extents(chapel):
    assert np.allclose(np.sort(chapel.extents), np.sort(REFERENCE_DIMS_M), rtol=0.02)


def test_decimate_noop_when_under_budget():
    small = trimesh.creation.box()
    out = optimise.decimate_to(small, 1000)
    assert len(out.faces) == len(small.faces)
