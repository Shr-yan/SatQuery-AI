from pathlib import Path

import numpy as np
import rasterio
from PIL import Image, ImageDraw, ImageOps


FUSION_PREVIEW_SIZE = 720
WATER_SCORE_THRESHOLD = 0.66
BUILT_SCORE_THRESHOLD = 0.66


def _is_raster(path):
    return Path(path).suffix.lower() in {".tif", ".tiff"}


def _same_raster_grid(optical_path, sar_path):
    with rasterio.open(optical_path) as optical, rasterio.open(sar_path) as sar:
        if optical.crs != sar.crs:
            return False, "CRS values do not match."

        if optical.width != sar.width or optical.height != sar.height:
            return False, "Raster dimensions do not match."

        if not np.allclose(
            tuple(optical.transform)[:6],
            tuple(sar.transform)[:6],
            rtol=0.0,
            atol=1e-7,
        ):
            return False, "Raster transforms/grids do not match."

        if not np.allclose(
            [
                optical.bounds.left,
                optical.bounds.bottom,
                optical.bounds.right,
                optical.bounds.top,
            ],
            [
                sar.bounds.left,
                sar.bounds.bottom,
                sar.bounds.right,
                sar.bounds.top,
            ],
            rtol=0.0,
            atol=1e-5,
        ):
            return False, "Raster bounds do not match."

    return True, "Optical and SAR GeoTIFFs are spatially compatible."


def validate_crossmodal_pair(
    optical_path,
    sar_path,
    optical_meta,
    sar_meta,
):
    same_dimensions = (
        optical_meta.get("width") == sar_meta.get("width")
        and optical_meta.get("height") == sar_meta.get("height")
    )

    both_georeferenced = bool(
        optical_meta.get("georeferenced")
        and sar_meta.get("georeferenced")
    )

    warnings = []
    geospatial_compatible = False

    if not same_dimensions:
        return {
            "compatible": False,
            "same_dimensions": False,
            "both_georeferenced": both_georeferenced,
            "geospatial_compatible": False,
            "message": (
                "The optical and SAR inputs have different pixel dimensions. "
                "Use a co-registered/spatially corresponding pair."
            ),
            "warnings": warnings,
        }

    optical_bands = int(optical_meta.get("bands") or 0)
    sar_bands = int(sar_meta.get("bands") or 0)

    if optical_bands <= 0 or sar_bands <= 0:
        return {
            "compatible": False,
            "same_dimensions": True,
            "both_georeferenced": both_georeferenced,
            "geospatial_compatible": False,
            "message": "One of the inputs does not contain readable image bands.",
            "warnings": warnings,
        }

    if sar_bands > 2:
        warnings.append(
            "The SAR slot contains more than two bands. SatQuery will still "
            "use the supplied SAR preview, but the user-provided modality role "
            "cannot be independently proven from band count alone."
        )

    if optical_bands == 1:
        warnings.append(
            "The optical slot is single-band. This can be valid for panchromatic "
            "optical imagery, but RGB/true-color semantics are not assumed."
        )

    if both_georeferenced:
        if not (_is_raster(optical_path) and _is_raster(sar_path)):
            return {
                "compatible": False,
                "same_dimensions": True,
                "both_georeferenced": True,
                "geospatial_compatible": False,
                "message": (
                    "Geospatial optical-SAR compatibility checking requires "
                    "GeoTIFF/TIFF inputs."
                ),
                "warnings": warnings,
            }

        geospatial_compatible, grid_message = _same_raster_grid(
            optical_path,
            sar_path,
        )

        if not geospatial_compatible:
            return {
                "compatible": False,
                "same_dimensions": True,
                "both_georeferenced": True,
                "geospatial_compatible": False,
                "message": grid_message,
                "warnings": warnings,
            }

        message = grid_message
    else:
        message = (
            "The pair has matching dimensions and can be used for benchmark-style "
            "cross-modal VQA. Geospatial co-registration cannot be independently "
            "verified because one or both inputs lack CRS/grid metadata."
        )
        warnings.append(
            "Use PNG/JPEG cross-modal pairs only when the benchmark/source dataset "
            "guarantees that the images are spatially corresponding."
        )

    return {
        "compatible": True,
        "same_dimensions": True,
        "both_georeferenced": both_georeferenced,
        "geospatial_compatible": geospatial_compatible,
        "declared_modalities": {
            "optical": "user-labelled optical/multispectral input",
            "sar": "user-labelled SAR input",
        },
        "message": message,
        "warnings": warnings,
    }


def _load_rgb(path):
    with Image.open(path) as image:
        return image.convert("RGB")


def _safe_minmax(array):
    array = np.asarray(array, dtype=np.float32)
    minimum = float(np.nanmin(array))
    maximum = float(np.nanmax(array))
    if maximum <= minimum:
        return np.zeros_like(array, dtype=np.float32)
    return np.clip((array - minimum) / (maximum - minimum), 0.0, 1.0)


