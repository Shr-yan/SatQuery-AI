import numpy as np
import torch
from torch.utils.data import Dataset
from pathlib import Path


class SatelliteDataset(Dataset):

    def __init__(
        self,
        chip_dir="data/processed/chips",
        label_dir="data/processed/labels"
    ):

        self.chip_dir = Path(chip_dir)
        self.label_dir = Path(label_dir)

        self.files = sorted(
            self.chip_dir.glob("*.npy")
        )

    def __len__(self):

        return len(self.files)

    def __getitem__(self, index):

        chip_file = self.files[index]

        label_file = (
            self.label_dir /
            chip_file.name
        )

        chip = np.load(chip_file)

        label = np.load(label_file)

        chip = torch.from_numpy(
            chip
        ).float()

        label = torch.tensor(
            label,
            dtype=torch.float32
        )

        return chip, label


if __name__ == "__main__":

    dataset = SatelliteDataset()

    print(
        "Number of samples:",
        len(dataset)
    )

    image, label = dataset[0]

    print(
        "Image shape:",
        image.shape
    )

    print(
        "Label:",
        label
    )

    print(
        "Label shape:",
        label.shape
    )