# GeoAR Prototype A — Unity project setup

Status: **code-complete, not yet verified in Unity or on device.** This checklist
is the exact path from this repo to a running build; every unchecked box is real
remaining work, not polish.

## Dev-machine setup

1. Unity **2022.3 LTS** (match the dissertation pipeline editor version).
2. Open `unity/GeoARPrototypeA/`. UPM restores glTFast + OpenXR from
   `Packages/manifest.json`.
3. Import the **XREAL SDK** (vendor download — .unitypackage / UPM tarball; not
   vendored in this repo, not on the UPM registry).
4. Add `XREAL_SDK_PRESENT` to *Project Settings → Player → Scripting Define
   Symbols* and fill in the NRSDK calls in
   `Assets/Scripts/Anchors/XrealAnchorProvider.cs`
   (marked **[Needs verification]** against the installed SDK version).
5. Run the optimisation pipeline (`python -m pipeline.cli`), copy
   `output/chapel_lod{0,1,2}.glb` into `Assets/Models/`.
6. Menu: **GeoAR → Build Prototype A Scene (Editor Sim)** — assembles and saves
   the scene with all components wired.

## Verification ladder (in order)

- [ ] Scripts compile with no SDK imported (interface + sim providers only)
- [ ] Play mode: MockSensorProvider drives FusionStateMachine through
      FUSED_LOCK / VISUAL_ONLY / GPS_ANCHOR_FALLBACK / NO_CONTENT by editing
      mock values in the inspector; content root shows/hides accordingly
- [ ] Play mode: stop + restart resolves the persisted sim anchor
      (re-localization path) and a session line lands in
      `persistentDataPath/geoar_field_tests.jsonl`
- [ ] XREAL SDK imported, `XrealAnchorProvider` filled in, compiles with
      `XREAL_SDK_PRESENT`
- [ ] Device build on the actual XREAL glasses: SLAM anchor place/persist/resolve
- [ ] Field test at the site with real GPS + visual lock; logger `source` flipped
      to `"field"`

## Swaps for the device build

| Editor sim | Device |
|---|---|
| `EditorSimAnchorProvider` | `XrealAnchorProvider` |
| `MockSensorProvider` (both roles) | `DeviceGpsProvider` + MultiSet/custom `IVisualLocalizer` |
| logger `source = "replay"` | `source = "field"` |

The visual fine-lock provider (MultiSet AI SDK vs custom feature matcher) is an
open integration task — `IVisualLocalizer` is the seam where it lands.
