import rasterio
from rasterio.warp import transform


def get_raster_bounds(file):

    with rasterio.open(file) as src:

        return {
            "crs": src.crs,
            "bounds": src.bounds
        }


def location_in_raster(
    latitude,
    longitude,
    file
):

    with rasterio.open(file) as src:

        x, y = transform(
            "EPSG:4326",
            src.crs,
            [longitude],
            [latitude]
        )

        x = x[0]
        y = y[0]

        bounds = src.bounds

        inside = (
            bounds.left <= x <= bounds.right
            and
            bounds.bottom <= y <= bounds.top
        )

        return inside


if __name__ == "__main__":

    file = (
        "data/raw/optical/"
        "sentinel2_test.tif"
    )

    # Test coordinates
    latitude = 26.8467
    longitude = 80.9462

    result = location_in_raster(
        latitude,
        longitude,
        file
    )

    print(
        "Location inside raster:",
        result
    )