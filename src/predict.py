import numpy as np
import torch

from model import SatelliteCNN


MODEL_PATH = (
    "data/processed/"
    "satellite_cnn.pth"
)

CHIP_PATH = (
    "data/processed/"
    "chips/chip_0000.npy"
)


def main():

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
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

    chip = np.load(CHIP_PATH)

    tensor = torch.from_numpy(
        chip
    ).float()

    tensor = tensor.unsqueeze(0)

    tensor = tensor.to(device)

    with torch.no_grad():

        prediction = model(tensor)

    print(
        "Prediction:",
        prediction.item()
    )


if __name__ == "__main__":
    main()