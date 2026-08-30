from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from bbox import create_bbox
from geocoder import geocode_location

from live_chip import (
    DISPLAY_CHIP_SIZE,
    build_display_chip,
    build_model_chip,
    build_scl_valid_mask,
    calculate_chip_ndbi,
    calculate_chip_ndvi,
    calculate_chip_ndwi,
    read_reflectance_band,
    read_scl_chip,
    summarize_chip_quality,
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

CHANGE_THRESHOLD = 0.05


def rank_scenes(
    scenes,
    target_date,
):

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


def select_scene_for_date(
    stac_bbox,
    target_date,
):

    scenes = search_sentinel2(
        bbox=stac_bbox,
        target_date=target_date,
    )

    if not scenes:

        raise RuntimeError(
            "No suitable Sentinel-2 "
            f"scenes found near {target_date}."
        )

    ranked = rank_scenes(
        scenes,
        target_date,
    )

    rejected = []

    for candidate in ranked:

        info = get_scene_info(
            candidate
        )

        try:

            band_urls = (
                get_signed_band_urls(
                    candidate
                )
            )

            model_chip = (
                build_model_chip(
                    band_urls,
                    stac_bbox,
                )
            )

            quality = (
                summarize_chip_quality(
                    model_chip
                )
            )

            coverage = (
                1.0
                - quality[
                    "zero_fraction"
                ]
            )

            if (
                coverage
                < MIN_VALID_COVERAGE
            ):

                rejected.append(
                    {
                        "id":
                        info["id"],

                        "date":
                        info["date"],

                        "reason":
                        "insufficient_coverage",

                        "valid_fraction":
                        coverage,
                    }
                )

                continue

            scl_url = (
                get_signed_scl_url(
                    candidate
                )
            )

            return {
                "scene":
                candidate,

                "scene_info":
                info,

                "band_urls":
                band_urls,

                "scl_url":
                scl_url,

                "coverage":
                coverage,

                "candidate_count":
                len(scenes),

                "rejected":
                rejected,
            }

        except Exception as error:

            rejected.append(
                {
                    "id":
                    info["id"],

                    "date":
                    info["date"],

                    "reason":
                    "read_error",

                    "error":
                    str(error),
                }
            )

    raise RuntimeError(
        "No Sentinel-2 scene provided "
        f"enough AOI coverage near "
        f"{target_date}."
    )


def load_index_for_scene(
    selected,
    stac_bbox,
    index_name,
):

    band_urls = (
        selected[
            "band_urls"
        ]
    )

    display_chip = (
        build_display_chip(
            band_urls,
            stac_bbox,
        )
    )

    scl = (
        read_scl_chip(
            selected[
                "scl_url"
            ],
            stac_bbox,
            chip_size=(
                DISPLAY_CHIP_SIZE
            ),
        )
    )

    valid_mask = (
        build_scl_valid_mask(
            scl
        )
    )

    if index_name == "ndvi":

        index = (
            calculate_chip_ndvi(
                display_chip,
                valid_mask=(
                    valid_mask
                ),
            )
        )

    elif index_name == "ndwi":

        index = (
            calculate_chip_ndwi(
                display_chip,
                valid_mask=(
                    valid_mask
                ),
            )
        )

    elif index_name == "ndbi":

        swir = (
            read_reflectance_band(
                band_urls["B11"],
                stac_bbox,
                chip_size=(
                    DISPLAY_CHIP_SIZE
                ),
            )
        )

        index = (
            calculate_chip_ndbi(
                display_chip,
                swir,
                valid_mask=(
                    valid_mask
                ),
            )
        )

    else:

        raise ValueError(
            "Unsupported change index."
        )

    return {
        "display_chip":
        display_chip,

        "index":
        index,

        "valid_mask":
        valid_mask,
    }


def summarize_array(
    array,
):

    valid = np.isfinite(
        array
    )

    if not np.any(valid):

        raise ValueError(
            "No valid pixels found."
        )

    values = array[
        valid
    ]

    return {
        "mean":
        float(
            np.mean(
                values
            )
        ),

        "min":
        float(
            np.min(
                values
            )
        ),

        "max":
        float(
            np.max(
                values
            )
        ),

        "std":
        float(
            np.std(
                values
            )
        ),

        "valid_pixel_fraction":
        float(
            np.mean(
                valid
            )
        ),
    }


def calculate_change_stats(
    before,
    after,
):

    valid = (
        np.isfinite(
            before
        )
        & np.isfinite(
            after
        )
    )

    if not np.any(valid):

        raise ValueError(
            "No common valid pixels "
            "between the two dates."
        )

    change = np.full(
        before.shape,
        np.nan,
        dtype=np.float32,
    )

    change[
        valid
    ] = (
        after[
            valid
        ]
        - before[
            valid
        ]
    )

    values = (
        change[
            valid
        ]
    )

    increased = (
        values
        > CHANGE_THRESHOLD
    )

    decreased = (
        values
        < -CHANGE_THRESHOLD
    )

    stable = (
        ~increased
        & ~decreased
    )

    return {
        "change_array":
        change,

        "mean_change":
        float(
            np.mean(
                values
            )
        ),

        "min_change":
        float(
            np.min(
                values
            )
        ),

        "max_change":
        float(
            np.max(
                values
            )
        ),

        "std_change":
        float(
            np.std(
                values
            )
        ),

        "increase_fraction":
        float(
            np.mean(
                increased
            )
        ),

        "decrease_fraction":
        float(
            np.mean(
                decreased
            )
        ),

        "stable_fraction":
        float(
            np.mean(
                stable
            )
        ),

        "valid_pixel_fraction":
        float(
            np.mean(
                valid
            )
        ),
    }


def classify_change(
    index_name,
    mean_change,
):

    magnitude = abs(
        mean_change
    )

    if magnitude < 0.02:

        return (
            "Overall change is small."
        )

    if index_name == "ndvi":

        if mean_change > 0:

            return (
                "Vegetation greenness "
                "increased overall."
            )

        return (
            "Vegetation greenness "
            "decreased overall."
        )

    if index_name == "ndwi":

        if mean_change > 0:

            return (
                "Surface-water signal "
                "increased overall."
            )

        return (
            "Surface-water signal "
            "decreased overall."
        )

    if index_name == "ndbi":

        if mean_change > 0:

            return (
                "Built-up signal "
                "increased overall."
            )

        return (
            "Built-up signal "
            "decreased overall."
        )

    return (
        "Change detected."
    )


def create_change_map(
    change,
    output_path,
    index_name,
):

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    masked = (
        np.ma.masked_invalid(
            change
        )
    )

    max_abs = (
        np.nanpercentile(
            np.abs(
                change
            ),
            98,
        )
    )

    if (
        not np.isfinite(
            max_abs
        )
        or max_abs < 0.05
    ):

        max_abs = 0.05

    plt.figure(
        figsize=(10, 9)
    )

    image = plt.imshow(
        masked,
        cmap="RdBu_r",
        vmin=-max_abs,
        vmax=max_abs,
    )

    plt.title(
        f"{index_name.upper()} "
        "Change Map"
    )

    plt.axis(
        "off"
    )

    colorbar = plt.colorbar(
        image,
        fraction=0.046,
        pad=0.04,
    )

    colorbar.set_label(
        f"Δ {index_name.upper()}"
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close()

    return str(
        output_path
    )


def analyze_change(
    location,
    analysis_type,
    date_start,
    date_end,
    size_km=5,
):

    if not date_start or not date_end:

        raise ValueError(
            "Two dates are required "
            "for change analysis."
        )

    analysis_type = (
        analysis_type.lower()
    )

    if analysis_type in {
        "ndvi",
        "vegetation",
    }:

        index_name = "ndvi"

    elif analysis_type in {
        "ndwi",
        "water",
    }:

        index_name = "ndwi"

    elif analysis_type in {
        "ndbi",
        "urban",
    }:

        index_name = "ndbi"

    else:

        raise ValueError(
            "Change analysis currently "
            "supports NDVI, NDWI and NDBI."
        )

    coordinates = (
        geocode_location(
            location
        )
    )

    if not coordinates:

        raise ValueError(
            f"Could not geocode "
            f"location: {location}"
        )

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

    before_scene = (
        select_scene_for_date(
            stac_bbox,
            date_start,
        )
    )

    after_scene = (
        select_scene_for_date(
            stac_bbox,
            date_end,
        )
    )

    before_data = (
        load_index_for_scene(
            before_scene,
            stac_bbox,
            index_name,
        )
    )

    after_data = (
        load_index_for_scene(
            after_scene,
            stac_bbox,
            index_name,
        )
    )

    before_stats = (
        summarize_array(
            before_data[
                "index"
            ]
        )
    )

    after_stats = (
        summarize_array(
            after_data[
                "index"
            ]
        )
    )

    change_stats = (
        calculate_change_stats(
            before_data[
                "index"
            ],
            after_data[
                "index"
            ],
        )
    )

    interpretation = (
        classify_change(
            index_name,
            change_stats[
                "mean_change"
            ],
        )
    )

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

    folder_name = (
        f"{safe_location}_"
        f"{index_name}_change_"
        f"{date_start}_"
        f"{date_end}"
    )

    result_folder = (
        RESULTS_DIR
        / folder_name
    )

    result_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    change_output = (
        result_folder
        / "change.png"
    )

    metadata_output = (
        result_folder
        / "change_result.json"
    )

    create_change_map(
        change_stats[
            "change_array"
        ],
        change_output,
        index_name,
    )

    result = {
        "analysis_type":
        index_name,

        "change_analysis":
        True,

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

        "requested_dates": {
            "start":
            date_start,

            "end":
            date_end,
        },

        "before": {
            "scene":
            before_scene[
                "scene_info"
            ],

            "coverage":
            before_scene[
                "coverage"
            ],

            "candidate_count":
            before_scene[
                "candidate_count"
            ],

            "rejected_count":
            len(
                before_scene[
                    "rejected"
                ]
            ),

            "stats":
            before_stats,
        },

        "after": {
            "scene":
            after_scene[
                "scene_info"
            ],

            "coverage":
            after_scene[
                "coverage"
            ],

            "candidate_count":
            after_scene[
                "candidate_count"
            ],

            "rejected_count":
            len(
                after_scene[
                    "rejected"
                ]
            ),

            "stats":
            after_stats,
        },

        "change": {
            "mean":
            change_stats[
                "mean_change"
            ],

            "min":
            change_stats[
                "min_change"
            ],

            "max":
            change_stats[
                "max_change"
            ],

            "std":
            change_stats[
                "std_change"
            ],

            "increase_fraction":
            change_stats[
                "increase_fraction"
            ],

            "decrease_fraction":
            change_stats[
                "decrease_fraction"
            ],

            "stable_fraction":
            change_stats[
                "stable_fraction"
            ],

            "valid_pixel_fraction":
            change_stats[
                "valid_pixel_fraction"
            ],

            "threshold":
            CHANGE_THRESHOLD,

            "interpretation":
            interpretation,
        },

        "resolution": {
            "display_chip":
            DISPLAY_CHIP_SIZE,
        },

        "outputs": {
            "folder":
            str(
                result_folder
            ),

            "change_preview":
            str(
                change_output
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

    result = analyze_change(
        location="Varanasi",
        analysis_type="vegetation",
        date_start="2026-02-10",
        date_end="2026-03-10",
    )

    print(
        result["before"]
    )

    print(
        result["after"]
    )

    print(
        result["change"]
    )

    print(
        result["outputs"]
    )