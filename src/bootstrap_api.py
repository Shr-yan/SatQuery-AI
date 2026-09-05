"""Lightweight ASGI bootstrap for SatQuery AI deployments.

Replit can probe the service before the full geospatial/ML stack has finished
importing. This wrapper answers only / and /health immediately, then lazily
imports the real FastAPI application on the first non-health request.

Local development can continue to run satquery_api:app directly. Replit should
run bootstrap_api:app via start_replit.sh.
"""

from __future__ import annotations

import asyncio
import importlib
import json
from typing import Any

APP_VERSION = "1.5.0"

_real_app: Any | None = None
_load_lock = asyncio.Lock()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


async def _send_json(send, status: int, payload: dict[str, Any]) -> None:
    body = _json_bytes(payload)
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json; charset=utf-8"),
                (b"content-length", str(len(body)).encode("ascii")),
                (b"cache-control", b"no-store"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


async def _load_real_app():
    global _real_app
    if _real_app is not None:
        return _real_app

    async with _load_lock:
        if _real_app is None:
            # Import in a worker thread so the event loop remains responsive.
            module = await asyncio.to_thread(importlib.import_module, "satquery_api")
            _real_app = module.app

    return _real_app


async def app(scope, receive, send):
    scope_type = scope.get("type")

    # Uvicorn/Replit startup must complete without importing Torch/rasterio/etc.
    if scope_type == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return
        
    if scope_type != "http":
        real_app = await _load_real_app()
        await real_app(scope, receive, send)
        return

    path = scope.get("path", "/")
    method = scope.get("method", "GET").upper()

    if method in {"GET", "HEAD"} and path == "/":
        await _send_json(
            send,
            200,
            {
                "name": "SatQuery AI",
                "status": "running",
                "version": APP_VERSION,
                "web_app": "/app",
                "health": "/health",
                "bootstrap": True,
            },
        )
        return

    if method in {"GET", "HEAD"} and path == "/health":
        await _send_json(
            send,
            200,
            {
                "status": "healthy",
                "version": APP_VERSION,
                "bootstrap": True,
            },
        )
        return

    real_app = await _load_real_app()
    await real_app(scope, receive, send)
