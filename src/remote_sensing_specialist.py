from __future__ import annotations

import json
import threading
from pathlib import Path

import numpy as np
import torch
from PIL import Image


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

MODEL_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "models"
)

MODEL_PATH = (
    MODEL_DIR
    / "satquery_eurosat_specialist.pt"
)

METRICS_PATH = (
    MODEL_DIR
    / "satquery_eurosat_metrics.json"
)

DEFAULT_CLASSES = [
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

_MODEL = None
_METADATA = None
_MODEL_LOCK = threading.Lock()


def _read_metrics_file():
    if not METRICS_PATH.exists():
        return {}

    try:
        return json.loads(
            METRICS_PATH.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return {}


def _load_model_and_metadata():
    global _MODEL
    global _METADATA

    if _MODEL is not None:
        return _MODEL, _METADATA or {}

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "SatQuery EuroSAT specialist model was not found at "
            f"{MODEL_PATH}."
        )

    with _MODEL_LOCK:
        if _MODEL is not None:
            return _MODEL, _METADATA or {}

        extra_files = {
            "metadata.json": ""
        }

        model = torch.jit.load(
            str(MODEL_PATH),
            map_location="cpu",
            _extra_files=extra_files,
        )

        model.eval()

        metadata = {}

        embedded = extra_files.get(
            "metadata.json",
            "",
        )

        if embedded:
            try:
                if isinstance(embedded, bytes):
                    embedded = embedded.decode(
                        "utf-8"
                    )

                metadata = json.loads(
                    embedded
                )
            except Exception:
                metadata = {}

        file_metadata = _read_metrics_file()

        if file_metadata:
            metadata = {
                **metadata,
                **file_metadata,
            }

        _MODEL = model
        _METADATA = metadata

    return _MODEL, _METADATA or {}


def specialist_status():
    metrics = _read_metrics_file()

    return {
        "available": MODEL_PATH.exists(),
        "model_path": str(MODEL_PATH),
        "metrics_path": str(METRICS_PATH),
        "model_name": metrics.get(
            "model_name",
            "SatQuery EuroSAT Scene Specialist v1",
        ),
        "dataset": metrics.get(
            "dataset",
            "EuroSAT RGB",
        ),
        "test_accuracy_percent": (
            round(
                float(metrics.get("test_accuracy")) * 100.0,
                2,
            )
            if metrics.get("test_accuracy") is not None
            else None
        ),
    }


def _prepare_tensor(
    image_path,
    metadata,
):
    input_size = int(
        metadata.get(
            "input_size",
            DEFAULT_INPUT_SIZE,
        )
    )

    mean = metadata.get(
        "normalization_mean",
        DEFAULT_MEAN,
    )

    std = metadata.get(
        "normalization_std",
        DEFAULT_STD,
    )

    with Image.open(image_path) as image:
        image = (
            image
            .convert("RGB")
            .resize(
                (input_size, input_size),
                Image.Resampling.LANCZOS,
            )
        )

        array = np.asarray(
            image,
            dtype=np.float32,
        ) / 255.0

    tensor = (
        torch.from_numpy(array)
        .permute(2, 0, 1)
        .unsqueeze(0)
    )

    mean_tensor = torch.tensor(
        mean,
        dtype=torch.float32,
    ).view(1, 3, 1, 1)

    std_tensor = torch.tensor(
        std,
        dtype=torch.float32,
    ).view(1, 3, 1, 1)

    tensor = (
        tensor - mean_tensor
    ) / std_tensor

    return tensor


def _applicability_note(
    input_metadata,
):
    preview_note = str(
        input_metadata.get(
            "preview_note",
            "",
        )
    )

    format_name = str(
        input_metadata.get(
            "format",
            "",
        )
    )

    if (
        "bands 1, 2 and 3 as RGB"
        in preview_note
    ):
        return (
            "The specialist is trained on EuroSAT RGB imagery, while this "
            "GeoTIFF preview uses bands 1-3 without confirmed true-color "
            "semantics. Treat the scene labels as weak supporting evidence only."
        )

    if format_name in {
        "PNG",
        "JPG",
        "JPEG",
    }:
        return (
            "The specialist is most applicable to optical RGB-like remote-sensing "
            "scene patches similar to EuroSAT. Scores are model outputs, not "
            "calibrated probabilities or ground-truth land-cover labels."
        )

    return (
        "The specialist is trained on EuroSAT RGB imagery. Use its scene labels "
        "as supporting evidence only; they are not calibrated confidence values "
        "and are not pixel-level classifications."
    )


def predict_scene(
    image_path,
    input_metadata=None,
    top_k=3,
):
    input_metadata = (
        input_metadata
        or {}
    )

    if not MODEL_PATH.exists():
        return {
            "available": False,
            "status": "model_not_found",
            "message": (
                "Remote-sensing specialist is not installed yet. "
                "Place satquery_eurosat_specialist.pt in "
                "data/processed/models/."
            ),
            "predictions": [],
        }

    model, metadata = (
        _load_model_and_metadata()
    )

    tensor = _prepare_tensor(
        image_path,
        metadata,
    )

    with torch.inference_mode():
        logits = model(tensor)
        scores = torch.softmax(
            logits,
            dim=1,
        )[0]

    classes = metadata.get(
        "classes",
        DEFAULT_CLASSES,
    )

    top_k = max(
        1,
        min(
            int(top_k),
            len(classes),
        ),
    )

    values, indices = torch.topk(
        scores,
        k=top_k,
    )

    predictions = []

    for value, index in zip(
        values.tolist(),
        indices.tolist(),
    ):
        predictions.append(
            {
                "label": classes[index],
                "model_score_percent": round(
                    float(value) * 100.0,
                    2,
                ),
            }
        )

    test_accuracy = metadata.get(
        "test_accuracy"
    )

    return {
        "available": True,
        "status": "completed",
        "model_name": metadata.get(
            "model_name",
            "SatQuery EuroSAT Scene Specialist v1",
        ),
        "model_type": metadata.get(
            "model_type",
            "remote_sensing_scene_classifier",
        ),
        "dataset": metadata.get(
            "dataset",
            "EuroSAT RGB",
        ),
        "parameter_count": metadata.get(
            "parameter_count",
            964170,
        ),
        "test_accuracy_percent": (
            round(
                float(test_accuracy) * 100.0,
                2,
            )
            if test_accuracy is not None
            else None
        ),
        "input_size": metadata.get(
            "input_size",
            DEFAULT_INPUT_SIZE,
        ),
        "predictions": predictions,
        "top_prediction": (
            predictions[0]
            if predictions
            else None
        ),
        "applicability_note": (
            _applicability_note(
                input_metadata
            )
        ),
        "score_note": (
            "Model scores are relative softmax outputs from the specialist and "
            "must not be presented as calibrated confidence."
        ),
    }
