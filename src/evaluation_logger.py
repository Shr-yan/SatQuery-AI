from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


TRACKED_API_PATHS = {
    "/analyze": "search_earth_analysis",
    "/chat": "search_earth_followup",
    "/vision-chat": "search_earth_vision",
    "/upload-image": "single_image_validation",
    "/uploaded-vision-chat": "single_image_vqa",
    "/upload-change-pair": "bitemporal_pair_validation",
    "/uploaded-change-chat": "bitemporal_change_vqa",
    "/upload-crossmodal-pair": "optical_sar_pair_validation",
    "/uploaded-crossmodal-chat": "optical_sar_joint_vqa",
    "/evidence-report": "evidence_report_generation",
    "/benchmark-evaluate": "benchmark_proxy_evaluation",
}


def utc_now_iso():
    return datetime.now(
        timezone.utc
    ).isoformat()


def log_api_event(
    log_path,
    path,
    method,
    status_code,
    duration_ms,
):
    """
    Append a compact, privacy-conscious audit event.

    The logger deliberately records route-level execution metadata rather
    than prompts, chat text, uploaded image bytes, API keys, or other user
    content. This keeps the audit useful for judging/testing without turning
    the log into a copy of user conversations.
    """

    workflow = TRACKED_API_PATHS.get(
        path
    )

    if workflow is None:
        return

    log_path = Path(
        log_path
    )

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    event = {
        "timestamp": utc_now_iso(),
        "workflow": workflow,
        "path": path,
        "method": method,
        "status_code": int(
            status_code
        ),
        "status": (
            "completed"
            if int(status_code) < 400
            else "failed"
        ),
        "duration_ms": round(
            float(duration_ms),
            2,
        ),
    }

    try:
        with log_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    event,
                    ensure_ascii=False,
                )
                + "\n"
            )
    except Exception:
        # Audit logging must never break the actual SatQuery workflow.
        return


def get_evaluation_summary(
    log_path,
    recent_limit=20,
):
    log_path = Path(
        log_path
    )

    if not log_path.exists():
        return {
            "total_events": 0,
            "successful_events": 0,
            "failed_events": 0,
            "workflow_counts": {},
            "average_duration_ms": None,
            "recent_events": [],
        }

    events = []

    try:
        for line in log_path.read_text(
            encoding="utf-8"
        ).splitlines():
            line = line.strip()
            if not line:
                continue

            try:
                event = json.loads(
                    line
                )
            except json.JSONDecodeError:
                continue

            if isinstance(
                event,
                dict,
            ):
                events.append(
                    event
                )
    except Exception:
        return {
            "total_events": 0,
            "successful_events": 0,
            "failed_events": 0,
            "workflow_counts": {},
            "average_duration_ms": None,
            "recent_events": [],
        }

    workflow_counts = Counter(
        event.get(
            "workflow",
            "unknown",
        )
        for event in events
    )

    successful = sum(
        1
        for event in events
        if event.get("status") == "completed"
    )

    failed = sum(
        1
        for event in events
        if event.get("status") == "failed"
    )

    durations = [
        float(event["duration_ms"])
        for event in events
        if isinstance(
            event.get("duration_ms"),
            (int, float),
        )
    ]

    average_duration = (
        round(
            sum(durations)
            / len(durations),
            2,
        )
        if durations
        else None
    )

    return {
        "total_events": len(events),
        "successful_events": successful,
        "failed_events": failed,
        "workflow_counts": dict(
            sorted(
                workflow_counts.items()
            )
        ),
        "average_duration_ms": average_duration,
        "recent_events": events[
            -max(
                1,
                int(recent_limit),
            ):
        ],
    }
