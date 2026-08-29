from datetime import datetime
from pathlib import Path

from live_visualization import (
    create_rgb_preview,
    create_ndvi_preview,
)
from bbox import create_bbox
from geocoder import geocode_location

from live_chip import (
    build_model_chip,
    summarize_chip_ndvi,
    summarize_chip_quality,
)

from model_inference import SatQueryModel

from real_data import (
    get_scene_info,
    get_signed_band_urls,
    search_sentinel2,
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

    # If the user supplied a date,
    # prioritize date proximity first
    # and cloud cover second.
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

    # Without a requested date,
    # prioritize lowest cloud cover.
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

    # ---------------------------------
    # 1. Geocode requested location
    # ---------------------------------

    coordinates = geocode_location(
        location
    )

    if not coordinates:

        raise ValueError(
            f"Could not geocode "
            f"location: {location}"
        )

    # ---------------------------------
    # 2. Create geographic AOI
    # ---------------------------------

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

    # ---------------------------------
    # 3. Search Sentinel-2 catalog
    # ---------------------------------

    scenes = search_sentinel2(
        bbox=stac_bbox,
        target_date=target_date,
    )

    if not scenes:

        raise RuntimeError(
            "No suitable Sentinel-2 "
            "scenes were found."
        )

    # ---------------------------------
    # 4. Rank candidate scenes
    # ---------------------------------

    ranked_scenes = rank_scenes(
        scenes,
        target_date=target_date,
    )

    scene = None
    scene_info = None
    chip = None
    chip_quality = None

    rejected_scenes = []

    # ---------------------------------
    # 5. Try scenes until we find one
    #    with sufficient AOI coverage
    # ---------------------------------

    for candidate in ranked_scenes:

        candidate_info = get_scene_info(
            candidate
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

            valid_fraction = (
                1.0
                - candidate_quality[
                    "zero_fraction"
                ]
            )

            # Reject scenes that only
            # partially cover the AOI.
            if (
                valid_fraction
                < MIN_VALID_COVERAGE
            ):

                rejected_scenes.append(
                    {
                        "id": (
                            candidate_info[
                                "id"
                            ]
                        ),
                        "date": (
                            candidate_info[
                                "date"
                            ]
                        ),
                        "valid_fraction": (
                            valid_fraction
                        ),
                    }
                )

                continue

            # Good scene found.
            scene = candidate
            scene_info = (
                candidate_info
            )
            chip = candidate_chip
            chip_quality = (
                candidate_quality
            )

            break

        except Exception as error:

            rejected_scenes.append(
                {
                    "id": (
                        candidate_info[
                            "id"
                        ]
                    ),
                    "date": (
                        candidate_info[
                            "date"
                        ]
                    ),
                    "error": str(
                        error
                    ),
                }
            )

            continue

    # ---------------------------------
    # 6. Ensure a usable scene exists
    # ---------------------------------

    if scene is None:

        raise RuntimeError(
            "No Sentinel-2 candidate "
            "provided at least 90% "
            "valid AOI coverage."
        )

    valid_coverage = (
        1.0
        - chip_quality[
            "zero_fraction"
        ]
    )

    # ---------------------------------
    # 7. Calculate date difference
    # ---------------------------------

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

    # ---------------------------------
    # 8. Scientific NDVI
    # ---------------------------------

    ndvi_stats = summarize_chip_ndvi(
        chip
    )

    vegetation_condition = (
        classify_vegetation(
            ndvi_stats["mean"]
        )
    )

    # ---------------------------------
    # 9. CNN inference
    # ---------------------------------

    if predictor is None:

        predictor = SatQueryModel()

    prediction = predictor.predict_chip(
        chip
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

    # ---------------------------------
    # 10. Generate visual products
    # ---------------------------------

    results_dir = Path(
        "data/processed/results"
    )

    results_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_location = (
        location.lower()
        .replace(" ", "_")
    )

    scene_date = scene_info[
        "date"
    ]

    rgb_output = (
        results_dir
        / (
            f"{safe_location}_"
            f"{scene_date}_rgb.png"
        )
    )

    ndvi_output = (
        results_dir
        / (
            f"{safe_location}_"
            f"{scene_date}_ndvi.png"
        )
    )

    create_rgb_preview(
        chip,
        rgb_output,
    )

    create_ndvi_preview(
        chip,
        ndvi_output,
    )

    # ---------------------------------
    # 11. Structured result
    # ---------------------------------

    return {

        "location": location,

        "coordinates": coordinates,

        "bbox": bbox_dict,

        "requested_date": (
            target_date
        ),

        "scene": scene_info,

        "candidate_scene_count": len(
            scenes
        ),

        "rejected_scene_count": len(
            rejected_scenes
        ),

        "rejected_scenes": (
            rejected_scenes
        ),

        "valid_coverage": (
            valid_coverage
        ),

        "chip_shape": list(
            chip.shape
        ),

        "chip_quality": (
            chip_quality
        ),

        "date_difference_days": (
            date_difference_days
        ),

        "ndvi": {

            "mean": (
                ndvi_stats["mean"]
            ),

            "min": (
                ndvi_stats["min"]
            ),

            "max": (
                ndvi_stats["max"]
            ),

            "std": (
                ndvi_stats["std"]
            ),

            "condition": (
                vegetation_condition
            ),
        },

        "model": {

            "prediction": (
                prediction
            ),

            "absolute_difference": (
                difference
            ),

            "agreement": (
                agreement
            ),
        },
        "outputs": {
            "rgb_preview": str(
                rgb_output
            ),
            "ndvi_preview": str(
                ndvi_output
            ),
        },
    }


if __name__ == "__main__":

    result = analyze_location(
        location="Varanasi",
        target_date="2026-02-10",
    )

    print(
        "\nSATQUERY LIVE ANALYSIS"
    )

    print(
        "----------------------"
    )

    print(
        "Location:",
        result["location"]
    )

    print(
        "Resolved location:",
        result[
            "coordinates"
        ].get("name")
    )

    print(
        "Requested date:",
        result["requested_date"]
    )

    print(
        "Selected scene:",
        result["scene"]
    )

    print(
        "Candidate scenes:",
        result[
            "candidate_scene_count"
        ]
    )

    print(
        "Rejected scenes:",
        result[
            "rejected_scene_count"
        ]
    )

    print(
        "Valid coverage:",
        result[
            "valid_coverage"
        ]
    )

    print(
        "NDVI mean:",
        result["ndvi"]["mean"]
    )

    print(
        "Vegetation:",
        result[
            "ndvi"
        ]["condition"]
    )

    print(
        "Model prediction:",
        result[
            "model"
        ]["prediction"]
    )

    print(
        "Difference:",
        result[
            "model"
        ]["absolute_difference"]
    )

    print(
        "Agreement:",
        result[
            "model"
        ]["agreement"]
    )