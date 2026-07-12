"""Celery wiring. Redis broker by default (GEOAR_BROKER_URL to override);
GEOAR_JOBS_EAGER=1 runs tasks in-process — used by the test suite so the real
task code executes without a worker, and available as a no-Redis dev fallback.

Run a worker:
    cd shared-infrastructure/backend
    celery -A app.jobs.celery_app.celery worker --loglevel=info --concurrency=1
"""

from __future__ import annotations

import os

from celery import Celery

celery = Celery(
    "geoar",
    broker=os.environ.get("GEOAR_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("GEOAR_RESULT_URL", "redis://localhost:6379/1"),
    include=["app.jobs.tasks"],
)

celery.conf.update(
    task_always_eager=os.environ.get("GEOAR_JOBS_EAGER", "0") == "1",
    task_eager_propagates=False,  # eager failures must still land in the DB, not raise
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # one heavy mesh job at a time
    task_time_limit=15 * 60,
)
