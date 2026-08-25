import json
import os

from src.ingestion import (
    inspect_and_extract,
    generate_ui_preview,
)

from src.tiler import generate_tiles


def main():

    # ------------------------------
    # Configuration
    # ------------------------------

    input_file = (
        "data/raw/optical/"
        "sample_optical.tif"
    )

    preview_path = (
        "data/previews/"
        "sample_optical_preview.png"
    )

    manifest_path = (
        "manifests/"
        "phase1_tiles.json"
    )

    print()
    print("======================================")
    print("     SATQUERY AI - PHASE 1A")
    print("======================================")

    # ------------------------------
    # 1. Read GeoTIFF
    # ------------------------------

    print("\n[1/3] Inspecting GeoTIFF...")

    meta, raw_array = inspect_and_extract(
        input_file
    )

    print("\nMetadata:")
    print(
        json.dumps(
            meta,
            indent=2,
            default=str
        )
    )

    print(
        "\nRaw array shape:",
        raw_array.shape
    )

    print(
        "Raw array dtype:",
        raw_array.dtype
    )

    # ------------------------------
    # 2. Generate UI preview
    # ------------------------------

    print("\n[2/3] Generating preview...")

    generate_ui_preview(
        raw_array,
        meta,
        preview_path
    )

    # ------------------------------
    # 3. Generate tiles
    # ------------------------------

    print("\n[3/3] Generating tiles...")

    tiles = generate_tiles(
        raw_array,
        meta,
        tile_size=512,
        overlap=64
    )

    # ------------------------------
    # 4. Save manifest
    # ------------------------------

    os.makedirs(
        "manifests",
        exist_ok=True
    )

    with open(
        manifest_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            tiles,
            f,
            indent=2,
            default=str
        )

    print(
        f"\n[+] Tile manifest saved: "
        f"{manifest_path}"
    )

    # ------------------------------
    # Final summary
    # ------------------------------

    print("\n======================================")
    print("       PHASE 1A COMPLETE")
    print("======================================")

    print(
        f"Input: {input_file}"
    )

    print(
        f"Raw array: {raw_array.shape}"
    )

    print(
        f"Tiles generated: {len(tiles)}"
    )

    print(
        f"Preview: {preview_path}"
    )

    print(
        f"Manifest: {manifest_path}"
    )

    print("======================================")


if __name__ == "__main__":
    main()