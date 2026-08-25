from query_parser import parse_query
from query_response import format_response
from geocoder import geocode_location
from bbox import create_bbox


from real_analysis import get_ndvi_statistics
from real_summary import create_real_summary

from analysis_engine import (
    calculate_ndvi_statistics,
    classify_vegetation
)

from data_catalog import (
    find_satellite_data,
    find_data_for_location,
    select_best_scene,
    get_scene_date,
    get_metadata,
    select_real_scene
)

from crop_scene import crop_around_point
from real_crop import crop_raster_to_bbox
from preview import create_preview
from indices import calculate_ndvi
from analysis_summary import create_summary


def process_query(query):

    parsed_query = parse_query(query)
    
    use_real_data = True
    real_scene = None

    if use_real_data:
        real_scene = select_real_scene()
       

    if use_real_data and real_scene is None:

        response = format_response(
            parsed_query
        )


        response += (
            "\n\nReal Sentinel-2 data "
            "is not available."
        )

        return parsed_query, response

    response = format_response(
        parsed_query
    )

    if use_real_data:

        response += (
            "\n\nReal Sentinel-2 scene:"
        )

        response += (
            f"\nScene date: "
            f"{real_scene['date']}"
        )

    location = parsed_query.get(
        "location"
    )

    coordinates = None

    if location:

        coordinates = geocode_location(
            location
        )

    response = format_response(
        parsed_query
    )

    if not coordinates:

        response += (
            "\n\nLocation could not "
            "be geocoded."
        )

        return parsed_query, response

    response += (
        "\n\nLocation coordinates:"
    )

    response += (
        f"\nLatitude: "
        f"{coordinates['latitude']}"
    )

    response += (
        f"\nLongitude: "
        f"{coordinates['longitude']}"
    )

    bbox = create_bbox(
        coordinates["latitude"],
        coordinates["longitude"],
        size_km=10
    )

    response += "\n\nRequested area:"

    response += (
        f"\nMinimum latitude: "
        f"{bbox['min_lat']}"
    )

    response += (
        f"\nMaximum latitude: "
        f"{bbox['max_lat']}"
    )

    response += (
        f"\nMinimum longitude: "
        f"{bbox['min_lon']}"
    )

    response += (
        f"\nMaximum longitude: "
        f"{bbox['max_lon']}"
    )

    if use_real_data:

        response += (
            "\n\nUsing real Sentinel-2 data:"
        )

        response += (
            f"\nScene date: "
            f"{real_scene['date']}"
        )

        response += (
            f"\nRed band: "
            f"{real_scene['b04']}"
        )

        response += (
            f"\nNIR band: "
            f"{real_scene['b08']}"
        )

        files = [
            real_scene["b04"],
            real_scene["b08"]
        ]

    else:

        files = find_satellite_data(
            parsed_query.get("data_type")
        )

        files = find_data_for_location(
            files,
            coordinates["latitude"],
            coordinates["longitude"]
        )

    if not files:

        response += (
            "\n- No satellite scene "
            "covers the requested location."
        )

        return parsed_query, response

    if use_real_data:

        selected_scene = real_scene["b04"]

    else:

        selected_scene = select_best_scene(
            files,
            parsed_query.get("date")
        )

    if use_real_data:

        response += (
            "\n\nSelected real Sentinel-2 scene:"
        )


        response += (
            f"\nRequested date: "
            f"{parsed_query.get('date')}"
        )
        response += (
            f"\nScene date: "
            f"{real_scene['date']}"
        )

        response += (
            f"\nRed band: "
            f"{real_scene['b04']}"
        )

        response += (
            f"\nNIR band: "
            f"{real_scene['b08']}"
        )

    else:

        response += (
            f"\nSelected scene: "
            f"{selected_scene}"
        )

        scene_date = get_scene_date(
            selected_scene
        )

        response += (
            f"\nScene date: "
            f"{scene_date}"
        )

        metadata = get_metadata(
            selected_scene
        )

        response += (
            f"\nCRS: "
            f"{metadata['crs']}"
        )

        response += (
            f"\nSize: "
            f"{metadata['width']} "
            f"x "
            f"{metadata['height']}"
        )

        response += (
            f"\nBands: "
            f"{metadata['bands']}"
        )

        response += (
            f"\nBounds: "
            f"{metadata['bounds']}"
        )

    if use_real_data:

        real_b04_crop = (
            "data/processed/results/"
            "real_B04_query_crop.tif"
        )

        real_b08_crop = (
            "data/processed/results/"
            "real_B08_query_crop.tif"
        )

        crop_raster_to_bbox(
            real_scene["b04"],
            real_b04_crop,
            bbox["min_lat"],
            bbox["min_lon"],
            bbox["max_lat"],
            bbox["max_lon"]
        )

        crop_raster_to_bbox(
            real_scene["b08"],
            real_b08_crop,
            bbox["min_lat"],
            bbox["min_lon"],
            bbox["max_lat"],
            bbox["max_lon"]
        )

        crop_output = real_b04_crop

    else:

        crop_output = (
            "data/processed/results/"
            "query_crop.tif"
        )

        crop_around_point(
            selected_scene,
            crop_output,
            coordinates["latitude"],
            coordinates["longitude"],
            size_km=5
        )

    response += (
        f"\n\nCropped scene: "
        f"{crop_output}"
    )

    preview_output = (
        "data/processed/results/"
        "query_preview.png"
    )

    create_preview(
        crop_output,
        preview_output
    )

    response += (
        f"\nPreview: "
        f"{preview_output}"
    )

    analysis_type = parsed_query.get(
        "analysis_type"
    )

    if analysis_type in [
        "ndvi",
        "vegetation"
    ]:

        if use_real_data:

            real_ndvi_file = (
                "data/processed/results/"
                "real_ndvi_crop.tif"
            )

            stats = get_ndvi_statistics(
                real_ndvi_file
            )

            summary = create_real_summary(
                stats
            )
            response += (
                "\n\nReal NDVI product:"
            )

            response += (
                "\nNDVI raster: "
                "data/processed/results/real_ndvi_crop.tif"
            )
        else:
            ndvi_output = (
                "data/processed/results/"
                "query_ndvi.tif"
            )

            calculate_ndvi(
                crop_output,
                ndvi_output
            )

            summary = create_summary(
                ndvi_output
            )

        response += (
            "\n\nSatellite Analysis:"
        )

        response += (
            f"\nMean NDVI: "
            f"{summary['ndvi_mean']:.4f}"
        )

        response += (
            f"\nMinimum NDVI: "
            f"{summary['ndvi_min']:.4f}"
        )

        response += (
            f"\nMaximum NDVI: "
            f"{summary['ndvi_max']:.4f}"
        )

        response += (
            f"\nVegetation condition: "
            f"{summary['vegetation_condition']}"
        )

        response += "\n\nAnswer:"

        response += (
            f"\nThe requested area near "
            f"{location} has a mean NDVI of "
            f"{summary['ndvi_mean']:.4f}."
        )

        response += (
            f"\nThe estimated vegetation "
            f"condition is "
            f"{summary['vegetation_condition']}."
        )

    return parsed_query, response


if __name__ == "__main__":

    query = (
        #"Show me Sentinel-2 satellite imagery "
        #"for Lucknow from 2026-01-15"

        #"Analyze vegetation using NDVI "
        #"for Lucknow from 2026-01-15"

        #"Show me NDVI for Lucknow "
        #"from 2026-01-15"
        
        "Analyze vegetation health "
        "for Lucknow from 2026-01-15"
    )

    parsed, response = process_query(
        query
    )

    print(response)