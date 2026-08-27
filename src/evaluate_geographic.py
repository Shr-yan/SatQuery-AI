
import sys
sys.path.insert(0, "src")

import numpy as np
import torch

from torch.utils.data import DataLoader

from geographic_dataset import CachedPlaceDataset
from model import SatelliteCNN


MODEL_PATH = (
    "data/processed/"
    "satquery_geographic_best.pth"
)


def main():

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("Using device:", device)

    if torch.cuda.is_available():
        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )

    # Hyderabad was never used for
    # training or validation.
    test_dataset = CachedPlaceDataset(
        "data/processed/"
        "multiplace/manifest.csv",
        split="test"
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=32,
        shuffle=False,
        num_workers=2,
        pin_memory=True
    )

    print(
        "Unseen test location: Hyderabad"
    )

    print(
        "Test samples:",
        len(test_dataset)
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
    targets = []

    with torch.no_grad():

        for images, labels in test_loader:

            images = images.to(
                device,
                non_blocking=True
            )

            outputs = model(images)

            predictions.extend(
                outputs
                .squeeze(1)
                .cpu()
                .numpy()
            )

            targets.extend(
                labels.numpy()
            )

    predictions = np.asarray(
        predictions
    )

    targets = np.asarray(
        targets
    )

    errors = predictions - targets

    mse = np.mean(
        errors ** 2
    )

    rmse = np.sqrt(mse)

    mae = np.mean(
        np.abs(errors)
    )

    correlation = np.corrcoef(
        predictions,
        targets
    )[0, 1]

    bias = np.mean(errors)

    print("\n==============================")
    print("GEOGRAPHIC GENERALIZATION TEST")
    print("==============================")

    print("Location: Hyderabad")
    print("Samples:", len(targets))

    print("\nTest MSE:", mse)
    print("Test RMSE:", rmse)
    print("Test MAE:", mae)
    print("Correlation:", correlation)
    print("Bias:", bias)

    print(
        "\nTarget mean:",
        targets.mean()
    )

    print(
        "Prediction mean:",
        predictions.mean()
    )

    print(
        "Target min/max:",
        targets.min(),
        targets.max()
    )

    print(
        "Prediction min/max:",
        predictions.min(),
        predictions.max()
    )


if __name__ == "__main__":
    main()
