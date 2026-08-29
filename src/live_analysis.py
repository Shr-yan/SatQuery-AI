from bbox import create_bbox
from datetime import datetime
from geocoder import geocode_location
from live_chip import (
    build_model_chip,
    summarize_chip_ndvi,
)
from model_inference import SatQueryModel
from real_data import (
    get_scene_info,
    get_signed_band_urls,
    search_sentinel2,
    select_best_scene,
)

def classify_vegetation(
    mean_ndvi
):

    if mean_ndvi < 0:
        return "Non-vegetated or water-dominated"

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

def analyze_location(
    location,
    target_date=None,
    size_km=5,
    predictor=None,
):

    # -------------------------
    # 1. Geocode location
    # -------------------------

    coordinates = geocode_location(
        location
    )

    if not coordinates:
        raise ValueError(
            f"Could not geocode location: "
            f"{location}"
        )

    # -------------------------
    # 2. Build geographic bbox
    # -------------------------

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

    # -------------------------
    # 3. Search Sentinel-2
    # -------------------------

    scenes = search_sentinel2(
        bbox=stac_bbox,
        target_date=target_date,
    )

    scene = select_best_scene(
        scenes,
        target_date=target_date,
    )

    if scene is None:
        raise RuntimeError(
            "No suitable Sentinel-2 "
            "scene found."
        )

    scene_info = get_scene_info(
        scene
    )

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
            (selected - requested).days
        )

    # -------------------------
    # 4. Read remote bands
    # -------------------------

    band_urls = get_signed_band_urls(
        scene
    )

    chip = build_model_chip(
        band_urls,
        stac_bbox,
    )

    # -------------------------
    # 5. Scientific NDVI
    # -------------------------

    ndvi_stats = summarize_chip_ndvi(
        chip
    )

    # -------------------------
    # 6. ML inference
    # -------------------------

    if predictor is None:

        predictor = SatQueryModel()

    prediction = predictor.predict_chip(
        chip
    )

    difference = abs(
        prediction
        - ndvi_stats["mean"]
    )

    # -------------------------
    # 7. Structured result
    # -------------------------

    return {
        "location": location,
        "coordinates": coordinates,
        "bbox": bbox_dict,

        "requested_date": target_date,

        "scene": scene_info,

        "candidate_scene_count": len(
            scenes
        ),

        "chip_shape": list(
            chip.shape
        ),

        "ndvi": {
            "mean": ndvi_stats["mean"],
            "min": ndvi_stats["min"],
            "max": ndvi_stats["max"],
            "std": ndvi_stats["std"],
            "condition": classify_vegetation(
                ndvi_stats["mean"]
            ),
        },

        "model": {
            "prediction": prediction,
            "absolute_difference": (
                difference
            ),
            "agreement": (
                classify_model_agreement(
                    difference
                )
            ),
        },
        "date_difference_days": (
            date_difference_days
        ),
    }

if __name__ == "__main__":

    result = analyze_location(
        location="Lucknow",
        target_date="2026-01-15",
    )

    print("\nSATQUERY LIVE ANALYSIS")
    print("----------------------")

    print(
        "Location:",
        result["location"]
    )

    print(
        "Coordinates:",
        result["coordinates"]
    )

    print(
        "Requested date:",
        result["requested_date"]
    )

    print(
        "Scene:",
        result["scene"]
    )

    print(
        "Candidates:",
        result[
            "candidate_scene_count"
        ]
    )

    print(
        "NDVI mean:",
        result["ndvi"]["mean"]
    )

    print(
        "Vegetation:",
        result["ndvi"]["condition"]
    )

    print(
        "Model prediction:",
        result["model"]["prediction"]
    )

    print(
        "Difference:",
        result[
            "model"
        ]["absolute_difference"]
    )