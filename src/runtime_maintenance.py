from __future__ import annotations

import os
import shutil
import threading
import time
from pathlib import Path
from typing import Iterable


_CLEANUP_LOCK = threading.Lock()
_LAST_CLEANUP_MONOTONIC = 0.0


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, value)


def runtime_policy() -> dict:
    """Return deployment-safe artifact retention settings.

    Values can be overridden in Replit/other deployments without code changes.
    """
    return {
        "upload_ttl_hours": _env_int("SATQUERY_UPLOAD_TTL_HOURS", 6),
        "report_ttl_hours": _env_int("SATQUERY_REPORT_TTL_HOURS", 24),
        "cleanup_interval_minutes": _env_int(
            "SATQUERY_CLEANUP_INTERVAL_MINUTES", 30
        ),
    }


def _folder_age_seconds(path: Path, now: float) -> float:
    try:
        return max(0.0, now - path.stat().st_mtime)
    except OSError:
        return 0.0


def _iter_children(directory: Path) -> Iterable[Path]:
    if not directory.exists():
        return []
    try:
        return list(directory.iterdir())
    except OSError:
        return []


def _remove_expired_children(directory: Path, ttl_seconds: float) -> dict:
    now = time.time()
    removed = 0
    kept = 0
    failed = 0

    for child in _iter_children(directory):
        if _folder_age_seconds(child, now) < ttl_seconds:
            kept += 1
            continue

        try:
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink(missing_ok=True)
            removed += 1
        except OSError:
            failed += 1

    return {
        "removed": removed,
        "kept": kept,
        "failed": failed,
    }


def cleanup_runtime_artifacts(
    uploads_dir: Path,
    reports_dir: Path,
) -> dict:
    policy = runtime_policy()

    upload_result = _remove_expired_children(
        uploads_dir,
        policy["upload_ttl_hours"] * 3600,
    )
    report_result = _remove_expired_children(
        reports_dir,
        policy["report_ttl_hours"] * 3600,
    )

    return {
        "policy": policy,
        "uploads": upload_result,
        "reports": report_result,
    }


def maybe_cleanup_runtime_artifacts(
    uploads_dir: Path,
    reports_dir: Path,
) -> dict:
    """Run cleanup at most once per configured interval per process.

    This is intentionally opportunistic rather than a background thread, which
    keeps the Replit deployment simple and avoids extra workers/timers.
    """
    global _LAST_CLEANUP_MONOTONIC

    policy = runtime_policy()
    interval_seconds = policy["cleanup_interval_minutes"] * 60
    now = time.monotonic()

    if now - _LAST_CLEANUP_MONOTONIC < interval_seconds:
        return {
            "ran": False,
            "policy": policy,
        }

    if not _CLEANUP_LOCK.acquire(blocking=False):
        return {
            "ran": False,
            "policy": policy,
        }

    try:
        now = time.monotonic()
        if now - _LAST_CLEANUP_MONOTONIC < interval_seconds:
            return {
                "ran": False,
                "policy": policy,
            }

        result = cleanup_runtime_artifacts(
            uploads_dir=uploads_dir,
            reports_dir=reports_dir,
        )
        _LAST_CLEANUP_MONOTONIC = now
        return {
            "ran": True,
            **result,
        }
    finally:
        _CLEANUP_LOCK.release()


def runtime_storage_status(
    uploads_dir: Path,
    reports_dir: Path,
) -> dict:
    def count_children(directory: Path) -> int:
        return len(list(_iter_children(directory)))

    return {
        "policy": runtime_policy(),
        "uploads_present": count_children(uploads_dir),
        "reports_present": count_children(reports_dir),
    }
