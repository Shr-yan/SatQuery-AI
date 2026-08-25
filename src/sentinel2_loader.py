import os

import numpy as np
import rasterio


BAND_FILES = {
    "B02": "B02_10m.jp2",
    "B03": "B03_10m.jp2",
    "B04": "B04_10m.jp2",
    "B08": "B08_10m.jp2",
}


def load_sentinel2_bands(input_dir):
    """
    Load Sentinel-2 B02, B03, B04 and B08
    into a single NumPy array.

    Output order:
        Band 1 = B02 Blue
        Band 2 = B03 Green
        Band 3 = B04 Red
        Band 4 = B08 NIR
    """

    arrays = {}
    reference_profile = None

    for band_name, filename in BAND_FILES.items():

        path = os.path.join(
            input_dir,
            filename
        )

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Missing Sentinel-2 band: {path}"
            )

        print(f"[+] Reading {band_name}: {filename}")

        with rasterio.open(path) as src:

            data = src.read(1)

            print(
                f"    Shape: {data.shape}"
            )

            print(
                f"    Dtype: {data.dtype}"
            )

            print(
                f"    CRS: {src.crs}"
            )

            print(
                f"    Resolution: {src.res}"
            )

            if reference_profile is None:
                reference_profile = src.profile.copy()

            else:
                # Make sure all bands use the same spatial grid.
                if data.shape != arrays["B02"].shape:
                    raise ValueError(
                        f"{band_name} does not have "
                        "the same dimensions as B02."
                    )

                if src.crs != reference_profile["crs"]:
                    raise ValueError(
                        f"{band_name} has a different CRS."
                    )

                if src.transform != reference_profile["transform"]:
                    raise ValueError(
                        f"{band_name} has a different "
                        "spatial transform."
                    )

            arrays[band_name] = data

    # B02, B03, B04, B08
    stacked = np.stack(
        [
            arrays["B02"],
            arrays["B03"],
            arrays["B04"],
            arrays["B08"],
        ],
        axis=0
    )

    print("\n======================================")
    print("Sentinel-2 bands successfully loaded")
    print("======================================")

    print(
        "Array shape:",
        stacked.shape
    )

    print(
        "Array dtype:",
        stacked.dtype
    )

    print(
        "CRS:",
        reference_profile["crs"]
    )

    print(
        "Resolution:",
        reference_profile["transform"].a,
        "m"
    )

    return stacked, reference_profile


def save_combined_geotiff(
    output_path,
    data,
    profile
):
    """
    Save B02/B03/B04/B08 as a
    four-band GeoTIFF.
    """

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )

    profile = profile.copy()

    profile.update(
        driver="GTiff",
        count=4,
        dtype=data.dtype,
        compress="deflate"
    )

    with rasterio.open(
        output_path,
        "w",
        **profile
    ) as dst:

        dst.write(data)

        # Store Sentinel-2 band identity.
        dst.set_band_description(
            1,
            "B02 - Blue"
        )

        dst.set_band_description(
            2,
            "B03 - Green"
        )

        dst.set_band_description(
            3,
            "B04 - Red"
        )

        dst.set_band_description(
            4,
            "B08 - NIR"
        )

    print(
        f"\n[+] Combined GeoTIFF saved:"
        f"\n    {output_path}"
    )


if __name__ == "__main__":

    input_directory = (
        "data/raw/optical/sentinel2"
    )

    output_file = (
        "data/raw/optical/"
        "sentinel2_test.tif"
    )

    data, profile = load_sentinel2_bands(
        input_directory
    )

    save_combined_geotiff(
        output_file,
        data,
        profile
    )