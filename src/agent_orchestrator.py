from __future__ import annotations

from agent_registry import (
    get_components,
)


ORCHESTRATOR_VERSION = "1.0"

CAPTION_TERMS = {
    "describe",
    "caption",
    "scene description",
    "summarize the image",
    "summarise the image",
}


def _question_intent(
    question,
):
    question_lower = (
        str(question or "")
        .strip()
        .lower()
    )

    if not question_lower:
        return "validation"

    if any(
        term in question_lower
        for term in CAPTION_TERMS
    ):
        return "captioning"

    return "vqa"


def _build_plan(
    task,
    registry_ids,
    routing_factors,
    observable_decision,
    key_parameters=None,
):
    selected_components = get_components(
        registry_ids
    )

    return {
        "task": task,
        "controller": "SatQuery Agent Controller",
        "orchestrator_version": ORCHESTRATOR_VERSION,
        "routing_factors": routing_factors,
        "observable_decision": observable_decision,
        "selected_components": selected_components,
        "tools": [
            component["name"]
            for component
            in selected_components
        ],
        "key_parameters": key_parameters or {},
    }


def route_uploaded_task(
    input_configuration,
    question=None,
    stage="analysis",
    specialist_available=True,
    input_metadata=None,
):
    """
    Build the observable SatQuery execution plan from the declared input
    configuration and user query. This returns an auditable routing trace,
    not hidden chain-of-thought reasoning.
    """

    input_metadata = input_metadata or {}

    if isinstance(
        input_configuration,
        str,
    ):
        kind = input_configuration
        configuration = {
            "kind": kind,
        }
    else:
        configuration = dict(
            input_configuration or {}
        )
        kind = configuration.get(
            "kind"
        )

    intent = _question_intent(
        question
    )

    routing_factors = {
        "input_configuration": kind,
        "input_count": configuration.get(
            "input_count"
        ),
        "declared_modalities": configuration.get(
            "modalities"
        ),
        "query_intent": intent,
        "stage": stage,
    }

    if kind == "single_image":
        if stage == "validation":
            return _build_plan(
                task="single_image_input_validation",
                registry_ids=[
                    "agent_controller",
                    "input_validator",
                ],
                routing_factors=routing_factors,
                observable_decision=(
                    "One uploaded image selected the single-image validation workflow."
                ),
                key_parameters={
                    "input_format": input_metadata.get(
                        "format"
                    ),
                    "input_bands": input_metadata.get(
                        "bands"
                    ),
                },
            )

        task = (
            "single_image_captioning"
            if intent == "captioning"
            else "single_image_vqa"
        )

        registry_ids = [
            "agent_controller",
            "input_validator",
        ]

        if specialist_available:
            registry_ids.append(
                "eurosat_scene_specialist"
            )

        registry_ids.append(
            "qwen_vision"
        )

        return _build_plan(
            task=task,
            registry_ids=registry_ids,
            routing_factors=routing_factors,
            observable_decision=(
                "One validated image selected the single-image vision-language workflow; "
                "caption wording selects captioning, otherwise VQA is used."
            ),
            key_parameters={
                "input_format": input_metadata.get(
                    "format"
                ),
                "input_bands": input_metadata.get(
                    "bands"
                ),
                "specialist_top_k": (
                    3
                    if specialist_available
                    else None
                ),
                "specialist_input_size": (
                    64
                    if specialist_available
                    else None
                ),
                "vision_reasoning_effort": "none",
            },
        )

    if kind == "bitemporal_pair":
        registry_ids = [
            "agent_controller",
            "input_validator",
            "pair_compatibility",
            "visual_change_tool",
        ]

        task = (
            "bi_temporal_pair_validation_and_visual_change"
            if stage == "validation"
            else "bi_temporal_change_vqa"
        )

        if stage != "validation":
            registry_ids.append(
                "qwen_vision"
            )

        return _build_plan(
            task=task,
            registry_ids=registry_ids,
            routing_factors=routing_factors,
            observable_decision=(
                "Two images declared as before/after observations selected the bi-temporal change workflow."
            ),
            key_parameters={
                "pair_role": "before_after",
                "visual_change_threshold": configuration.get(
                    "visual_change_threshold"
                ),
                "vision_reasoning_effort": (
                    "none"
                    if stage != "validation"
                    else None
                ),
            },
        )

    if kind == "optical_sar_pair":
        registry_ids = [
            "agent_controller",
            "input_validator",
            "pair_compatibility",
            "optical_sar_fusion",
        ]

        task = (
            "optical_sar_pair_validation_and_fusion"
            if stage == "validation"
            else "optical_sar_joint_vqa"
        )

        if stage != "validation":
            registry_ids.append(
                "qwen_vision"
            )

        return _build_plan(
            task=task,
            registry_ids=registry_ids,
            routing_factors=routing_factors,
            observable_decision=(
                "A co-registered optical/SAR input configuration selected the cross-modal fusion workflow."
            ),
            key_parameters={
                "pair_role": "optical_sar",
                "vision_reasoning_effort": (
                    "none"
                    if stage != "validation"
                    else None
                ),
            },
        )

    raise ValueError(
        "Unsupported SatQuery input configuration for agent routing: "
        f"{kind}"
    )


def build_search_earth_plan(
    analysis_result,
):
    analysis_type = str(
        analysis_result.get(
            "analysis_type",
            "imagery",
        )
    ).lower()

    is_change = bool(
        analysis_result.get(
            "change_analysis"
        )
    )
    is_trend = bool(
        analysis_result.get(
            "trend_analysis"
        )
    )

    registry_ids = [
        "agent_controller",
        "geospatial_aoi",
        "sentinel_stac",
    ]

    if is_trend:
        task = "vegetation_trend_analysis"
        registry_ids.extend(
            [
                "scientific_index_engine",
                "trend_tool",
            ]
        )
    elif is_change:
        task = "earth_search_change_analysis"
        registry_ids.extend(
            [
                "scientific_index_engine",
                "visual_change_tool",
            ]
        )
    elif analysis_type in {
        "ndvi",
        "vegetation",
    }:
        task = "earth_search_vegetation_analysis"
        registry_ids.extend(
            [
                "scientific_index_engine",
                "cnn_ndvi_validator",
            ]
        )
    elif analysis_type in {
        "ndwi",
        "water",
        "ndbi",
        "urban",
    }:
        task = "earth_search_environmental_index_analysis"
        registry_ids.append(
            "scientific_index_engine"
        )
    else:
        task = "earth_search_imagery_retrieval"

    return _build_plan(
        task=task,
        registry_ids=registry_ids,
        routing_factors={
            "input_configuration": "search_earth",
            "input_count": 0,
            "analysis_type": analysis_type,
            "change_analysis": is_change,
            "trend_analysis": is_trend,
        },
        observable_decision=(
            "The parsed natural-language request selected the Search Earth workflow and its required geospatial tools."
        ),
        key_parameters={
            "analysis_type": analysis_type,
            "requested_date": (
                analysis_result.get(
                    "date",
                    {}
                ).get(
                    "requested"
                )
                if isinstance(
                    analysis_result.get("date"),
                    dict,
                )
                else None
            ),
        },
    )
