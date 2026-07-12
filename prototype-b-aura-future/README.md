# Prototype B — XREAL Aura / Android XR (Future Architecture)

**Status: architecture only. Nothing in this directory is built, running, or
device-tested — the target hardware (XREAL Aura, powered by Android XR) ships
Fall 2026.** Everything here is framed as *designed for* / *planned*, and
anything not publicly confirmed is tagged **[Needs verification]**.

Spec: [`../docs/geoAR_prototype_B_aura_future.md`](../docs/geoAR_prototype_B_aura_future.md)

## Contents

| Document | What it covers |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | System data flow, tracking-vs-geospatial layer separation, anchor lifecycle, fallback chain — with diagrams |
| [`docs/vps_comparison.md`](docs/vps_comparison.md) | Niantic Spatial vs MultiSet AI, one-page comparison with a written recommendation |
| [`docs/migration_from_prototype_a.md`](docs/migration_from_prototype_a.md) | What ports directly from Prototype A, what gets replaced, what's new |

The stubbed Unity/Android XR project scaffold from the spec's MVP boundary is
deliberately deferred (documentation-first pass); it is listed in the migration
doc as the first task once dev-kit access opens.

## The one-paragraph pitch

Prototype B keeps everything that is already working in Prototype A — the LiDAR
capture/optimisation pipeline, the shared backend, the field-test log schema,
and the fusion decision logic — and swaps the two hardware-bound layers: the
older XREAL SDK's SLAM + Spatial Anchors is replaced by ARCore/Android XR
native tracking, and the single-site visual fine lock is replaced by a
VPS-grade geospatial anchoring service (Niantic Spatial as primary candidate,
MultiSet AI as fallback — see the comparison doc). Prototype A's provider
interfaces were written for exactly this swap.
