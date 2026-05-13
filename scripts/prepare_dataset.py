#!/usr/bin/env python3

"""
Prepare COCO polygon UAV weed dataset for YOLO training.

Features:
- Supports COCO annotations exported from Roboflow
- Supports single or multiple Annotated folders
- Train / validation / test split
- YOLO detection format
- YOLO segmentation format
- Keeps negative images with empty labels
- Automatic YOLO data.yaml creation
- Handles duplicate filenames automatically

Example usage:

1. YOLO segmentation
python prepare_dataset.py \
  --input "Summer 2025/Thessaloniki/Phantom Flight at 10 m Altitude/Annotated" \
  --output prepared_dataset \
  --task segmentation

2. YOLO detection
python prepare_dataset.py \
  --input "Summer 2025/Thessaloniki/Phantom Flight at 10 m Altitude/Annotated" \
  --output prepared_dataset_detection \
  --task detection

3. All annotated folders recursively
python prepare_dataset.py \
  --input "." \
  --output prepared_dataset \
  --task segmentation
"""

import argparse
import json
import random
import shutil
from pathlib import Path


# Supported image extensions
IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
}


def find_annotation_files(input_path):
    """
    Find COCO annotation JSON files.

    Supports:
    - Single JSON file
    - One Annotated folder
    - Entire dataset root recursively
    """

    input_path = Path(input_path)

    common_names = [
        "_annotations.coco.json",
        "annotations.json",
        "_annotations.json",
    ]

    files = []

    # ---------------------------------------------------
    # Input is already a JSON file
    # ---------------------------------------------------
    if (
        input_path.is_file()
        and input_path.suffix == ".json"
    ):
        return [input_path]

    # ---------------------------------------------------
    # Search common annotation filenames recursively
    # ---------------------------------------------------
    for name in common_names:
        files.extend(input_path.rglob(name))

    # ---------------------------------------------------
    # Fallback: any JSON file
    # ---------------------------------------------------
    if not files:
        files = list(input_path.rglob("*.json"))

    if not files:
        raise FileNotFoundError(
            "No annotation JSON files found."
        )

    return sorted(set(files))


def find_image(annotation_dir, file_name):
    """
    Find image either:
    - inside annotation folder
    - inside images/ subfolder
    """

    candidates = [
        annotation_dir / file_name,
        annotation_dir / "images" / file_name,
    ]

    for path in candidates:

        if path.exists():
            return path

    raise FileNotFoundError(
        f"Image not found: {file_name}"
    )


def load_coco(json_path):
    """
    Load COCO annotation file.

    Returns:
        images:
            image_id -> image metadata

        categories:
            category_id -> category name

        annotations_by_image:
            image_id -> list of annotations
    """

    with open(json_path, "r", encoding="utf-8") as f:
        coco = json.load(f)

    # ---------------------------------------------------
    # Images dictionary
    # ---------------------------------------------------
    images = {
        img["id"]: img
        for img in coco.get("images", [])
    }

    # ---------------------------------------------------
    # Categories dictionary
    # ---------------------------------------------------
    categories = {
        cat["id"]: cat["name"]
        for cat in coco.get("categories", [])
    }

    # ---------------------------------------------------
    # Group annotations by image id
    # ---------------------------------------------------
    annotations_by_image = {}

    for ann in coco.get("annotations", []):

        image_id = ann["image_id"]

        if image_id not in annotations_by_image:
            annotations_by_image[image_id] = []

        annotations_by_image[image_id].append(ann)

    return (
        images,
        categories,
        annotations_by_image,
    )


def build_category_mapping(annotation_files):
    """
    Build continuous YOLO class ids.

    COCO category ids are not always sequential,
    while YOLO requires continuous class ids:
    0, 1, 2, ...
    """

    used_categories = {}
    all_categories = {}

    for json_path in annotation_files:

        (
            images,
            categories,
            annotations_by_image,
        ) = load_coco(json_path)

        all_categories.update(categories)

        for anns in annotations_by_image.values():

            for ann in anns:

                category_id = ann["category_id"]

                used_categories[
                    category_id
                ] = categories.get(
                    category_id,
                    f"class_{category_id}",
                )

    sorted_ids = sorted(
        used_categories.keys()
    )

    # COCO id -> YOLO id
    category_to_yolo = {
        category_id: idx
        for idx, category_id in enumerate(sorted_ids)
    }

    # YOLO class names
    names = [
        used_categories[category_id]
        for category_id in sorted_ids
    ]

    return category_to_yolo, names


