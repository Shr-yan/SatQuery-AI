from geopy.geocoders import Nominatim


geolocator = Nominatim(
    user_agent="satquery-ai"
)


def geocode_location(location):

    result = geolocator.geocode(location)

    if result is None:
        return None

    return {
        "name": result.address,
        "latitude": result.latitude,
        "longitude": result.longitude
    }


if __name__ == "__main__":

    location = "Lucknow, India"

    result = geocode_location(location)

    print(result)