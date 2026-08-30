from pathlib import Path


def choose_vision_image(
    analysis_result,
    question,
):

    outputs = (
        analysis_result.get(
            "outputs",
            {}
        )
    )


    question_lower = (
        question.lower()
    )


    candidates = []


    # ----------------------------
    # Explicit image requests
    # ----------------------------

    if (
        "change" in question_lower
        and outputs.get(
            "change_preview"
        )
    ):

        candidates.append(
            (
                "change map",
                outputs[
                    "change_preview"
                ],
            )
        )


    if (
        "trend" in question_lower
        and outputs.get(
            "trend_preview"
        )
    ):

        candidates.append(
            (
                "vegetation trend chart",
                outputs[
                    "trend_preview"
                ],
            )
        )


    if (
        (
            "ndvi"
            in question_lower
            or "vegetation map"
            in question_lower
        )
        and outputs.get(
            "ndvi_preview"
        )
    ):

        candidates.append(
            (
                "NDVI map",
                outputs[
                    "ndvi_preview"
                ],
            )
        )


    if (
        (
            "ndwi"
            in question_lower
            or "water map"
            in question_lower
        )
        and outputs.get(
            "index_preview"
        )
    ):

        candidates.append(
            (
                "NDWI map",
                outputs[
                    "index_preview"
                ],
            )
        )


    if (
        (
            "ndbi"
            in question_lower
            or "built-up map"
            in question_lower
            or "urban map"
            in question_lower
        )
        and outputs.get(
            "index_preview"
        )
    ):

        candidates.append(
            (
                "NDBI map",
                outputs[
                    "index_preview"
                ],
            )
        )


    if (
        (
            "rgb"
            in question_lower
            or "satellite image"
            in question_lower
            or "imagery"
            in question_lower
            or "what do you see"
            in question_lower
            or "visually"
            in question_lower
        )
        and outputs.get(
            "rgb_preview"
        )
    ):

        candidates.append(
            (
                "Sentinel-2 RGB image",
                outputs[
                    "rgb_preview"
                ],
            )
        )


    # ----------------------------
    # Sensible fallback
    # ----------------------------

    if not candidates:

        if outputs.get(
            "change_preview"
        ):

            candidates.append(
                (
                    "change map",
                    outputs[
                        "change_preview"
                    ],
                )
            )

        elif outputs.get(
            "index_preview"
        ):

            index_name = (
                analysis_result
                .get(
                    "index",
                    {}
                )
                .get(
                    "name",
                    "analysis"
                )
            )

            candidates.append(
                (
                    f"{index_name} map",
                    outputs[
                        "index_preview"
                    ],
                )
            )

        elif outputs.get(
            "ndvi_preview"
        ):

            candidates.append(
                (
                    "NDVI map",
                    outputs[
                        "ndvi_preview"
                    ],
                )
            )

        elif outputs.get(
            "rgb_preview"
        ):

            candidates.append(
                (
                    "Sentinel-2 RGB image",
                    outputs[
                        "rgb_preview"
                    ],
                )
            )

        elif outputs.get(
            "trend_preview"
        ):

            candidates.append(
                (
                    "vegetation trend chart",
                    outputs[
                        "trend_preview"
                    ],
                )
            )


    if not candidates:

        return (
            None,
            None
        )


    image_type, image_path = (
        candidates[0]
    )


    path = Path(
        image_path
    )


    if not path.exists():

        return (
            None,
            None
        )


    return (
        image_type,
        str(
            path
        ),
    )