"""
SatQuery AI - VRSBench public subset diagnostic runner.

Designed for Kaggle/Colab so the deployed Replit app does not need a large
benchmark dependency. The script streams the public VRSBench_MINI.tsv
benchmark derivative, takes one deterministic example from each of the 12
question categories, optionally runs the SatQuery EuroSAT specialist as
supporting evidence, asks the same Groq Qwen VLM used by SatQuery, scores the
answers with SatQuery's local normalized Exact Match + token F1, and writes a
JSON file that can be imported into the SatQuery Evaluation Center.

This is a real public VRSBench subset diagnostic, but the local metrics are not
an official full VRSBench leaderboard score.
"""

from __future__ import annotations

import base64
import csv
import sys
import io
import importlib
import json
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests
import torch
from PIL import Image

# VRSBench_MINI contains base64-encoded images inside TSV fields.
# Python's default CSV field limit (131072 bytes) is too small.
csv.field_size_limit(sys.maxsize)

try:
    from groq import Groq
except ImportError as exc:
    raise RuntimeError(
        "groq is not installed. In Kaggle run: !pip install -q groq"
    ) from exc


VRSBENCH_MINI_URL = (
    "https://huggingface.co/datasets/YuJJJJin/VRSBench.tsv/"
    "resolve/main/VRSBench_MINI.tsv?download=true"
)

VISION_MODEL = "qwen/qwen3.6-27b"
OUTPUT_PATH = Path("/kaggle/working/vrsbench_public_subset_results.json")
MAX_ROWS_TO_SCAN = 5000
REQUEST_TIMEOUT_SECONDS = 120
SEED_NOTE = "first encountered example per category in VRSBench_MINI.tsv"

TARGET_CATEGORIES = [
    "object existence",
    "object quantity",
    "object position",
    "object category",
    "object color",
    "scene type",
    "object shape",
    "image",
    "object size",
    "reasoning",
    "object direction",
    "rural or urban",
]

EUROSAT_CLASSES = [
    "AnnualCrop",
    "Forest",
    "HerbaceousVegetation",
    "Highway",
    "Industrial",
    "Pasture",
    "PermanentCrop",
    "Residential",
    "River",
    "SeaLake",
]

DEFAULT_MEAN = [0.5, 0.5, 0.5]
DEFAULT_STD = [0.25, 0.25, 0.25]
DEFAULT_INPUT_SIZE = 64


def get_groq_key() -> str:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if key:
        return key

    try:
        # Import dynamically so local VS Code/Pylance does not report
        # kaggle_secrets as an unresolved import. The module exists only
        # inside Kaggle notebooks.
        kaggle_secrets = importlib.import_module("kaggle_secrets")
        user_secrets_client = getattr(kaggle_secrets, "UserSecretsClient")

        key = user_secrets_client().get_secret("GROQ_API_KEY").strip()
        if key:
            return key
    except Exception:
        pass

    raise RuntimeError(
        "GROQ_API_KEY was not found. Add it as a Kaggle Secret named "
        "GROQ_API_KEY or set the environment variable."
    )


def normalize_text(value: str) -> str:
    value = str(value or "").lower().strip()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def exact_match(reference: str, prediction: str) -> float:
    return float(normalize_text(reference) == normalize_text(prediction))


def token_f1(reference: str, prediction: str) -> float:
    ref = normalize_text(reference).split()
    pred = normalize_text(prediction).split()

    if not ref and not pred:
        return 1.0
    if not ref or not pred:
        return 0.0

    ref_counts = Counter(ref)
    pred_counts = Counter(pred)
    overlap = sum((ref_counts & pred_counts).values())

    if overlap == 0:
        return 0.0

    precision = overlap / len(pred)
    recall = overlap / len(ref)
    return 2 * precision * recall / (precision + recall)


