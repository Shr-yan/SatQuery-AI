from pathlib import Path

import numpy as np
import torch

from model import SatelliteCNN


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DEFAULT_MODEL_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "satquery_geographic_best.pth"
)


class SatQueryModel:

    def __init__(
        self,
        model_path=DEFAULT_MODEL_PATH,
        device=None
    ):

        self.model_path = Path(
            model_path
        )

        if not self.model_path.exists():

            raise FileNotFoundError(
                f"Model not found: "
                f"{self.model_path}"
            )

        if device is None:

            device = (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )

        self.device = torch.device(
            device
        )

        self.model = SatelliteCNN(
            num_bands=4
        )

        state_dict = torch.load(
            self.model_path,
            map_location=self.device
        )

        self.model.load_state_dict(
            state_dict
        )

        self.model = self.model.to(
            self.device
        )

        self.model.eval()

    def predict_chip(
        self,
        chip
    ):

        chip = np.asarray(
            chip,
            dtype=np.float32
        )

        if chip.shape != (
            4,
            256,
            256
        ):

            raise ValueError(
                "Expected chip shape "
                "(4, 256, 256), "
                f"got {chip.shape}"
            )

        tensor = torch.from_numpy(
            chip
        )

        tensor = tensor.unsqueeze(0)

        tensor = tensor.to(
            self.device
        )

        with torch.no_grad():

            prediction = self.model(
                tensor
            )

        return float(
            prediction.item()
        )


if __name__ == "__main__":

    predictor = SatQueryModel()

    print(
        "Model device:",
        predictor.device
    )

    dummy_chip = np.random.rand(
        4,
        256,
        256
    ).astype(
        np.float32
    )

    prediction = predictor.predict_chip(
        dummy_chip
    )

    print(
        "Dummy prediction:",
        prediction
    )