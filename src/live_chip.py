import numpy as np
import rasterio

from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds as window_from_bounds


BAND_ORDER = [
    "B02",
    "B03",
    "B04",
    "B08",
]

CHIP_SIZE = 256


def read_band_chip(
    url,
    bbox,
    chip_size=CHIP_SIZE,
):

    min_lon, min_lat, max_lon, max_lat = bbox

    with rasterio.open(url) as src:

        raster_bounds = transform_bounds(
            "EPSG:4326",
            src.crs,
            min_lon,
            min_lat,
            max_lon,
            max_lat,
            densify_pts=21,
        )

        window = window_from_bounds(
            *raster_bounds,
            transform=src.transform,
        )

        data = src.read(
            1,
            window=window,
            out_shape=(
                chip_size,
                chip_size,
            ),
            resampling=Resampling.bilinear,
            boundless=True,
            fill_value=0,
        )

    return data


def build_model_chip(
    band_urls,
    bbox,
):

    bands = []

    for band in BAND_ORDER:

        if band not in band_urls:
            raise KeyError(
                f"Missing required band: {band}"
            )

        array = read_band_chip(
            band_urls[band],
            bbox,
        )

        bands.append(array)

    chip = np.stack(
        bands,
        axis=0,
    ).astype(np.float32)

    chip /= 10000.0

    chip = np.clip(
        chip,
        0.0,
        1.0,
    )

    return chip


def calculate_chip_ndvi(chip):

    if chip.shape[0] != 4:
        raise ValueError(
            "Expected four bands."
        )

    red = chip[2]
    nir = chip[3]

    denominator = nir + red

    ndvi = np.divide(
        nir - red,
        denominator,
        out=np.zeros_like(
            denominator,
            dtype=np.float32,
        ),
        where=np.abs(denominator) > 1e-6,
    )

    return ndvi


def summarize_chip_ndvi(chip):

    ndvi = calculate_chip_ndvi(chip)

    valid = np.isfinite(ndvi)

    if not np.any(valid):
        raise ValueError(
            "No valid NDVI pixels found."
        )

    values = ndvi[valid]

    return {
        "mean": float(np.mean(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "std": float(np.std(values)),
    }