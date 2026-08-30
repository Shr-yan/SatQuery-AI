from datetime import datetime, timezone

from change_analysis import (
    analyze_change,
)

from environmental_analysis import (
    analyze_environmental_index,
)

from live_analysis import (
    analyze_location,
    get_location_imagery,
)

from query_parser import (
    parse_query,
)

from trend_analysis import (
    analyze_vegetation_trend,
)


SUPPORTED_ANALYSES = {
    "ndvi",
    "vegetation",
    "imagery",
    "ndwi",
    "water",
    "ndbi",
    "urban",
}


def build_common_sections(
    result,
):

    return {

        "location": {
            "requested":
            result["location"],

            "resolved":
            result["resolved_location"],

            "latitude":
            result[
                "coordinates"
            ]["latitude"],

            "longitude":
            result[
                "coordinates"
            ]["longitude"],
        },

        "date": {
            "requested":
            result["requested_date"],

            "selected":
            result["scene"]["date"],

            "difference_days":
            result[
                "date_difference_days"
            ],
        },

        "scene": {
            "id":
            result["scene"]["id"],

            "tile":
            result[
                "scene"
            ].get(
                "tile"
            ),

            "cloud_cover_percent":
            result[
                "scene"
            ]["cloud_cover"],

            "candidate_count":
            result[
                "candidate_scene_count"
            ],

            "rejected_count":
            result[
                "rejected_scene_count"
            ],

            "aoi_coverage_percent":
            (
                result[
                    "valid_coverage"
                ]
                * 100.0
            ),
        },
    }


def build_success_response(
    query,
    parsed,
    result,
):

    common = (
        build_common_sections(
            result
        )
    )

    return {

        "success":
        True,

        "query":
        query,

        "parsed_query":
        parsed,

        "analysis_type":
        parsed.get(
            "analysis_type"
        ),

        "change_analysis":
        False,

        "trend_analysis":
        False,

        **common,

        "quality": {
            "scl_valid_percent":
            (
                result[
                    "scl_quality"
                ]["valid_fraction"]
                * 100.0
            ),

            "cloud_percent":
            (
                result[
                    "scl_quality"
                ]["cloud_fraction"]
                * 100.0
            ),

            "shadow_percent":
            (
                result[
                    "scl_quality"
                ]["shadow_fraction"]
                * 100.0
            ),

            "snow_percent":
            (
                result[
                    "scl_quality"
                ]["snow_fraction"]
                * 100.0
            ),
        },

        "vegetation": {
            "mean_ndvi":
            result[
                "ndvi"
            ]["mean"],

            "min_ndvi":
            result[
                "ndvi"
            ]["min"],

            "max_ndvi":
            result[
                "ndvi"
            ]["max"],

            "std_ndvi":
            result[
                "ndvi"
            ]["std"],

            "valid_pixel_percent":
            (
                result[
                    "ndvi"
                ][
                    "valid_pixel_fraction"
                ]
                * 100.0
            ),

            "condition":
            result[
                "ndvi"
            ]["condition"],
        },

        "model": {
            "predicted_mean_ndvi":
            result[
                "model"
            ]["prediction"],

            "absolute_difference":
            result[
                "model"
            ][
                "absolute_difference"
            ],

            "agreement":
            result[
                "model"
            ]["agreement"],
        },

        "resolution": {
            "model":
            result[
                "resolution"
            ]["model_chip"],

            "display":
            result[
                "resolution"
            ]["display_chip"],
        },

        "outputs":
        result["outputs"],

        "message": (
            "The selected Sentinel-2 "
            "observation for "
            f"{result['location']} "
            "has a quality-masked "
            "mean NDVI of "
            f"{result['ndvi']['mean']:.4f}. "
            "Vegetation condition: "
            f"{result['ndvi']['condition']}."
        ),

        "generated_at":
        datetime.now(
            timezone.utc
        ).isoformat(),
    }


