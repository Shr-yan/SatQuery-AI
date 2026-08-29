from live_analysis import (
    analyze_location,
)

from query_parser import (
    parse_query,
)


def build_analysis_response(
    parsed,
    result,
):

    scene = result[
        "scene"
    ]

    ndvi = result[
        "ndvi"
    ]

    model = result[
        "model"
    ]

    coordinates = result[
        "coordinates"
    ]

    quality = result[
        "chip_quality"
    ]

    scl_quality = result[
        "scl_quality"
    ]

    outputs = result[
        "outputs"
    ]

    resolved_location = (
        coordinates.get(
            "name",
            result["location"],
        )
    )

    lines = [

        "SatQuery AI Result",
        "==================",
        "",

        (
            "Location: "
            f"{result['location']}"
        ),

        (
            "Resolved location: "
            f"{resolved_location}"
        ),

        (
            "Coordinates: "
            f"{coordinates['latitude']:.6f}, "
            f"{coordinates['longitude']:.6f}"
        ),

        (
            "Requested date: "
            f"{result['requested_date']}"
        ),

        (
            "Selected scene date: "
            f"{scene['date']}"
        ),

        (
            "Sentinel-2 scene: "
            f"{scene['id']}"
        ),

        (
            "Cloud cover "
            "(scene metadata): "
            f"{scene['cloud_cover']:.3f}%"
        ),

        (
            "Candidate scenes: "
            f"{result['candidate_scene_count']}"
        ),

        (
            "Scenes rejected for "
            "coverage/error: "
            f"{result['rejected_scene_count']}"
        ),

        (
            "Selected-scene AOI "
            "coverage: "
            f"{result['valid_coverage'] * 100:.1f}%"
        ),
    ]

    if (
        result[
            "date_difference_days"
        ]
        is not None
    ):

        lines.append(
            (
                "Difference from "
                "requested date: "
                f"{result['date_difference_days']} "
                "days"
            )
        )

    # --------------------------------
    # Pixel quality
    # --------------------------------

    lines.extend(
        [
            "",
            "AOI Pixel Quality",
            "-----------------",

            (
                "SCL-valid pixels: "
                f"{scl_quality['valid_fraction'] * 100:.2f}%"
            ),

            (
                "Cloud pixels: "
                f"{scl_quality['cloud_fraction'] * 100:.2f}%"
            ),

            (
                "Shadow pixels: "
                f"{scl_quality['shadow_fraction'] * 100:.2f}%"
            ),

            (
                "Snow/ice pixels: "
                f"{scl_quality['snow_fraction'] * 100:.2f}%"
            ),

            "",
            "Vegetation Analysis",
            "-------------------",

            (
                "All-zero raster "
                "pixel fraction: "
                f"{quality['zero_fraction']:.4f}"
            ),

            (
                "NDVI pixels used "
                "after masking: "
                f"{ndvi['valid_pixel_fraction'] * 100:.2f}%"
            ),

            (
                "Mean NDVI: "
                f"{ndvi['mean']:.4f}"
            ),

            (
                "Minimum NDVI: "
                f"{ndvi['min']:.4f}"
            ),

            (
                "Maximum NDVI: "
                f"{ndvi['max']:.4f}"
            ),

            (
                "NDVI standard "
                "deviation: "
                f"{ndvi['std']:.4f}"
            ),

            (
                "Vegetation condition: "
                f"{ndvi['condition']}"
            ),

            "",
            "ML Verification",
            "---------------",

            (
                "CNN predicted "
                "mean NDVI: "
                f"{model['prediction']:.4f}"
            ),

            (
                "Difference from "
                "quality-masked NDVI: "
                f"{model['absolute_difference']:.4f}"
            ),

            (
                "Model/reference "
                "agreement: "
                f"{model['agreement']}"
            ),

            "",
            "Generated Products",
            "------------------",

            (
                "RGB preview: "
                f"{outputs['rgb_preview']}"
            ),

            (
                "Quality-masked "
                "NDVI map: "
                f"{outputs['ndvi_preview']}"
            ),

            "",
            "Answer",
            "------",

            (
                "The Sentinel-2 "
                "observation selected "
                f"for {result['location']} "
                "has a quality-masked "
                "mean NDVI of "
                f"{ndvi['mean']:.4f}. "
                "This is heuristically "
                "classified as "
                f"{ndvi['condition'].lower()}."
            ),
        ]
    )

    return "\n".join(
        lines
    )


def process_query(query):

    parsed = parse_query(
        query
    )

    location = parsed.get(
        "location"
    )

    if not location:

        return (
            parsed,
            (
                "SatQuery could not "
                "determine the "
                "requested location."
            ),
        )

    analysis_type = parsed.get(
        "analysis_type"
    )

    if analysis_type not in [
        "ndvi",
        "vegetation",
    ]:

        return (
            parsed,
            (
                "SatQuery understood "
                "the request, but this "
                "Phase 4 pipeline "
                "currently supports "
                "NDVI/vegetation analysis."
            ),
        )

    try:

        result = analyze_location(
            location=location,
            target_date=parsed.get(
                "date"
            ),
        )

    except Exception as error:

        return (
            parsed,
            (
                "SatQuery analysis "
                "failed: "
                f"{error}"
            ),
        )

    response = (
        build_analysis_response(
            parsed,
            result,
        )
    )

    return (
        parsed,
        response,
    )


if __name__ == "__main__":

    query = (
        "Analyze vegetation health "
        "for Varanasi on 2026-02-10"
    )

    parsed, response = (
        process_query(
            query
        )
    )

    print(
        response
    )