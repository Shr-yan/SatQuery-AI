from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

import torch
from torch.utils.data import Dataset


class MultiSceneDataset(Dataset):

    def __init__(
        self,
        manifest_file,
        root_dir="data/raw/multiscene",
        chip_size=256
    ):

        self.df = pd.read_csv(manifest_file)
        self.root_dir = Path(root_dir)
        self.chip_size = chip_size

    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):

        row = self.df.iloc[index]

        scene = str(row["scene"])
        x = int(row["x"])
        y = int(row["y"])

        scene_dir = self.root_dir / scene

        window = rasterio.windows.Window(
            x,
            y,
            self.chip_size,
            self.chip_size
        )

        bands = []

        for band_name in [
            "B02",
            "B03",
            "B04",
            "B08"
        ]:

            with rasterio.open(
                scene_dir / f"{band_name}.tif"
            ) as src:

                band = src.read(
                    1,
                    window=window
                ).astype(np.float32)

            band = np.clip(
                band / 10000.0,
                0.0,
                1.0
            )

            bands.append(band)

        chip = np.stack(
            bands,
            axis=0
        )

        red = chip[2]
        nir = chip[3]

        valid = (
            (red > 0)
            | (nir > 0)
        )

        ndvi = (
            (nir - red)
            /
            (nir + red + 1e-6)
        )

        target = (
            float(ndvi[valid].mean())
            if valid.any()
            else 0.0
        )

        return (
            torch.from_numpy(chip).float(),
            torch.tensor(
                target,
                dtype=torch.float32
            )
        )