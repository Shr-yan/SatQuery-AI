import re
from datetime import datetime


DATE_FORMATS = [
    (
        r"\b\d{4}-\d{2}-\d{2}\b",
        "%Y-%m-%d",
    ),
    (
        r"\b\d{2}/\d{2}/\d{4}\b",
        "%d/%m/%Y",
    ),
    (
        r"\b\d{2}-\d{2}-\d{4}\b",
        "%d-%m-%Y",
    ),
]


def normalize_date(
    date_text,
    date_format,
):

    try:

        parsed = datetime.strptime(
            date_text,
            date_format,
        )

        return parsed.strftime(
            "%Y-%m-%d"
        )

    except ValueError:

        return None


def extract_all_dates(
    query,
):

    found = []

    for pattern, date_format in DATE_FORMATS:

        for match in re.finditer(
            pattern,
            query,
        ):

            normalized = normalize_date(
                match.group(),
                date_format,
            )

            if normalized:

                found.append(
                    (
                        match.start(),
                        normalized,
                    )
                )

    found.sort(
        key=lambda item:
        item[0]
    )

    return [
        value
        for _, value in found
    ]


def extract_date(
    query,
):

    dates = extract_all_dates(
        query
    )

    if dates:
        return dates[0]

    return None


def extract_date_range(
    query,
):

    dates = extract_all_dates(
        query
    )

    if len(dates) >= 2:

        return (
            dates[0],
            dates[1],
        )

    return (
        None,
        None,
    )


def detect_trend_request(
    query,
):

    query_lower = query.lower()

    trend_terms = [
        "trend",
        "trends",
        "over time",
        "time series",
        "timeseries",
        "progression",
    ]

    date_start, date_end = (
        extract_date_range(
            query
        )
    )

    return (
        date_start is not None
        and date_end is not None
        and any(
            term in query_lower
            for term in trend_terms
        )
    )


def detect_change_request(
    query,
):

    if detect_trend_request(
        query
    ):
        return False

    query_lower = query.lower()

    change_terms = [
        "compare",
        "comparison",
        "change",
        "changes",
        "difference",
        "differences",
        "changed",
        "increase",
        "decrease",
        "between",
    ]

    date_start, date_end = (
        extract_date_range(
            query
        )
    )

    return (
        date_start is not None
        and date_end is not None
        and any(
            term in query_lower
            for term in change_terms
        )
    )


def detect_analysis_type(
    query,
):

    query_lower = query.lower()

    if "ndwi" in query_lower:
        return "ndwi"

    water_terms = [
        "water",
        "water body",
        "water bodies",
        "surface water",
        "water detection",
        "water analysis",
    ]

    if any(
        term in query_lower
        for term in water_terms
    ):
        return "water"

    if "ndbi" in query_lower:
        return "ndbi"

    urban_terms = [
        "built-up",
        "built up",
        "builtup",
        "urban",
        "urban area",
        "urban areas",
        "urbanization",
        "urbanisation",
        "built-up area",
        "built-up areas",
    ]

    if any(
        term in query_lower
        for term in urban_terms
    ):
        return "urban"

    if "ndvi" in query_lower:
        return "ndvi"

    vegetation_terms = [
        "vegetation",
        "crop health",
        "plant health",
        "greenness",
        "crop",
    ]

    if any(
        term in query_lower
        for term in vegetation_terms
    ):
        return "vegetation"

    return "imagery"


def detect_request_type(
    query,
    analysis_type,
    change_analysis=False,
    trend_analysis=False,
):

    if trend_analysis:
        return "trend_analysis"

    if change_analysis:
        return "change_analysis"

    query_lower = query.lower()

    analysis_types = [
        "ndvi",
        "vegetation",
        "ndwi",
        "water",
        "ndbi",
        "urban",
    ]

    if analysis_type in analysis_types:
        return "analysis"

    analysis_words = [
        "analyze",
        "analyse",
        "analysis",
        "detect",
        "identify",
        "assess",
        "measure",
        "calculate",
        "map",
    ]

    if any(
        word in query_lower
        for word in analysis_words
    ):
        return "analysis"

    imagery_words = [
        "show",
        "find",
        "get",
        "retrieve",
        "download",
        "imagery",
        "image",
    ]

    if any(
        word in query_lower
        for word in imagery_words
    ):
        return "imagery"

    return "unknown"


def extract_location(
    query,
):

    cleaned = query.strip()

    pattern = (
        r"\b(?:for|in|near|around)\s+"
        r"([A-Za-z][A-Za-z\s.'-]*?)"
        r"(?=\s+(?:from|on|between|during|using)\b|$)"
    )

    match = re.search(
        pattern,
        cleaned,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    location = (
        match.group(1)
        .strip()
    )

    location = re.sub(
        r"\s+(?:satellite|imagery|image)$",
        "",
        location,
        flags=re.IGNORECASE,
    ).strip()

    if location:
        return location.title()

    return None


def parse_query(
    query,
):

    query = query.strip()

    analysis_type = (
        detect_analysis_type(
            query
        )
    )

    date_start, date_end = (
        extract_date_range(
            query
        )
    )

    trend_analysis = (
        detect_trend_request(
            query
        )
    )

    change_analysis = (
        detect_change_request(
            query
        )
    )

    single_date = extract_date(
        query
    )

    if (
        change_analysis
        or trend_analysis
    ):
        single_date = None

    return {
        "original_query":
        query,

        "location":
        extract_location(
            query
        ),

        "date":
        single_date,

        "date_start":
        date_start,

        "date_end":
        date_end,

        "change_analysis":
        change_analysis,

        "trend_analysis":
        trend_analysis,

        "data_type":
        "sentinel-2",

        "request_type":
        detect_request_type(
            query,
            analysis_type,
            change_analysis=(
                change_analysis
            ),
            trend_analysis=(
                trend_analysis
            ),
        ),

        "analysis_type":
        analysis_type,
    }


if __name__ == "__main__":

    tests = [
        (
            "Analyze vegetation trend in "
            "Varanasi between "
            "2026-01-10 and 2026-04-10"
        ),
        (
            "Compare vegetation in "
            "Varanasi between "
            "2026-02-10 and 2026-03-10"
        ),
        (
            "Show NDWI for Varanasi "
            "on 2026-02-10"
        ),
    ]

    for query in tests:

        print(
            "\nQUERY:"
        )

        print(
            query
        )

        print(
            parse_query(
                query
            )
        )