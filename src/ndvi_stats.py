import rasterio
import numpy as np


def get_ndvi_stats(file):

    with rasterio.open(file) as src:

        ndvi = src.read(1)

        valid = ndvi[
            np.isfinite(ndvi)
        ]

        return {
            "min": float(valid.min()),
            "max": float(valid.max()),
            "mean": float(valid.mean()),
            "median": float(
                np.median(valid)
            )
        }


if __name__ == "__main__":

    stats = get_ndvi_stats(
        "data/processed/results/query_ndvi.tif"
    )

    for key, value in stats.items():

        print(
            f"{key}: {value}"
        )