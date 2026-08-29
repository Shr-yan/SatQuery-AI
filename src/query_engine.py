from satquery_service import (
    execute_query,
)


def format_success_response(
    response,
):

    location = (
        response[
            "location"
        ]
    )

    date = (
        response[
            "date"
        ]
    )

    scene = (
        response[
            "scene"
        ]
    )

    quality = (
        response[
            "quality"
        ]
    )

    vegetation = (
        response[
            "vegetation"
        ]
    )

    model = (
        response[
            "model"
        ]
    )

    outputs = (
        response[
            "outputs"
        ]
    )

    resolution = (
        response[
            "resolution"
        ]
    )

    lines = [

        "SatQuery AI Result",
        "==================",
        "",

        (
            "Location: "
            f"{location['requested']}"
        ),

        (
            "Resolved location: "
            f"{location['resolved']}"
        ),

        (
            "Coordinates: "
            f"{location['latitude']:.6f}, "
            f"{location['longitude']:.6f}"
        ),

        (
            "Requested date: "
            f"{date['requested']}"
        ),

        (
            "Selected scene date: "
            f"{date['selected']}"
        ),

        (
            "Difference from "
            "requested date: "
            f"{date['difference_days']} days"
        ),

        "",
        "Scene Information",
        "-----------------",

        (
            "Sentinel-2 scene: "
            f"{scene['id']}"
        ),

        (
            "MGRS tile: "
            f"{scene['tile']}"
        ),

        (
            "Cloud cover "
            "(scene metadata): "
            f"{scene['cloud_cover_percent']:.3f}%"
        ),

        (
            "Candidate scenes: "
            f"{scene['candidate_count']}"
        ),

        (
            "Rejected scenes: "
            f"{scene['rejected_count']}"
        ),

        (
            "AOI coverage: "
            f"{scene['aoi_coverage_percent']:.2f}%"
        ),

        "",
        "AOI Pixel Quality",
        "-----------------",

        (
            "SCL-valid pixels: "
            f"{quality['scl_valid_percent']:.2f}%"
        ),

        (
            "Cloud pixels: "
            f"{quality['cloud_percent']:.2f}%"
        ),

        (
            "Shadow pixels: "
            f"{quality['shadow_percent']:.2f}%"
        ),

        (
            "Snow/ice pixels: "
            f"{quality['snow_percent']:.2f}%"
        ),

        "",
        "Vegetation Analysis",
        "-------------------",

        (
            "Mean NDVI: "
            f"{vegetation['mean_ndvi']:.4f}"
        ),

        (
            "Minimum NDVI: "
            f"{vegetation['min_ndvi']:.4f}"
        ),

        (
            "Maximum NDVI: "
            f"{vegetation['max_ndvi']:.4f}"
        ),

        (
            "NDVI standard deviation: "
            f"{vegetation['std_ndvi']:.4f}"
        ),

        (
            "NDVI pixels used: "
            f"{vegetation['valid_pixel_percent']:.2f}%"
        ),

        (
            "Vegetation condition: "
            f"{vegetation['condition']}"
        ),

        "",
        "ML Verification",
        "---------------",

        (
            "CNN predicted "
            "mean NDVI: "
            f"{model['predicted_mean_ndvi']:.4f}"
        ),

        (
            "Difference from "
            "scientific NDVI: "
            f"{model['absolute_difference']:.4f}"
        ),

        (
            "Model/reference agreement: "
            f"{model['agreement']}"
        ),

        "",
        "Generated Products",
        "------------------",

        (
            "Model resolution: "
            f"{resolution['model']}x"
            f"{resolution['model']}"
        ),

        (
            "Display resolution: "
            f"{resolution['display']}x"
            f"{resolution['display']}"
        ),

        (
            "RGB preview: "
            f"{outputs['rgb_preview']}"
        ),

        (
            "NDVI map: "
            f"{outputs['ndvi_preview']}"
        ),

        (
            "Result metadata: "
            f"{outputs['metadata']}"
        ),

        "",
        "Answer",
        "------",

        response[
            "message"
        ],
    ]

    return "\n".join(
        lines
    )


def format_error_response(
    response,
):

    error = response[
        "error"
    ]

    return (
        "SatQuery AI Error\n"
        "=================\n\n"
        f"Type: {error['type']}\n"
        f"Message: {error['message']}"
    )


def process_query(
    query,
):

    response = execute_query(
        query
    )

    if response[
        "success"
    ]:

        formatted = (
            format_success_response(
                response
            )
        )

    else:

        formatted = (
            format_error_response(
                response
            )
        )

    return (
        response,
        formatted,
    )


if __name__ == "__main__":

    response, formatted = (
        process_query(
            "Analyze vegetation "
            "health for Varanasi "
            "on 2026-02-10"
        )
    )

    print(
        formatted
    )