# Prototype A — Current XREAL SDK (Build Now)

Location-based historical AR on existing hardware: XREAL SLAM + Spatial Anchors,
GPS coarse lock, visual fine lock, historical model rendered aligned to the
physical site (test case: Oystermouth Castle Chapel).

Spec: [`../docs/geoAR_prototype_A_xreal_now.md`](../docs/geoAR_prototype_A_xreal_now.md)

## Layout

| Path | What it is | Verifiable without hardware? |
|---|---|---|
| `pipeline/` | Model optimisation pipeline: placeholder-mesh generation → decimation → LOD tiers → GLB export → quality report | **Yes** — runs and is tested in CI/container |
| `fusion/` | Geospatial fusion state machine (GPS + visual lock + anchor fallback), reference implementation | **Yes** — tested against mocked GPS/visual feeds |
| `unity/GeoARPrototypeA/` | Unity 2022.3 LTS project sources: Spatial Anchor manager, historical content renderer, C# port of the fusion state machine, field-test logger, editor scene builder | **No** — requires Unity Editor + XREAL device. Code-complete, compiles against an abstraction layer, **not device-verified yet** |
| `tests/` | pytest suite for `pipeline/` and `fusion/` | **Yes** |
| `output/` | Generated LODs + quality report (gitignored except manifest) | — |

## Run it

```bash
# from repo root
pip install trimesh numpy fast-simplification pytest

# 1. Optimisation pipeline: placeholder chapel mesh → LOD0/1/2 GLBs + quality report
python -m prototype-a-xreal-now.pipeline.cli   # or: cd prototype-a-xreal-now && python -m pipeline.cli

# 2. Fusion state machine demo against mocked sensor feeds
cd prototype-a-xreal-now && python -m fusion.demo

# 3. Tests
cd prototype-a-xreal-now && python -m pytest tests/ -v
```

## Honest status (what is real tonight)

- **Real and runnable:** optimisation pipeline (on a *placeholder* procedural mesh —
  the real Oystermouth LiDAR asset drops in as a `.glb`/`.ply` input, same code path),
  fusion decision logic with full fallback tree, field-test log emission matching the
  shared schema (`../shared-infrastructure/schemas/field_test_log.schema.json`).
- **Code-complete but unverified:** Unity/XREAL layer. Written against
  `INativeAnchorProvider` so it compiles without the XREAL SDK present; the NRSDK
  adapter is behind a define. Needs: Unity 2022.3 LTS, XREAL SDK import, device build.
  **[Needs verification on hardware before the 24 July demo.]**
- **Mocked tonight:** GPS accuracy and visual confidence values (no live device
  session possible in this environment). The mocks exercise every branch of the
  decision logic in the spec.
