
from pathlib import Path
import json

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds

from pystac_client import Client
import planetary_computer


STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

BANDS = ["B02", "B03", "B04", "B08"]

CHIP_SIZE = 256

# Approx. 40 km x 40 km geographic AOI
HALF_BOX_DEG = 0.18

OUTPUT_ROOT = Path(
    "data/processed/multiplace"
)

LOCATIONS = {

    "delhi": {
        "lat": 28.6139,
        "lon": 77.2090,
        "split": "train",
    },

    "jaipur": {
        "lat": 26.9124,
        "lon": 75.7873,
        "split": "train",
    },

    "bhopal": {
        "lat": 23.2599,
        "lon": 77.4126,
        "split": "val",
    },

    "hyderabad": {
        "lat": 17.3850,
        "lon": 78.4867,
        "split": "test",
    },
}


def find_scene(catalog, lat, lon):

    search_bbox = [
        lon - 0.02,
        lat - 0.02,
        lon + 0.02,
        lat + 0.02,
    ]

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=search_bbox,
        datetime="2025-11-01/2026-03-31",
        query={
            "eo:cloud_cover": {
                "lt": 5
            }
        },
        max_items=50,
    )

    items = list(search.items())

    items.sort(
        key=lambda x: x.properties.get(
            "eo:cloud_cover",
            100
        )
    )

    if not items:
        raise RuntimeError(
            "No suitable Sentinel-2 scene found."
        )

    return items[0]


def read_remote_aoi(
    asset,
    lat,
    lon
):

    href = planetary_computer.sign(
        asset.href
    )

    with rasterio.open(href) as src:

        geographic_bounds = [
            lon - HALF_BOX_DEG,
            lat - HALF_BOX_DEG,
            lon + HALF_BOX_DEG,
            lat + HALF_BOX_DEG,
        ]

        projected_bounds = transform_bounds(
            "EPSG:4326",
            src.crs,
            *geographic_bounds
        )

        window = from_bounds(
            *projected_bounds,
            transform=src.transform
        )

        # Keep requested area inside raster.
        window = window.intersection(
            rasterio.windows.Window(
                0,
                0,
                src.width,
                src.height
            )
        )

        array = src.read(
            1,
            window=window
        ).astype(np.float32)

    return array


def main():

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )

    catalog = Client.open(
        STAC_URL
    )

    all_records = []

    scene_metadata = {}

    for place, info in LOCATIONS.items():

        print("\n")
        print("=" * 60)
        print("PLACE:", place.upper())
        print("=" * 60)

        lat = info["lat"]
        lon = info["lon"]

        scene = find_scene(
            catalog,
            lat,
            lon
        )

        print("Scene:", scene.id)
        print("Date:", scene.datetime.date())
        print(
            "Cloud:",
            scene.properties.get(
                "eo:cloud_cover"
            )
        )
        print(
            "Tile:",
            scene.properties.get(
                "s2:mgrs_tile"
            )
        )

        scene_metadata[place] = {
            "scene_id": scene.id,
            "date": str(
                scene.datetime.date()
            ),
            "cloud_cover":
                scene.properties.get(
                    "eo:cloud_cover"
                ),
            "tile":
                scene.properties.get(
                    "s2:mgrs_tile"
                ),
            "split": info["split"],
        }

        arrays = []

        for band_name in BANDS:

            print(
                "Reading remote",
                band_name,
                "..."
            )

            asset = scene.assets[
                band_name
            ]

            band = read_remote_aoi(
                asset,
                lat,
                lon
            )

            print(
                band_name,
                "shape:",
                band.shape
            )

            arrays.append(band)

        # Ensure all bands have identical shape.
        min_height = min(
            a.shape[0]
            for a in arrays
        )

        min_width = min(
            a.shape[1]
            for a in arrays
        )

        arrays = [
            a[:min_height, :min_width]
            for a in arrays
        ]

        image = np.stack(
            arrays,
            axis=0
        )

        # Sentinel-2 L2A scaling
        image = np.clip(
            image / 10000.0,
            0.0,
            1.0
        )

        place_dir = (
            OUTPUT_ROOT
            / place
        )

        place_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        count = 0

        height = image.shape[1]
        width = image.shape[2]

        for y in range(
            0,
            height - CHIP_SIZE + 1,
            CHIP_SIZE
        ):

            for x in range(
                0,
                width - CHIP_SIZE + 1,
                CHIP_SIZE
            ):

                chip = image[
                    :,
                    y:y + CHIP_SIZE,
                    x:x + CHIP_SIZE
                ]

                # Reject chips dominated by zeros.
                zero_fraction = np.mean(
                    chip == 0
                )

                if zero_fraction > 0.10:
                    continue

                red = chip[2]
                nir = chip[3]

                valid = (
                    (red > 0)
                    | (nir > 0)
                )

                if not valid.any():
                    continue

                ndvi = (
                    (nir - red)
                    /
                    (nir + red + 1e-6)
                )

                target = float(
                    ndvi[valid].mean()
                )

                chip_name = (
                    f"{place}_{count:05d}.npy"
                )

                chip_path = (
                    place_dir
                    / chip_name
                )

                np.save(
                    chip_path,
                    chip.astype(
                        np.float16
                    )
                )

                all_records.append({
                    "path": str(
                        chip_path
                    ),
                    "place": place,
                    "split": info["split"],
                    "target": target,
                    "scene": scene.id,
                    "x": x,
                    "y": y,
                })

                count += 1

        print(
            "Saved chips:",
            count
        )

    manifest = pd.DataFrame(
        all_records
    )

    manifest_path = (
        OUTPUT_ROOT
        / "manifest.csv"
    )

    manifest.to_csv(
        manifest_path,
        index=False
    )

    with open(
        OUTPUT_ROOT / "scenes.json",
        "w"
    ) as f:

        json.dump(
            scene_metadata,
            f,
            indent=2
        )

    print("\n")
    print("=" * 60)
    print("MULTI-PLACE CACHE COMPLETE")
    print("=" * 60)

    print(
        manifest.groupby(
            ["split", "place"]
        ).size()
    )

    print(
        "\nTotal new chips:",
        len(manifest)
    )

    print(
        "Manifest:",
        manifest_path
    )


if __name__ == "__main__":
    main()
