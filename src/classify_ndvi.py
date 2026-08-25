import rasterio
import numpy as np


def classify_ndvi(
    input_file,
    output_file
):

    with rasterio.open(input_file) as src:

        ndvi = src.read(1)

        classification = np.zeros(
            ndvi.shape,
            dtype=np.uint8
        )

        classification[
            ndvi < 0
        ] = 1

        classification[
            (ndvi >= 0) &
            (ndvi < 0.3)
        ] = 2

        classification[
            (ndvi >= 0.3) &
            (ndvi < 0.6)
        ] = 3

        classification[
            ndvi >= 0.6
        ] = 4

        profile = src.profile.copy()

        profile.update(
            count=1,
            dtype="uint8"
        )

        with rasterio.open(
            output_file,
            "w",
            **profile
        ) as dst:

            dst.write(
                classification,
                1
            )


if __name__ == "__main__":

    classify_ndvi(
        "data/processed/results/query_ndvi.tif",
        "data/processed/results/query_ndvi_class.tif"
    )

    print(
        "NDVI classification created."
    )