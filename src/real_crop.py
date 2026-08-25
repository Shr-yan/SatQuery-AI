import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom


def crop_raster_to_bbox(
    input_file,
    output_file,
    min_lat,
    min_lon,
    max_lat,
    max_lon
):

    with rasterio.open(input_file) as src:

        bbox = {
            "type": "Polygon",
            "coordinates": [[
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat]
            ]]
        }

        bbox_projected = transform_geom(
            "EPSG:4326",
            src.crs,
            bbox
        )

        cropped, transform = mask(
            src,
            [bbox_projected],
            crop=True
        )

        profile = src.profile.copy()

        profile.update(
            height=cropped.shape[1],
            width=cropped.shape[2],
            transform=transform
        )

        with rasterio.open(
            output_file,
            "w",
            **profile
        ) as dst:

            dst.write(cropped)


if __name__ == "__main__":

    min_lat = 26.7480099
    min_lon = 80.8336345
    max_lat = 26.9281900
    max_lon = 81.0355656

    crop_raster_to_bbox(
        "data/raw/sentinel2/20260117/B04_20260117.tif",
        "data/processed/results/real_B04_crop.tif",
        min_lat,
        min_lon,
        max_lat,
        max_lon
    )

    crop_raster_to_bbox(
        "data/raw/sentinel2/20260117/B08_20260117.tif",
        "data/processed/results/real_B08_crop.tif",
        min_lat,
        min_lon,
        max_lat,
        max_lon
    )

    print(
        "B04 and B08 crops created."
    )