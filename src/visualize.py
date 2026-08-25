import numpy as np
import matplotlib.pyplot as plt


CHIP = "data/processed/chips/chip_0000.npy"

data = np.load(CHIP)

print("Shape:", data.shape)


for band in range(data.shape[0]):

    plt.figure()

    plt.imshow(data[band])

    plt.title(
        f"Satellite Band {band + 1}"
    )

    plt.axis("off")

    output = (
        f"data/processed/"
        f"chip_0000_band{band + 1}.png"
    )

    plt.savefig(
        output,
        bbox_inches="tight"
    )

    plt.close()

    print("Saved:", output)


print("Visualization completed.")