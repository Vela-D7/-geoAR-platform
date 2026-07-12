# GeoAR Engine

AI-orchestrated **LiDAR Capture → Optimisation → Geospatial Localisation → XR
Deployment** platform for placing scanned 3D reconstructions of real historical
sites back onto those physical locations, viewed through AR glasses.

Test site: **Oystermouth Castle Chapel**. Meeting deadline: **24 July 2026**.
Honest per-component status (real vs simulated vs architecture-only): **[STATUS.md](STATUS.md)**.

## Monorepo layout

| Path | What it is |
|---|---|
| [`prototype-a-xreal-now/`](prototype-a-xreal-now/) | **Prototype A** — current XREAL SDK (SLAM + Spatial Anchors) + GPS coarse lock + visual fine lock. Optimisation pipeline + fusion state machine run and are tested here; the Unity layer is code-complete pending device verification |
| [`prototype-b-aura-future/`](prototype-b-aura-future/) | **Prototype B** — XREAL Aura / Android XR architecture (diagrams, VPS partner comparison, migration plan, stub scaffold). *Architecture-only until dev kits ship — never claimed as working* |
| [`shared-infrastructure/`](shared-infrastructure/) | Shared backend (FastAPI + PostgreSQL/SQLite + Celery/Redis jobs), canonical field-test log schema, self-learning loop v0 (rule-based) |
| [`web-app/`](web-app/) | Operator console (Next.js + Tailwind + Three.js): upload → processing → registry → deploy → monitor → self-learning → 3D preview |
| [`docs/`](docs/) | The three source specification documents |
| [`tasks/`](tasks/) | Build plan (`todo.md`) and self-improvement notes (`lessons.md`) |
| [`docker-compose.yml`](docker-compose.yml) | Full stack: postgres + redis + api + worker + web |

## Quick start (dev, no Docker)

```bash
pip install -r shared-infrastructure/backend/requirements.txt
redis-server --daemonize yes

cd shared-infrastructure/backend
python seed_synthetic.py                                   # demo site + SYNTHETIC sessions
uvicorn app.main:app --port 8000 &
celery -A app.jobs.celery_app.celery worker --concurrency=1 &

cd ../../web-app && npm install && npm run build && npm start   # http://localhost:3000
```

Docker path: `docker compose up --build` (config-validated; full run
**[Needs verification]** — this development container's network policy blocks
Docker Hub image pulls).

## Tests

```bash
(cd prototype-a-xreal-now && python -m pytest tests -q)          # 31 — pipeline + fusion
(cd shared-infrastructure/backend && python -m pytest tests -q)  # 23 — API + jobs + deploys + learning
(cd shared-infrastructure && python -m pytest self_learning/tests -q)  # 9 — v0 rules
```

## Ground rules (from the specs)

- Synthetic/replay data is tagged at the row level and labelled in every UI —
  never presented as field results.
- The self-learning loop is **v0, rule-based** — not a trained model, and says so.
- Prototype B is framed *designed/planned*, never "works".
- Unverifiable SDK surfaces ship as loud stubs behind interfaces, tagged
  **[Needs verification]** — not plausible-looking guesses.
- Not built around Vuforia (no native XREAL support; it only sits atop
  ARKit/ARCore/HoloLens2 tracking anyway).
