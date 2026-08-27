
import sys
sys.path.insert(0, "src")

import torch
import torch.nn as nn
import torch.optim as optim

from torch.utils.data import DataLoader

from geographic_dataset import (
    GeographicTrainDataset,
    CachedPlaceDataset
)

from model import SatelliteCNN


BASE_MODEL = (
    "data/processed/"
    "satquery_multiscene_best.pth"
)

OUTPUT_MODEL = (
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

    train_dataset = GeographicTrainDataset(
        "data/processed/"
        "multiscene_manifests/train.csv",

        "data/processed/"
        "multiplace/manifest.csv"
    )

    val_dataset = CachedPlaceDataset(
        "data/processed/"
        "multiplace/manifest.csv",
        split="val"
    )

    print(
        "Training samples:",
        len(train_dataset)
    )

    print(
        "Validation samples:",
        len(val_dataset)
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=32,
        shuffle=True,
        num_workers=2,
        pin_memory=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=32,
        shuffle=False,
        num_workers=2,
        pin_memory=True
    )

    model = SatelliteCNN(
        num_bands=4
    )

    model.load_state_dict(
        torch.load(
            BASE_MODEL,
            map_location=device
        )
    )

    model = model.to(device)

    print(
        "Loaded previous multi-scene model."
    )

    criterion = nn.MSELoss()

    # Lower LR because this is fine-tuning.
    optimizer = optim.Adam(
        model.parameters(),
        lr=0.0002
    )

    scheduler = (
        optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=0.5,
            patience=2
        )
    )

    epochs = 12
    best_val = float("inf")

    for epoch in range(epochs):

        model.train()

        train_loss = 0.0

        for images, targets in train_loader:

            images = images.to(
                device,
                non_blocking=True
            )

            targets = (
                targets
                .unsqueeze(1)
                .to(
                    device,
                    non_blocking=True
                )
            )

            optimizer.zero_grad()

            predictions = model(images)

            loss = criterion(
                predictions,
                targets
            )

            loss.backward()

            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(
            train_loader
        )

        model.eval()

        val_loss = 0.0
        val_mae = 0.0

        with torch.no_grad():

            for images, targets in val_loader:

                images = images.to(
                    device,
                    non_blocking=True
                )

                targets = (
                    targets
                    .unsqueeze(1)
                    .to(
                        device,
                        non_blocking=True
                    )
                )

                predictions = model(
                    images
                )

                val_loss += criterion(
                    predictions,
                    targets
                ).item()

                val_mae += torch.abs(
                    predictions - targets
                ).mean().item()

        val_loss /= len(val_loader)
        val_mae /= len(val_loader)

        scheduler.step(val_loss)

        lr = optimizer.param_groups[0][
            "lr"
        ]

        print(
            f"Epoch {epoch + 1}/{epochs} "
            f"- Train Loss: {train_loss:.6f} "
            f"- Bhopal Val MSE: {val_loss:.6f} "
            f"- Bhopal Val MAE: {val_mae:.6f} "
            f"- LR: {lr:.6f}"
        )

        if val_loss < best_val:

            best_val = val_loss

            torch.save(
                model.state_dict(),
                OUTPUT_MODEL
            )

            print(
                "Saved new best geographic model."
            )

    print("\nTraining complete.")

    print(
        "Best Bhopal validation MSE:",
        best_val
    )


if __name__ == "__main__":
    main()
