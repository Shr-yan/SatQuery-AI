import sys

sys.path.insert(0, "src")

import torch
import torch.nn as nn
import torch.optim as optim

from torch.utils.data import DataLoader

from multiscene_dataset import MultiSceneDataset
from model import SatelliteCNN


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

    train_dataset = MultiSceneDataset(
        "data/processed/"
        "multiscene_manifests/train.csv"
    )

    val_dataset = MultiSceneDataset(
        "data/processed/"
        "multiscene_manifests/val.csv"
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
        batch_size=16,
        shuffle=True,
        num_workers=2,
        pin_memory=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=16,
        shuffle=False,
        num_workers=2,
        pin_memory=True
    )

    model = SatelliteCNN(
        num_bands=4
    ).to(device)

    criterion = nn.MSELoss()

    optimizer = optim.Adam(
        model.parameters(),
        lr=0.001
    )

    scheduler = (
        optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=0.5,
            patience=2
        )
    )

    epochs = 15
    best_val_loss = float("inf")

    for epoch in range(epochs):

        # ====================
        # TRAIN
        # ====================

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

            predictions = model(
                images
            )

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

        # ====================
        # VALIDATION
        # ====================

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

                loss = criterion(
                    predictions,
                    targets
                )

                mae = torch.abs(
                    predictions - targets
                ).mean()

                val_loss += loss.item()
                val_mae += mae.item()

        val_loss /= len(
            val_loader
        )

        val_mae /= len(
            val_loader
        )

        scheduler.step(
            val_loss
        )

        current_lr = (
            optimizer
            .param_groups[0]["lr"]
        )

        print(
            f"Epoch {epoch + 1}/{epochs} "
            f"- Train Loss: {train_loss:.6f} "
            f"- Val Loss: {val_loss:.6f} "
            f"- Val MAE: {val_mae:.6f} "
            f"- LR: {current_lr:.6f}"
        )

        if val_loss < best_val_loss:

            best_val_loss = val_loss

            torch.save(
                model.state_dict(),
                "data/processed/"
                "satquery_multiscene_best.pth"
            )

            print(
                "Saved new best model."
            )

    print(
        "\nTraining complete."
    )

    print(
        "Best validation MSE:",
        best_val_loss
    )


if __name__ == "__main__":
    main()