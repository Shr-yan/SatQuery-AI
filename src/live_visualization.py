from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from live_chip import (
    calculate_chip_ndbi,
    calculate_chip_ndvi,
    calculate_chip_ndwi,
)


def stretch_rgb(
    rgb,
):

    output = np.zeros_like(
        rgb,
        dtype=np.float32,
    )

    for channel in range(3):

        band = rgb[
            :,
            :,
            channel
        ]

        valid = (
            np.isfinite(band)
            & (band > 0)
        )

        if not np.any(valid):
            continue

        low = np.percentile(
            band[valid],
            2,
        )

        high = np.percentile(
            band[valid],
            98,
        )

        if high <= low:
            continue

        output[
            :,
            :,
            channel
        ] = (
            (band - low)
            / (high - low)
        )

    return np.clip(
        output,
        0.0,
        1.0,
    )


def create_rgb_preview(
    chip,
    output_path,
):

    red = chip[2]
    green = chip[1]
    blue = chip[0]

    rgb = np.stack(
        [
            red,
            green,
            blue,
        ],
        axis=-1,
    )

    rgb = stretch_rgb(
        rgb
    )

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(
        figsize=(9, 9)
    )

    plt.imshow(
        rgb
    )

    plt.title(
        "Sentinel-2 RGB Preview"
    )

    plt.axis(
        "off"
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close()

    return str(
        output_path
    )


def create_index_preview(
    index,
    output_path,
    title,
    label,
    cmap,
):

    masked_index = (
        np.ma.masked_invalid(
            index
        )
    )

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(
        figsize=(10, 9)
    )

    image = plt.imshow(
        masked_index,
        cmap=cmap,
        vmin=-1,
        vmax=1,
    )

    plt.title(
        title
    )

    plt.axis(
        "off"
    )

    colorbar = plt.colorbar(
        image,
        fraction=0.046,
        pad=0.04,
    )

    colorbar.set_label(
        label
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close()

    return str(
        output_path
    )


def create_ndvi_preview(
    chip,
    output_path,
    valid_mask=None,
):

    ndvi = calculate_chip_ndvi(
        chip,
        valid_mask=valid_mask,
    )

    return create_index_preview(
        index=ndvi,
        output_path=output_path,
        title=(
            "Sentinel-2 NDVI "
            "(SCL Quality Masked)"
        ),
        label="NDVI",
        cmap="RdYlGn",
    )


def create_ndwi_preview(
    chip,
    output_path,
    valid_mask=None,
):

    ndwi = calculate_chip_ndwi(
        chip,
        valid_mask=valid_mask,
    )

    return create_index_preview(
        index=ndwi,
        output_path=output_path,
        title=(
            "Sentinel-2 NDWI "
            "(SCL Quality Masked)"
        ),
        label="NDWI",
        cmap="BrBG",
    )


def create_ndbi_preview(
    chip,
    swir,
    output_path,
    valid_mask=None,
):

    ndbi = calculate_chip_ndbi(
        chip,
        swir,
        valid_mask=valid_mask,
    )

    return create_index_preview(
        index=ndbi,
        output_path=output_path,
        title=(
            "Sentinel-2 NDBI "
            "(SCL Quality Masked)"
        ),
        label="NDBI",
        cmap="RdBu_r",
    )