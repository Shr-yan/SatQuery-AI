import rasterio
import numpy as np


def calculate_ndvi_statistics(
    ndvi_file
):

    with rasterio.open(ndvi_file) as src:

        ndvi = src.read(1).astype(
            "float32"
        )

    valid = ndvi[
        np.isfinite(ndvi)
    ]

    if len(valid) == 0:

        return {
            "mean": None,
            "minimum": None,
            "maximum": None
        }

    return {
        "mean": float(
            np.mean(valid)
        ),
        "minimum": float(
            np.min(valid)
        ),
        "maximum": float(
            np.max(valid)
        )
    }


def classify_vegetation(
    mean_ndvi
):

    if mean_ndvi is None:
        return "No valid vegetation data"

    if mean_ndvi < 0:
        return "Very low vegetation"

    if mean_ndvi < 0.2:
        return "Low vegetation"

    if mean_ndvi < 0.4:
        return "Moderate vegetation"

    if mean_ndvi < 0.6:
        return "Good vegetation"

    return "High vegetation"