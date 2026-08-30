from datetime import datetime
from pathlib import Path

import numpy as np

from bbox import create_bbox
from geocoder import geocode_location

from live_chip import (
    DISPLAY_CHIP_SIZE,
    build_display_chip,
    build_model_chip,
    build_scl_valid_mask,
    calculate_chip_ndbi,
    calculate_chip_ndwi,
    read_reflectance_band,
    read_scl_chip,
    summarize_chip_ndbi,
    summarize_chip_ndwi,
    summarize_chip_quality,
    summarize_scl_quality,
)

from live_visualization import (
    create_ndbi_preview,
    create_ndwi_preview,
    create_rgb_preview,
)

from real_data import (
    get_scene_info,
    get_signed_band_urls,
    get_signed_scl_url,
    search_sentinel2,
)

from result_export import (
    save_result_json,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "results"
)

MIN_VALID_COVERAGE = 0.90


def rank_scenes(
    scenes,
    target_date=None,
):

    if not scenes:
        return []

    if target_date:

        target = datetime.strptime(
            target_date,
            "%Y-%m-%d",
        ).date()

        return sorted(
            scenes,
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

    return sorted(
        scenes,
        key=lambda item:
        item.properties.get(
            "eo:cloud_cover",
            100,
        ),
    )


def calculate_positive_fraction(
    index,
):

    valid = np.isfinite(
        index
    )

    if not np.any(valid):
        return 0.0

    return float(
        np.mean(
            index[valid] > 0
        )
    )


def classify_water_signal(
    fraction,
):

    if fraction < 0.05:
        return "Low surface-water signal"

    if fraction < 0.20:
        return "Moderate surface-water presence"

    return "High surface-water presence"


def classify_builtup_signal(
    fraction,
):

    if fraction < 0.10:
        return "Low built-up signal"

    if fraction < 0.30:
        return "Moderate built-up presence"

    return "High built-up presence"


def analyze_environmental_index(
    location,
    analysis_type,
    target_date=None,
    size_km=5,
):

    analysis_type = (
        analysis_type.lower()
    )

    if analysis_type in [
        "water",
        "ndwi",
    ]:
        index_name = "ndwi"

    elif analysis_type in [
        "urban",
        "ndbi",
    ]:
        index_name = "ndbi"

    else:
        raise ValueError(
            "Environmental analysis "
            "must be NDWI/water or "
            "NDBI/urban."
        )

    # -----------------------------
    # 1. Geocode
    # -----------------------------

    coordinates = geocode_location(
        location
    )

    if not coordinates:

        raise ValueError(
            f"Could not geocode "
            f"location: {location}"
        )

    # -----------------------------
    # 2. AOI
    # -----------------------------

    bbox_dict = create_bbox(
        coordinates["latitude"],
        coordinates["longitude"],
        size_km=size_km,
    )

    stac_bbox = [
        bbox_dict["min_lon"],
        bbox_dict["min_lat"],
        bbox_dict["max_lon"],
        bbox_dict["max_lat"],
    ]

    # -----------------------------
    # 3. Search Sentinel-2
    # -----------------------------

    scenes = search_sentinel2(
        bbox=stac_bbox,
        target_date=target_date,
    )

    if not scenes:

        raise RuntimeError(
            "No suitable Sentinel-2 "
            "scenes were found."
        )

    ranked_scenes = rank_scenes(
        scenes,
        target_date=target_date,
    )

    scene_info = None
    band_urls = None
    scl_url = None
    valid_coverage = None

    rejected_scenes = []

    # -----------------------------
    # 4. AOI-aware selection
    # -----------------------------

    for candidate in ranked_scenes:

        candidate_info = (
            get_scene_info(
                candidate
            )
        )

        try:

            candidate_urls = (
                get_signed_band_urls(
                    candidate
                )
            )

            candidate_chip = (
                build_model_chip(
                    candidate_urls,
                    stac_bbox,
                )
            )

            candidate_quality = (
                summarize_chip_quality(
                    candidate_chip
                )
            )

            candidate_coverage = (
                1.0
                - candidate_quality[
                    "zero_fraction"
                ]
            )

            if (
                candidate_coverage
                < MIN_VALID_COVERAGE
            ):

                rejected_scenes.append(
                    {
                        "id":
                        candidate_info["id"],

                        "date":
                        candidate_info[
                            "date"
                        ],

                        "reason":
                        "insufficient_coverage",

                        "valid_fraction":
                        candidate_coverage,
                    }
                )

                continue

            candidate_scl_url = (
                get_signed_scl_url(
                    candidate
                )
            )

            scene_info = (
                candidate_info
            )

            band_urls = (
                candidate_urls
            )

            scl_url = (
                candidate_scl_url
            )

            valid_coverage = (
                candidate_coverage
            )

            break

        except Exception as error:

            rejected_scenes.append(
                {
                    "id":
                    candidate_info["id"],

                    "date":
                    candidate_info[
                        "date"
                    ],

                    "reason":
                    "read_error",

                    "error":
                    str(error),
                }
            )

    if scene_info is None:

        raise RuntimeError(
            "No Sentinel-2 candidate "
            "provided at least 90% "
            "valid AOI coverage."
        )

    # -----------------------------
    # 5. Date difference
    # -----------------------------

    date_difference_days = None

    if target_date:

        requested = datetime.strptime(
            target_date,
            "%Y-%m-%d",
        ).date()

        selected = datetime.strptime(
            scene_info["date"],
            "%Y-%m-%d",
        ).date()

        date_difference_days = abs(
            (
                selected
                - requested
            ).days
        )

    # -----------------------------
    # 6. High-resolution bands
    # -----------------------------

    display_chip = (
        build_display_chip(
            band_urls,
            stac_bbox,
        )
    )

    display_scl = (
        read_scl_chip(
            scl_url,
            stac_bbox,
            chip_size=(
                DISPLAY_CHIP_SIZE
            ),
        )
    )

    scl_valid_mask = (
        build_scl_valid_mask(
            display_scl
        )
    )

    scl_quality = (
        summarize_scl_quality(
            display_scl
        )
    )

    # -----------------------------
    # 7. Calculate requested index
    # -----------------------------

    swir = None

    if index_name == "ndwi":

        index_array = (
            calculate_chip_ndwi(
                display_chip,
                valid_mask=(
                    scl_valid_mask
                ),
            )
        )

        index_stats = (
            summarize_chip_ndwi(
                display_chip,
                valid_mask=(
                    scl_valid_mask
                ),
            )
        )

        positive_fraction = (
            calculate_positive_fraction(
                index_array
            )
        )

        interpretation = (
            classify_water_signal(
                positive_fraction
            )
        )

    else:

        swir = (
            read_reflectance_band(
                band_urls["B11"],
                stac_bbox,
                chip_size=(
                    DISPLAY_CHIP_SIZE
                ),
            )
        )

        index_array = (
            calculate_chip_ndbi(
                display_chip,
                swir,
                valid_mask=(
                    scl_valid_mask
                ),
            )
        )

        index_stats = (
            summarize_chip_ndbi(
                display_chip,
                swir,
                valid_mask=(
                    scl_valid_mask
                ),
            )
        )

        positive_fraction = (
            calculate_positive_fraction(
                index_array
            )
        )

        interpretation = (
            classify_builtup_signal(
                positive_fraction
            )
        )

    # -----------------------------
    # 8. Result folder
    # -----------------------------

    safe_location = (
        location.lower()
        .replace(
            " ",
            "_"
        )
        .replace(
            ",",
            ""
        )
    )

    scene_date = (
        scene_info["date"]
    )

    result_folder = (
        RESULTS_DIR
        / (
            f"{safe_location}_"
            f"{scene_date}"
        )
    )

    result_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    rgb_output = (
        result_folder
        / "rgb.png"
    )

    index_output = (
        result_folder
        / f"{index_name}.png"
    )

    metadata_output = (
        result_folder
        / (
            f"{index_name}_"
            "result.json"
        )
    )

    # -----------------------------
    # 9. Visualizations
    # -----------------------------

    create_rgb_preview(
        display_chip,
        rgb_output,
    )

    if index_name == "ndwi":

        create_ndwi_preview(
            display_chip,
            index_output,
            valid_mask=(
                scl_valid_mask
            ),
        )

    else:

        create_ndbi_preview(
            display_chip,
            swir,
            index_output,
            valid_mask=(
                scl_valid_mask
            ),
        )

    # -----------------------------
    # 10. Result object
    # -----------------------------

    result = {

        "analysis_type":
        index_name,

        "location":
        location,

        "resolved_location":
        coordinates.get(
            "name",
            location,
        ),

        "coordinates":
        coordinates,

        "bbox":
        bbox_dict,

        "requested_date":
        target_date,

        "scene":
        scene_info,

        "candidate_scene_count":
        len(scenes),

        "rejected_scene_count":
        len(
            rejected_scenes
        ),

        "rejected_scenes":
        rejected_scenes,

        "valid_coverage":
        valid_coverage,

        "date_difference_days":
        date_difference_days,

        "resolution": {
            "display_chip":
            DISPLAY_CHIP_SIZE,
        },

        "scl_quality":
        scl_quality,

        "index": {
            "name":
            index_name.upper(),

            "mean":
            index_stats["mean"],

            "min":
            index_stats["min"],

            "max":
            index_stats["max"],

            "std":
            index_stats["std"],

            "valid_pixel_fraction":
            index_stats[
                "valid_pixel_fraction"
            ],

            "positive_fraction":
            positive_fraction,

            "interpretation":
            interpretation,
        },

        "outputs": {
            "folder":
            str(
                result_folder
            ),

            "rgb_preview":
            str(
                rgb_output
            ),

            "index_preview":
            str(
                index_output
            ),

            "metadata":
            str(
                metadata_output
            ),
        },
    }

    save_result_json(
        result,
        metadata_output,
    )

    return result


if __name__ == "__main__":

    water = (
        analyze_environmental_index(
            location="Varanasi",
            analysis_type="ndwi",
            target_date="2026-02-10",
        )
    )

    print(
        "\nNDWI RESULT"
    )

    print(
        water["index"]
    )