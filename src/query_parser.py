import re
from datetime import datetime


# KNOWN_LOCATIONS = [
#     "lucknow",
#     "delhi",
#     "mumbai",
#     "kolkata",
#     "chennai",
#     "bengaluru",
#     "bangalore",
#     "hyderabad",
#     "jaipur",
#     "kanpur",
#     "agra",
#     "bhopal",
#     "pune",
#     "ahmedabad",
# ]


def detect_analysis_type(query):

    query_lower = query.lower()

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

    return "imagery"


def detect_request_type(
    query,
    analysis_type,
):

    query_lower = query.lower()

    if analysis_type in [
        "ndvi",
        "vegetation",
    ]:
        return "analysis"

    analysis_words = [
        "analyze",
        "analyse",
        "analysis",
        "detect",
        "identify",
        "assess",
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


def extract_date(query):

    formats = [
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

    for pattern, date_format in formats:

        match = re.search(
            pattern,
            query,
        )

        if not match:
            continue

        try:

            parsed = datetime.strptime(
                match.group(),
                date_format,
            )

            return parsed.strftime(
                "%Y-%m-%d"
            )

        except ValueError:
            continue

    return None


def extract_location(query):

    cleaned = query.strip()

    patterns = [
        r"\b(?:for|in|near|around)\s+"
        r"([A-Za-z][A-Za-z\s.'-]*?)"
        r"(?=\s+(?:from|on|between|during|using)\b|$)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            cleaned,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        location = match.group(1).strip()

        # Remove common trailing words that
        # describe the request rather than place.
        location = re.sub(
            r"\s+(?:satellite|imagery|image)$",
            "",
            location,
            flags=re.IGNORECASE,
        ).strip()

        if location:
            return location.title()

    return None


def parse_query(query):

    query = query.strip()

    analysis_type = detect_analysis_type(
        query
    )

    return {
        "original_query": query,

        "location": extract_location(
            query
        ),

        "date": extract_date(
            query
        ),

        "data_type": "sentinel-2",

        "request_type": (
            detect_request_type(
                query,
                analysis_type,
            )
        ),

        "analysis_type": analysis_type,
    }


if __name__ == "__main__":

    tests = [
        (
            "Analyze vegetation health "
            "for Lucknow from 2026-01-15"
        ),
        (
            "Show NDVI for Jaipur "
            "on 04/12/2025"
        ),
        (
            "Assess crop health in Bhopal "
            "on 09-02-2026"
        ),
        (
            "Analyze vegetation health "
            "for Varanasi on 2026-02-10"
        ),
        (
            "Show NDVI around Nagpur "
            "on 2026-01-20"
        ),
        (
            "Analyze vegetation in "
            "New Delhi on 2026-03-06"
        ),
    ]

    for query in tests:

        print("\nQUERY:")
        print(query)

        print("PARSED:")
        print(
            parse_query(query)
        )