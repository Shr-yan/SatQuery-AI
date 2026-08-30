import numpy as np
import rasterio

from rasterio.enums import Resampling
from rasterio.warp import transform_bounds
from rasterio.windows import (
    from_bounds as window_from_bounds,
)


# IMPORTANT:
# Keep these four bands unchanged.
# The trained CNN expects exactly
# B02, B03, B04 and B08.
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


def read_reflectance_band(
    url,
    bbox,
    chip_size=DISPLAY_CHIP_SIZE,
):
    """
    Read one Sentinel-2 reflectance band
    and convert it to scaled reflectance.

    This is also used for B11, which has
    a native 20 m resolution. Rasterio
    resamples it to the requested chip size.
    """

    data = read_band_chip(
        url,
        bbox,
        chip_size=chip_size,
    )

    data = data.astype(
        np.float32
    )

    data /= 10000.0

    data = np.clip(
        data,
        0.0,
        1.0,
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


def calculate_normalized_difference(
    band_a,
    band_b,
    valid_mask=None,
):
    """
    Generic normalized difference:

        (band_a - band_b)
        -----------------
        (band_a + band_b)
    """

    if (
        band_a.shape
        != band_b.shape
    ):
        raise ValueError(
            "Index bands must have "
            "the same shape."
        )

    denominator = (
        band_a + band_b
    )

    raster_valid = (
        (
            band_a > 0
        )
        | (
            band_b > 0
        )
    )

    valid = (
        raster_valid
        & np.isfinite(
            band_a
        )
        & np.isfinite(
            band_b
        )
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
            != band_a.shape
        ):
            raise ValueError(
                "Validity mask has "
                "incorrect shape."
            )

        valid &= valid_mask

    index = np.full(
        band_a.shape,
        np.nan,
        dtype=np.float32,
    )

    index[valid] = (
        (
            band_a[valid]
            - band_b[valid]
        )
        /
        denominator[valid]
    )

    return index


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

    return calculate_normalized_difference(
        nir,
        red,
        valid_mask=valid_mask,
    )


def calculate_chip_ndwi(
    chip,
    valid_mask=None,
):
    """
    McFeeters NDWI:

        (Green - NIR)
        -------------
        (Green + NIR)

    Sentinel-2:
        Green = B03
        NIR   = B08
    """

    if chip.shape[0] != 4:

        raise ValueError(
            "Expected four bands."
        )

    green = chip[1]
    nir = chip[3]

    return calculate_normalized_difference(
        green,
        nir,
        valid_mask=valid_mask,
    )


def calculate_chip_ndbi(
    chip,
    swir,
    valid_mask=None,
):
    """
    NDBI:

        (SWIR - NIR)
        ------------
        (SWIR + NIR)

    Sentinel-2:
        NIR  = B08
        SWIR = B11

    B11 is supplied separately so the
    four-band CNN input remains unchanged.
    """

    if chip.shape[0] != 4:

        raise ValueError(
            "Expected four-band "
            "Sentinel-2 chip."
        )

    nir = chip[3]

    if (
        swir.shape
        != nir.shape
    ):
        raise ValueError(
            "B11/SWIR shape must match "
            "the Sentinel-2 chip."
        )

    return calculate_normalized_difference(
        swir,
        nir,
        valid_mask=valid_mask,
    )


def summarize_index(
    index,
):

    valid = np.isfinite(
        index
    )

    if not np.any(valid):

        raise ValueError(
            "No valid index pixels found."
        )

    values = index[
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


def summarize_chip_ndvi(
    chip,
    valid_mask=None,
):

    ndvi = calculate_chip_ndvi(
        chip,
        valid_mask=valid_mask,
    )

    return summarize_index(
        ndvi
    )


def summarize_chip_ndwi(
    chip,
    valid_mask=None,
):

    ndwi = calculate_chip_ndwi(
        chip,
        valid_mask=valid_mask,
    )

    return summarize_index(
        ndwi
    )


def summarize_chip_ndbi(
    chip,
    swir,
    valid_mask=None,
):

    ndbi = calculate_chip_ndbi(
        chip,
        swir,
        valid_mask=valid_mask,
    )

    return summarize_index(
        ndbi
    )


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
        np.mean(
            all_zero
        )
    )

    finite_fraction = float(
        np.mean(
            np.isfinite(
                chip
            )
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