import numpy as np
from pathlib import Path
import shutil


CHIP_DIR = Path("data/processed/chips")
LABEL_DIR = Path("data/processed/labels")

TRAIN_DIR = Path("data/processed/train")
VAL_DIR = Path("data/processed/val")

TRAIN_LABEL_DIR = Path("data/processed/train_labels")
VAL_LABEL_DIR = Path("data/processed/val_labels")


LABEL_DIR.mkdir(parents=True, exist_ok=True)
TRAIN_LABEL_DIR.mkdir(parents=True, exist_ok=True)
VAL_LABEL_DIR.mkdir(parents=True, exist_ok=True)


files = sorted(CHIP_DIR.glob("*.npy"))

print("Found chips:", len(files))


# Create labels for every chip
for file in files:

    chip = np.load(file)

    # Synthetic target
    target = float(chip.mean())

    label_file = LABEL_DIR / file.name

    np.save(
        label_file,
        np.array(target, dtype=np.float32)
    )


print(
    "Labels created:",
    len(list(LABEL_DIR.glob("*.npy")))
)


# Copy labels to training/validation folders
train_files = sorted(TRAIN_DIR.glob("*.npy"))
val_files = sorted(VAL_DIR.glob("*.npy"))


for file in train_files:

    source = LABEL_DIR / file.name
    destination = TRAIN_LABEL_DIR / file.name

    if source.exists():
        shutil.copy2(source, destination)


for file in val_files:

    source = LABEL_DIR / file.name
    destination = VAL_LABEL_DIR / file.name

    if source.exists():
        shutil.copy2(source, destination)


print(
    "Training labels:",
    len(list(TRAIN_LABEL_DIR.glob("*.npy")))
)

print(
    "Validation labels:",
    len(list(VAL_LABEL_DIR.glob("*.npy")))
)