def build_imagery_response(
    query,
    parsed,
    result,
):

    common = (
        build_common_sections(
            result
        )
    )

    return {

        "success":
        True,

        "query":
        query,

        "parsed_query":
        parsed,

        "analysis_type":
        "imagery",

        "change_analysis":
        False,

        "trend_analysis":
        False,

        **common,

        "resolution": {
            "display":
            result[
                "resolution"
            ]["display_chip"],
        },

        "outputs":
        result["outputs"],

        "message": (
            "Sentinel-2 RGB imagery "
            "was retrieved for "
            f"{result['location']} "
            "using the observation "
            f"from "
            f"{result['scene']['date']}."
        ),

        "generated_at":
        datetime.now(
            timezone.utc
        ).isoformat(),
    }


def build_environmental_response(
    query,
    parsed,
    result,
):

    common = (
        build_common_sections(
            result
        )
    )

    index = (
        result["index"]
    )

    index_name = (
        index["name"]
    )

    positive_percent = (
        index[
            "positive_fraction"
        ]
        * 100.0
    )

    return {

        "success":
        True,

        "query":
        query,

        "parsed_query":
        parsed,

        "analysis_type":
        result[
            "analysis_type"
        ],

        "change_analysis":
        False,

        "trend_analysis":
        False,

        **common,

        "quality": {
            "scl_valid_percent":
            (
                result[
                    "scl_quality"
                ]["valid_fraction"]
                * 100.0
            ),

            "cloud_percent":
            (
                result[
                    "scl_quality"
                ]["cloud_fraction"]
                * 100.0
            ),

            "shadow_percent":
            (
                result[
                    "scl_quality"
                ]["shadow_fraction"]
                * 100.0
            ),

            "snow_percent":
            (
                result[
                    "scl_quality"
                ]["snow_fraction"]
                * 100.0
            ),
        },

        "index": {
            "name":
            index_name,

            "mean":
            index["mean"],

            "min":
            index["min"],

            "max":
            index["max"],

            "std":
            index["std"],

            "valid_pixel_percent":
            (
                index[
                    "valid_pixel_fraction"
                ]
                * 100.0
            ),

            "positive_pixel_percent":
            positive_percent,

            "interpretation":
            index[
                "interpretation"
            ],
        },

        "resolution": {
            "display":
            result[
                "resolution"
            ]["display_chip"],
        },

        "outputs":
        result["outputs"],

        "message": (
            f"{index_name} analysis for "
            f"{result['location']} found "
            f"a mean {index_name} of "
            f"{index['mean']:.4f}. "
            f"{positive_percent:.2f}% of "
            "valid pixels have a positive "
            f"{index_name} value. "
            f"{index['interpretation']}."
        ),

        "generated_at":
        datetime.now(
            timezone.utc
        ).isoformat(),
    }


def build_change_response(
    query,
    parsed,
    result,
):

    index_name = (
        result[
            "analysis_type"
        ].upper()
    )

    before = (
        result["before"]
    )

    after = (
        result["after"]
    )

    change = (
        result["change"]
    )

    return {

        "success":
        True,

        "query":
        query,

        "parsed_query":
        parsed,

        "analysis_type":
        result[
            "analysis_type"
        ],

        "change_analysis":
        True,

        "trend_analysis":
        False,

        "location": {
            "requested":
            result["location"],

            "resolved":
            result[
                "resolved_location"
            ],

            "latitude":
            result[
                "coordinates"
            ]["latitude"],

            "longitude":
            result[
                "coordinates"
            ]["longitude"],
        },

        "dates": {
            "requested_start":
            result[
                "requested_dates"
            ]["start"],

            "requested_end":
            result[
                "requested_dates"
            ]["end"],

            "selected_start":
            before[
                "scene"
            ]["date"],

            "selected_end":
            after[
                "scene"
            ]["date"],
        },

        "before": {
            "scene":
            before["scene"],

            "coverage_percent":
            (
                before[
                    "coverage"
                ]
                * 100.0
            ),

            "candidate_count":
            before[
                "candidate_count"
            ],

            "rejected_count":
            before[
                "rejected_count"
            ],

            "mean":
            before[
                "stats"
            ]["mean"],

            "min":
            before[
                "stats"
            ]["min"],

            "max":
            before[
                "stats"
            ]["max"],

            "std":
            before[
                "stats"
            ]["std"],
        },

        "after": {
            "scene":
            after["scene"],

            "coverage_percent":
            (
                after[
                    "coverage"
                ]
                * 100.0
            ),

            "candidate_count":
            after[
                "candidate_count"
            ],

            "rejected_count":
            after[
                "rejected_count"
            ],

            "mean":
            after[
                "stats"
            ]["mean"],

            "min":
            after[
                "stats"
            ]["min"],

            "max":
            after[
                "stats"
            ]["max"],

            "std":
            after[
                "stats"
            ]["std"],
        },

        "change": {
            "index_name":
            index_name,

            "mean":
            change["mean"],

            "min":
            change["min"],

            "max":
            change["max"],

            "std":
            change["std"],

            "increase_percent":
            (
                change[
                    "increase_fraction"
                ]
                * 100.0
            ),

            "decrease_percent":
            (
                change[
                    "decrease_fraction"
                ]
                * 100.0
            ),

            "stable_percent":
            (
                change[
                    "stable_fraction"
                ]
                * 100.0
            ),

            "valid_pixel_percent":
            (
                change[
                    "valid_pixel_fraction"
                ]
                * 100.0
            ),

            "threshold":
            change[
                "threshold"
            ],

            "interpretation":
            change[
                "interpretation"
            ],
        },

        "resolution": {
            "display":
            result[
                "resolution"
            ]["display_chip"],
        },

        "outputs":
        result["outputs"],

        "message": (
            f"{index_name} change analysis "
            f"for {result['location']} "
            f"found a mean change of "
            f"{change['mean']:+.4f} "
            f"between "
            f"{before['scene']['date']} "
            f"and "
            f"{after['scene']['date']}. "
            f"{change['interpretation']}"
        ),

        "generated_at":
        datetime.now(
            timezone.utc
        ).isoformat(),
    }


