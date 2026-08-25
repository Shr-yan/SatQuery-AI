import rasterio
import numpy as np


def calculate_real_ndvi(
    red_file,
    nir_file,
    output_file
):

    with rasterio.open(red_file) as red_src:

        red = red_src.read(1).astype(
            "float32"
        )

        profile = red_src.profile.copy()

    with rasterio.open(nir_file) as nir_src:

        nir = nir_src.read(1).astype(
            "float32"
        )

    ndvi = (
        (nir - red) /
        (nir + red + 1e-6)
    )

    profile.update(
        count=1,
        dtype="float32"
    )

    with rasterio.open(
        output_file,
        "w",
        **profile
    ) as dst:

        dst.write(
            ndvi,
            1
        )


if __name__ == "__main__":

    calculate_real_ndvi(
        "data/processed/results/real_B04_crop.tif",
        "data/processed/results/real_B08_crop.tif",
        "data/processed/results/real_ndvi_crop.tif"
    )

    print(
        "Real Sentinel-2 NDVI created."
    )