# Migration Plan: Prototype A → Prototype B

What changes when the hardware arrives — and, more importantly, what doesn't.
Percentages of reuse are structural claims about this codebase, not effort
estimates.

## Ports directly (no rework)

| Asset | Why it ports |
|---|---|
| LiDAR capture + optimisation pipeline (`prototype-a-xreal-now/pipeline/`) | Outputs GLB LODs + quality report; nothing in it references the XREAL SDK. Spec quality check satisfied by construction: same output format for both prototypes. |
| Field-test log schema v1 (`shared-infrastructure/schemas/`) | Written for both generations from day one — `device_profile: "android_xr_aura"` is already an allowed value. The self-learning loop ingests Prototype B sessions with zero changes. |
| Shared backend (sites, anchors, thresholds, ingest, upload) | Anchor records store an opaque provider handle + WGS84 coordinates; a VPS geo-anchor ID stores identically to an XREAL map handle. |
| Fusion decision core (`FusionStateMachine.cs` + Python reference + tests) | Pure logic, no engine/SDK types. The tested decision table *is* the Prototype B fallback chain (see architecture doc §4). |
| Operator web app | Talks only to the shared backend. |
| Historical content renderer + LOD assets | Unity-side, engine-level code; no XREAL dependency. LOD budgets may need retuning for Aura's thermal envelope **[Needs verification]**. |

## Gets replaced (the two hardware-bound bindings)

| Prototype A binding | Prototype B replacement | Status |
|---|---|---|
| `XrealAnchorProvider` (XREAL SLAM + Spatial Anchors) | `ArCoreAnchorProvider` (ARCore/Android XR anchors) behind the same `INativeAnchorProvider` interface | Design only — **[Needs verification]** on Aura anchor-persistence semantics |
| MultiSet/custom visual fine lock behind `IVisualLocalizer` | VPS client (Niantic Spatial primary, MultiSet fallback) | Design only — see vps_comparison.md |
| `DeviceGpsProvider` (Unity location service via tether) | Android GNSS provider | Trivial binding; behaviour on Aura **[Needs verification]** |

## Needs a deliberate refactor (the only one identified)

`IVisualLocalizer` → `IGeospatialLocalizer`: Prototype A's fine lock returns a
target pose in session space; a VPS returns earth-anchored poses. The seam
gains a `coordinate_frame` field (`session` | `earth`), and Prototype A's
implementation declares `session`. Small, and it can be made in Prototype A's
codebase *before* Aura arrives so both prototypes share the seam from then on.

## New work unique to Prototype B

1. Stubbed Unity/Android XR project scaffold (deferred from tonight's
   documentation pass — first task, does not require hardware, only the
   public Android XR tooling **[Needs verification: tooling availability]**)
2. VPS partner site-onboarding (blocked on dev kit + partner engagement)
3. Device profiling: thermal/battery vs LOD budgets (blocked on hardware)
4. Unity digital twin of the site for remote debugging via recorded sessions
   (adopted from the Project Jade lesson; can start now, benefits Prototype A)

## Sequencing once dev kits open

```
dev kit access
  → scaffold compiles against real Android XR tooling
  → ArCoreAnchorProvider passes Prototype A's anchor lifecycle expectations
  → VPS partner bake-off on the mapped site (decision checklist in vps_comparison.md)
  → port fusion controller bindings; replay Prototype A's mock scenarios on-device
  → field sessions logged with device_profile=android_xr_aura
  → self-learning loop ingests both generations' sessions unchanged
```

The bar for "migration done": the same six fusion scenarios that pass in
Prototype A's test suite pass as on-device replays on Aura, and a field session
from each generation sits side by side in the shared field-test monitor.
