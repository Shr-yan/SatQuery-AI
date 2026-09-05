"""
SatQuery AI - CDVQA public-subset diagnostic runner.

This script evaluates a small number of public CDVQA change-VQA examples
without downloading the entire TEOChatlas dataset.  It downloads only:

- eval/CDVQA.json (TEOChatlas conversion of the public CDVQA evaluation data)
- eval/External_images.tar.gz (shared external evaluation image archive)

The archive is large (~6 GB), but it is used only inside Kaggle.  The script
extracts only the selected image pairs instead of unpacking the whole archive.

Output:
    /kaggle/working/cdvqa_public_subset_results.json

This is a diagnostic subset, not an official full CDVQA leaderboard score.
"""

from __future__ import annotations

import base64
import io
import json
import math
import os
import re
import tarfile
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import torch
from groq import Groq
from huggingface_hub import hf_hub_download
from PIL import Image, ImageChops, ImageDraw


MODEL_NAME = "qwen/qwen3.6-27b"
MAX_CASES = 10
HF_REPO = "jirvin16/TEOChatlas"
HF_JSON = "eval/CDVQA.json"
HF_IMAGES = "eval/External_images.tar.gz"
HF_CACHE = Path("/kaggle/working/hf_cache")
WORK_DIR = Path("/kaggle/working/cdvqa_subset")
OUTPUT_PATH = Path("/kaggle/working/cdvqa_public_subset_results.json")

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


SYSTEM_PROMPT = """
You are SatQuery AI's remote-sensing change-VQA benchmark assistant.

The supplied image is a three-panel view of the same location:
LEFT = BEFORE image, MIDDLE = AFTER image, RIGHT = absolute visual difference.

Answer only the benchmark question. Return the shortest possible answer and no
explanation. Use the two temporal images as the primary evidence. The optional
EuroSAT specialist output is scene-level supporting evidence only and may be
wrong for a particular local change.

Typical CDVQA answers are short closed-form answers such as yes/no, a land-cover
class, increased/decreased, or a percentage interval. Do not invent detail.
""".strip()


def find_file(filename: str) -> Path | None:
    for root in (Path("/kaggle/input"), Path("/kaggle/working")):
        if not root.exists():
            continue
        matches = list(root.rglob(filename))
        if matches:
            return matches[0]
    return None


def clean_question(text: str) -> str:
    text = str(text or "")
    text = text.replace("<video>", " ").replace("<image>", " ")
    text = re.sub(r"\s+", " ", text).strip()
    prefixes = [
        "This is a satellite image:",
        "This is a satellite image pair:",
        "This is a remote sensing image:",
    ]
    for prefix in prefixes:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()
    return text


def extract_qa(example: dict[str, Any]) -> tuple[str, str] | None:
    conversations = example.get("conversations")
    if isinstance(conversations, list) and len(conversations) >= 2:
        first = conversations[0]
        second = conversations[1]
        if isinstance(first, dict) and isinstance(second, dict):
            question = clean_question(
                first.get("value") or first.get("content") or first.get("text")
            )
            answer = str(
                second.get("value") or second.get("content") or second.get("text") or ""
            ).strip()
            if question and answer:
                return question, answer

    question = clean_question(
        example.get("question") or example.get("text") or example.get("prompt")
    )
    answer = str(
        example.get("answer") or example.get("ground_truth") or example.get("label") or ""
    ).strip()
    if question and answer:
        return question, answer
    return None


def classify_question(question: str) -> str:
    q = question.lower()

    if any(term in q for term in ("percentage", "percent", "ratio", "%")):
        return "change ratio"
    if any(term in q for term in ("largest", "maximum", "most changed", "greatest")):
        return "largest change"
    if any(term in q for term in ("smallest", "minimum", "least changed")):
        return "smallest change"
    if "changed from" in q or "change from" in q or "changed to" in q:
        return "semantic transition"
    if any(term in q for term in ("increase", "increased", "decrease", "decreased")):
        return "increase or decrease"
    if any(term in q for term in ("pre-event", "first image", "before image")):
        return "before-state question"
    if any(term in q for term in ("post-event", "second image", "after image")):
        return "after-state question"
    if q.startswith(("is ", "are ", "does ", "did ", "has ", "have ")):
        return "change existence"
    if any(term in q for term in ("more", "less", "higher", "lower")):
        return "temporal comparison"
    return "other change question"