def build_trend_response(
    query,
    parsed,
    result,
):

    trend = (
        result["trend"]
    )

    observations = []

    for item in result[
        "observations"
    ]:

        observations.append(
            {
                "requested_date":
                item[
                    "requested_date"
                ],

                "selected_date":
                item[
                    "selected_date"
                ],

                "scene_id":
                item[
                    "scene_id"
                ],

                "tile":
                item.get(
                    "tile"
                ),

                "cloud_cover_percent":
                item.get(
                    "cloud_cover"
                ),

                "coverage_percent":
                item[
                    "coverage_percent"
                ],

                "mean_ndvi":
                item[
                    "mean_ndvi"
                ],

                "min_ndvi":
                item[
                    "min_ndvi"
                ],

                "max_ndvi":
                item[
                    "max_ndvi"
                ],

                "std_ndvi":
                item[
                    "std_ndvi"
                ],
            }
        )

    return {

        "success":
        True,

        "query":
        query,

        "parsed_query":
        parsed,

        "analysis_type":
        "ndvi",

        "change_analysis":
        False,

        "trend_analysis":
        True,

        "location": {
            "requested":
            result["location"],

            "resolved":
            result[
                "resolved_location"
            ],

            "latitude":
            result[
                "coordinates"
            ]["latitude"],

            "longitude":
            result[
                "coordinates"
            ]["longitude"],
        },

        "dates": {
            "requested_start":
            result[
                "requested_dates"
            ]["start"],

            "requested_end":
            result[
                "requested_dates"
            ]["end"],
        },

        "observation_count":
        result[
            "observation_count"
        ],

        "observations":
        observations,

        "trend": {
            "first_mean_ndvi":
            trend[
                "first_mean_ndvi"
            ],

            "last_mean_ndvi":
            trend[
                "last_mean_ndvi"
            ],

            "total_change":
            trend[
                "total_change"
            ],

            "slope_per_day":
            trend[
                "slope_per_day"
            ],

            "slope_per_30_days":
            trend[
                "slope_per_30_days"
            ],

            "interpretation":
            trend[
                "interpretation"
            ],
        },

        "outputs":
        result["outputs"],

        "message": (
            "Vegetation trend analysis "
            f"for {result['location']} "
            f"used "
            f"{result['observation_count']} "
            "Sentinel-2 observations. "
            "Mean NDVI changed from "
            f"{trend['first_mean_ndvi']:.4f} "
            "to "
            f"{trend['last_mean_ndvi']:.4f}. "
            f"{trend['interpretation']}"
        ),

        "generated_at":
        datetime.now(
            timezone.utc
        ).isoformat(),
    }


