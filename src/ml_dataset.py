import rasterio
import numpy as np
from pathlib import Path


OUTPUT_DIR = Path("data/processed/ml")
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def create_ndvi_dataset(
    red_file,
    nir_file,
    output_file
):

    with rasterio.open(red_file) as red_src:

        red = red_src.read(1).astype(
            np.float32
        )

    with rasterio.open(nir_file) as nir_src:

        nir = nir_src.read(1).astype(
            np.float32
        )

    ndvi = (
        (nir - red) /
        (nir + red + 1e-6)
    )

    valid = np.isfinite(ndvi)

    features = ndvi[valid]

    np.save(
        output_file,
        features
    )

    print(
        "Dataset created:"
    )

    print(
        "Samples:",
        len(features)
    )

    print(
        "Mean:",
        features.mean()
    )

    print(
        "Min:",
        features.min()
    )

    print(
        "Max:",
        features.max()
    )


if __name__ == "__main__":

    create_ndvi_dataset(
        "data/processed/results/real_B04_crop.tif",
        "data/processed/results/real_B08_crop.tif",
        OUTPUT_DIR / "ndvi_features.npy"
    )