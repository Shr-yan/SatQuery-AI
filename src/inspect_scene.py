import rasterio


def inspect_scene(file):

    with rasterio.open(file) as src:

        print("File:", file)
        print("CRS:", src.crs)
        print("Width:", src.width)
        print("Height:", src.height)
        print("Bands:", src.count)
        print("Dtype:", src.dtypes)
        print("Bounds:", src.bounds)
        print("Resolution:", src.res)


if __name__ == "__main__":

    inspect_scene(
        "data/raw/optical/lucknow_test.tif"
    )