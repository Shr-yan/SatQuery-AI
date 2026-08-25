import torch
import torch.nn as nn

from dataset import SatelliteDataset
from model import SatelliteCNN


MODEL_PATH = "data/processed/satellite_cnn.pth"


def main():

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    dataset = SatelliteDataset(
        chip_dir="data/processed/val",
        label_dir="data/processed/val_labels"
    )

    model = SatelliteCNN()

    model.load_state_dict(
        torch.load(
            MODEL_PATH,
            map_location=device
        )
    )

    model = model.to(device)
    model.eval()

    criterion = nn.MSELoss()

    total_loss = 0.0
    total_mae = 0.0
    with torch.no_grad():

        for i in range(len(dataset)):

            image, label = dataset[i]

            image = image.unsqueeze(0).to(device)

            label = label.reshape(1, 1).to(device)

            prediction = model(image)
            mae = torch.abs(
                prediction - label
                ).mean()

            total_mae += mae.item()
            loss = criterion(
                prediction,
                label
            )

            total_loss += loss.item()

    average_loss = total_loss / len(dataset)
    average_mae = total_mae / len(dataset)

    print("Validation MAE:", average_mae)
    print("Validation samples:", len(dataset))
    print("Validation MSE:", average_loss)


if __name__ == "__main__":
    main()