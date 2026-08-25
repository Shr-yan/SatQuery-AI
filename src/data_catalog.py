from pathlib import Path
import rasterio
from spatial import location_in_raster

OPTICAL_DIR = Path(
    "data/raw/optical"
)

def is_real_sentinel_data(file):
    return "sentinel2" in str(file).lower()

def select_real_scene():

    from pathlib import Path

    scene_dir = Path(
        "data/raw/sentinel2/20260117"
    )

    if not scene_dir.exists():
        return None

    b04 = scene_dir / "B04_20260117.tif"
    b08 = scene_dir / "B08_20260117.tif"

    if b04.exists() and b08.exists():
        return {
            "date": "2026-01-17",
            "b04": str(b04),
            "b08": str(b08)
        }

    return None

def find_data_for_location(
    files,
    latitude,
    longitude
):

    matching_files = []

    for file in files:

        if location_in_raster(
            latitude,
            longitude,
            file
        ):

            matching_files.append(file)

    return matching_files
def find_satellite_data(
    data_type=None
):

    files = []

    if data_type in [
        "sentinel-2",
        "satellite",
        None
    ]:

        files.extend(
            OPTICAL_DIR.glob("*.tif")
        )

    return files

def select_best_scene(
    files,
    requested_date=None
):

    if not files:
        return None

    if requested_date:

        for file in files:

            scene_date = get_scene_date(
                file
            )

            if scene_date == requested_date:
                return file

    return files[0]
def get_scene_date(file):

    name = str(file)

    if "20260117" in name:
        return "2026-01-17"

    return None
def get_metadata(file):

    with rasterio.open(file) as src:

        return {
            "file": str(file),
            "crs": str(src.crs),
            "width": src.width,
            "height": src.height,
            "bands": src.count,
            "bounds": str(src.bounds),
            "resolution": src.res
        }


if __name__ == "__main__":

    files = find_satellite_data(
        "sentinel-2"
    )

    latitude = 26.8381
    longitude = 80.9346001

    matching = find_data_for_location(
        files,
        latitude,
        longitude
    )

    print(
        "Matching files:"
    )

    for file in matching:
        print(
            "Scene date:",
            get_scene_date(file)
        )
        print(file)