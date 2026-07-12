# GeoAR Prototype B — stubbed Unity/Android XR scaffold

**This is a scaffold, not a build.** No XREAL Aura hardware or Android XR
dev kit exists in our hands (device ships Fall 2026). Everything here either
compiles without any XR SDK present or is explicitly gated behind the
`ANDROID_XR_PRESENT` define with the SDK calls left unwritten.

## What's here vs what ports

| Piece | Origin |
|---|---|
| `IGeospatialLocalizer` | The one refactor the migration plan identifies: the fine-lock seam generalised with a `CoordinateFrame` so a session-space matcher (Prototype A) and an earth-anchored VPS (Prototype B) share it |
| `ArCoreAnchorProvider` | Stub for `INativeAnchorProvider` — the same interface Prototype A binds to the XREAL SDK. **[Needs verification]** against real Android XR anchor semantics on Aura |
| `VpsLocalizerStub` | The VPS partner seam (Niantic Spatial primary / MultiSet fallback — see `../../docs/vps_comparison.md`). Credentials are server-side by design; the device receives short-lived session tokens from our backend |
| Fusion core, content renderer, field-test logger | **Not duplicated here.** They port unchanged from `prototype-a-xreal-now/unity/.../Scripts/` per the migration plan — copying them now would just fork them |

## First tasks when dev-kit access opens

1. Fill `Packages/manifest.json` versions against the real Android XR tooling
   (all currently **[Needs verification]**), confirm the project compiles.
2. Implement `ArCoreAnchorProvider` and run Prototype A's anchor lifecycle
   expectations against it.
3. Wire the chosen VPS SDK behind `IGeospatialLocalizer` and replay Prototype
   A's six fusion mock scenarios on-device.
