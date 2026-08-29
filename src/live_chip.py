import numpy as np
import rasterio

from rasterio.enums import Resampling
from rasterio.warp import transform_bounds
from rasterio.windows import (
    from_bounds as window_from_bounds,
)


BAND_ORDER = [
    "B02",
    "B03",
    "B04",
    "B08",
]

MODEL_CHIP_SIZE = 256
DISPLAY_CHIP_SIZE = 768


INVALID_SCL_CLASSES = {
    0,   # No data
    1,   # Saturated / defective
    2,   # Dark / shadow pixels
    3,   # Cloud shadow
    8,   # Medium probability cloud
    9,   # High probability cloud
    10,  # Thin cirrus
    11,  # Snow / ice
}


def read_band_chip(
    url,
    bbox,
    chip_size=MODEL_CHIP_SIZE,
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


def read_scl_chip(
    url,
    bbox,
    chip_size=MODEL_CHIP_SIZE,
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

        scl = src.read(
            1,
            window=window,
            out_shape=(
                chip_size,
                chip_size,
            ),
            resampling=Resampling.nearest,
            boundless=True,
            fill_value=0,
        )

    return scl.astype(
        np.uint8
    )


def build_chip(
    band_urls,
    bbox,
    chip_size,
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
            chip_size=chip_size,
        )

        bands.append(
            array
        )

    chip = np.stack(
        bands,
        axis=0,
    ).astype(
        np.float32
    )

    # Sentinel-2 L2A reflectance scaling.
    chip /= 10000.0

    chip = np.clip(
        chip,
        0.0,
        1.0,
    )

    return chip


def build_model_chip(
    band_urls,
    bbox,
):

    return build_chip(
        band_urls,
        bbox,
        MODEL_CHIP_SIZE,
    )


def build_display_chip(
    band_urls,
    bbox,
):

    return build_chip(
        band_urls,
        bbox,
        DISPLAY_CHIP_SIZE,
    )


def build_scl_valid_mask(
    scl,
):

    valid = np.ones(
        scl.shape,
        dtype=bool,
    )

    for class_id in INVALID_SCL_CLASSES:

        valid &= (
            scl != class_id
        )

    return valid


def calculate_chip_ndvi(
    chip,
    valid_mask=None,
):

    if chip.shape[0] != 4:

        raise ValueError(
            "Expected four bands."
        )

    red = chip[2]
    nir = chip[3]

    raster_valid = np.any(
        chip > 0,
        axis=0,
    )

    denominator = (
        nir + red
    )

    valid = (
        raster_valid
        & np.isfinite(red)
        & np.isfinite(nir)
        & (
            np.abs(
                denominator
            )
            > 1e-6
        )
    )

    if valid_mask is not None:

        if (
            valid_mask.shape
            != red.shape
        ):

            raise ValueError(
                "NDVI validity mask has "
                "incorrect shape."
            )

        valid &= valid_mask

    ndvi = np.full(
        red.shape,
        np.nan,
        dtype=np.float32,
    )

    ndvi[valid] = (
        (
            nir[valid]
            - red[valid]
        )
        /
        denominator[valid]
    )

    return ndvi


def summarize_chip_ndvi(
    chip,
    valid_mask=None,
):

    ndvi = calculate_chip_ndvi(
        chip,
        valid_mask=valid_mask,
    )

    valid = np.isfinite(
        ndvi
    )

    if not np.any(valid):

        raise ValueError(
            "No valid NDVI pixels found."
        )

    values = ndvi[
        valid
    ]

    return {
        "mean": float(
            np.mean(values)
        ),

        "min": float(
            np.min(values)
        ),

        "max": float(
            np.max(values)
        ),

        "std": float(
            np.std(values)
        ),

        "valid_pixel_fraction": float(
            np.mean(valid)
        ),
    }


def summarize_chip_quality(
    chip,
):

    if chip.shape[0] != 4:

        raise ValueError(
            "Expected four bands."
        )

    all_zero = np.all(
        chip == 0,
        axis=0,
    )

    zero_fraction = float(
        np.mean(all_zero)
    )

    finite_fraction = float(
        np.mean(
            np.isfinite(chip)
        )
    )

    band_means = {
        BAND_ORDER[index]:
        float(
            np.mean(
                chip[index]
            )
        )
        for index in range(4)
    }

    return {
        "zero_fraction":
        zero_fraction,

        "finite_fraction":
        finite_fraction,

        "band_means":
        band_means,
    }


def summarize_scl_quality(
    scl,
):

    valid_mask = (
        build_scl_valid_mask(
            scl
        )
    )

    cloud_classes = (
        (scl == 8)
        | (scl == 9)
        | (scl == 10)
    )

    shadow_classes = (
        (scl == 2)
        | (scl == 3)
    )

    return {

        "valid_fraction": float(
            np.mean(
                valid_mask
            )
        ),

        "invalid_fraction": float(
            1.0
            - np.mean(
                valid_mask
            )
        ),

        "cloud_fraction": float(
            np.mean(
                cloud_classes
            )
        ),

        "shadow_fraction": float(
            np.mean(
                shadow_classes
            )
        ),

        "snow_fraction": float(
            np.mean(
                scl == 11
            )
        ),
    }