
import numpy as np
import pandas as pd
import torch

from torch.utils.data import Dataset

from multiscene_dataset import MultiSceneDataset


class CachedPlaceDataset(Dataset):

    def __init__(self, manifest_path, split=None):

        self.df = pd.read_csv(manifest_path)

        if split is not None:
            self.df = (
                self.df[
                    self.df["split"] == split
                ]
                .reset_index(drop=True)
            )

    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):

        row = self.df.iloc[index]

        chip = np.load(
            row["path"]
        ).astype(np.float32)

        target = float(
            row["target"]
        )

        return (
            torch.from_numpy(chip),
            torch.tensor(
                target,
                dtype=torch.float32
            )
        )


class GeographicTrainDataset(Dataset):

    def __init__(
        self,
        lucknow_manifest,
        multiplace_manifest
    ):

        self.lucknow = MultiSceneDataset(
            lucknow_manifest
        )

        df = pd.read_csv(
            multiplace_manifest
        )

        self.delhi = (
            df[
                (df["place"] == "delhi")
                & (df["split"] == "train")
            ]
            .reset_index(drop=True)
        )

        self.jaipur = (
            df[
                (df["place"] == "jaipur")
                & (df["split"] == "train")
            ]
            .reset_index(drop=True)
        )

        # One epoch has equal contribution
        # from all three geographic groups.
        self.samples_per_place = 2000

        self.total_samples = (
            self.samples_per_place * 3
        )

    def __len__(self):
        return self.total_samples

    def load_cached(self, df, index):

        row = df.iloc[
            index % len(df)
        ]

        chip = np.load(
            row["path"]
        ).astype(np.float32)

        target = float(
            row["target"]
        )

        return (
            torch.from_numpy(chip),
            torch.tensor(
                target,
                dtype=torch.float32
            )
        )

    def __getitem__(self, index):

        group = (
            index
            // self.samples_per_place
        )

        local_index = (
            index
            % self.samples_per_place
        )

        if group == 0:

            # Cycle through Lucknow.
            return self.lucknow[
                local_index
                % len(self.lucknow)
            ]

        if group == 1:

            return self.load_cached(
                self.delhi,
                local_index
            )

        return self.load_cached(
            self.jaipur,
            local_index
        )
