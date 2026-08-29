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

QUALITY_BAND = "SCL"


def connect_catalog():

    return Client.open(
        STAC_URL
    )


def search_sentinel2(
    bbox,
    target_date=None,
    days_before=30,
    days_after=30,
    max_cloud=20,
    max_items=100,
):

    catalog = connect_catalog()

    if target_date:

        target = datetime.strptime(
            target_date,
            "%Y-%m-%d",
        )

        start = (
            target
            - timedelta(
                days=days_before
            )
        )

        end = (
            target
            + timedelta(
                days=days_after
            )
        )

    else:

        end = datetime.utcnow()

        start = (
            end
            - timedelta(
                days=90
            )
        )

    date_range = (
        f"{start.strftime('%Y-%m-%d')}"
        "/"
        f"{end.strftime('%Y-%m-%d')}"
    )

    search = catalog.search(
        collections=[
            COLLECTION
        ],
        bbox=bbox,
        datetime=date_range,
        query={
            "eo:cloud_cover": {
                "lte": max_cloud
            }
        },
        max_items=max_items,
    )

    items = list(
        search.items()
    )

    valid_items = []

    for item in items:

        assets = item.assets

        if not all(
            band in assets
            for band in REQUIRED_BANDS
        ):
            continue

        # SCL is now required because
        # SatQuery uses it for pixel-level
        # quality masking.
        if QUALITY_BAND not in assets:
            continue

        valid_items.append(
            item
        )

    return valid_items


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

    urls = {}

    for band in REQUIRED_BANDS:

        asset = item.assets[
            band
        ]

        urls[band] = (
            planetary_computer.sign(
                asset.href
            )
        )

    return urls


def get_signed_scl_url(item):

    if QUALITY_BAND not in item.assets:

        raise KeyError(
            "Selected Sentinel-2 scene "
            "does not contain an SCL asset."
        )

    return planetary_computer.sign(
        item.assets[
            QUALITY_BAND
        ].href
    )


def get_scene_info(item):

    cloud_cover = (
        item.properties.get(
            "eo:cloud_cover"
        )
    )

    tile = (
        item.properties.get(
            "s2:mgrs_tile"
        )
        or item.properties.get(
            "s2:tile_id"
        )
    )

    return {
        "id": item.id,

        "date": (
            item.datetime
            .date()
            .isoformat()
        ),

        "cloud_cover": (
            float(cloud_cover)
            if cloud_cover
            is not None
            else None
        ),

        "tile": tile,
    }


if __name__ == "__main__":

    test_bbox = [
        80.90,
        26.80,
        80.97,
        26.88,
    ]

    scenes = search_sentinel2(
        bbox=test_bbox,
        target_date="2026-01-15",
    )

    print(
        "Scenes found:",
        len(scenes)
    )

    if scenes:

        best = select_best_scene(
            scenes,
            target_date="2026-01-15",
        )

        print(
            "Best scene:",
            get_scene_info(best)
        )

        print(
            "Bands:",
            list(
                get_signed_band_urls(
                    best
                ).keys()
            )
        )

        print(
            "SCL available:",
            bool(
                get_signed_scl_url(
                    best
                )
            )
        )