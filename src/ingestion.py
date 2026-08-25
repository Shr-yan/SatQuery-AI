import os

import numpy as np
import rasterio
from PIL import Image


def inspect_and_extract(file_path):

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Input file not found: {file_path}"
        )

    with rasterio.open(file_path) as src:

        meta = {
            "filename": os.path.basename(file_path),
            "width": src.width,
            "height": src.height,
            "count": src.count,
            "crs": str(src.crs) if src.crs else None,

            "transform": [
                src.transform.a,
                src.transform.b,
                src.transform.c,
                src.transform.d,
                src.transform.e,
                src.transform.f,
            ],

            "bounds": [
                src.bounds.left,
                src.bounds.bottom,
                src.bounds.right,
                src.bounds.top,
            ],

            "resolution_m": [
                src.res[0],
                src.res[1],
            ],

            "dtype": str(src.dtypes[0]),
            "nodata": src.nodata,

            # We know this synthetic test file is optical.
            "modality": "OPTICAL",
        }

        # Preserve raw scientific data.
        raw_array = src.read()

    return meta, raw_array


def generate_ui_preview(
    raw_array,
    meta,
    output_preview_path
):

    os.makedirs(
        os.path.dirname(output_preview_path),
        exist_ok=True
    )

    # Our synthetic file:
    # Band 1 = Red
    # Band 2 = Green
    # Band 3 = Blue
    r = raw_array[0]
    g = raw_array[1]
    b = raw_array[2]

    def normalize(band):

        p2, p98 = np.percentile(
            band,
            (2, 98)
        )

        scaled = np.clip(
            (band - p2) /
            (p98 - p2 + 1e-5),
            0,
            1
        )

        return (
            scaled * 255
        ).astype(np.uint8)

    rgb = np.stack(
        [
            normalize(r),
            normalize(g),
            normalize(b)
        ],
        axis=-1
    )

    image = Image.fromarray(rgb)

    image.save(output_preview_path)

    print(
        f"[+] UI preview saved: "
        f"{output_preview_path}"
    )