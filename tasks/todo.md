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
- [x] 10. Web app: full 7-page spec — all pages live, production build passes,
       smoke-tested against the seeded backend, screenshot-reviewed
  - [x] Upload (validation results; auto-enqueues processing)
  - [x] Site registry
  - [x] Site detail / 3D preview (Three.js)
  - [x] Processing status (per-step badges, self-cancelling poll, retry surfaced)
  - [x] Deploy (trigger + history + live-anchor approval gate surfaced as confirm step)
  - [x] Field-test monitor (table + provenance filter + validated trend charts)
  - [x] Self-learning panel (threshold history, before/after replay, run-cycle button)
- [x] 11. Prototype B: architecture docs + partial scaffold (IGeospatialLocalizer
       seam, ArCoreAnchorProvider stub behind ANDROID_XR_PRESENT, VPS client stub
       with server-side-credential posture; package versions [Needs verification])
- [x] 12. Test suite — 63 passing (31 Prototype A · 23 backend · 9 self-learning)
- [x] 13. Deployment — docker-compose (postgres + redis + api + worker + web) +
       Dockerfiles; `docker compose config` validates. Full `up --build`
       **[Needs verification]**: this container's network policy blocks Docker Hub
       pulls (CONNECT 403 to production.cloudfront.docker.com) — run on the dev
       machine or allow docker domains in the environment network policy
- [x] 14. Documentation — root README rewritten; STATUS.md refreshed

## Explicitly out of MVP
Marketplace, multi-user sync, payments, advanced analytics, any claim that
Prototype B "works".

## Review — session of 11–12 July (Parts 1–3)
Shipped: pipeline, fusion core + mocks, Unity sources, backend, self-learning v0,
3 live web pages, Prototype B docs, STATUS.md. Deferred → this session: 7-page
web completion, job queue, Prototype B scaffold, Docker. [Needs verification]
carried: NRSDK adapter API names, Aura/Android XR capabilities, VPS coverage
for Oystermouth, package versions vs pinned Unity editor.
