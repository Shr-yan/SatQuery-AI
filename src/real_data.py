from datetime import datetime, timedelta

import planetary_computer
from pystac_client import Client


STAC_URL = (
    "https://planetarycomputer.microsoft.com/"
    "api/stac/v1"
)

COLLECTION = "sentinel-2-l2a"

REQUIRED_BANDS = [
    "B02",
    "B03",
    "B04",
    "B08",
]


def connect_catalog():

    return Client.open(STAC_URL)


def search_sentinel2(
    bbox,
    target_date=None,
    days_before=30,
    days_after=30,
    max_cloud=20,
    max_items=100,
):

    if len(bbox) != 4:
        raise ValueError(
            "bbox must be "
            "[min_lon, min_lat, max_lon, max_lat]"
        )

    if target_date:

        target = datetime.strptime(
            target_date,
            "%Y-%m-%d",
        )

        start = (
            target - timedelta(days=days_before)
        ).date()

        end = (
            target + timedelta(days=days_after)
        ).date()

    else:

        end = datetime.utcnow().date()

        start = end - timedelta(days=90)

    date_range = f"{start}/{end}"

    catalog = connect_catalog()

    search = catalog.search(
        collections=[COLLECTION],
        bbox=bbox,
        datetime=date_range,
        max_items=max_items,
    )

    items = list(search.items())

    candidates = []

    for item in items:

        cloud = item.properties.get(
            "eo:cloud_cover"
        )

        if cloud is None:
            continue

        if cloud > max_cloud:
            continue

        if not all(
            band in item.assets
            for band in REQUIRED_BANDS
        ):
            continue

        candidates.append(item)

    return candidates


def select_best_scene(
    items,
    target_date=None,
):

    if not items:
        return None

    if target_date:

        target = datetime.strptime(
            target_date,
            "%Y-%m-%d",
        ).date()

        return min(
            items,
            key=lambda item: (
                abs(
                    (
                        item.datetime.date()
                        - target
                    ).days
                ),
                item.properties.get(
                    "eo:cloud_cover",
                    100,
                ),
            ),
        )

    return min(
        items,
        key=lambda item:
        item.properties.get(
            "eo:cloud_cover",
            100,
        ),
    )


def get_signed_band_urls(item):

    if item is None:
        raise ValueError(
            "Scene item cannot be None."
        )

    urls = {}

    for band in REQUIRED_BANDS:

        asset = item.assets.get(band)

        if asset is None:
            raise KeyError(
                f"Scene is missing band {band}"
            )

        urls[band] = (
            planetary_computer.sign(
                asset.href
            )
        )

    return urls


def get_scene_info(item):

    if item is None:
        return None

    return {
        "id": item.id,
        "date": (
            item.datetime.date().isoformat()
        ),
        "cloud_cover": (
            item.properties.get(
                "eo:cloud_cover"
            )
        ),
        "tile": (
            item.properties.get(
                "s2:mgrs_tile"
            )
        ),
    }


if __name__ == "__main__":

    # Small standalone test around Lucknow.
    test_bbox = [
        80.90,
        26.80,
        80.97,
        26.88,
    ]

    target_date = "2026-01-15"

    scenes = search_sentinel2(
        bbox=test_bbox,
        target_date=target_date,
    )

    print(
        "Candidate scenes:",
        len(scenes)
    )

    best = select_best_scene(
        scenes,
        target_date=target_date,
    )

    if best is None:

        print("No suitable scene found.")

    else:

        info = get_scene_info(best)

        print("Selected scene:")
        print(info)

        urls = get_signed_band_urls(best)

        print(
            "Available signed bands:",
            list(urls.keys())
        )