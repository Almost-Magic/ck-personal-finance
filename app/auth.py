"""Swappable authentication boundary for the local Finance Suite runtime.

The current backend is HTTP Basic for a single local user. Replace
``build_auth_backend`` when the VPS deployment adopts OIDC, SSO, or accounts;
routes and services must depend only on ``AuthBackend.authenticate``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
PUBLIC_PATHS = {"/api/health"}


@dataclass(frozen=True)
class AuthPrincipal:
    subject: str
    tenant_id: str
    roles: frozenset[str]


class AuthBackend(Protocol):
    def authenticate(self, request: Request) -> AuthPrincipal | None: ...


class ConfigurationError(RuntimeError):
    pass


def hash_password(password: str, *, iterations: int = 600_000, salt: bytes | None = None) -> str:
    """Return a versioned PBKDF2 hash suitable for FINANCE_AUTH_PASSWORD_HASH."""

    if not password:
        raise ValueError("Password must not be empty")
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, raw_iterations, salt_hex, expected_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(raw_iterations)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
    except (TypeError, ValueError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


class LocalBasicAuthBackend:
    def __init__(self, username: str, password_hash: str, tenant_id: str = "local") -> None:
        if not username or not password_hash:
            raise ConfigurationError(
                "Local authentication requires FINANCE_AUTH_USERNAME and "
                "FINANCE_AUTH_PASSWORD_HASH"
            )
        self.username = username
        self.password_hash = password_hash
        self.tenant_id = tenant_id

    def authenticate(self, request: Request) -> AuthPrincipal | None:
        authorization = request.headers.get("authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "basic" or not token:
            return None
        try:
            raw = base64.b64decode(token, validate=True).decode("utf-8")
            username, password = raw.split(":", 1)
        except (ValueError, UnicodeDecodeError):
            return None
        if not hmac.compare_digest(username, self.username):
            return None
        if not verify_password(password, self.password_hash):
            return None
        return AuthPrincipal(
            subject=username,
            tenant_id=self.tenant_id,
            roles=frozenset({"read", "write", "review", "admin"}),
        )


class DisabledTestAuthBackend:
    def authenticate(self, request: Request) -> AuthPrincipal:
        return AuthPrincipal("test-user", "test-tenant", frozenset({"read", "write", "review", "admin"}))


def build_auth_backend() -> AuthBackend:
    mode = os.getenv("FINANCE_AUTH_MODE", "local").strip().lower()
    environment = os.getenv("FINANCE_ENV", "local").strip().lower()
    if mode == "disabled" and environment == "test":
        return DisabledTestAuthBackend()
    if mode != "local":
        raise ConfigurationError(f"Unsupported FINANCE_AUTH_MODE: {mode}")
    return LocalBasicAuthBackend(
        os.getenv("FINANCE_AUTH_USERNAME", ""),
        os.getenv("FINANCE_AUTH_PASSWORD_HASH", ""),
        os.getenv("FINANCE_AUTH_TENANT", "local"),
    )


def _same_origin(request: Request) -> bool:
    source = request.headers.get("origin") or request.headers.get("referer")
    if not source:
        return False
    source_url = urlsplit(source)
    host = request.headers.get("host", "")
    return source_url.scheme in {"http", "https"} and source_url.netloc == host


class FinanceAuthMiddleware(BaseHTTPMiddleware):
    """Apply the selected auth backend without coupling routes to its scheme."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        try:
            backend = build_auth_backend()
        except ConfigurationError:
            return JSONResponse(
                status_code=503,
                content={"error": "Authentication is not configured."},
            )
        principal = backend.authenticate(request)
        if principal is None:
            return JSONResponse(
                status_code=401,
                content={"error": "Authentication required."},
                headers={"WWW-Authenticate": 'Basic realm="Finance Suite", charset="UTF-8"'},
            )
        if request.method not in SAFE_METHODS and not _same_origin(request):
            return JSONResponse(
                status_code=403,
                content={"error": "State-changing requests require a same-origin Origin or Referer header."},
            )
        request.state.principal = principal
        return await call_next(request)
