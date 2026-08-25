import rasterio
import numpy as np
from pathlib import Path


INPUT = "data/raw/optical/sentinel2_test.tif"
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "sentinel2_normalized.npy"

with rasterio.open(INPUT) as src:
    data = src.read().astype(np.float32)

print("Original shape:", data.shape)
print("Original dtype:", data.dtype)

# Normalize each band separately
for i in range(data.shape[0]):
    band = data[i]

    min_val = band.min()
    max_val = band.max()

    if max_val > min_val:
        data[i] = (band - min_val) / (max_val - min_val)
    else:
        data[i] = 0

print("Normalized min:", data.min())
print("Normalized max:", data.max())

np.save(OUTPUT, data)

print("Saved:", OUTPUT)