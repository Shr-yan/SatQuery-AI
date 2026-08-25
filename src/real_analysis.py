import rasterio
import numpy as np


def get_ndvi_statistics(ndvi_file):

    with rasterio.open(ndvi_file) as src:

        ndvi = src.read(1).astype(
            "float32"
        )

        nodata = src.nodata

    if nodata is not None:

        ndvi = ndvi[
            ndvi != nodata
        ]

    ndvi = ndvi[
        np.isfinite(ndvi)
    ]

    ndvi = ndvi[
        (ndvi >= -1) &
        (ndvi <= 1)
    ]

    return {
        "mean": float(np.mean(ndvi)),
        "min": float(np.min(ndvi)),
        "max": float(np.max(ndvi))
    }


if __name__ == "__main__":

    file = (
        "data/processed/results/"
        "real_ndvi_crop.tif"
    )

    stats = get_ndvi_statistics(
        file
    )

    print("Real NDVI statistics:")
    print("Mean:", stats["mean"])
    print("Min:", stats["min"])
    print("Max:", stats["max"])