def coco_bbox_to_yolo(
    bbox,
    image_width,
    image_height,
):
    """
    Convert COCO bbox:
        [x, y, width, height]

    To YOLO bbox:
        [x_center, y_center, width, height]

    All coordinates normalized to [0, 1].
    """

    x, y, w, h = bbox

    x_center = (
        x + w / 2
    ) / image_width

    y_center = (
        y + h / 2
    ) / image_height

    width = w / image_width
    height = h / image_height

    return (
        x_center,
        y_center,
        width,
        height,
    )


def coco_polygon_to_yolo(
    segmentation,
    image_width,
    image_height,
):
    """
    Convert COCO polygon coordinates
    into normalized YOLO segmentation format.
    """

    points = []

    for i in range(
        0,
        len(segmentation),
        2,
    ):

        x = segmentation[i] / image_width
        y = segmentation[i + 1] / image_height

        # Clamp coordinates safely
        x = min(max(x, 0.0), 1.0)
        y = min(max(y, 0.0), 1.0)

        points.extend([x, y])

    return points


def make_unique_name(
    source_path,
    used_names,
):
    """
    Avoid filename collisions when merging
    multiple Annotated folders.
    """

    name = source_path.name

    if name not in used_names:

        used_names.add(name)
        return name

    stem = source_path.stem
    suffix = source_path.suffix

    counter = 1

    while True:

        new_name = (
            f"{stem}_{counter}{suffix}"
        )

        if new_name not in used_names:

            used_names.add(new_name)
            return new_name

        counter += 1


def write_label_file(
    label_path,
    annotations,
    category_to_yolo,
    image_width,
    image_height,
    task,
):
    """
    Write YOLO label file.

    Supports:
    - Detection format
    - Segmentation format

    Empty label files are kept for
    negative/background images.
    """

    lines = []

    for ann in annotations:

        category_id = ann["category_id"]

        if category_id not in category_to_yolo:
            continue

        class_id = category_to_yolo[
            category_id
        ]

        # ---------------------------------------------------
        # YOLO DETECTION
        # ---------------------------------------------------
        if task == "detection":

            bbox = ann.get("bbox")

            if not bbox:
                continue

            values = coco_bbox_to_yolo(
                bbox,
                image_width,
                image_height,
            )

            line = [class_id] + list(values)

        # ---------------------------------------------------
        # YOLO SEGMENTATION
        # ---------------------------------------------------
        elif task == "segmentation":

            segmentations = ann.get(
                "segmentation",
                [],
            )

            if not isinstance(
                segmentations,
                list,
            ):
                continue

            for segmentation in segmentations:

                # Need at least 3 polygon points
                if len(segmentation) < 6:
                    continue

                polygon = coco_polygon_to_yolo(
                    segmentation,
                    image_width,
                    image_height,
                )

                line = [class_id] + polygon

                lines.append(
                    " ".join(
                        (
                            f"{v:.6f}"
                            if isinstance(v, float)
                            else str(v)
                        )
                        for v in line
                    )
                )

            continue

        else:

            raise ValueError(
                f"Unsupported task: {task}"
            )

        lines.append(
            " ".join(
                (
                    f"{v:.6f}"
                    if isinstance(v, float)
                    else str(v)
                )
                for v in line
            )
        )

    # Create parent folder if needed
    label_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Write label file
    with open(
        label_path,
        "w",
        encoding="utf-8",
    ) as f:

        f.write("\n".join(lines))


def split_items(
    items,
    train_ratio,
    val_ratio,
    seed,
):
    """
    Split dataset into:
    - train
    - validation
    - test
    """

    random.seed(seed)
    random.shuffle(items)

    total = len(items)

    train_end = int(
        total * train_ratio
    )

    val_end = (
        train_end +
        int(total * val_ratio)
    )

    return {
        "train": items[:train_end],
        "val": items[train_end:val_end],
        "test": items[val_end:],
    }


