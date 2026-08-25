import rasterio


def read_scene_metadata(file):

    with rasterio.open(file) as src:

        metadata = {
            "crs": str(src.crs),
            "width": src.width,
            "height": src.height,
            "bands": src.count,
            "dtype": src.dtypes,
            "bounds": {
                "left": src.bounds.left,
                "bottom": src.bounds.bottom,
                "right": src.bounds.right,
                "top": src.bounds.top
            },
            "transform": str(src.transform)
        }

    return metadata


if __name__ == "__main__":

    file = (
        "data/raw/optical/"
        "sentinel2_test.tif"
    )

    metadata = read_scene_metadata(
        file
    )

    for key, value in metadata.items():

        print(
            f"{key}: {value}"
        )