from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROXY_METRIC_NOTE = (
    "These are lightweight local proxy metrics for development and demo "
    "readiness. They are not official VRSBench, CDVQA or ISRO/SAC benchmark "
    "scores. Official evaluation should use the benchmark-prescribed scripts "
    "and hidden evaluation protocol where applicable."
)


IMPLEMENTATION_READINESS = [
    {
        "id": "single_image_vqa",
        "requirement": "Single-image visual question answering",
        "status": "implemented",
        "evidence": "Uploaded-image VQA with validated preview and Qwen vision reasoning.",
    },
    {
        "id": "single_image_captioning",
        "requirement": "Additional single-image task",
        "status": "implemented",
        "evidence": "Scene description/captioning is available in the single-image workspace.",
    },
    {
        "id": "remote_sensing_adaptation",
        "requirement": "Remote-sensing-adapted visual component",
        "status": "implemented",
        "evidence": "SatQuery EuroSAT Scene Specialist v1 is trained on EuroSAT RGB and supplies top-k scene evidence.",
    },
    {
        "id": "bitemporal_change",
        "requirement": "Bi-temporal change understanding / change VQA",
        "status": "implemented",
        "evidence": "Before/after pair validation, visual change evidence and change-focused VQA are available.",
    },
    {
        "id": "optical_sar",
        "requirement": "Optical-SAR paired-image analysis",
        "status": "implemented",
        "evidence": "Cross-modal validation, candidate evidence fusion and joint optical-SAR VQA are available.",
    },
    {
        "id": "agentic_orchestration",
        "requirement": "Agentic model/tool selection",
        "status": "implemented",
        "evidence": "SatQuery Agent Controller routes input configuration and intent through a predefined registry and exposes an execution trace.",
    },
    {
        "id": "visual_evidence_reports",
        "requirement": "Visual evidence, execution summary and downloadable report",
        "status": "implemented",
        "evidence": "HTML/JSON evidence reports package outputs, model/tool trace and visual evidence.",
    },
]


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def normalize_text(value):
    value = str(value or "").lower().strip()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def token_f1(reference, prediction):
    reference_tokens = normalize_text(reference).split()
    prediction_tokens = normalize_text(prediction).split()

    if not reference_tokens and not prediction_tokens:
        return 1.0
    if not reference_tokens or not prediction_tokens:
        return 0.0

    reference_counts = defaultdict(int)
    prediction_counts = defaultdict(int)

    for token in reference_tokens:
        reference_counts[token] += 1
    for token in prediction_tokens:
        prediction_counts[token] += 1

    overlap = sum(
        min(reference_counts[token], prediction_counts[token])
        for token in reference_counts
    )

    if overlap == 0:
        return 0.0

    precision = overlap / len(prediction_tokens)
    recall = overlap / len(reference_tokens)

    return 2 * precision * recall / (precision + recall)


def exact_match(reference, prediction):
    return float(normalize_text(reference) == normalize_text(prediction))


def _round_percent(value):
    return round(float(value) * 100.0, 2)


def evaluate_records(records):
    """
    Evaluate already-produced reference/prediction pairs.

    Expected record fields:
      task, question, reference_answer, model_answer
    Optional:
      case_id, category, source

    No VLM/API call is made here. This is intentionally an offline scoring
    helper so benchmark evaluation does not consume Groq quota.
    """

    if not isinstance(records, list) or not records:
        raise ValueError("At least one evaluation record is required.")

    scored = []

    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"Record {index} is not an object.")

        reference = record.get("reference_answer")
        prediction = record.get("model_answer")

        if reference is None or prediction is None:
            raise ValueError(
                f"Record {index} must contain reference_answer and model_answer."
            )

        task = str(record.get("task") or "unspecified").strip() or "unspecified"
        em = exact_match(reference, prediction)
        f1 = token_f1(reference, prediction)

        scored.append(
            {
                "case_id": record.get("case_id", f"case_{index:04d}"),
                "task": task,
                "category": record.get("category"),
                "source": record.get("source"),
                "question": record.get("question"),
                "reference_answer": reference,
                "model_answer": prediction,
                "exact_match": em,
                "token_f1": f1,
            }
        )

    def summarize(items):
        count = len(items)
        return {
            "count": count,
            "exact_match_percent": _round_percent(
                sum(item["exact_match"] for item in items) / count
            ),
            "token_f1_percent": _round_percent(
                sum(item["token_f1"] for item in items) / count
            ),
        }

    by_task = {}
    tasks = sorted({item["task"] for item in scored})

    for task in tasks:
        by_task[task] = summarize(
            [item for item in scored if item["task"] == task]
        )

    return {
        "metric_type": "local_proxy",
        "metric_note": PROXY_METRIC_NOTE,
        "generated_at": utc_now_iso(),
        "overall": summarize(scored),
        "by_task": by_task,
        "records": scored,
    }


def save_benchmark_run(results_dir, result):
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = results_dir / f"benchmark_proxy_{timestamp}.json"

    counter = 1
    while output_path.exists():
        output_path = results_dir / f"benchmark_proxy_{timestamp}_{counter}.json"
        counter += 1

    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path


def get_benchmark_summary(results_dir):
    results_dir = Path(results_dir)

    if not results_dir.exists():
        return {
            "run_count": 0,
            "latest_run": None,
            "metric_note": PROXY_METRIC_NOTE,
        }

    files = sorted(
        results_dir.glob("benchmark_proxy_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not files:
        return {
            "run_count": 0,
            "latest_run": None,
            "metric_note": PROXY_METRIC_NOTE,
        }

    latest = None

    try:
        latest = json.loads(files[0].read_text(encoding="utf-8"))
    except Exception:
        latest = None

    return {
        "run_count": len(files),
        "latest_run": latest,
        "metric_note": PROXY_METRIC_NOTE,
    }


def load_demo_cases(path):
    path = Path(path)

    if not path.exists():
        return []

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

    return value if isinstance(value, list) else []
