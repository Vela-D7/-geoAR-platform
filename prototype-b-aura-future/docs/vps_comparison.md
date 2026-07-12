# VPS Partner Comparison — Niantic Spatial vs MultiSet AI

One page, per the MVP boundary. Factual basis is limited to what the project
spec records as confirmed; everything else is tagged. Neither option has been
tested against our site — that is impossible before dev-kit access.

## Comparison

| Criterion | Niantic Spatial | MultiSet AI |
|---|---|---|
| **Glasses-generation precedent** | Strongest available: multi-year strategic partnership with Snap to build VPS for AR glasses; **Project Jade** demo (Snap Spectacles + VPS + persistent 6DoF anchors, built in 8 weeks, shown live at AWE) is the closest real-world precedent for our exact architecture | Lists smart glasses among supported SDK targets; no equivalent public flagship demo cited in our research |
| **Localization accuracy** | Centimeter-level claimed in the Project Jade context | ≤5 cm claimed |
| **Map creation from our assets** | Localization quality is a function of their underlying map data (their own published lesson from Jade); site onboarding workflow for our chapel **[Needs verification]** | Accepts LiDAR, E57 and Scaniverse/Polycam captures directly — i.e. our existing Prototype A capture pipeline output could seed the map **[workflow fit still Needs verification]** |
| **Cross-prototype reuse** | Prototype B only | Could serve as the visual fine-lock vendor on Prototype A *today* and the VPS layer on Prototype B — one vendor across both generations |
| **Android XR / Aura support** | Not publicly confirmed for Aura specifically **[Needs verification]** | Not publicly confirmed for Aura specifically **[Needs verification]** |
| **Coverage of our site (Oystermouth)** | **[Needs verification]** — unknown for both; a small heritage site will need bespoke mapping either way | **[Needs verification]** |
| **Commercial terms** | **[Needs verification]** | **[Needs verification]** |
| **Vendor risk** | Larger, proven at scale; roadmap driven by big partners (Snap) | Smaller vendor; more likely to engage closely with a small team, higher continuity risk |

*(A free coarse layer — Google ARCore Geospatial API, Street View-based — is
noted in the architecture doc as a possible extra fallback tier: global and
free, but street-level coverage only, weak for a chapel interior. It is not a
candidate for the primary fine-lock layer.)*

## Recommendation

**Design for Niantic Spatial as the primary VPS path; qualify MultiSet AI in
parallel as both the fallback and the near-term bridge.**

Reasoning:

1. **Precedent is the scarcest asset.** Project Jade is the only cited
   real-world proof of this precise stack (glasses + VPS + persistent 6DoF
   anchors) shipping on a timeline like ours. When pitching a heritage-AR
   product on unreleased hardware, building on the demonstrated path is the
   defensible choice.
2. **MultiSet hedges two risks at once.** If Niantic Spatial's coverage or
   terms fail for a small Welsh heritage site (a real possibility for a
   partner whose roadmap is driven by Snap-scale deals), MultiSet's direct
   LiDAR/E57 ingestion means our existing captures seed its map. And because
   MultiSet is also the leading candidate for Prototype A's visual fine lock,
   qualifying it is work we largely have to do anyway — one integration
   effort, two prototypes.
3. **The architecture makes the choice cheap to defer.** The VPS sits behind
   the `IGeospatialLocalizer` seam with server-side credentials; switching
   partners is a binding swap, not a rework. The genuinely binding decision —
   whose *map* of the site we invest in — should be made only after both
   vendors' site-onboarding workflows are tested with dev-kit access.

**Adopted from Jade regardless of vendor:** their published practice of
building a Unity digital twin of the physical site to test and debug remotely
via recorded AR sessions — worth adopting for Prototype A's field-testing
workflow now, not waiting for Prototype B.

## Decision checklist (gates the final pick)

- [ ] Confirm each vendor's Android XR / Aura SDK support in writing
- [ ] Run each vendor's site-mapping workflow on the Oystermouth captures
- [ ] Measure localization confidence semantics against our threshold model
- [ ] Commercial terms for a single-site pilot
- [ ] Data residency/processing terms acceptable for a public heritage site
