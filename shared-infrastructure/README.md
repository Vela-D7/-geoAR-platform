# Shared Infrastructure

Backend registry + field-test logging, self-learning loop v0, and the operator
web app. Sits above both prototypes; consumes Prototype A's logs today and is
schema-compatible with Prototype B later.

Spec: [`../docs/geoAR_shared_infrastructure.md`](../docs/geoAR_shared_infrastructure.md)

## Components

| Path | What it is | Status |
|---|---|---|
| `schemas/` | Canonical field-test log JSON Schema (v1) — single source of truth for device loggers, backend ingest, and the self-learning loop | working |
| `backend/` | FastAPI: site registry, anchors (live-overwrite approval gate), field-test ingest (schema-validated), versioned thresholds, scan upload validation, model delivery | working, 14 tests |
| `self_learning/` | v0 rule-based threshold adjuster (explicitly NOT ML) + cycle runner producing before/after reports | working, 9 tests |
| `website/` | Next.js operator console. **Live pages:** Upload, Site registry, Site detail/3D preview (Three.js). **Placeholders (labelled "coming next"):** Deploy, Field-test monitor, Self-learning panel | builds + smoke-tested |

## Run the whole stack

```bash
pip install fastapi uvicorn sqlalchemy pydantic jsonschema trimesh numpy python-multipart

# 1. Backend (SQLite dev DB; set GEOAR_DATABASE_URL for PostgreSQL)
cd shared-infrastructure/backend
python seed_synthetic.py            # test site + 25 SYNTHETIC sessions + model asset
uvicorn app.main:app --port 8000

# 2. One self-learning cycle (writes reports/before_after.{md,json}, appends threshold version)
cd shared-infrastructure
python -m self_learning.run_cycle

# 3. Web app
cd shared-infrastructure/website
npm install && npm run build && npm start   # http://localhost:3000

# Tests
cd shared-infrastructure/backend && python -m pytest tests -q   # 14
cd shared-infrastructure && python -m pytest self_learning/tests -q  # 9
```

Auth: single shared operator token (`X-Operator-Token`), MVP posture per spec.
Dev default is `geoar-dev-operator`; set `GEOAR_OPERATOR_TOKEN` (backend) and the
same on the web server for anything beyond local dev. The browser never sees the
token — the Next server proxy injects it.

## Data honesty

Seeded sessions are generated from Prototype A's fusion mock scenarios and are
tagged `source="synthetic"` at the row level; the UI labels them wherever shown.
The demonstrated self-learning cycle (LOOSEN 0.70 → 0.65 on dusk near-miss
sessions) ran on that synthetic data — a real adjustment cycle on replayed
data, exactly as the spec's MVP scope allows, and labelled v0/rule-based.