def select_subset(data: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen_categories: set[str] = set()
    seen_questions: set[str] = set()
    deferred: list[dict[str, Any]] = []

    for index, example in enumerate(data):
        video = example.get("video") or example.get("images")
        if not isinstance(video, list) or len(video) < 2:
            continue

        qa = extract_qa(example)
        if qa is None:
            continue
        question, reference = qa
        signature = re.sub(r"\d+", "#", question.lower()).strip()
        if signature in seen_questions:
            continue
        seen_questions.add(signature)

        category = classify_question(question)
        item = {
            "source_index": index,
            "id": str(example.get("id") or example.get("question_id") or index),
            "question": question,
            "reference": reference,
            "category": category,
            "video": [str(video[0]), str(video[1])],
        }

        if category not in seen_categories:
            selected.append(item)
            seen_categories.add(category)
        else:
            deferred.append(item)

        if len(selected) >= limit:
            return selected[:limit]

    for item in deferred:
        if len(selected) >= limit:
            break
        selected.append(item)

    if len(selected) < limit:
        raise RuntimeError(
            f"Only {len(selected)} usable CDVQA examples were found; expected {limit}."
        )
    return selected[:limit]


def normalize_path(value: str) -> str:
    return str(value).replace("\\", "/").lstrip("./").strip("/")


def suffix_candidates(value: str) -> list[str]:
    parts = [part for part in normalize_path(value).split("/") if part]
    candidates = []
    for count in (5, 4, 3, 2, 1):
        if len(parts) >= count:
            candidates.append("/".join(parts[-count:]).lower())
    return candidates


def locate_tar_members(
    archive: tarfile.TarFile,
    targets: list[str],
) -> dict[str, tarfile.TarInfo]:
    target_suffixes = {target: suffix_candidates(target) for target in targets}
    basename_to_targets: dict[str, list[str]] = {}
    for target in targets:
        basename = Path(normalize_path(target)).name.lower()
        basename_to_targets.setdefault(basename, []).append(target)

    found: dict[str, tuple[int, tarfile.TarInfo]] = {}

    for member in archive:
        if not member.isfile():
            continue
        member_name = normalize_path(member.name).lower()
        basename = Path(member_name).name.lower()
        possible = basename_to_targets.get(basename, [])
        if not possible:
            continue

        for target in possible:
            best_score = 0
            for suffix in target_suffixes[target]:
                if member_name.endswith(suffix):
                    best_score = max(best_score, suffix.count("/") + 1)
                    break
            current = found.get(target)
            if best_score and (current is None or best_score > current[0]):
                found[target] = (best_score, member)

    missing = [target for target in targets if target not in found]
    if missing:
        preview = "\n  - ".join(missing[:5])
        raise FileNotFoundError(
            "Could not match some CDVQA image paths inside External_images.tar.gz:\n"
            f"  - {preview}"
        )

    return {target: found[target][1] for target in targets}


def read_member_image(archive: tarfile.TarFile, member: tarfile.TarInfo) -> Image.Image:
    handle = archive.extractfile(member)
    if handle is None:
        raise FileNotFoundError(member.name)
    data = handle.read()
    return Image.open(io.BytesIO(data)).convert("RGB")


def visual_difference(before: Image.Image, after: Image.Image) -> Image.Image:
    before = before.convert("RGB")
    after = after.convert("RGB").resize(before.size, Image.Resampling.BILINEAR)
    diff = np.asarray(ImageChops.difference(before, after), dtype=np.float32)
    scale = float(np.percentile(diff, 99.0))
    if scale < 1.0:
        scale = 1.0
    diff = np.clip(diff / scale * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(diff, mode="RGB")


def make_panel(before: Image.Image, after: Image.Image) -> Image.Image:
    size = 384
    before_r = before.resize((size, size), Image.Resampling.LANCZOS)
    after_r = after.resize((size, size), Image.Resampling.LANCZOS)
    diff_r = visual_difference(before_r, after_r)

    header = 34
    panel = Image.new("RGB", (size * 3, size + header), "white")
    panel.paste(before_r, (0, header))
    panel.paste(after_r, (size, header))
    panel.paste(diff_r, (size * 2, header))

    draw = ImageDraw.Draw(panel)
    labels = ["BEFORE", "AFTER", "ABSOLUTE VISUAL DIFFERENCE"]
    for i, label in enumerate(labels):
        draw.text((i * size + 10, 10), label, fill="black")
    return panel


def image_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def load_specialist() -> tuple[Any | None, Path | None]:
    model_path = find_file("satquery_eurosat_specialist.pt")
    if model_path is None:
        print("Remote-sensing specialist: not found (continuing without it)")
        return None, None

    model = torch.jit.load(str(model_path), map_location="cpu")
    model.eval()
    print(f"Remote-sensing specialist: {model_path}")
    return model, model_path


def specialist_evidence(model: Any | None, image: Image.Image) -> list[dict[str, Any]]:
    if model is None:
        return []

    resized = image.convert("RGB").resize((64, 64), Image.Resampling.BILINEAR)
    array = np.asarray(resized, dtype=np.float32) / 255.0
    array = (array - 0.5) / 0.25
    tensor = torch.from_numpy(array.transpose(2, 0, 1)).unsqueeze(0)

    with torch.no_grad():
        logits = model(tensor)
        probabilities = torch.softmax(logits, dim=1)[0]
        values, indices = torch.topk(probabilities, k=3)

    evidence = []
    for value, index in zip(values.tolist(), indices.tolist()):
        evidence.append(
            {
                "label": EUROSAT_CLASSES[index],
                "score_percent": round(value * 100.0, 2),
            }
        )
    return evidence


def format_specialist(before_evidence, after_evidence) -> str:
    if not before_evidence and not after_evidence:
        return "Remote-sensing specialist evidence was unavailable."

    def format_side(items):
        return ", ".join(
            f"{item['label']} ({item['score_percent']:.2f}%)" for item in items
        )

    return (
        "EuroSAT scene specialist (supporting evidence only):\n"
        f"BEFORE top-3: {format_side(before_evidence)}\n"
        f"AFTER top-3: {format_side(after_evidence)}"
    )


def ask_groq(
    client: Groq,
    question: str,
    panel: Image.Image,
    before_evidence: list[dict[str, Any]],
    after_evidence: list[dict[str, Any]],
) -> str:
    prompt = (
        f"QUESTION:\n{question}\n\n"
        f"{format_specialist(before_evidence, after_evidence)}\n\n"
        "Return only the answer, with no explanation."
    )

    data_url = image_to_data_url(panel)
    last_error = None

    for attempt in range(1, 4):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    },
                ],
                reasoning_effort="none",
                include_reasoning=False,
                temperature=0.0,
                max_completion_tokens=48,
            )
            answer = (response.choices[0].message.content or "").strip()
            if answer:
                return answer
            raise RuntimeError("Groq returned an empty answer.")
        except Exception as error:
            last_error = error
            if attempt == 3:
                break
            wait_seconds = 3 * attempt
            print(f"  Groq attempt {attempt} failed; retrying in {wait_seconds}s: {error}")
            time.sleep(wait_seconds)

    raise RuntimeError(f"Groq request failed after retries: {last_error}")


