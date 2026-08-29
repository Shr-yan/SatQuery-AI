from datetime import datetime
from pathlib import Path

from bbox import create_bbox
from geocoder import geocode_location

from live_chip import (
    DISPLAY_CHIP_SIZE,
    MODEL_CHIP_SIZE,
    build_display_chip,
    build_model_chip,
    build_scl_valid_mask,
    read_scl_chip,
    summarize_chip_ndvi,
    summarize_chip_quality,
    summarize_scl_quality,
)

from live_visualization import (
    create_ndvi_preview,
    create_rgb_preview,
)

from model_inference import (
    SatQueryModel,
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


MIN_VALID_COVERAGE = 0.90


def classify_vegetation(
    mean_ndvi
):

    if mean_ndvi < 0:

        return (
            "Non-vegetated or "
            "water-dominated"
        )

    if mean_ndvi < 0.2:

        return "Sparse vegetation"

    if mean_ndvi < 0.4:

        return "Moderate vegetation"

    if mean_ndvi < 0.6:

        return "Healthy vegetation"

    return "Dense healthy vegetation"


def classify_model_agreement(
    difference
):

    if difference <= 0.01:

        return "strong"

    if difference <= 0.03:

        return "moderate"

    return "weak"


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


def analyze_location(
    location,
    target_date=None,
    size_km=5,
    predictor=None,
):

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
    # 3. Search
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

    scene = None
    scene_info = None

    model_chip = None
    model_chip_quality = None

    band_urls = None
    scl_url = None

    rejected_scenes = []

    # -----------------------------
    # 4. AOI-aware scene selection
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

            candidate_model_chip = (
                build_model_chip(
                    candidate_urls,
                    stac_bbox,
                )
            )

            candidate_quality = (
                summarize_chip_quality(
                    candidate_model_chip
                )
            )

            valid_fraction = (
                1.0
                - candidate_quality[
                    "zero_fraction"
                ]
            )

            if (
                valid_fraction
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
                        valid_fraction,
                    }
                )

                continue

            candidate_scl_url = (
                get_signed_scl_url(
                    candidate
                )
            )

            scene = candidate

            scene_info = (
                candidate_info
            )

            model_chip = (
                candidate_model_chip
            )

            model_chip_quality = (
                candidate_quality
            )

            band_urls = (
                candidate_urls
            )

            scl_url = (
                candidate_scl_url
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

    if scene is None:

        raise RuntimeError(
            "No Sentinel-2 candidate "
            "provided at least 90% "
            "valid AOI coverage."
        )

    valid_coverage = (
        1.0
        - model_chip_quality[
            "zero_fraction"
        ]
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
    # 6. High-resolution display /
    #    scientific chip
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
    # 7. Scientific NDVI
    # -----------------------------

    ndvi_stats = (
        summarize_chip_ndvi(
            display_chip,
            valid_mask=(
                scl_valid_mask
            ),
        )
    )

    vegetation_condition = (
        classify_vegetation(
            ndvi_stats["mean"]
        )
    )

    # -----------------------------
    # 8. CNN
    # -----------------------------

    if predictor is None:

        predictor = (
            SatQueryModel()
        )

    prediction = (
        predictor.predict_chip(
            model_chip
        )
    )

    difference = abs(
        prediction
        - ndvi_stats["mean"]
    )

    agreement = (
        classify_model_agreement(
            difference
        )
    )

    # -----------------------------
    # 9. Query-specific folder
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
        Path(
            "data/processed/results"
        )
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

    ndvi_output = (
        result_folder
        / "ndvi.png"
    )

    metadata_output = (
        result_folder
        / "result.json"
    )

    create_rgb_preview(
        display_chip,
        rgb_output,
    )

    create_ndvi_preview(
        display_chip,
        ndvi_output,
        valid_mask=(
            scl_valid_mask
        ),
    )

    # -----------------------------
    # 10. Result object
    # -----------------------------

    result = {

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

        "resolution": {

            "model_chip":
            MODEL_CHIP_SIZE,

            "display_chip":
            DISPLAY_CHIP_SIZE,
        },

        "chip_quality":
        model_chip_quality,

        "scl_quality":
        scl_quality,

        "date_difference_days":
        date_difference_days,

        "ndvi": {

            "mean":
            ndvi_stats["mean"],

            "min":
            ndvi_stats["min"],

            "max":
            ndvi_stats["max"],

            "std":
            ndvi_stats["std"],

            "valid_pixel_fraction":
            ndvi_stats[
                "valid_pixel_fraction"
            ],

            "condition":
            vegetation_condition,
        },

        "model": {

            "prediction":
            prediction,

            "absolute_difference":
            difference,

            "agreement":
            agreement,
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

            "ndvi_preview":
            str(
                ndvi_output
            ),

            "metadata":
            str(
                metadata_output
            ),
        },
    }

    # -----------------------------
    # 11. Save JSON metadata
    # -----------------------------

    save_result_json(
        result,
        metadata_output,
    )

    return result


if __name__ == "__main__":

    result = analyze_location(
        location="Varanasi",
        target_date="2026-02-10",
    )

    print(
        "\nSATQUERY ANALYSIS"
    )

    print(
        "-----------------"
    )

    print(
        "Location:",
        result["location"]
    )

    print(
        "Scene:",
        result["scene"]["id"]
    )

    print(
        "Model resolution:",
        result[
            "resolution"
        ]["model_chip"]
    )

    print(
        "Display resolution:",
        result[
            "resolution"
        ]["display_chip"]
    )

    print(
        "NDVI:",
        result["ndvi"]
    )

    print(
        "Outputs:",
        result["outputs"]
    )