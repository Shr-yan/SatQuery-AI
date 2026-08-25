from torch.utils.data import DataLoader

from dataset import SatelliteDataset


def create_dataloader(
    chip_dir="data/processed/chips",
    label_dir="data/processed/labels",
    batch_size=4,
    shuffle=True
):

    dataset = SatelliteDataset(
        chip_dir=chip_dir,
        label_dir=label_dir
    )

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle
    )

    return loader


if __name__ == "__main__":

    loader = create_dataloader()

    print(
        "Number of batches:",
        len(loader)
    )

    images, labels = next(
        iter(loader)
    )

    print(
        "Images shape:",
        images.shape
    )

    print(
        "Labels shape:",
        labels.shape
    )
    