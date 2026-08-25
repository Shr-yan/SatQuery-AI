import os

import numpy as np
import rasterio
from rasterio.transform import from_origin


def create_dummy_optical_geotiff(
    output_path="data/raw/optical/lucknow_test.tif"
):
    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )

    width = 1024
    height = 1024
    num_bands = 4

    # Synthetic spatial patterns
    x = np.linspace(0, 10, width)
    y = np.linspace(0, 10, height)

    xx, yy = np.meshgrid(x, y)

    red = (
        np.sin(xx) * 500 + 1000
    ).astype(np.uint16)

    green = (
        np.cos(yy) * 600 + 1200
    ).astype(np.uint16)

    blue = (
        np.sin(xx + yy) * 400 + 800
    ).astype(np.uint16)

    nir = (
        np.sin(xx) *
        np.cos(yy) *
        2000 + 3000
    ).astype(np.uint16)

    data = np.stack(
        [red, green, blue, nir]
    )

    # UTM coordinates around Lucknow
    # EPSG:32644
    transform = from_origin(
        488000,
        2973500,
        10,
        10
    )

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=num_bands,
        dtype="uint16",
        crs="EPSG:32644",
        transform=transform,
    ) as dst:

        dst.write(data)

    print(
        f"[+] Created: {output_path}"
    )


if __name__ == "__main__":
    create_dummy_optical_geotiff()