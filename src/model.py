import torch
import torch.nn as nn


class SatelliteCNN(nn.Module):

    def __init__(self, num_bands=4):
        super().__init__()

        self.features = nn.Sequential(

            nn.Conv2d(
                in_channels=num_bands,
                out_channels=32,
                kernel_size=3,
                padding=1
            ),
            nn.ReLU(),

            nn.Conv2d(
                in_channels=32,
                out_channels=64,
                kernel_size=3,
                padding=1
            ),
            nn.ReLU(),

            nn.MaxPool2d(2),

            nn.Conv2d(
                in_channels=64,
                out_channels=128,
                kernel_size=3,
                padding=1
            ),
            nn.ReLU(),

            nn.MaxPool2d(2)
        )

        self.classifier = nn.Sequential(

            nn.AdaptiveAvgPool2d((1, 1)),

            nn.Flatten(),

            nn.Linear(128, 64),

            nn.ReLU(),

            nn.Linear(64, 1)
        )

    def forward(self, x):

        x = self.features(x)

        x = self.classifier(x)

        return x


if __name__ == "__main__":

    model = SatelliteCNN()

    x = torch.randn(2, 4, 256, 256)

    output = model(x)

    print("Input shape:", x.shape)
    print("Output shape:", output.shape)

    print(model)