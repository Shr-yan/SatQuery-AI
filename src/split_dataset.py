from pathlib import Path
import random
import shutil


SOURCE_DIR = Path("data/processed/chips")

TRAIN_DIR = Path("data/processed/train")
VAL_DIR = Path("data/processed/val")

TRAIN_DIR.mkdir(parents=True, exist_ok=True)
VAL_DIR.mkdir(parents=True, exist_ok=True)

files = sorted(SOURCE_DIR.glob("*.npy"))

random.seed(42)
random.shuffle(files)

split_index = int(len(files) * 0.8)

train_files = files[:split_index]
val_files = files[split_index:]

print("Total:", len(files))
print("Training:", len(train_files))
print("Validation:", len(val_files))

for file in train_files:
    shutil.copy2(
        file,
        TRAIN_DIR / file.name
    )

for file in val_files:
    shutil.copy2(
        file,
        VAL_DIR / file.name
    )

print("Dataset split completed.")