def _gradient_strength(gray):
    dy, dx = np.gradient(gray.astype(np.float32))
    magnitude = np.sqrt(dx * dx + dy * dy)
    return _safe_minmax(magnitude)


def create_crossmodal_outputs(
    optical_preview_path,
    sar_preview_path,
    fusion_map_path,
    composite_path,
):
    optical = _load_rgb(optical_preview_path)
    sar = _load_rgb(sar_preview_path)

    if optical.size != sar.size:
        raise ValueError(
            "Generated optical and SAR previews do not have matching dimensions."
        )

    optical_array = np.asarray(optical, dtype=np.float32) / 255.0
    sar_array = np.asarray(sar, dtype=np.float32) / 255.0

    optical_gray = np.mean(optical_array, axis=2)
    sar_gray = np.mean(sar_array, axis=2)

    optical_texture = _gradient_strength(optical_gray)
    sar_texture = _gradient_strength(sar_gray)

    # These scores intentionally use only relative display-level cues.
    # Water-like candidates combine relatively low/smooth SAR return with
    # relatively smooth/darker optical appearance. Built-up-like candidates
    # combine higher/rougher SAR return with stronger optical texture.
    water_score = np.clip(
        0.50 * (1.0 - sar_gray)
        + 0.25 * (1.0 - sar_texture)
        + 0.15 * (1.0 - optical_texture)
        + 0.10 * (1.0 - optical_gray),
        0.0,
        1.0,
    )

    built_score = np.clip(
        0.42 * sar_gray
        + 0.28 * sar_texture
        + 0.30 * optical_texture,
        0.0,
        1.0,
    )

    water_mask = water_score >= WATER_SCORE_THRESHOLD
    built_mask = built_score >= BUILT_SCORE_THRESHOLD

    # Blue = water-like relative evidence; orange/red = built-up-like
    # relative structural evidence; dim background preserves context.
    background = np.stack(
        [
            optical_gray * 0.20,
            optical_gray * 0.20,
            optical_gray * 0.20,
        ],
        axis=-1,
    )

    evidence = background.copy()
    evidence[..., 2] += water_score * 0.85
    evidence[..., 0] += built_score * 0.90
    evidence[..., 1] += built_score * 0.35
    evidence = np.clip(evidence, 0.0, 1.0)

    fusion_image = Image.fromarray(
        (evidence * 255.0).astype(np.uint8),
        mode="RGB",
    )

    fusion_map_path = Path(fusion_map_path)
    composite_path = Path(composite_path)
    fusion_map_path.parent.mkdir(parents=True, exist_ok=True)
    fusion_image.save(fusion_map_path)

    panels = []
    for image in (optical, sar, fusion_image):
        panel = ImageOps.contain(
            image,
            (FUSION_PREVIEW_SIZE, FUSION_PREVIEW_SIZE),
            method=Image.Resampling.LANCZOS,
        )
        panels.append(panel)

    panel_width = max(panel.width for panel in panels)
    panel_height = max(panel.height for panel in panels)
    label_height = 40

    canvas = Image.new(
        "RGB",
        (panel_width * 3, panel_height + label_height),
        (16, 22, 32),
    )

    draw = ImageDraw.Draw(canvas)
    labels = ["OPTICAL", "SAR", "CROSS-MODAL EVIDENCE"]

    for index, (panel, label) in enumerate(zip(panels, labels)):
        x = index * panel_width + (panel_width - panel.width) // 2
        y = label_height + (panel_height - panel.height) // 2
        canvas.paste(panel, (x, y))
        draw.text(
            (index * panel_width + 12, 12),
            label,
            fill=(238, 244, 250),
        )

    canvas.save(composite_path)

    return {
        "water_like_candidate_percent": round(
            float(np.mean(water_mask) * 100.0),
            3,
        ),
        "built_up_like_candidate_percent": round(
            float(np.mean(built_mask) * 100.0),
            3,
        ),
        "mean_sar_display_intensity_percent": round(
            float(np.mean(sar_gray) * 100.0),
            3,
        ),
        "mean_optical_texture_percent": round(
            float(np.mean(optical_texture) * 100.0),
            3,
        ),
        "mean_sar_texture_percent": round(
            float(np.mean(sar_texture) * 100.0),
            3,
        ),
        "water_score_threshold": WATER_SCORE_THRESHOLD,
        "built_score_threshold": BUILT_SCORE_THRESHOLD,
        "interpretation": (
            "Display-level cross-modal candidate evidence only. Blue emphasizes "
            "relative low/smooth-SAR + smooth/darker optical cues; orange/red "
            "emphasizes relative stronger/rougher-SAR + optical texture cues. "
            "These are not calibrated water or building classifications."
        ),
    }
