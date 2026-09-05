from pathlib import Path

import numpy as np
import rasterio
from PIL import Image, ImageDraw, ImageOps


VISUAL_CHANGE_THRESHOLD = 0.10
PAIR_PREVIEW_SIZE = 720


def _is_raster(path):
    return Path(path).suffix.lower() in {".tif", ".tiff"}


def _same_raster_grid(before_path, after_path):
    with rasterio.open(before_path) as before, rasterio.open(after_path) as after:
        if before.crs != after.crs:
            return False, "CRS values do not match."

        if before.width != after.width or before.height != after.height:
            return False, "Raster dimensions do not match."

        if not np.allclose(
            tuple(before.transform)[:6],
            tuple(after.transform)[:6],
            rtol=0.0,
            atol=1e-7,
        ):
            return False, "Raster transforms/grids do not match."

        if not np.allclose(
            [
                before.bounds.left,
                before.bounds.bottom,
                before.bounds.right,
                before.bounds.top,
            ],
            [
                after.bounds.left,
                after.bounds.bottom,
                after.bounds.right,
                after.bounds.top,
            ],
            rtol=0.0,
            atol=1e-5,
        ):
            return False, "Raster bounds do not match."

    return True, "GeoTIFF grids are spatially compatible."


def validate_pair(before_path, after_path, before_meta, after_meta):
    same_dimensions = (
        before_meta.get("width") == after_meta.get("width")
        and before_meta.get("height") == after_meta.get("height")
    )

    both_georeferenced = bool(
        before_meta.get("georeferenced")
        and after_meta.get("georeferenced")
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
                "The two images have different pixel dimensions. "
                "Use a spatially corresponding/co-registered pair."
            ),
            "warnings": warnings,
        }

    if both_georeferenced:
        if not (_is_raster(before_path) and _is_raster(after_path)):
            return {
                "compatible": False,
                "same_dimensions": True,
                "both_georeferenced": True,
                "geospatial_compatible": False,
                "message": "Georeferenced pair validation requires GeoTIFF/TIFF inputs.",
                "warnings": warnings,
            }

        geospatial_compatible, grid_message = _same_raster_grid(
            before_path,
            after_path,
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
            "The images have matching dimensions and can be used for "
            "benchmark-style visual change VQA. Geospatial alignment "
            "cannot be independently verified because one or both inputs "
            "lack CRS/grid metadata."
        )
        warnings.append(
            "Treat the pair as visually corresponding only if the source "
            "dataset guarantees registration."
        )

    return {
        "compatible": True,
        "same_dimensions": True,
        "both_georeferenced": both_georeferenced,
        "geospatial_compatible": geospatial_compatible,
        "message": message,
        "warnings": warnings,
    }


def _load_preview_rgb(path):
    with Image.open(path) as image:
        return image.convert("RGB")


def create_visual_change_outputs(
    before_preview_path,
    after_preview_path,
    change_map_path,
    composite_path,
):
    before = _load_preview_rgb(before_preview_path)
    after = _load_preview_rgb(after_preview_path)

    if before.size != after.size:
        raise ValueError(
            "Generated previews do not have matching dimensions."
        )

    before_array = np.asarray(before, dtype=np.float32) / 255.0
    after_array = np.asarray(after, dtype=np.float32) / 255.0

    difference = np.mean(
        np.abs(after_array - before_array),
        axis=2,
    )

    changed_mask = difference >= VISUAL_CHANGE_THRESHOLD

    mean_difference_percent = float(
        np.mean(difference) * 100.0
    )

    changed_pixel_percent = float(
        np.mean(changed_mask) * 100.0
    )

    # High difference appears bright. This is intentionally a visual
    # comparison heuristic, not a semantic land-cover change mask.
    intensity = np.clip(
        difference / max(VISUAL_CHANGE_THRESHOLD * 3.0, 1e-6),
        0.0,
        1.0,
    )

    change_rgb = np.stack(
        [
            intensity,
            intensity * 0.55,
            intensity * 0.20,
        ],
        axis=-1,
    )

    change_image = Image.fromarray(
        (change_rgb * 255.0).astype(np.uint8),
        mode="RGB",
    )

    change_map_path = Path(change_map_path)
    composite_path = Path(composite_path)
    change_map_path.parent.mkdir(parents=True, exist_ok=True)
    change_image.save(change_map_path)

    panels = []
    for image in (before, after, change_image):
        panel = ImageOps.contain(
            image,
            (PAIR_PREVIEW_SIZE, PAIR_PREVIEW_SIZE),
            method=Image.Resampling.LANCZOS,
        )
        panels.append(panel)

    panel_width = max(panel.width for panel in panels)
    panel_height = max(panel.height for panel in panels)
    label_height = 38

    canvas = Image.new(
        "RGB",
        (panel_width * 3, panel_height + label_height),
        (16, 22, 32),
    )

    draw = ImageDraw.Draw(canvas)
    labels = ["BEFORE", "AFTER", "VISUAL DIFFERENCE"]

    for index, (panel, label) in enumerate(zip(panels, labels)):
        x = index * panel_width + (panel_width - panel.width) // 2
        y = label_height + (panel_height - panel.height) // 2
        canvas.paste(panel, (x, y))
        draw.text(
            (index * panel_width + 12, 11),
            label,
            fill=(238, 244, 250),
        )

    canvas.save(composite_path)

    return {
        "mean_visual_difference_percent": round(
            mean_difference_percent,
            3,
        ),
        "changed_pixel_percent": round(
            changed_pixel_percent,
            3,
        ),
        "visual_change_threshold": VISUAL_CHANGE_THRESHOLD,
        "interpretation": (
            "Pixel-level visual difference heuristic only; it does not "
            "by itself identify the physical cause or semantic class of change."
        ),
    }
