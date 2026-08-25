import rasterio
import numpy as np
from PIL import Image


def create_preview(
    input_file,
    output_file
):

    with rasterio.open(input_file) as src:

        if src.count == 1:

            image = src.read(1)

            min_val = np.nanmin(image)
            max_val = np.nanmax(image)

            if max_val > min_val:
                image = (
                    (image - min_val)
                    / (max_val - min_val)
                    * 255
                )

            image = image.astype(
                np.uint8
            )

        else:

            image = src.read(
                [1, 2, 3]
            )

            min_val = image.min()
            max_val = image.max()

            if max_val > min_val:
                image = (
                    (image - min_val)
                    / (max_val - min_val)
                    * 255
                )

            image = image.astype(
                np.uint8
            )

            image = np.transpose(
                image,
                (1, 2, 0)
            )

    Image.fromarray(
        image
    ).save(
        output_file
    )

    print(
        "Preview created:",
        output_file
    )


if __name__ == "__main__":

    create_preview(
        "data/processed/results/query_crop.tif",
        "data/processed/results/query_preview.png"
    )