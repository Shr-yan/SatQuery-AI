from datetime import datetime, timezone

from live_analysis import (
    analyze_location,
    get_location_imagery,
)

from query_parser import (
    parse_query,
)


SUPPORTED_ANALYSES = {
    "ndvi",
    "vegetation",
    "imagery",
}


def build_success_response(
    query,
    parsed,
    result,
):

    return {

        "success": True,

        "query": query,

        "parsed_query": parsed,

        "analysis_type": (
            parsed.get(
                "analysis_type"
            )
        ),

        "location": {
            "requested": (
                result["location"]
            ),

            "resolved": (
                result[
                    "resolved_location"
                ]
            ),

            "latitude": (
                result[
                    "coordinates"
                ]["latitude"]
            ),

            "longitude": (
                result[
                    "coordinates"
                ]["longitude"]
            ),
        },

        "date": {
            "requested": (
                result[
                    "requested_date"
                ]
            ),

            "selected": (
                result[
                    "scene"
                ]["date"]
            ),

            "difference_days": (
                result[
                    "date_difference_days"
                ]
            ),
        },

        "scene": {
            "id": (
                result[
                    "scene"
                ]["id"]
            ),

            "tile": (
                result[
                    "scene"
                ].get(
                    "tile"
                )
            ),

            "cloud_cover_percent": (
                result[
                    "scene"
                ]["cloud_cover"]
            ),

            "candidate_count": (
                result[
                    "candidate_scene_count"
                ]
            ),

            "rejected_count": (
                result[
                    "rejected_scene_count"
                ]
            ),

            "aoi_coverage_percent": (
                result[
                    "valid_coverage"
                ]
                * 100.0
            ),
        },

        "quality": {
            "scl_valid_percent": (
                result[
                    "scl_quality"
                ]["valid_fraction"]
                * 100.0
            ),

            "cloud_percent": (
                result[
                    "scl_quality"
                ]["cloud_fraction"]
                * 100.0
            ),

            "shadow_percent": (
                result[
                    "scl_quality"
                ]["shadow_fraction"]
                * 100.0
            ),

            "snow_percent": (
                result[
                    "scl_quality"
                ]["snow_fraction"]
                * 100.0
            ),
        },

        "vegetation": {
            "mean_ndvi": (
                result[
                    "ndvi"
                ]["mean"]
            ),

            "min_ndvi": (
                result[
                    "ndvi"
                ]["min"]
            ),

            "max_ndvi": (
                result[
                    "ndvi"
                ]["max"]
            ),

            "std_ndvi": (
                result[
                    "ndvi"
                ]["std"]
            ),

            "valid_pixel_percent": (
                result[
                    "ndvi"
                ][
                    "valid_pixel_fraction"
                ]
                * 100.0
            ),

            "condition": (
                result[
                    "ndvi"
                ]["condition"]
            ),
        },

        "model": {
            "predicted_mean_ndvi": (
                result[
                    "model"
                ]["prediction"]
            ),

            "absolute_difference": (
                result[
                    "model"
                ][
                    "absolute_difference"
                ]
            ),

            "agreement": (
                result[
                    "model"
                ]["agreement"]
            ),
        },

        "resolution": {
            "model": (
                result[
                    "resolution"
                ]["model_chip"]
            ),

            "display": (
                result[
                    "resolution"
                ]["display_chip"]
            ),
        },

        "outputs": (
            result[
                "outputs"
            ]
        ),

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

        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }


def build_imagery_response(
    query,
    parsed,
    result,
):

    return {

        "success": True,

        "query": query,

        "parsed_query": parsed,

        "analysis_type": "imagery",

        "location": {
            "requested": (
                result["location"]
            ),

            "resolved": (
                result[
                    "resolved_location"
                ]
            ),

            "latitude": (
                result[
                    "coordinates"
                ]["latitude"]
            ),

            "longitude": (
                result[
                    "coordinates"
                ]["longitude"]
            ),
        },

        "date": {
            "requested": (
                result[
                    "requested_date"
                ]
            ),

            "selected": (
                result[
                    "scene"
                ]["date"]
            ),

            "difference_days": (
                result[
                    "date_difference_days"
                ]
            ),
        },

        "scene": {
            "id": (
                result[
                    "scene"
                ]["id"]
            ),

            "tile": (
                result[
                    "scene"
                ].get(
                    "tile"
                )
            ),

            "cloud_cover_percent": (
                result[
                    "scene"
                ]["cloud_cover"]
            ),

            "candidate_count": (
                result[
                    "candidate_scene_count"
                ]
            ),

            "rejected_count": (
                result[
                    "rejected_scene_count"
                ]
            ),

            "aoi_coverage_percent": (
                result[
                    "valid_coverage"
                ]
                * 100.0
            ),
        },

        "resolution": {
            "display": (
                result[
                    "resolution"
                ]["display_chip"]
            ),
        },

        "outputs": (
            result[
                "outputs"
            ]
        ),

        "message": (
            "Sentinel-2 RGB imagery "
            "was retrieved for "
            f"{result['location']} "
            "using the observation "
            f"from {result['scene']['date']}."
        ),

        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }


def build_error_response(
    query,
    parsed,
    error_type,
    message,
):

    return {

        "success": False,

        "query": query,

        "parsed_query": parsed,

        "error": {
            "type": (
                error_type
            ),

            "message": (
                message
            ),
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
                "supports Sentinel-2 "
                "imagery, NDVI, and "
                "vegetation analysis."
            ),
        )

    try:

        if analysis_type == "imagery":

            result = get_location_imagery(
                location=location,
                target_date=(
                    parsed.get(
                        "date"
                    )
                ),
            )

            return build_imagery_response(
                query=query,
                parsed=parsed,
                result=result,
            )

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
        "Show Sentinel-2 imagery "
        "for Varanasi on 2026-02-10"
    )

    print(
        response
    )