def _decode_image(image_base64: str) -> Image.Image:
    raw = str(image_base64 or "").strip()
    if raw.startswith("data:"):
        raw = raw.split(",", 1)[1]

    image_bytes = base64.b64decode(raw)
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def _image_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=92)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def collect_category_subset() -> list[dict]:
    print("Streaming VRSBench_MINI.tsv...")
    response = requests.get(
        VRSBENCH_MINI_URL,
        stream=True,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    # iter_lines avoids keeping the 207 MB benchmark file in memory. We stop as
    # soon as all 12 VQA categories have one example.
    line_iter = response.iter_lines(decode_unicode=True)
    reader = csv.DictReader(line_iter, delimiter="\t")

    selected: dict[str, dict] = {}

    for row_index, row in enumerate(reader, start=1):
        category = str(row.get("category") or "").strip().lower()

        if category in TARGET_CATEGORIES and category not in selected:
            selected[category] = row
            print(f"  selected {category}: {row.get('index')}")

        if len(selected) == len(TARGET_CATEGORIES):
            break

        if row_index >= MAX_ROWS_TO_SCAN:
            break

    response.close()

    missing = [category for category in TARGET_CATEGORIES if category not in selected]
    if missing:
        raise RuntimeError(
            "Could not collect all target VRSBench categories. Missing: "
            + ", ".join(missing)
        )

    return [selected[category] for category in TARGET_CATEGORIES]


def find_specialist_model() -> Path | None:
    explicit = os.getenv("SATQUERY_RS_MODEL", "").strip()
    if explicit:
        path = Path(explicit)
        if path.exists():
            return path

    for root in (Path("/kaggle/input"), Path("/kaggle/working"), Path(".")):
        if not root.exists():
            continue

        matches = list(root.rglob("satquery_eurosat_specialist.pt"))
        if matches:
            return matches[0]

    return None


class Specialist:
    def __init__(self, path: Path):
        extra_files = {"metadata.json": ""}
        self.model = torch.jit.load(
            str(path),
            map_location="cpu",
            _extra_files=extra_files,
        ).eval()

        metadata = {}
        embedded = extra_files.get("metadata.json")
        if embedded:
            try:
                if isinstance(embedded, bytes):
                    embedded = embedded.decode("utf-8")
                metadata = json.loads(embedded)
            except Exception:
                metadata = {}

        self.classes = metadata.get("classes", EUROSAT_CLASSES)
        self.mean = metadata.get("normalization_mean", DEFAULT_MEAN)
        self.std = metadata.get("normalization_std", DEFAULT_STD)
        self.input_size = int(metadata.get("input_size", DEFAULT_INPUT_SIZE))
        self.path = path

    def predict(self, image: Image.Image, top_k: int = 3) -> list[dict]:
        image = image.convert("RGB").resize(
            (self.input_size, self.input_size),
            Image.Resampling.LANCZOS,
        )
        array = np.asarray(image, dtype=np.float32) / 255.0
        tensor = torch.from_numpy(array).permute(2, 0, 1).unsqueeze(0)

        mean = torch.tensor(self.mean, dtype=torch.float32).view(1, 3, 1, 1)
        std = torch.tensor(self.std, dtype=torch.float32).view(1, 3, 1, 1)
        tensor = (tensor - mean) / std

        with torch.inference_mode():
            scores = torch.softmax(self.model(tensor), dim=1)[0]

        values, indices = torch.topk(scores, k=min(top_k, len(self.classes)))
        return [
            {
                "label": self.classes[int(index)],
                "score_percent": round(float(value) * 100.0, 2),
            }
            for value, index in zip(values, indices)
        ]


def build_prompt(question: str, specialist_predictions: list[dict]) -> str:
    evidence = "No remote-sensing scene-specialist evidence was supplied."

    if specialist_predictions:
        evidence = ", ".join(
            f"{item['label']} ({item['score_percent']:.2f}% model score)"
            for item in specialist_predictions
        )

    return (
        "You are answering one VRSBench remote-sensing visual question.\n"
        "Give only the shortest direct answer that resolves the question. "
        "Do not explain your reasoning and do not add a sentence around a "
        "one-word or numeric answer.\n"
        "The SatQuery EuroSAT scene specialist evidence below is supporting "
        "evidence only, not ground truth.\n\n"
        f"SPECIALIST EVIDENCE: {evidence}\n\n"
        f"QUESTION: {question}"
    )


def ask_vlm(
    client: Groq,
    image: Image.Image,
    question: str,
    specialist_predictions: list[dict],
) -> str:
    data_url = _image_data_url(image)
    prompt = build_prompt(question, specialist_predictions)

    last_error = None
    for attempt in range(1, 4):
        try:
            completion = client.chat.completions.create(
                model=VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
                reasoning_effort="none",
                include_reasoning=False,
                temperature=0.0,
                max_completion_tokens=80,
            )
            answer = (completion.choices[0].message.content or "").strip()
            if answer:
                return answer
        except Exception as error:
            last_error = error
            if attempt < 3:
                time.sleep(2 * attempt)

    raise RuntimeError(f"Vision request failed after retries: {last_error}")


def summarize(records: list[dict]) -> tuple[dict, dict]:
    exact = sum(record["exact_match"] for record in records) / len(records)
    f1 = sum(record["token_f1"] for record in records) / len(records)

    by_category = defaultdict(list)
    for record in records:
        by_category[record["category"]].append(record)

    category_metrics = {}
    for category, items in sorted(by_category.items()):
        category_metrics[category] = {
            "count": len(items),
            "exact_match_percent": round(
                sum(item["exact_match"] for item in items) / len(items) * 100.0,
                2,
            ),
            "token_f1_percent": round(
                sum(item["token_f1"] for item in items) / len(items) * 100.0,
                2,
            ),
        }

    return (
        {
            "exact_match_percent": round(exact * 100.0, 2),
            "token_f1_percent": round(f1 * 100.0, 2),
        },
        category_metrics,
    )


def main() -> None:
    client = Groq(api_key=get_groq_key())
    subset = collect_category_subset()

    specialist_path = find_specialist_model()
    specialist = None

    if specialist_path:
        print(f"Remote-sensing specialist: {specialist_path}")
        specialist = Specialist(specialist_path)
    else:
        print(
            "WARNING: satquery_eurosat_specialist.pt was not found. The run "
            "will still test Qwen VQA, but upload the 3.72 MB SatQuery model to "
            "Kaggle if you want the diagnostic to include SatQuery specialist evidence."
        )

    scored_records = []

    for number, row in enumerate(subset, start=1):
        image = _decode_image(row["image"])
        category = str(row["category"]).strip()
        question = str(row["question"]).strip()
        reference = str(row["answer"]).strip()

        specialist_predictions = (
            specialist.predict(image, top_k=3)
            if specialist is not None
            else []
        )

        print(f"[{number:02d}/{len(subset)}] {category}: {question}")
        prediction = ask_vlm(
            client,
            image,
            question,
            specialist_predictions,
        )
        print(f"  reference: {reference}")
        print(f"  SatQuery:  {prediction}")

        scored_records.append(
            {
                "case_id": row.get("index") or f"case_{number:02d}",
                "task": "single_image_vqa",
                "category": category,
                "question": question,
                "reference_answer": reference,
                "model_answer": prediction,
                "exact_match": exact_match(reference, prediction),
                "token_f1": token_f1(reference, prediction),
                "specialist_predictions": specialist_predictions,
            }
        )

        # Gentle pacing for a free API tier.
        time.sleep(0.8)

    metrics, category_metrics = summarize(scored_records)

    result = {
        "schema_version": "1.0",
        "benchmark": "VRSBench",
        "subset_name": "VRSBench_MINI 12-category diagnostic subset",
        "source_repo": "YuJJJJin/VRSBench.tsv",
        "source_note": (
            "Records are drawn from a public derivative of the VRSBench test "
            "set. One deterministic example is used from each of the 12 VQA categories."
        ),
        "selection_method": SEED_NOTE,
        "sample_count": len(scored_records),
        "categories": TARGET_CATEGORIES,
        "model": VISION_MODEL,
        "satquery_rs_specialist_used": specialist is not None,
        "satquery_rs_specialist_model": (
            "SatQuery EuroSAT Scene Specialist v1"
            if specialist is not None
            else None
        ),
        "metrics": metrics,
        "category_metrics": category_metrics,
        "evaluation_note": (
            "This is a real public VRSBench subset diagnostic. Exact Match and "
            "token F1 are SatQuery local diagnostic metrics, not an official "
            "full VRSBench leaderboard score."
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "records": scored_records,
    }

    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\nDONE")
    print(f"Cases: {result['sample_count']}")
    print(f"Exact Match: {metrics['exact_match_percent']}%")
    print(f"Token F1: {metrics['token_f1_percent']}%")
    print(f"RS specialist used: {result['satquery_rs_specialist_used']}")
    print(f"Result: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
