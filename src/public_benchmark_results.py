from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = {
    "benchmark",
    "subset_name",
    "sample_count",
    "model",
    "metrics",
    "records",
}


def _safe_number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def validate_public_benchmark_run(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Public benchmark result must be a JSON object.")

    missing = sorted(REQUIRED_TOP_LEVEL - set(payload))
    if missing:
        raise ValueError(
            "Public benchmark result is missing required fields: "
            + ", ".join(missing)
        )

    benchmark = str(payload.get("benchmark") or "").strip()
    subset_name = str(payload.get("subset_name") or "").strip()
    model = str(payload.get("model") or "").strip()
    records = payload.get("records")
    metrics = payload.get("metrics")

    if not benchmark:
        raise ValueError("benchmark cannot be empty.")
    if not subset_name:
        raise ValueError("subset_name cannot be empty.")
    if not model:
        raise ValueError("model cannot be empty.")
    if not isinstance(records, list) or not records:
        raise ValueError("records must be a non-empty list.")
    if len(records) > 200:
        raise ValueError("Import at most 200 public-benchmark records per run.")
    if not isinstance(metrics, dict):
        raise ValueError("metrics must be a JSON object.")

    sample_count = int(payload.get("sample_count") or 0)
    if sample_count != len(records):
        raise ValueError(
            "sample_count must match the number of records in the imported run."
        )

    exact_match = _safe_number(metrics.get("exact_match_percent"))
    token_f1 = _safe_number(metrics.get("token_f1_percent"))

    if not (0.0 <= exact_match <= 100.0):
        raise ValueError("exact_match_percent must be between 0 and 100.")
    if not (0.0 <= token_f1 <= 100.0):
        raise ValueError("token_f1_percent must be between 0 and 100.")

    cleaned = {
        **payload,
        "benchmark": benchmark,
        "subset_name": subset_name,
        "sample_count": sample_count,
        "model": model,
        "metrics": {
            **metrics,
            "exact_match_percent": round(exact_match, 2),
            "token_f1_percent": round(token_f1, 2),
        },
        "imported_at": datetime.now(timezone.utc).isoformat(),
    }

    cleaned.setdefault(
        "evaluation_note",
        (
            "This is a public-benchmark subset diagnostic using SatQuery's "
            "local normalized exact-match and token-F1 metrics. It is not an "
            "official full-benchmark score unless the benchmark-prescribed "
            "evaluation protocol is run separately."
        ),
    )

    return cleaned


def save_public_benchmark_run(
    output_dir: Path,
    payload: dict[str, Any],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned = validate_public_benchmark_run(payload)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    safe_name = "".join(
        char.lower() if char.isalnum() else "_"
        for char in cleaned["benchmark"]
    ).strip("_") or "benchmark"

    output_path = output_dir / f"{timestamp}_{safe_name}.json"
    output_path.write_text(
        json.dumps(cleaned, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path


def get_public_benchmark_summary(output_dir: Path) -> dict[str, Any]:
    """Return overall and per-benchmark summaries for imported diagnostics.

    Older Chunk 9 clients used ``latest_run``.  That field is intentionally
    preserved while Chunk 10 also exposes ``latest_by_benchmark`` so the
    Evaluation Center can keep VRSBench and CDVQA evidence visible together.
    """

    empty = {
        "run_count": 0,
        "latest_run": None,
        "latest_by_benchmark": {},
        "run_counts_by_benchmark": {},
    }

    if not output_dir.exists():
        return empty

    paths = sorted(output_dir.glob("*.json"))
    if not paths:
        return empty

    runs: list[dict[str, Any]] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if isinstance(payload, dict):
            runs.append(payload)

    if not runs:
        return empty

    latest_by_benchmark: dict[str, dict[str, Any]] = {}
    run_counts_by_benchmark: dict[str, int] = {}

    for payload in runs:
        benchmark = str(payload.get("benchmark") or "Unknown").strip() or "Unknown"
        run_counts_by_benchmark[benchmark] = (
            run_counts_by_benchmark.get(benchmark, 0) + 1
        )
        latest_by_benchmark[benchmark] = payload

    return {
        "run_count": len(runs),
        "latest_run": runs[-1],
        "latest_by_benchmark": latest_by_benchmark,
        "run_counts_by_benchmark": run_counts_by_benchmark,
    }
