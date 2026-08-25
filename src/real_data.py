import requests
from pathlib import Path
from pystac_client import Client
import planetary_computer
from datetime import datetime
STAC_URL = (
    "https://planetarycomputer.microsoft.com/"
    "api/stac/v1"
)


def connect_catalog():

    catalog = Client.open(
        STAC_URL
    )

    return catalog


def select_best_scene(
    items,
    target_date=None
):

    candidates = []

    for item in items:

        cloud_cover = item.properties.get(
            "eo:cloud_cover"
        )

        if cloud_cover is None:
            continue

        if cloud_cover > 20:
            continue

        candidates.append(item)

    if not candidates:
        return None

    if target_date:

        target = datetime.strptime(
            target_date,
            "%Y-%m-%d"
        ).date()

        

        candidates.sort(
            key=lambda item: (
                abs(
                    item.datetime.date()
                    - target
                ),
                item.properties.get(
                    "eo:cloud_cover"
                )
            )
        )

    else:

        candidates.sort(
            key=lambda item:
            item.properties.get(
                "eo:cloud_cover"
            )
        )

    return candidates[0]

def download_asset(
    asset,
    output_path
):

    signed_href = planetary_computer.sign(
        asset.href
    )

    response = requests.get(
        signed_href,
        stream=True
    )

    response.raise_for_status()

    with open(
        output_path,
        "wb"
    ) as f:

        for chunk in response.iter_content(
            chunk_size=1024 * 1024
        ):

            if chunk:
                f.write(chunk)

    print(
        "Downloaded:",
        output_path
    )


if __name__ == "__main__":

    catalog = connect_catalog()

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        datetime="2026-01-01/2026-01-31",
        bbox=[
            80.90,
            26.80,
            80.97,
            26.88
        ],
        max_items=50
    )

    items = list(
        search.items()
    )

    print(
        "Sentinel-2 scenes found:",
        len(items)
    )

    best_scene = select_best_scene(
        items,
        "2026-01-15"
    )

    if best_scene is None:

        print(
            "No scene with cloud "
            "cover <= 20% found."
        )

        raise SystemExit

    print("\nBest scene:")

    print(
        "ID:",
        best_scene.id
    )

    print(
        "Date:",
        best_scene.datetime
    )

    print(
        "Cloud cover:",
        best_scene.properties.get(
            "eo:cloud_cover"
        )
    )

    target_date = datetime.strptime(
        "2026-01-15",
        "%Y-%m-%d"
    ).date()

    distance = abs(
        best_scene.datetime.date()
        - target_date
    ).days

    print(
        "Days from requested date:",
        distance
    )

    print("\nBand assets:")

    for band in [
        "B02",
        "B03",
        "B04",
        "B08"
    ]:

        asset = best_scene.assets.get(
            band
        )

        if asset:

            print(
                band,
                "->",
                asset.href
            )

    output_dir = Path(
        "data/raw/sentinel2"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # -------------------------
    # Download Red band
    # -------------------------

    red_asset = best_scene.assets[
        "B04"
    ]

    red_output = (
        output_dir /
        "B04_20260117.tif"
    )

    download_asset(
        red_asset,
        red_output
    )

    #  -------------------------
    #  Download NIR band
    #  -------------------------

    nir_asset = best_scene.assets[
        "B08"
    ]

    nir_output = (
        output_dir /
        "B08_20260117.tif"
    )

    download_asset(
        nir_asset,
        nir_output
    )