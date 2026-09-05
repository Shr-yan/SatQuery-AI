from __future__ import annotations


MODEL_REGISTRY = {
    "agent_controller": {
        "name": "SatQuery Agent Controller",
        "kind": "controller",
        "role": "routes a query and input configuration to the appropriate remote-sensing workflow",
    },
    "input_validator": {
        "name": "SatQuery Input Validator",
        "kind": "tool",
        "role": "format, metadata and compatibility validation",
    },
    "pair_compatibility": {
        "name": "SatQuery Pair Compatibility Checker",
        "kind": "tool",
        "role": "checks dimensions, georeferencing and spatial correspondence for paired imagery",
    },
    "eurosat_scene_specialist": {
        "name": "SatQuery EuroSAT Scene Specialist v1",
        "kind": "remote_sensing_model",
        "role": "remote-sensing optical scene evidence",
        "adaptation": "trained on EuroSAT RGB",
    },
    "qwen_vision": {
        "name": "Qwen Vision-Language Model",
        "kind": "vision_language_model",
        "role": "visual-language reasoning and response generation",
    },
    "visual_change_tool": {
        "name": "SatQuery Visual Change Tool",
        "kind": "tool",
        "role": "bi-temporal visual-difference evidence",
    },
    "optical_sar_fusion": {
        "name": "SatQuery Optical-SAR Evidence Fusion Tool",
        "kind": "tool",
        "role": "cross-modal candidate evidence fusion",
    },
    "scientific_index_engine": {
        "name": "SatQuery Scientific Index Engine",
        "kind": "tool",
        "role": "NDVI, NDWI and NDBI calculations",
    },
    "sentinel_stac": {
        "name": "Sentinel-2 STAC Retrieval Tool",
        "kind": "tool",
        "role": "searches and selects Sentinel-2 L2A observations",
    },
    "geospatial_aoi": {
        "name": "SatQuery Geospatial AOI Tool",
        "kind": "tool",
        "role": "geocodes locations and constructs the analysis area",
    },
    "trend_tool": {
        "name": "SatQuery Vegetation Trend Tool",
        "kind": "tool",
        "role": "runs repeated observations and summarizes temporal NDVI trends",
    },
    "cnn_ndvi_validator": {
        "name": "SatQuery Geographic NDVI CNN",
        "kind": "remote_sensing_model",
        "role": "learned NDVI consistency estimate",
    },
    "evidence_reporter": {
        "name": "SatQuery Evidence Report Generator",
        "kind": "tool",
        "role": "packages structured results, execution traces and visual evidence into downloadable audit reports",
    },
    "evaluation_logger": {
        "name": "SatQuery Evaluation Logger",
        "kind": "tool",
        "role": "records privacy-conscious route-level execution outcomes and timings for evaluation",
    },
    "benchmark_proxy_evaluator": {
        "name": "SatQuery Benchmark Proxy Evaluator",
        "kind": "evaluation_tool",
        "role": "computes local normalized exact-match and token-F1 development metrics from reference/prediction pairs",
    },
}


def get_component(
    registry_id,
):
    component = MODEL_REGISTRY.get(
        registry_id
    )

    if component is None:
        raise KeyError(
            f"Unknown SatQuery registry component: {registry_id}"
        )

    return {
        "registry_id": registry_id,
        **component,
    }


def get_components(
    registry_ids,
):
    return [
        get_component(registry_id)
        for registry_id in registry_ids
    ]


def get_registry_snapshot():
    return {
        key: dict(value)
        for key, value
        in MODEL_REGISTRY.items()
    }
