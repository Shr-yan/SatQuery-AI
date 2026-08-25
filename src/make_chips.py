import numpy as np
from pathlib import Path

INPUT = "data/processed/sentinel2_normalized.npy"
OUTPUT_DIR = Path("data/processed/chips")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

data = np.load(INPUT)

print("Input shape:", data.shape)

chip_size = 256

height = data.shape[1]
width = data.shape[2]

count = 0

for y in range(0, height - chip_size + 1, chip_size):
    for x in range(0, width - chip_size + 1, chip_size):

        chip = data[:, y:y+chip_size, x:x+chip_size]

        output = OUTPUT_DIR / f"chip_{count:04d}.npy"
        np.save(output, chip)

        count += 1

        # For now, create only 20 chips
        if count >= 20:
            break

    if count >= 20:
        break

print("Created", count, "chips")
print("Saved in:", OUTPUT_DIR)