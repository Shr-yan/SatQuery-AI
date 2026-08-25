import rasterio
import numpy as np


INPUT = "data/raw/optical/sentinel2_test.tif"


def validate_geotiff(path):

    print("Validating:", path)

    with rasterio.open(path) as src:

        print("CRS:", src.crs)
        print("Width:", src.width)
        print("Height:", src.height)
        print("Bands:", src.count)
        print("Dtypes:", src.dtypes)
        print("Bounds:", src.bounds)

        # Basic checks
        if src.count != 4:
            raise ValueError(
                f"Expected 4 bands, found {src.count}"
            )

        if src.width == 0 or src.height == 0:
            raise ValueError(
                "Raster has invalid dimensions"
            )

        if src.crs is None:
            raise ValueError(
                "Raster has no CRS"
            )

        # Read a small window instead of loading
        # the entire 10,980 x 10,980 image.
        window = rasterio.windows.Window(
            0,
            0,
            min(256, src.width),
            min(256, src.height)
        )

        sample = src.read(window=window)

        print(
            "Sample shape:",
            sample.shape
        )

        if not np.isfinite(sample).all():
            raise ValueError(
                "Raster contains NaN or infinite values"
            )

    print("Validation successful!")


if __name__ == "__main__":
    validate_geotiff(INPUT)