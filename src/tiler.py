import os

import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.windows import bounds
from rasterio.windows import transform


def generate_tiles(
    raw_array,
    meta,
    tile_size=512,
    overlap=64,
    output_dir="data/tiles"
):

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    bands, height, width = raw_array.shape

    stride = tile_size - overlap

    affine_transform = rasterio.Affine(
        *meta["transform"]
    )

    tile_manifests = []

    tile_count = 0

    for y in range(0, height, stride):

        for x in range(0, width, stride):

            y_end = min(
                y + tile_size,
                height
            )

            x_end = min(
                x + tile_size,
                width
            )

            crop = raw_array[
                :,
                y:y_end,
                x:x_end
            ]

            actual_height = y_end - y
            actual_width = x_end - x

            pad_y = tile_size - actual_height
            pad_x = tile_size - actual_width

            if pad_y > 0 or pad_x > 0:

                crop = np.pad(
                    crop,
                    (
                        (0, 0),
                        (0, pad_y),
                        (0, pad_x)
                    ),
                    mode="constant",
                    constant_values=0
                )

            window = Window(
                x,
                y,
                actual_width,
                actual_height
            )

            tile_transform = transform(
                window,
                affine_transform
            )

            tile_bounds = bounds(
                window,
                affine_transform
            )

            tile_id = (
                f"tile_{tile_count:03d}"
                f"_x{x}_y{y}"
            )

            npy_path = os.path.join(
                output_dir,
                f"{tile_id}.npy"
            )

            np.save(
                npy_path,
                crop
            )

            tile_info = {
                "tile_id": tile_id,

                "pixel_bbox": [
                    x,
                    y,
                    x_end,
                    y_end
                ],

                "actual_shape": [
                    bands,
                    actual_height,
                    actual_width
                ],

                "padded_shape": list(
                    crop.shape
                ),

                "padding": {
                    "bottom": pad_y,
                    "right": pad_x
                },

                "geographic_bounds": list(
                    tile_bounds
                ),

                "crs": meta["crs"],

                "transform": [
                    tile_transform.a,
                    tile_transform.b,
                    tile_transform.c,
                    tile_transform.d,
                    tile_transform.e,
                    tile_transform.f,
                ],

                "npy_path": npy_path
            }

            tile_manifests.append(
                tile_info
            )

            tile_count += 1

    print(
        f"[+] Generated "
        f"{len(tile_manifests)} tiles."
    )

    return tile_manifests