from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

RAW_OPTICAL_DIR = PROJECT_ROOT / "data" / "raw" / "optical"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CHIPS_DIR = PROCESSED_DIR / "chips"

MODEL_DIR = PROCESSED_DIR / "models"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

CHIP_SIZE = 256

NUM_BANDS = 4

BATCH_SIZE = 4

LEARNING_RATE = 0.001

EPOCHS = 5