def normalize_answer(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s*%\s*", "%", text)
    text = re.sub(r"\s*-\s*", "-", text)
    text = re.sub(r"[^a-z0-9%\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def token_f1(reference: Any, prediction: Any) -> float:
    ref_tokens = normalize_answer(reference).split()
    pred_tokens = normalize_answer(prediction).split()

    if not ref_tokens and not pred_tokens:
        return 1.0
    if not ref_tokens or not pred_tokens:
        return 0.0

    overlap = Counter(ref_tokens) & Counter(pred_tokens)
    common = sum(overlap.values())
    if common == 0:
        return 0.0

    precision = common / len(pred_tokens)
    recall = common / len(ref_tokens)
    return 2.0 * precision * recall / (precision + recall)


def calculate_metrics(records: list[dict[str, Any]]) -> dict[str, float]:
    exact = [
        normalize_answer(item["reference_answer"])
        == normalize_answer(item["model_answer"])
        for item in records
    ]
    f1_values = [
        token_f1(item["reference_answer"], item["model_answer"])
        for item in records
    ]

    return {
        "exact_match_percent": round(100.0 * sum(exact) / len(exact), 2),
        "token_f1_percent": round(100.0 * sum(f1_values) / len(f1_values), 2),
    }


def main() -> None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY was not found. Add it as a Kaggle Secret/environment variable."
        )

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    HF_CACHE.mkdir(parents=True, exist_ok=True)

    print("Downloading CDVQA public evaluation metadata...")
    json_path = Path(
        hf_hub_download(
            repo_id=HF_REPO,
            repo_type="dataset",
            filename=HF_JSON,
            cache_dir=str(HF_CACHE),
        )
    )

    data = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise RuntimeError("Unexpected CDVQA.json format: expected a JSON list.")

    subset = select_subset(data, MAX_CASES)
    print(f"Selected {len(subset)} CDVQA diagnostic cases:")
    for item in subset:
        print(f"  {item['category']}: {item['id']}")

    print("\nDownloading the shared external evaluation image archive (~6 GB).")
    print("This is temporary Kaggle data; the script extracts only the selected image pairs.")
    archive_path = Path(
        hf_hub_download(
            repo_id=HF_REPO,
            repo_type="dataset",
            filename=HF_IMAGES,
            cache_dir=str(HF_CACHE),
        )
    )
    print(f"Image archive: {archive_path}")

    target_paths = []
    for item in subset:
        target_paths.extend(item["video"])
    target_paths = list(dict.fromkeys(target_paths))

    specialist, specialist_path = load_specialist()
    client = Groq(api_key=api_key)
    records: list[dict[str, Any]] = []

    print("Indexing selected images inside the archive...")
    with tarfile.open(archive_path, "r:gz") as archive:
        members = locate_tar_members(archive, target_paths)
        print(f"Matched {len(members)} required image files.")

        for number, item in enumerate(subset, start=1):
            before = read_member_image(archive, members[item["video"][0]])
            after = read_member_image(archive, members[item["video"][1]])
            panel = make_panel(before, after)

            before_evidence = specialist_evidence(specialist, before)
            after_evidence = specialist_evidence(specialist, after)

            print(f"[{number:02d}/{len(subset):02d}] {item['category']}: {item['question']}")
            print(f"  reference: {item['reference']}")

            answer = ask_groq(
                client,
                item["question"],
                panel,
                before_evidence,
                after_evidence,
            )
            print(f"  SatQuery:  {answer}")

            records.append(
                {
                    "case_id": item["id"],
                    "task": "change_vqa",
                    "category": item["category"],
                    "question": item["question"],
                    "reference_answer": item["reference"],
                    "model_answer": answer,
                    "before_specialist": before_evidence,
                    "after_specialist": after_evidence,
                }
            )

    metrics = calculate_metrics(records)
    categories = sorted({item["category"] for item in records})

    result = {
        "benchmark": "CDVQA",
        "subset_name": "Public CDVQA 10-case temporal diagnostic subset",
        "sample_count": len(records),
        "model": MODEL_NAME,
        "metrics": metrics,
        "records": records,
        "categories": categories,
        "satquery_rs_specialist_used": specialist is not None,
        "satquery_rs_specialist_model": (
            "SatQuery EuroSAT Scene Specialist v1" if specialist is not None else None
        ),
        "temporal_visual_evidence": "before + after + absolute visual difference panel",
        "source": {
            "dataset": "CDVQA",
            "image_source": "SECOND public image pairs",
            "distribution_source": "jirvin16/TEOChatlas external CDVQA evaluation conversion",
        },
        "evaluation_note": (
            "This is a small public CDVQA temporal diagnostic using SatQuery's "
            "normalized Exact Match and token-F1 metrics. It is not an official "
            "full CDVQA leaderboard score."
        ),
    }

    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\nDONE")
    print(f"Cases: {len(records)}")
    print(f"Exact Match: {metrics['exact_match_percent']}%")
    print(f"Token F1: {metrics['token_f1_percent']}%")
    print(f"RS specialist used: {specialist is not None}")
    print(f"Result: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
