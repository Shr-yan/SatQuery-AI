import torch
import torch.nn as nn
import torch.optim as optim

from dataloader import create_dataloader
from model import SatelliteCNN


def main():

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("Using device:", device)

    loader = create_dataloader(
        batch_size=4,
        shuffle=True
    )

    model = SatelliteCNN()

    model = model.to(device)

    criterion = nn.MSELoss()

    optimizer = optim.Adam(
        model.parameters(),
        lr=0.001
    )

    epochs = 5

    for epoch in range(epochs):

        model.train()

        total_loss = 0.0

        for images, labels in loader:

            images = images.to(device)

            labels = labels.to(device)

            labels = labels.unsqueeze(1)

            optimizer.zero_grad()

            predictions = model(images)

            loss = criterion(
                predictions,
                labels
            )

            loss.backward()

            optimizer.step()

            total_loss += loss.item()

        average_loss = (
            total_loss /
            len(loader)
        )

        print(
            f"Epoch {epoch + 1}/{epochs} "
            f"- Loss: {average_loss:.6f}"
        )

    model_path = (
        "data/processed/"
        "satellite_cnn.pth"
    )

    torch.save(
        model.state_dict(),
        model_path
    )

    print(
        "Model saved:",
        model_path
    )


if __name__ == "__main__":
    main()