"""
SatQuery AI - Chunk 11
Download one REAL, near-date Sentinel-2 optical + Sentinel-1 RTC SAR pair
from Microsoft Planetary Computer and force both rasters onto the same grid.

Output is intended for SatQuery's existing:
Analyze My Imagery -> Optical + SAR Pair workflow.

The two outputs are real satellite observations. The script does not synthesize
SAR values. Sentinel-1 VV is radiometrically terrain-corrected linear intensity.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import planetary_computer
import rasterio
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import transform_bounds
from rasterio.vrt import WarpedVRT


STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
S2_COLLECTION = "sentinel-2-l2a"
S1_COLLECTION = "sentinel-1-rtc"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Download and co-register one real Sentinel-2 optical + "
            "Sentinel-1 RTC SAR pair for SatQuery AI."
        )
    )
    parser.add_argument("--location", default="Varanasi, India")
    parser.add_argument("--lat", type=float, default=25.3176)
    parser.add_argument("--lon", type=float, default=82.9739)
    parser.add_argument("--start", default="2026-01-15")
    parser.add_argument("--end", default="2026-04-15")
    parser.add_argument(
        "--size-km",
        type=float,
        default=4.0,
        help="Approximate square AOI side length in kilometres.",
    )
    parser.add_argument(
        "--max-cloud",
        type=float,
        default=30.0,
        help="Maximum Sentinel-2 scene cloud-cover metadata percentage.",
    )
    parser.add_argument(
        "--max-gap-days",
        type=int,
        default=18,
        help="Maximum allowed acquisition-date gap between S1 and S2.",
    )
    parser.add_argument(
        "--output",
        default="data/demo/real_optical_sar",
        help="Output directory.",
    )
    return parser.parse_args()


def make_bbox(lat: float, lon: float, size_km: float):
    half_km = size_km / 2.0
    dlat = half_km / 111.32
    lon_scale = max(0.2, math.cos(math.radians(lat)))
    dlon = half_km / (111.32 * lon_scale)
    return [lon - dlon, lat - dlat, lon + dlon, lat + dlat]


def item_datetime(item):
    dt = item.datetime
    if dt is None:
        raw = item.properties.get("datetime")
        if not raw:
            raise ValueError(f"Item {item.id} has no acquisition datetime")
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def choose_real_pair(s2_items, s1_items, max_gap_days: int):
    s2_candidates = []
    for item in s2_items:
        if not all(key in item.assets for key in ("B02", "B03", "B04")):
            continue
        cloud = item.properties.get("eo:cloud_cover")
        try:
            cloud = float(cloud) if cloud is not None else 100.0
        except (TypeError, ValueError):
            cloud = 100.0
        s2_candidates.append((item, cloud, item_datetime(item)))

    s1_candidates = []
    for item in s1_items:
        if "vv" not in item.assets:
            continue
        s1_candidates.append((item, item_datetime(item)))

    if not s2_candidates:
        raise RuntimeError("No usable Sentinel-2 RGB candidates were found.")
    if not s1_candidates:
        raise RuntimeError("No Sentinel-1 RTC candidates with VV were found.")

    ranked = []
    for s2, cloud, s2_dt in s2_candidates:
        for s1, s1_dt in s1_candidates:
            gap_days = abs((s1_dt - s2_dt).total_seconds()) / 86400.0
            if gap_days <= max_gap_days:
                # Strongly prioritize temporal closeness, then S2 cloud cover.
                score = (gap_days * 4.0) + cloud
                ranked.append((score, gap_days, cloud, s2, s1, s2_dt, s1_dt))

    if not ranked:
        raise RuntimeError(
            "No Sentinel-1/Sentinel-2 pair was found within the requested "
            f"{max_gap_days}-day gap. Increase --max-gap-days or date range."
        )

    ranked.sort(key=lambda row: (row[0], row[1], row[2]))
    return ranked


def aligned_grid_from_s2(s2_item, bbox):
    """Build a 10 m-ish target grid from the Sentinel-2 B04 source CRS."""
    with rasterio.open(s2_item.assets["B04"].href) as src:
        target_crs = src.crs
        if target_crs is None:
            raise RuntimeError("Selected Sentinel-2 asset has no CRS.")

        resolution = abs(float(src.transform.a))
        if not math.isfinite(resolution) or resolution <= 0:
            resolution = 10.0

        left, bottom, right, top = transform_bounds(
            "EPSG:4326",
            target_crs,
            *bbox,
            densify_pts=21,
        )

        # Snap the AOI outward to the target pixel grid.
        left = math.floor(left / resolution) * resolution
        bottom = math.floor(bottom / resolution) * resolution
        right = math.ceil(right / resolution) * resolution
        top = math.ceil(top / resolution) * resolution

        width = int(round((right - left) / resolution))
        height = int(round((top - bottom) / resolution))

        if width < 32 or height < 32:
            raise RuntimeError("Computed AOI grid is unexpectedly small.")
        if width * height > 4_000_000:
            raise RuntimeError(
                "Computed AOI is too large for this demo. Reduce --size-km."
            )

        transform = from_origin(left, top, resolution, resolution)
        return target_crs, transform, width, height, resolution


def read_to_grid(asset_href, target_crs, transform, width, height, resampling, out_dtype):
    with rasterio.open(asset_href) as src:
        src_nodata = src.nodata
        vrt_nodata = 0 if np.issubdtype(np.dtype(out_dtype), np.integer) else -9999.0

        with WarpedVRT(
            src,
            crs=target_crs,
            transform=transform,
            width=width,
            height=height,
            resampling=resampling,
            src_nodata=src_nodata,
            nodata=vrt_nodata,
        ) as vrt:
            data = vrt.read(1, out_dtype=out_dtype)

    return data, vrt_nodata


def valid_fraction(array, nodata):
    mask = np.isfinite(array)
    if nodata is not None:
        mask &= array != nodata
    return float(mask.mean()) if mask.size else 0.0


def write_optical(path, arrays, crs, transform, s2_item, s2_dt):
    stack = np.stack(arrays, axis=0).astype(np.uint16, copy=False)
    profile = {
        "driver": "GTiff",
        "height": stack.shape[1],
        "width": stack.shape[2],
        "count": 3,
        "dtype": "uint16",
        "crs": crs,
        "transform": transform,
        "compress": "deflate",
        "predictor": 2,
        "nodata": 0,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(stack)
        dst.set_band_description(1, "Red - Sentinel-2 B04")
        dst.set_band_description(2, "Green - Sentinel-2 B03")
        dst.set_band_description(3, "Blue - Sentinel-2 B02")
        dst.update_tags(
            satquery_role="optical",
            sensor="Sentinel-2 L2A",
            stac_collection=S2_COLLECTION,
            scene_id=s2_item.id,
            acquisition_datetime=s2_dt.isoformat(),
            displayed_bands="B04,B03,B02",
            real_satellite_data="true",
        )


def write_sar(path, vv, crs, transform, s1_item, s1_dt, nodata):
    profile = {
        "driver": "GTiff",
        "height": vv.shape[0],
        "width": vv.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "compress": "deflate",
        "predictor": 3,
        "nodata": float(nodata),
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(vv.astype(np.float32, copy=False), 1)
        dst.set_band_description(1, "Sentinel-1 RTC VV linear intensity")
        dst.update_tags(
            satquery_role="sar",
            sensor="Sentinel-1 RTC",
            stac_collection=S1_COLLECTION,
            scene_id=s1_item.id,
            acquisition_datetime=s1_dt.isoformat(),
            polarization="VV",
            sar_pixel_content="linear intensity",
            real_satellite_data="true",
        )


def try_materialize_pair(pair_row, bbox, output_dir):
    _, gap_days, cloud, s2, s1, s2_dt, s1_dt = pair_row

    target_crs, transform, width, height, resolution = aligned_grid_from_s2(
        s2,
        bbox,
    )

    red, optical_nodata = read_to_grid(
        s2.assets["B04"].href,
        target_crs,
        transform,
        width,
        height,
        Resampling.bilinear,
        "uint16",
    )
    green, _ = read_to_grid(
        s2.assets["B03"].href,
        target_crs,
        transform,
        width,
        height,
        Resampling.bilinear,
        "uint16",
    )
    blue, _ = read_to_grid(
        s2.assets["B02"].href,
        target_crs,
        transform,
        width,
        height,
        Resampling.bilinear,
        "uint16",
    )
    vv, sar_nodata = read_to_grid(
        s1.assets["vv"].href,
        target_crs,
        transform,
        width,
        height,
        Resampling.bilinear,
        "float32",
    )

    optical_valid = min(
        valid_fraction(red, optical_nodata),
        valid_fraction(green, optical_nodata),
        valid_fraction(blue, optical_nodata),
    )
    sar_valid = valid_fraction(vv, sar_nodata)

    if optical_valid < 0.70:
        raise RuntimeError(
            f"Selected optical scene has only {optical_valid:.1%} valid AOI coverage."
        )
    if sar_valid < 0.70:
        raise RuntimeError(
            f"Selected SAR scene has only {sar_valid:.1%} valid AOI coverage."
        )

    optical_path = output_dir / "varanasi_real_sentinel2_optical.tif"
    sar_path = output_dir / "varanasi_real_sentinel1_vv.tif"

    write_optical(optical_path, [red, green, blue], target_crs, transform, s2, s2_dt)
    write_sar(sar_path, vv, target_crs, transform, s1, s1_dt, sar_nodata)

    # Re-open both to prove exact co-registration after writing.
    with rasterio.open(optical_path) as opt, rasterio.open(sar_path) as sar:
        exact_grid_match = (
            opt.crs == sar.crs
            and opt.transform == sar.transform
            and opt.width == sar.width
            and opt.height == sar.height
        )

    manifest = {
        "dataset_role": "real cross-modal SatQuery demo pair",
        "real_satellite_data": True,
        "synthetic": False,
        "location": None,
        "bbox_wgs84": bbox,
        "optical": {
            "sensor": "Sentinel-2 L2A",
            "collection": S2_COLLECTION,
            "scene_id": s2.id,
            "acquisition_datetime": s2_dt.isoformat(),
            "scene_cloud_cover_percent": cloud,
            "bands": ["B04", "B03", "B02"],
            "file": optical_path.name,
            "valid_aoi_fraction": optical_valid,
        },
        "sar": {
            "sensor": "Sentinel-1 RTC",
            "collection": S1_COLLECTION,
            "scene_id": s1.id,
            "acquisition_datetime": s1_dt.isoformat(),
            "polarization": "VV",
            "pixel_content": "linear intensity",
            "file": sar_path.name,
            "valid_aoi_fraction": sar_valid,
        },
        "temporal_gap_days": gap_days,
        "co_registration": {
            "exact_output_grid_match": exact_grid_match,
            "crs": str(target_crs),
            "width": width,
            "height": height,
            "pixel_size": [resolution, resolution],
        },
        "interpretation_note": (
            "The pair is spatially co-registered by resampling Sentinel-1 RTC onto "
            "the Sentinel-2 analysis grid. Acquisition times can differ, so treat "
            "cross-modal evidence as near-date complementary observations rather "
            "than perfectly simultaneous measurements."
        ),
    }

    return optical_path, sar_path, manifest


def main():
    args = parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    bbox = make_bbox(args.lat, args.lon, args.size_km)
    time_range = f"{args.start}/{args.end}"

    print("Connecting to Microsoft Planetary Computer...")
    catalog = Client.open(
        STAC_URL,
        modifier=planetary_computer.sign_inplace,
    )

    print("Searching real Sentinel-2 L2A scenes...")
    s2_items = list(
        catalog.search(
            collections=[S2_COLLECTION],
            bbox=bbox,
            datetime=time_range,
            query={"eo:cloud_cover": {"lt": args.max_cloud}},
            max_items=80,
        ).items()
    )

    print("Searching real Sentinel-1 RTC scenes...")
    s1_items = list(
        catalog.search(
            collections=[S1_COLLECTION],
            bbox=bbox,
            datetime=time_range,
            max_items=120,
        ).items()
    )

    print(f"Sentinel-2 candidates: {len(s2_items)}")
    print(f"Sentinel-1 candidates: {len(s1_items)}")

    ranked_pairs = choose_real_pair(s2_items, s1_items, args.max_gap_days)
    print(f"Near-date candidate pairs: {len(ranked_pairs)}")

    last_error = None
    result = None
    for rank, pair in enumerate(ranked_pairs[:12], start=1):
        _, gap_days, cloud, s2, s1, s2_dt, s1_dt = pair
        print(
            f"Trying pair {rank}: S2 {s2_dt.date()} cloud={cloud:.2f}% | "
            f"S1 {s1_dt.date()} | gap={gap_days:.2f} days"
        )
        try:
            result = try_materialize_pair(pair, bbox, output_dir)
            break
        except Exception as exc:
            last_error = exc
            print(f"  rejected: {exc}")

    if result is None:
        raise RuntimeError(
            "Could not materialize a well-covered real pair. Last error: "
            f"{last_error}"
        )

    optical_path, sar_path, manifest = result
    manifest["location"] = args.location
    manifest["center"] = {"latitude": args.lat, "longitude": args.lon}
    manifest["requested_date_range"] = {"start": args.start, "end": args.end}

    manifest_path = output_dir / "real_optical_sar_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\nREAL OPTICAL + SAR PAIR READY")
    print("--------------------------------")
    print(f"Location: {args.location}")
    print(f"Optical:  {optical_path}")
    print(f"SAR:      {sar_path}")
    print(f"Manifest: {manifest_path}")
    print(
        "S2 scene: ",
        manifest["optical"]["scene_id"],
        manifest["optical"]["acquisition_datetime"],
    )
    print(
        "S1 scene: ",
        manifest["sar"]["scene_id"],
        manifest["sar"]["acquisition_datetime"],
    )
    print(f"Temporal gap: {manifest['temporal_gap_days']:.2f} days")
    print(f"CRS: {manifest['co_registration']['crs']}")
    print(
        "Grid: "
        f"{manifest['co_registration']['width']} x "
        f"{manifest['co_registration']['height']}"
    )
    print(
        "Exact output grid match: ",
        manifest["co_registration"]["exact_output_grid_match"],
    )
    print("Synthetic data: False")
    print("\nUse these two TIFFs in SatQuery -> Analyze My Imagery -> Optical + SAR Pair.")


if __name__ == "__main__":
    main()
