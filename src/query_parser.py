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


def detect_change_request(
    query,
):

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
        "trend",
        "between",
    ]

    date_start, date_end = (
        extract_date_range(
            query
        )
    )

    has_two_dates = (
        date_start is not None
        and date_end is not None
    )

    has_change_term = any(
        term in query_lower
        for term in change_terms
    )

    return (
        has_two_dates
        and has_change_term
    )


def detect_analysis_type(
    query,
):

    query_lower = query.lower()

    # -----------------------------
    # Water / NDWI
    # -----------------------------

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

    # -----------------------------
    # Built-up / NDBI
    # -----------------------------

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

    # -----------------------------
    # Vegetation / NDVI
    # -----------------------------

    if "ndvi" in query_lower:
        return "ndvi"

    vegetation_terms = [
        "vegetation",
        "crop health",
        "plant health",
        "greenness",
    ]

    if any(
        term in query_lower
        for term in vegetation_terms
    ):
        return "vegetation"

    # -----------------------------
    # Default
    # -----------------------------

    return "imagery"


def detect_request_type(
    query,
    analysis_type,
    change_analysis=False,
):

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

    patterns = [
        (
            r"\b(?:for|in|near|around)\s+"
            r"([A-Za-z][A-Za-z\s.'-]*?)"
            r"(?=\s+(?:from|on|between|during|using)\b|$)"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            cleaned,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

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

    change_analysis = (
        detect_change_request(
            query
        )
    )

    single_date = (
        extract_date(
            query
        )
    )

    if change_analysis:
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

        "data_type":
        "sentinel-2",

        "request_type":
        detect_request_type(
            query,
            analysis_type,
            change_analysis=(
                change_analysis
            ),
        ),

        "analysis_type":
        analysis_type,
    }


if __name__ == "__main__":

    tests = [
        (
            "Analyze vegetation health "
            "for Varanasi on 2026-02-10"
        ),
        (
            "Show NDWI for Varanasi "
            "on 2026-02-10"
        ),
        (
            "Show NDBI for New Delhi "
            "on 2026-03-06"
        ),
        (
            "Compare vegetation in "
            "Varanasi between "
            "2026-02-10 and "
            "2026-03-10"
        ),
        (
            "Compare NDWI for "
            "Varanasi between "
            "2026-02-10 and "
            "2026-03-10"
        ),
        (
            "Compare NDBI for "
            "New Delhi between "
            "2025-12-01 and "
            "2026-03-06"
        ),
        (
            "Show Sentinel-2 imagery "
            "for Varanasi on 2026-02-10"
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
            "PARSED:"
        )

        print(
            parse_query(
                query
            )
        )