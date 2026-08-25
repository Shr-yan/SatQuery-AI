from pyproj import Transformer


def latlon_to_utm(
    latitude,
    longitude,
    utm_zone=44
):

    transformer = Transformer.from_crs(
        "EPSG:4326",
        f"EPSG:{32600 + utm_zone}",
        always_xy=True
    )

    x, y = transformer.transform(
        longitude,
        latitude
    )

    return x, y


def utm_to_latlon(
    x,
    y,
    utm_zone=44
):

    transformer = Transformer.from_crs(
        f"EPSG:{32600 + utm_zone}",
        "EPSG:4326",
        always_xy=True
    )

    longitude, latitude = transformer.transform(
        x,
        y
    )

    return latitude, longitude


if __name__ == "__main__":

    latitude = 26.8467
    longitude = 80.9462

    x, y = latlon_to_utm(
        latitude,
        longitude
    )

    print("UTM X:", x)
    print("UTM Y:", y)

    lat, lon = utm_to_latlon(
        x,
        y
    )

    print("Latitude:", lat)
    print("Longitude:", lon)