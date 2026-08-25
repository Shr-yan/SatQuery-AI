def format_response(parsed_query):

    location = parsed_query.get("location")
    date = parsed_query.get("date")
    data_type = parsed_query.get("data_type")
    request_type = parsed_query.get("request_type")

    response = []

    response.append("SatQuery AI Result")
    response.append("------------------")

    response.append(
        f"Request type: {request_type}"
    )

    response.append(
        f"Location: {location or 'Not specified'}"
    )

    response.append(
        f"Date: {date or 'Not specified'}"
    )

    response.append(
        f"Data source: {data_type or 'Not specified'}"
    )

    return "\n".join(response)


if __name__ == "__main__":

    sample = {
        "location": "Lucknow",
        "date": "2026-01-15",
        "data_type": "sentinel-2",
        "request_type": "imagery"
    }

    print(format_response(sample))