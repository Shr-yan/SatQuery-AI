from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling


SUPPORTED_UPLOAD_EXTENSIONS = {
    ".tif",
    ".tiff",
    ".png",
    ".jpg",
    ".jpeg",
}


PREVIEW_MAX_SIZE = 1200


def _normalize_band(band):
    band = np.asarray(band, dtype=np.float32)
    finite_mask = np.isfinite(band)

    if not finite_mask.any():
        return np.zeros(band.shape, dtype=np.uint8)

    values = band[finite_mask]
    p2, p98 = np.percentile(values, (2, 98))

    if not np.isfinite(p2) or not np.isfinite(p98) or p98 <= p2:
        minimum = float(np.nanmin(values))
        maximum = float(np.nanmax(values))
        p2 = minimum
        p98 = maximum

    if p98 <= p2:
        return np.zeros(band.shape, dtype=np.uint8)

    scaled = np.clip((band - p2) / (p98 - p2), 0.0, 1.0)
    scaled[~finite_mask] = 0.0

    return (scaled * 255.0).astype(np.uint8)


def _preview_shape(width, height):
    scale = min(
        1.0,
        PREVIEW_MAX_SIZE / max(width, height),
    )

    return (
        max(1, int(round(height * scale))),
        max(1, int(round(width * scale))),
    )


def _process_raster(input_path, preview_path):
    warnings = []

    with rasterio.open(input_path) as src:
        if src.width <= 0 or src.height <= 0:
            raise ValueError("Raster has invalid dimensions.")

        if src.count <= 0:
            raise ValueError("Raster does not contain any bands.")

        out_height, out_width = _preview_shape(
            src.width,
            src.height,
        )

        sample = src.read(
            1,
            out_shape=(
                min(256, src.height),
                min(256, src.width),
            ),
            resampling=Resampling.nearest,
        )

        finite_fraction = float(
            np.isfinite(sample).sum() / sample.size
        )

        if finite_fraction == 0.0:
            raise ValueError(
                "Raster sample contains no finite pixel values."
            )

        if src.count >= 3:
            preview_bands = [1, 2, 3]
            preview_note = (
                "Preview uses raster bands 1, 2 and 3 as RGB. "
                "Band semantics will be validated more deeply in the "
                "analysis workflow."
            )

            data = src.read(
                preview_bands,
                out_shape=(
                    3,
                    out_height,
                    out_width,
                ),
                resampling=Resampling.bilinear,
            )

            rgb = np.stack(
                [
                    _normalize_band(data[0]),
                    _normalize_band(data[1]),
                    _normalize_band(data[2]),
                ],
                axis=-1,
            )

        else:
            preview_bands = [1]
            preview_note = (
                "Single-band raster preview is shown as grayscale. "
                "A single band may represent SAR, elevation, an index, "
                "or another raster product; modality is not assumed yet."
            )

            data = src.read(
                1,
                out_shape=(
                    out_height,
                    out_width,
                ),
                resampling=Resampling.bilinear,
            )

            gray = _normalize_band(data)
            rgb = np.stack([gray, gray, gray], axis=-1)

        Image.fromarray(rgb, mode="RGB").save(preview_path)

        crs = str(src.crs) if src.crs else None

        if crs is None:
            warnings.append(
                "No CRS was found. Single-image visual analysis can still "
                "run, but geospatial pair compatibility checks may fail."
            )

        metadata = {
            "filename": input_path.name,
            "format": "GeoTIFF/TIFF",
            "width": src.width,
            "height": src.height,
            "bands": src.count,
            "dtype": str(src.dtypes[0]),
            "crs": crs,
            "georeferenced": crs is not None,
            "bounds": [
                float(src.bounds.left),
                float(src.bounds.bottom),
                float(src.bounds.right),
                float(src.bounds.top),
            ],
            "resolution": [
                float(abs(src.res[0])),
                float(abs(src.res[1])),
            ],
            "nodata": (
                None
                if src.nodata is None
                else float(src.nodata)
            ),
            "finite_sample_percent": round(
                finite_fraction * 100.0,
                2,
            ),
            "preview_bands": preview_bands,
            "preview_note": preview_note,
            "modality_hint": (
                "optical_or_multispectral_candidate"
                if src.count >= 3
                else "single_band_modality_requires_classification"
            ),
            "warnings": warnings,
        }

    return metadata


def _process_standard_image(input_path, preview_path):
    warnings = [
        "PNG/JPEG input has no guaranteed geospatial metadata. "
        "It is suitable for single-image VQA/captioning and approved "
        "benchmark demonstrations, but not geospatial pair alignment."
    ]

    with Image.open(input_path) as image:
        image.verify()

    with Image.open(input_path) as image:
        original_mode = image.mode
        width, height = image.size

        if width <= 0 or height <= 0:
            raise ValueError("Image has invalid dimensions.")

        image = image.convert("RGB")
        image.thumbnail(
            (PREVIEW_MAX_SIZE, PREVIEW_MAX_SIZE),
            Image.Resampling.LANCZOS,
        )
        image.save(preview_path)

    return {
        "filename": input_path.name,
        "format": input_path.suffix.lower().lstrip(".").upper(),
        "width": width,
        "height": height,
        "bands": 3,
        "dtype": "uint8",
        "crs": None,
        "georeferenced": False,
        "bounds": None,
        "resolution": None,
        "nodata": None,
        "finite_sample_percent": 100.0,
        "preview_bands": ["R", "G", "B"],
        "preview_note": "Standard RGB preview generated from the uploaded image.",
        "original_mode": original_mode,
        "modality_hint": "visual_image_modality_requires_classification",
        "warnings": warnings,
    }


def inspect_uploaded_image(input_path, preview_path):
    input_path = Path(input_path)
    preview_path = Path(preview_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Uploaded image was not found: {input_path}"
        )

    extension = input_path.suffix.lower()

    if extension not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. Use GeoTIFF/TIFF, PNG, JPG or JPEG."
        )

    preview_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if extension in {".tif", ".tiff"}:
        metadata = _process_raster(
            input_path,
            preview_path,
        )
    else:
        metadata = _process_standard_image(
            input_path,
            preview_path,
        )

    metadata["supported_for_single_image_vqa"] = True
    metadata["validation_status"] = "valid"

    return metadata
