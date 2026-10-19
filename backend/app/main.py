
"""FastAPI entry point for ApexiveAI Workforce Payroll SaaS."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.auth import get_current_user, router as auth_router
from app.api.companies import router as companies_router
from app.database import get_engine


# Importing app.database loads backend/.env before these values are read.
APP_NAME = os.getenv("APP_NAME", "ApexiveAI Workforce")
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("apexiveai.workforce")


def get_cors_origins() -> list[str]:
    """Parse comma-separated or JSON-array CORS origins."""

    raw = os.getenv("CORS_ORIGINS", "").strip()

    if not raw:
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

    if raw.startswith("["):
        try:
            parsed = json.loads(raw)

            if isinstance(parsed, list):
                origins = [
                    str(item).strip().rstrip("/")
                    for item in parsed
                    if str(item).strip()
                ]
                if origins:
                    return origins

        except json.JSONDecodeError:
            logger.warning(
                "CORS_ORIGINS looks like JSON but could not be parsed."
            )

    return [
        item.strip().rstrip("/")
        for item in raw.split(",")
        if item.strip()
    ]


def require_super_admin(
    current_user: Any = Depends(get_current_user),
) -> Any:
    """Reject company-management operations unless the user is SUPER_ADMIN."""

    if isinstance(current_user, dict):
        role = current_user.get("role")
    else:
        role = getattr(current_user, "role", None)

    # Supports string roles and enum-style roles.
    role_value = getattr(role, "value", role)
    normalized_role = str(role_value or "").strip().upper()

    if normalized_role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="SUPER_ADMIN permission is required.",
        )

    return current_user


is_production = APP_ENV == "production"

app = FastAPI(
    title=APP_NAME,
    description=(
        "Mobile-first workforce, company, attendance and payroll API."
    ),
    version="1.0.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

cors_origins = get_cors_origins()
wildcard_cors = "*" in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=not wildcard_cors,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Accept",
        "Authorization",
        "Content-Type",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=["X-Request-ID"],
    max_age=600,
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add baseline security headers to API responses."""

    response = await call_next(request)

    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault(
        "Referrer-Policy",
        "strict-origin-when-cross-origin",
    )
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(self), microphone=(), geolocation=()",
    )

    return response


# Authentication stays public for the login request itself.
# Protected endpoints inside auth.py must continue checking their JWT.
app.include_router(auth_router)

# This dependency is applied to every route in the company router.
# Therefore Company endpoints are not available to unauthenticated users
# or ordinary company admins.
app.include_router(
    companies_router,
    dependencies=[Depends(require_super_admin)],
)


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    """Basic API information; does not reveal database credentials."""

    return {
        "app": APP_NAME,
        "status": "running",
        "environment": APP_ENV,
    }


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    """Liveness check. Does not require a database query."""

    return {
        "app": APP_NAME,
        "status": "ok",
        "environment": APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/database", tags=["Health"])
def database_health() -> dict[str, str]:
    """Check PostgreSQL connectivity without returning sensitive details."""

    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception:
        logger.exception("Database health check failed")

        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "unavailable",
            },
        ) from None
