# GeoAR Engine — build plan (master orchestration prompt, 12 July 2026)

Reconciled against work completed on 11–12 July (commits `f975207`, `5445712`,
`df9891b`). Checked = done and verified per its own test plan. Deadline: 24 July.

## Stage map (First Build Order)

- [x] 1. Monorepo structure — `prototype-a-xreal-now/`, `prototype-b-aura-future/`,
       `shared-infrastructure/`, `tasks/`; **`web-app/` move done this session**
- [x] 2. FastAPI backend + DB schema (sites, anchors, field-test logs, threshold
       versions) — 14 API tests. **This session: + processing jobs + deploys tables,
       Celery/Redis job queue with retry-with-fallback-settings**
- [x] 3. LiDAR capture → cleaned mesh pipeline (placeholder mesh; real asset is a
       drop-in `.glb` through the same path). Texture bake = declared stub (Blender job)
- [x] 4. Model optimisation pipeline (LODs, quality report) — runs, tested
- [x] 5. Prototype A: XREAL scene — anchors + content rendering (code-complete,
       **NOT Unity-compiled / device-verified** — see verification ladder in SceneSetup.md)
- [x] 6. Prototype A: recognition/localisation layer — interface seam (`IVisualLocalizer`)
       + mock provider; MultiSet-vs-custom decision still open (hardware-side task)
- [x] 7. Prototype A: geospatial fusion state machine — 31 tests, all spec branches
- [x] 8. Field-test logging pipeline — schema v1, ingest validated, synthetic-tagged
- [x] 9. Self-learning v0 — rule-based, one real LOOSEN cycle demonstrated, 9 tests.
       **This session: exposed via API for the web panel**
- [ ] 10. Web app: full 7-page spec
  - [x] Upload (validation results)
  - [x] Site registry
  - [x] Site detail / 3D preview (Three.js)
  - [ ] Processing status (live per-step view over the new job pipeline)
  - [ ] Deploy (trigger + history + live-anchor approval gate surfaced)
  - [ ] Field-test monitor (sessions table + provenance filter + trend chart)
  - [ ] Self-learning panel (threshold history, before/after, run-cycle button)
- [ ] 11. Prototype B: architecture docs — done (diagrams, VPS comparison, migration
       plan); **partial Unity/Android XR scaffold now in scope this session**
- [ ] 12. Test suite — extend to jobs/deploy/learning endpoints (54 passing now)
- [ ] 13. Deployment — docker-compose (postgres + redis + api + worker + web)
       [Needs verification: no Docker daemon in this container → compose files
       validated by config-parse only]
- [ ] 14. Documentation — refresh READMEs + STATUS.md to match this session

## Explicitly out of MVP
Marketplace, multi-user sync, payments, advanced analytics, any claim that
Prototype B "works".

## Review — session of 11–12 July (Parts 1–3)
Shipped: pipeline, fusion core + mocks, Unity sources, backend, self-learning v0,
3 live web pages, Prototype B docs, STATUS.md. Deferred → this session: 7-page
web completion, job queue, Prototype B scaffold, Docker. [Needs verification]
carried: NRSDK adapter API names, Aura/Android XR capabilities, VPS coverage
for Oystermouth, package versions vs pinned Unity editor.
