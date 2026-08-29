from bbox import create_bbox
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


LOCATION = "Lucknow"
TARGET_DATE = "2026-01-15"


coordinates = geocode_location(
    LOCATION
)

if not coordinates:
    raise RuntimeError(
        "Could not geocode location."
    )

bbox_dict = create_bbox(
    coordinates["latitude"],
    coordinates["longitude"],
    size_km=5,
)

stac_bbox = [
    bbox_dict["min_lon"],
    bbox_dict["min_lat"],
    bbox_dict["max_lon"],
    bbox_dict["max_lat"],
]

print(
    "Coordinates:",
    coordinates
)

print(
    "Search bbox:",
    stac_bbox
)

scenes = search_sentinel2(
    bbox=stac_bbox,
    target_date=TARGET_DATE,
)

print(
    "Candidate scenes:",
    len(scenes)
)

scene = select_best_scene(
    scenes,
    target_date=TARGET_DATE,
)

if scene is None:
    raise RuntimeError(
        "No suitable Sentinel-2 scene found."
    )

scene_info = get_scene_info(
    scene
)

print(
    "Selected scene:",
    scene_info
)

band_urls = get_signed_band_urls(
    scene
)

chip = build_model_chip(
    band_urls,
    stac_bbox,
)

print(
    "Chip shape:",
    chip.shape
)

print(
    "Chip dtype:",
    chip.dtype
)

print(
    "Chip range:",
    float(chip.min()),
    float(chip.max())
)

scientific = summarize_chip_ndvi(
    chip
)

print(
    "Calculated mean NDVI:",
    scientific["mean"]
)

predictor = SatQueryModel()

prediction = predictor.predict_chip(
    chip
)

print(
    "Model predicted mean NDVI:",
    prediction
)

difference = abs(
    prediction
    - scientific["mean"]
)

print(
    "Absolute difference:",
    difference
)