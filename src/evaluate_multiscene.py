import sys

sys.path.insert(0, "src")

import numpy as np
import torch

from torch.utils.data import DataLoader

from multiscene_dataset import MultiSceneDataset
from model import SatelliteCNN


MODEL_PATH = (
    "data/processed/"
    "satquery_multiscene_best.pth"
)


def main():

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        "Using device:",
        device
    )

    if torch.cuda.is_available():
        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )

    test_dataset = MultiSceneDataset(
        "data/processed/"
        "multiscene_manifests/test.csv"
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=16,
        shuffle=False,
        num_workers=2,
        pin_memory=True
    )

    model = SatelliteCNN(
        num_bands=4
    )

    model.load_state_dict(
        torch.load(
            MODEL_PATH,
            map_location=device
        )
    )

    model = model.to(device)
    model.eval()

    predictions = []
    targets_all = []

    with torch.no_grad():

        for images, targets in test_loader:

            images = images.to(
                device,
                non_blocking=True
            )

            output = model(
                images
            )

            predictions.extend(
                output
                .squeeze(1)
                .cpu()
                .numpy()
            )

            targets_all.extend(
                targets
                .cpu()
                .numpy()
            )

    predictions = np.array(
        predictions
    )

    targets_all = np.array(
        targets_all
    )

    errors = (
        predictions
        - targets_all
    )

    mse = np.mean(
        errors ** 2
    )

    rmse = np.sqrt(
        mse
    )

    mae = np.mean(
        np.abs(errors)
    )

    correlation = np.corrcoef(
        predictions,
        targets_all
    )[0, 1]

    print(
        "\nTest scene: 2026-03-08"
    )

    print(
        "Test samples:",
        len(test_dataset)
    )

    print(
        "Test MSE:",
        mse
    )

    print(
        "Test RMSE:",
        rmse
    )

    print(
        "Test MAE:",
        mae
    )

    print(
        "Correlation:",
        correlation
    )

    print(
        "\nTarget mean:",
        targets_all.mean()
    )

    print(
        "Prediction mean:",
        predictions.mean()
    )


if __name__ == "__main__":
    main()