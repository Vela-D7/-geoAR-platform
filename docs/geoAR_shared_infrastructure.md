# GeoAR — Shared Infrastructure

## Self-Learning Loop, Autonomous Build Loop, and End-to-End Website

You are acting as a senior AI software orchestration system.

This document covers the three components that sit **above** both hardware-specific prototypes rather than belonging to either one:

1. **Self-learning loop** — improves localization accuracy over time using field-test logs
2. **Autonomous build loop** — how an agentic coding environment (e.g. Claude Code) should self-correct while building any of these documents
3. **End-to-end website** — the full web application covering upload → process → deploy → monitor

Companion documents:
- `geoAR_prototype_A_xreal_now.md` — the working prototype whose field-test logs feed the self-learning loop below
- `geoAR_prototype_B_aura_future.md` — the future architecture this infrastructure should be designed to extend to later

---

## Deadline Constraint

**Hard deadline: 24 July 2026 (meeting with Kirill in London).**

- The **field-test logging pipeline** must be fully working — it's the prerequisite for everything else in this document.
- The **self-learning loop** should show one real, visible before/after adjustment cycle — this is v0, rule-based, explicitly not a trained ML model yet.
- The **website** must cover the full lifecycle end-to-end, even where individual pages show data from only one test site.

If a stage cannot be finished in time, ship it as a clearly labelled stub with a working UI/API contract rather than skipping it — Kirill should see the full shape of the system even where internals are incomplete.

---

## 1. Self-Learning Loop (Localization Improvement Over Time)

The platform must not treat localization as a static, one-time-tuned system. Every field session — from Prototype A today, and from Prototype B once it exists — feeds back into the next.

**Loop:**

```
Device session runs (GPS lock, visual lock, anchor placement)
  → Log: GPS accuracy, visual confidence score, time-to-lock, drift, lighting/time-of-day, success/failure
  → Aggregate logs per site
  → Nightly/on-demand job re-scores recognition target quality against accumulated data
  → Adjust target thresholds (confidence cutoffs, fallback triggers) per site automatically
  → Flag sites where accuracy is degrading (e.g. seasonal facade change) for re-scan
  → Version each threshold/config change so regressions can be rolled back
```

**MVP scope for the self-learning loop (by 24 July):**
- Logging pipeline fully working — this is the prerequisite for everything else.
- A simple rule-based adjustment (not a trained ML model) that tightens/loosens confidence thresholds based on the last N sessions.
- One visible "before/after" comparison from at least one real adjustment cycle, even on synthetic/replayed log data if live field data is thin.
- Explicitly label this as **v0 of the self-learning loop** to Kirill — a real learned model (e.g. a small classifier over lighting/pose features) is a post-MVP milestone, not a same-day claim.

**[Needs verification]:** whether a genuine ML-based improvement loop can be trained and validated meaningfully on a single test site in this timeframe. Default to the rule-based version above unless there is clearly enough logged data to justify more.

**Log schema note:** keep this schema identical across Prototype A and (eventually) Prototype B, so the same self-learning loop can ingest data from both hardware generations without rework.

---

## 2. Autonomous Build Loop (Agent Instructions)

When operating in an agentic coding environment (e.g. Claude Code) against any of the three GeoAR documents, run a self-correcting build loop rather than a single linear pass:

```
1. Pick the next incomplete stage (from whichever document is currently in scope).
2. Implement it.
3. Run the stage's own test plan.
4. If tests fail → diagnose → fix → re-test (up to 3 automatic attempts).
5. If still failing after 3 attempts → stop, report the blocker clearly, do not silently skip.
6. If tests pass → write the "after coding" summary (files, how to run, tests, limitations, next stage).
7. Move to the next stage.
8. Periodically (every 2-3 stages) re-check the Deadline Constraint and MVP Boundary in the active document — cut scope, not quality, if behind schedule.
```

Do not run this loop unattended past a security-sensitive stage (auth, secrets, deployment credentials, live anchor writes) without explicit human approval, per the security checks in the relevant prototype document.

Do not use this loop to attempt Prototype B stages that require real Android XR hardware — those are blocked by definition, not a build failure to retry against.

---

## 3. End-to-End Website (Full Application, Not Just a Dashboard)

This is a complete web application, covering the full lifecycle — not a stub admin panel.

**Pages/flows required for the 24 July demo:**

1. **Upload** — operator uploads a LiDAR scan (or points to existing processed asset for the test site); shows validation status (coverage, density, scale check).
2. **Processing status** — live/polling view of the optimisation pipeline (mesh cleanup → LOD generation → texture bake → recognition target build), with pass/fail per step.
3. **Site registry** — list of registered sites with GPS anchor coordinates, recognition target status, last field-test result.
4. **Deploy** — trigger export/push of the optimised model + recognition target to the Unity/XREAL build (Prototype A today; extendable to Prototype B later).
5. **Field-test monitor** — table/chart of logged sessions: GPS accuracy, visual confidence, time-to-lock, drift, success/fail, timestamped.
6. **Self-learning panel** — shows current confidence thresholds per site, history of automatic adjustments, and the before/after comparison from the self-learning loop above.
7. **Site detail / 3D preview** — Three.js viewer of the optimised model, so Kirill can inspect the asset without opening Unity.

**Stack:** Next.js + React + Tailwind + Three.js (WebXR preview optional, not required for MVP), talking to the FastAPI backend shared with both prototypes. Auth can be a single shared operator login for MVP — no multi-tenant system needed yet.

**Explicitly out of scope for 24 July:** multi-user roles, billing, public-facing marketing pages, mobile-responsive polish, any page that assumes Prototype B is live. This is an internal tool for the two of you to review together, not a public product yet.

---

## Backend (Shared Across Everything)

- Python / FastAPI
- PostgreSQL (model metadata, anchor coordinates, site registry, field-test logs, self-learning thresholds)
- Object storage for LiDAR assets and optimised model exports
- Signed URLs for model delivery to device

**MCP tooling (if using Claude Code / agentic build):**
- Filesystem MCP
- GitHub MCP
- Blender MCP
- Unity MCP
- Custom Geospatial Anchor MCP

---

## Build Order

1. Backend: site/anchor registry API, field-test logging tables
2. Field-test logging pipeline (wired to Prototype A first — this is the real, working data source)
3. Self-learning v0: rule-based threshold adjustment over logged sessions
4. Web app: upload, processing status, site registry, deploy trigger
5. Web app: field-test monitor, self-learning panel
6. Web app: site detail / 3D preview
7. Test suite
8. Documentation, written for a non-technical stakeholder review (Kirill meeting, 24 July)

---

## Output Format for Every Response

```
Stage:
Objective:
Files to create:
Architecture:
Implementation:
Tests:
Validation:
Risks:
Next action:
```

---

## Behaviour Rules

- Be strict.
- The self-learning loop is v0 and rule-based — do not claim a trained ML model exists unless it genuinely does. Mark anything unconfirmed as **[Needs verification]**.
- Prefer a working small system over a large incomplete one.
- When blocked, create a stub interface and state exactly what real implementation is required later.
- The website must present real data from Prototype A wherever possible — do not fabricate field-test results to make the dashboard look more populated than the actual testing has produced.
- Target audience for the final documentation pass: a technical co-founder/investor meeting, not an academic panel. Keep language direct and commercially framed, but do not overstate what has actually been verified.
