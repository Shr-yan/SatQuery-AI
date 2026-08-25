import re
from datetime import datetime


def parse_query(query):

    query = query.strip()
    data_type = "sentinel-2"

    analysis_type = detect_analysis_type(
        query
    )
    if analysis_type in [
        "ndvi",
        "vegetation"
    ]:
        data_type = "sentinel-2"
        
    result = {
        "original_query": query,
        "location": None,
        "date": None,
        "data_type": data_type,
        "request_type": None,
        "analysis_type": analysis_type
    }

    # -------------------------
    # Detect request type
    # -------------------------

    query_lower = query.lower()

    if any(word in query_lower for word in [
        "show",
        "find",
        "get",
        "retrieve",
        "download"
    ]):
        result["request_type"] = "imagery"

    elif any(word in query_lower for word in [
        "analyze",
        "analysis",
        "detect",
        "identify"
    ]):
        result["request_type"] = "analysis"

    else:
        result["request_type"] = "unknown"

    # -------------------------
    # Detect data type
    # -------------------------

    if "sentinel-2" in query_lower or "sentinel 2" in query_lower:
        result["data_type"] = "sentinel-2"

    elif "sentinel-1" in query_lower or "sentinel 1" in query_lower:
        result["data_type"] = "sentinel-1"

    elif "landsat" in query_lower:
        result["data_type"] = "landsat"

    elif "satellite" in query_lower:
        result["data_type"] = "satellite"

    # -------------------------
    # Detect date
    # -------------------------

    date_patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{2}/\d{2}/\d{4}\b",
        r"\b\d{2}-\d{2}-\d{4}\b"
    ]

    for pattern in date_patterns:

        match = re.search(pattern, query)

        if match:
            date_text = match.group()

            try:

                datetime.strptime(
                    date_text,
                    "%Y-%m-%d"
                )

                result["date"] = date_text

            except ValueError:

                result["date"] = None

            break

    # -------------------------
    # Simple location detection
    # -------------------------

    known_locations = [
        "lucknow",
        "delhi",
        "mumbai",
        "kolkata",
        "chennai",
        "bengaluru",
        "hyderabad",
        "jaipur",
        "kanpur",
        "agra"
    ]

    for location in known_locations:

        if location in query_lower:
            result["location"] = location.title()
            break

    return result
def detect_analysis_type(query):

    query = query.lower()

    if "ndvi" in query:
        return "ndvi"

    if (
        "vegetation" in query
        or "vegetation health" in query
    ):
        return "vegetation"

    if "imagery" in query:
        return "imagery"

    return "imagery"

if __name__ == "__main__":

    test_query = (
        "Show me Sentinel-2 satellite imagery "
        "for Lucknow from 2026-01-15"
        #"Show me NDVI for Lucknow from 2026-01-15"
    )

    result = parse_query(test_query)

    print("Query:")
    print(test_query)

    print("\nParsed result:")

    for key, value in result.items():
        print(f"{key}: {value}")