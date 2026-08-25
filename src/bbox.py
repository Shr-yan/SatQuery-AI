def create_bbox(
    latitude,
    longitude,
    size_km=10
):

    lat_offset = size_km / 111.0

    lon_offset = (
        size_km /
        (111.0 *
         max(
             0.1,
             abs(
                 __import__(
                     "math"
                 ).cos(
                     __import__(
                         "math"
                     ).radians(latitude)
                 )
             )
         ))
    )

    return {
        "min_lat": latitude - lat_offset,
        "max_lat": latitude + lat_offset,
        "min_lon": longitude - lon_offset,
        "max_lon": longitude + lon_offset
    }


if __name__ == "__main__":

    bbox = create_bbox(
        26.8467,
        80.9462,
        10
    )

    print(bbox)