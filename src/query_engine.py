from live_analysis import analyze_location
from query_parser import parse_query


def build_analysis_response(
    parsed,
    result,
):

    scene = result["scene"]
    ndvi = result["ndvi"]
    model = result["model"]
    coordinates = result["coordinates"]

    lines = [
        "SatQuery AI Result",
        "==================",
        "",
        f"Location: {result['location']}",
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
            "Cloud cover: "
            f"{scene['cloud_cover']:.3f}%"
        ),
        (
            "Candidate scenes: "
            f"{result['candidate_scene_count']}"
        ),
        (
            "Difference from requested date: "
            f"{result['date_difference_days']} days"
            if result["date_difference_days"]
            is not None
            else
            "Requested date: latest available search"
        ),
        "",
        "Vegetation Analysis",
        "-------------------",
        f"Mean NDVI: {ndvi['mean']:.4f}",
        f"Minimum NDVI: {ndvi['min']:.4f}",
        f"Maximum NDVI: {ndvi['max']:.4f}",
        f"NDVI standard deviation: {ndvi['std']:.4f}",
        (
            "Vegetation condition: "
            f"{ndvi['condition']}"
        ),
        "",
        "ML Verification",
        "---------------",
        (
            "CNN predicted mean NDVI: "
            f"{model['prediction']:.4f}"
        ),
        (
            "Difference from calculated NDVI: "
            f"{model['absolute_difference']:.4f}"
        ),
        (
            "Model/reference agreement: "
            f"{model['agreement']}"
        ),
        "",
        "Answer",
        "------",
        (
            f"The Sentinel-2 observation selected "
            f"for {result['location']} has a mean "
            f"NDVI of {ndvi['mean']:.4f}. "
            f"This is heuristically classified as "
            f"{ndvi['condition'].lower()}."
        ),
    ]

    return "\n".join(lines)


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
            "SatQuery could not determine "
            "the requested location."
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
            "SatQuery understood the request, "
            "but this Phase 4 pipeline currently "
            "supports NDVI/vegetation analysis."
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
            "SatQuery analysis failed: "
            f"{error}"
        )

    response = build_analysis_response(
        parsed,
        result,
    )

    return parsed, response


if __name__ == "__main__":

    query = (
        "Analyze vegetation health "
        "for Lucknow from 2026-01-15"
    )

    parsed, response = process_query(
        query
    )

    print(response)