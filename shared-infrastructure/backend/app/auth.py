"""MVP auth: one shared operator token (per spec: 'single shared operator login').

Token comes from GEOAR_OPERATOR_TOKEN; there is a dev default so the demo runs
out of the box, clearly not a production posture. Multi-user auth is post-MVP.
"""

from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException

DEV_DEFAULT_TOKEN = "geoar-dev-operator"


def operator_token() -> str:
    return os.environ.get("GEOAR_OPERATOR_TOKEN", DEV_DEFAULT_TOKEN)


async def require_operator(x_operator_token: str = Header(default="")) -> None:
    if not secrets.compare_digest(x_operator_token, operator_token()):
        raise HTTPException(status_code=401, detail="missing or invalid X-Operator-Token")
