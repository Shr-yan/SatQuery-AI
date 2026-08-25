def create_real_result(
    scene_date,
    scene_id,
    cloud_cover,
    stats,
    summary
):

    return {
        "scene_date": scene_date,
        "scene_id": scene_id,
        "cloud_cover": cloud_cover,
        "ndvi_mean": stats["mean"],
        "ndvi_min": stats["min"],
        "ndvi_max": stats["max"],
        "vegetation_condition":
            summary[
                "vegetation_condition"
            ]
    }