def build_error_response(
    query,
    parsed,
    error_type,
    message,
):

    return {

        "success":
        False,

        "query":
        query,

        "parsed_query":
        parsed,

        "error": {
            "type":
            error_type,

            "message":
            message,
        },
    }


def execute_query(
    query,
):

    parsed = parse_query(
        query
    )

    location = parsed.get(
        "location"
    )

    if not location:

        return build_error_response(
            query=query,
            parsed=parsed,
            error_type=(
                "location_not_found"
            ),
            message=(
                "SatQuery could not "
                "determine the requested "
                "location."
            ),
        )

    analysis_type = parsed.get(
        "analysis_type"
    )

    if (
        analysis_type
        not in SUPPORTED_ANALYSES
    ):

        return build_error_response(
            query=query,
            parsed=parsed,
            error_type=(
                "unsupported_analysis"
            ),
            message=(
                "SatQuery currently "
                "supports imagery, NDVI, "
                "vegetation, NDWI/water, "
                "NDBI/urban, change "
                "analysis and vegetation "
                "trend analysis."
            ),
        )

    try:

        # -----------------------------
        # TREND ANALYSIS
        # -----------------------------

        if parsed.get(
            "trend_analysis"
        ):

            if (
                analysis_type
                not in {
                    "ndvi",
                    "vegetation",
                }
            ):

                return build_error_response(
                    query=query,
                    parsed=parsed,
                    error_type=(
                        "unsupported_trend_analysis"
                    ),
                    message=(
                        "Trend analysis currently "
                        "supports vegetation / "
                        "NDVI queries."
                    ),
                )

            result = (
                analyze_vegetation_trend(
                    location=location,

                    date_start=parsed.get(
                        "date_start"
                    ),

                    date_end=parsed.get(
                        "date_end"
                    ),
                )
            )

            return build_trend_response(
                query=query,
                parsed=parsed,
                result=result,
            )

        # -----------------------------
        # CHANGE ANALYSIS
        # -----------------------------

        if parsed.get(
            "change_analysis"
        ):

            if (
                analysis_type
                == "imagery"
            ):

                return build_error_response(
                    query=query,
                    parsed=parsed,
                    error_type=(
                        "unsupported_change_analysis"
                    ),
                    message=(
                        "Two-date change "
                        "analysis currently "
                        "supports NDVI, "
                        "vegetation, NDWI/water "
                        "and NDBI/urban."
                    ),
                )

            result = analyze_change(
                location=location,

                analysis_type=(
                    analysis_type
                ),

                date_start=parsed.get(
                    "date_start"
                ),

                date_end=parsed.get(
                    "date_end"
                ),
            )

            return build_change_response(
                query=query,
                parsed=parsed,
                result=result,
            )

        # -----------------------------
        # IMAGERY
        # -----------------------------

        if (
            analysis_type
            == "imagery"
        ):

            result = (
                get_location_imagery(
                    location=location,

                    target_date=(
                        parsed.get(
                            "date"
                        )
                    ),
                )
            )

            return build_imagery_response(
                query=query,
                parsed=parsed,
                result=result,
            )

        # -----------------------------
        # NDWI / NDBI
        # -----------------------------

        if (
            analysis_type
            in {
                "ndwi",
                "water",
                "ndbi",
                "urban",
            }
        ):

            result = (
                analyze_environmental_index(
                    location=location,

                    analysis_type=(
                        analysis_type
                    ),

                    target_date=(
                        parsed.get(
                            "date"
                        )
                    ),
                )
            )

            return build_environmental_response(
                query=query,
                parsed=parsed,
                result=result,
            )

        # -----------------------------
        # NDVI / VEGETATION
        # -----------------------------

        result = analyze_location(
            location=location,

            target_date=(
                parsed.get(
                    "date"
                )
            ),
        )

    except Exception as error:

        return build_error_response(
            query=query,
            parsed=parsed,
            error_type=(
                "analysis_failed"
            ),
            message=str(
                error
            ),
        )

    return build_success_response(
        query=query,
        parsed=parsed,
        result=result,
    )


if __name__ == "__main__":

    response = execute_query(
        "Analyze vegetation trend "
        "in Varanasi between "
        "2026-01-10 and 2026-04-10"
    )

    print(
        response
    )