from datetime import (
    datetime,
    timedelta,
)

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from bbox import create_bbox
from geocoder import geocode_location

from change_analysis import (
    load_index_for_scene,
    select_scene_for_date,
    summarize_array,
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


DEFAULT_SAMPLE_COUNT = 5


def build_sample_dates(
    date_start,
    date_end,
    sample_count=DEFAULT_SAMPLE_COUNT,
):

    start = datetime.strptime(
        date_start,
        "%Y-%m-%d",
    )

    end = datetime.strptime(
        date_end,
        "%Y-%m-%d",
    )

    if end <= start:

        raise ValueError(
            "Trend end date must be "
            "after the start date."
        )

    total_days = (
        end - start
    ).days

    offsets = np.linspace(
        0,
        total_days,
        sample_count,
    )

    dates = []

    for offset in offsets:

        date = (
            start
            + timedelta(
                days=int(
                    round(
                        offset
                    )
                )
            )
        )

        dates.append(
            date.strftime(
                "%Y-%m-%d"
            )
        )

    return dates


def classify_trend(
    total_change,
):

    if abs(
        total_change
    ) < 0.03:

        return "Vegetation trend is relatively stable."

    if total_change > 0:

        return (
            "Vegetation greenness shows "
            "an overall increasing trend."
        )

    return (
        "Vegetation greenness shows "
        "an overall decreasing trend."
    )


def create_trend_chart(
    observations,
    output_path,
):

    dates = [
        datetime.strptime(
            item["selected_date"],
            "%Y-%m-%d",
        )
        for item in observations
    ]

    means = [
        item["mean_ndvi"]
        for item in observations
    ]

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(
        figsize=(10, 6)
    )

    plt.plot(
        dates,
        means,
        marker="o",
    )

    plt.title(
        "Vegetation NDVI Trend"
    )

    plt.xlabel(
        "Observation Date"
    )

    plt.ylabel(
        "Mean NDVI"
    )

    plt.grid(
        alpha=0.25
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


def analyze_vegetation_trend(
    location,
    date_start,
    date_end,
    size_km=5,
    sample_count=DEFAULT_SAMPLE_COUNT,
):

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

    requested_dates = (
        build_sample_dates(
            date_start,
            date_end,
            sample_count=(
                sample_count
            ),
        )
    )

    observations = []

    used_scene_ids = set()

    for requested_date in requested_dates:

        selected = (
            select_scene_for_date(
                stac_bbox,
                requested_date,
            )
        )

        scene_info = selected[
            "scene_info"
        ]

        if (
            scene_info["id"]
            in used_scene_ids
        ):
            continue

        used_scene_ids.add(
            scene_info["id"]
        )

        data = (
            load_index_for_scene(
                selected,
                stac_bbox,
                "ndvi",
            )
        )

        stats = summarize_array(
            data["index"]
        )

        observations.append(
            {
                "requested_date":
                requested_date,

                "selected_date":
                scene_info["date"],

                "scene_id":
                scene_info["id"],

                "tile":
                scene_info.get(
                    "tile"
                ),

                "cloud_cover":
                scene_info.get(
                    "cloud_cover"
                ),

                "coverage_percent":
                (
                    selected[
                        "coverage"
                    ]
                    * 100.0
                ),

                "mean_ndvi":
                stats["mean"],

                "min_ndvi":
                stats["min"],

                "max_ndvi":
                stats["max"],

                "std_ndvi":
                stats["std"],
            }
        )

    observations.sort(
        key=lambda item:
        item["selected_date"]
    )

    if len(
        observations
    ) < 2:

        raise RuntimeError(
            "Trend analysis requires "
            "at least two distinct "
            "Sentinel-2 observations."
        )

    first_mean = (
        observations[0][
            "mean_ndvi"
        ]
    )

    last_mean = (
        observations[-1][
            "mean_ndvi"
        ]
    )

    total_change = (
        last_mean
        - first_mean
    )

    selected_dates = [
        datetime.strptime(
            item[
                "selected_date"
            ],
            "%Y-%m-%d",
        )
        for item in observations
    ]

    start_selected = (
        selected_dates[0]
    )

    day_offsets = np.array(
        [
            (
                date
                - start_selected
            ).days
            for date in selected_dates
        ],
        dtype=np.float32,
    )

    ndvi_values = np.array(
        [
            item[
                "mean_ndvi"
            ]
            for item
            in observations
        ],
        dtype=np.float32,
    )

    slope_per_day = float(
        np.polyfit(
            day_offsets,
            ndvi_values,
            1,
        )[0]
    )

    slope_per_30_days = (
        slope_per_day
        * 30.0
    )

    interpretation = (
        classify_trend(
            total_change
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

    result_folder = (
        RESULTS_DIR
        / (
            f"{safe_location}_"
            f"vegetation_trend_"
            f"{date_start}_"
            f"{date_end}"
        )
    )

    result_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    chart_output = (
        result_folder
        / "trend.png"
    )

    metadata_output = (
        result_folder
        / "trend_result.json"
    )

    create_trend_chart(
        observations,
        chart_output,
    )

    result = {

        "analysis_type":
        "ndvi",

        "trend_analysis":
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

        "requested_dates": {
            "start":
            date_start,

            "end":
            date_end,
        },

        "observation_count":
        len(
            observations
        ),

        "observations":
        observations,

        "trend": {
            "first_mean_ndvi":
            first_mean,

            "last_mean_ndvi":
            last_mean,

            "total_change":
            total_change,

            "slope_per_day":
            slope_per_day,

            "slope_per_30_days":
            slope_per_30_days,

            "interpretation":
            interpretation,
        },

        "outputs": {
            "folder":
            str(
                result_folder
            ),

            "trend_preview":
            str(
                chart_output
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

    result = (
        analyze_vegetation_trend(
            location="Varanasi",
            date_start="2026-01-10",
            date_end="2026-04-10",
        )
    )

    print(
        result[
            "observations"
        ]
    )

    print(
        result[
            "trend"
        ]
    )

    print(
        result[
            "outputs"
        ]
    )