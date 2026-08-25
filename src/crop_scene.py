import os

import rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer


def crop_around_point(
    input_file,
    output_file,
    latitude,
    longitude,
    size_km=5
):

    os.makedirs(
        os.path.dirname(output_file),
        exist_ok=True
    )

    with rasterio.open(input_file) as src:

        transformer = Transformer.from_crs(
            "EPSG:4326",
            src.crs,
            always_xy=True
        )

        x, y = transformer.transform(
            longitude,
            latitude
        )

        half_size = (
            size_km * 1000 / 2
        )

        min_x = x - half_size
        max_x = x + half_size
        min_y = y - half_size
        max_y = y + half_size

        window = from_bounds(
            min_x,
            min_y,
            max_x,
            max_y,
            src.transform
        )

        data = src.read(
            window=window
        )

        profile = src.profile.copy()

        profile.update({
            "height": data.shape[1],
            "width": data.shape[2],
            "transform": src.window_transform(
                window
            )
        })

        with rasterio.open(
            output_file,
            "w",
            **profile
        ) as dst:

            dst.write(data)


if __name__ == "__main__":

    crop_around_point(
        "data/raw/optical/lucknow_test.tif",
        "data/processed/results/lucknow_crop.tif",
        26.8381,
        80.9346001,
        size_km=5
    )

    print(
        "Crop created successfully."
    )