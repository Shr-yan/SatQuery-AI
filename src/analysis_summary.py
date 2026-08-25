from ndvi_stats import get_ndvi_stats


def create_summary(
    ndvi_file
):

    stats = get_ndvi_stats(
        ndvi_file
    )

    if stats["mean"] < 0:
        condition = "Mostly non-vegetated"

    elif stats["mean"] < 0.3:
        condition = "Low vegetation"

    elif stats["mean"] < 0.6:
        condition = "Moderate vegetation"

    else:
        condition = "High vegetation"

    return {
        "ndvi_mean": stats["mean"],
        "ndvi_min": stats["min"],
        "ndvi_max": stats["max"],
        "vegetation_condition": condition
    }


if __name__ == "__main__":

    summary = create_summary(
        "data/processed/results/query_ndvi.tif"
    )

    for key, value in summary.items():

        print(
            f"{key}: {value}"
        )