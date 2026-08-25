def vegetation_condition(
    mean_ndvi
):

    if mean_ndvi < 0:
        return "Very low vegetation"

    if mean_ndvi < 0.2:
        return "Low vegetation"

    if mean_ndvi < 0.4:
        return "Moderate vegetation"

    if mean_ndvi < 0.6:
        return "Healthy vegetation"

    return "Very healthy vegetation"


def create_real_summary(
    stats
):

    mean_ndvi = stats["mean"]

    return {
        "ndvi_mean": mean_ndvi,
        "ndvi_min": stats["min"],
        "ndvi_max": stats["max"],
        "vegetation_condition":
            vegetation_condition(
                mean_ndvi
            )
    }