# GeoAR shared backend (API + worker share this image; compose overrides the
# command for the worker). Build context = repo root: the backend imports the
# Prototype A pipeline, the self_learning package and the shared schemas.
FROM python:3.11-slim

WORKDIR /srv

COPY shared-infrastructure/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared-infrastructure/schemas /srv/shared-infrastructure/schemas
COPY shared-infrastructure/self_learning /srv/shared-infrastructure/self_learning
COPY shared-infrastructure/backend /srv/shared-infrastructure/backend
COPY prototype-a-xreal-now/pipeline /srv/prototype-a-xreal-now/pipeline
COPY prototype-a-xreal-now/fusion /srv/prototype-a-xreal-now/fusion

WORKDIR /srv/shared-infrastructure/backend

# Non-root, least-privilege runtime user; storage dir owned by it.
RUN useradd -r -m geoar && mkdir -p storage && chown -R geoar /srv
USER geoar

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