def write_data_yaml(
    output_dir,
    names,
):
    """
    Create YOLO data.yaml file.
    """

    yaml_path = output_dir / "data.yaml"

    with open(
        yaml_path,
        "w",
        encoding="utf-8",
    ) as f:

        f.write("path: .\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        f.write("test: images/test\n\n")

        f.write(f"nc: {len(names)}\n")

        f.write("names:\n")

        for idx, name in enumerate(names):

            f.write(
                f"  {idx}: {name}\n"
            )

    print(f"Saved: {yaml_path}")


def prepare_dataset(args):
    """
    Main dataset preparation pipeline.
    """

    input_path = Path(args.input)
    output_dir = Path(args.output)

    # ---------------------------------------------------
    # Find annotation files
    # ---------------------------------------------------
    annotation_files = find_annotation_files(
        input_path
    )

    # ---------------------------------------------------
    # Build category mapping
    # ---------------------------------------------------
    (
        category_to_yolo,
        names,
    ) = build_category_mapping(
        annotation_files
    )

    dataset_items = []

    # ---------------------------------------------------
    # Collect dataset items
    # ---------------------------------------------------
    for json_path in annotation_files:

        annotation_dir = json_path.parent

        (
            images,
            categories,
            annotations_by_image,
        ) = load_coco(json_path)

        for (
            image_id,
            image_info,
        ) in images.items():

            image_path = find_image(
                annotation_dir,
                image_info["file_name"],
            )

            annotations = (
                annotations_by_image.get(
                    image_id,
                    [],
                )
            )

            dataset_items.append(
                {
                    "image_path": image_path,
                    "image_info": image_info,
                    "annotations": annotations,
                }
            )

    # ---------------------------------------------------
    # Split dataset
    # ---------------------------------------------------
    splits = split_items(
        dataset_items,
        args.train_ratio,
        args.val_ratio,
        args.seed,
    )

    used_names = set()

    # ---------------------------------------------------
    # Export dataset
    # ---------------------------------------------------
    for split_name, items in splits.items():

        image_output_dir = (
            output_dir /
            "images" /
            split_name
        )

        label_output_dir = (
            output_dir /
            "labels" /
            split_name
        )

        image_output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        label_output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        for item in items:

            image_path = item["image_path"]

            image_info = item["image_info"]

            annotations = item["annotations"]

            # Avoid filename collisions
            new_image_name = make_unique_name(
                image_path,
                used_names,
            )

            output_image_path = (
                image_output_dir /
                new_image_name
            )

            # Copy image
            shutil.copy2(
                image_path,
                output_image_path,
            )

            image_width = image_info["width"]
            image_height = image_info["height"]

            label_name = (
                Path(new_image_name).stem
                + ".txt"
            )

            label_path = (
                label_output_dir /
                label_name
            )

            # Create YOLO label file
            write_label_file(
                label_path=label_path,
                annotations=annotations,
                category_to_yolo=category_to_yolo,
                image_width=image_width,
                image_height=image_height,
                task=args.task,
            )

        print(
            f"{split_name}: "
            f"{len(items)} images"
        )

    # ---------------------------------------------------
    # Create data.yaml
    # ---------------------------------------------------
    write_data_yaml(
        output_dir,
        names,
    )

    print(
        "Dataset preparation completed."
    )


def main():
    """
    Script entry point.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Prepare COCO UAV weed dataset "
            "for YOLO training."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        help=(
            "Path to Annotated folder, "
            "dataset root, or COCO JSON file."
        ),
    )

    parser.add_argument(
        "--output",
        default="prepared_dataset",
        help="Output dataset folder.",
    )

    parser.add_argument(
        "--task",
        choices=[
            "detection",
            "segmentation",
        ],
        default="segmentation",
        help="YOLO output task format.",
    )

    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Training split ratio.",
    )

    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.1,
        help="Validation split ratio.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help=(
            "Random seed for reproducible "
            "dataset splits."
        ),
    )

    args = parser.parse_args()

    # Validate split ratios
    if (
        args.train_ratio +
        args.val_ratio
        >= 1.0
    ):

        raise ValueError(
            "train_ratio + val_ratio "
            "must be less than 1.0"
        )

    prepare_dataset(args)


if __name__ == "__main__":
    main()
