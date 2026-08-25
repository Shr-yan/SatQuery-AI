import rasterio
import numpy as np


def calculate_ndvi(input_file, output_file):

    with rasterio.open(input_file) as src:

        red = src.read(3).astype("float32")
        nir = src.read(4).astype("float32")

        ndvi = (nir - red) / (
            nir + red + 1e-6
        )

        profile = src.profile.copy()

        profile.update(
            count=1,
            dtype="float32"
        )

        with rasterio.open(
            output_file,
            "w",
            **profile
        ) as dst:

            dst.write(ndvi, 1)


if __name__ == "__main__":

    calculate_ndvi(
        "data/processed/results/query_crop.tif",
        "data/processed/results/query_ndvi.tif"
    )

    print("NDVI created.")