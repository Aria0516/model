"""Audit a fresh notebook execution against the outputs archived upstream."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image


def load_notebook(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def image_outputs(notebook: dict) -> dict:
    images = {}
    for cell_index, cell in enumerate(notebook["cells"]):
        for output_index, output in enumerate(cell.get("outputs", [])):
            for mime in ("image/png", "image/jpeg"):
                encoded = output.get("data", {}).get(mime)
                if encoded is not None:
                    if isinstance(encoded, list):
                        encoded = "".join(encoded)
                    images[(cell_index, output_index, mime)] = base64.b64decode(encoded)
    return images


def compare_image(author_bytes: bytes, run_bytes: bytes) -> dict:
    author_array = np.asarray(Image.open(io.BytesIO(author_bytes))).astype(np.int16)
    run_array = np.asarray(Image.open(io.BytesIO(run_bytes))).astype(np.int16)
    same_shape = author_array.shape == run_array.shape
    if same_shape:
        delta = np.abs(author_array - run_array)
        different_values = int(np.count_nonzero(delta))
        total_values = int(delta.size)
        max_abs_diff = int(delta.max()) if delta.size else 0
        mean_abs_diff = float(delta.mean()) if delta.size else 0.0
    else:
        different_values = None
        total_values = None
        max_abs_diff = None
        mean_abs_diff = None
    return {
        "author_bytes": len(author_bytes),
        "run_bytes": len(run_bytes),
        "author_sha256": hashlib.sha256(author_bytes).hexdigest(),
        "run_sha256": hashlib.sha256(run_bytes).hexdigest(),
        "encoded_bytes_identical": author_bytes == run_bytes,
        "same_shape": same_shape,
        "author_shape": list(author_array.shape),
        "run_shape": list(run_array.shape),
        "pixel_values_identical": same_shape and different_values == 0,
        "different_pixel_values": different_values,
        "total_pixel_values": total_values,
        "max_abs_diff": max_abs_diff,
        "mean_abs_diff": mean_abs_diff,
    }


def csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8") as stream:
        return max(0, sum(1 for _ in stream) - 1)


def pipeline_inventory(root: Path) -> dict:
    files = [path for path in root.rglob("*") if path.is_file()]
    timepoints = {}
    for timepoint in ("t00", "t05", "t10"):
        raw_signal = list(root.rglob("*_{}_signal_data.csv".format(timepoint)))
        aligned_l1 = list(root.rglob("*_{}_aligned_L1_normalized_signal_data.csv".format(timepoint)))
        primordia = list(root.rglob("*_{}_aligned_primordia_extrema.csv".format(timepoint)))
        if not (len(raw_signal) == len(aligned_l1) == len(primordia) == 1):
            raise RuntimeError("Unexpected CSV inventory for {}".format(timepoint))
        timepoints[timepoint] = {
            "detected_nuclei": csv_rows(raw_signal[0]),
            "aligned_l1_cells": csv_rows(aligned_l1[0]),
            "primordia_extrema_rows": csv_rows(primordia[0]),
        }
    extension_counts = {}
    for path in files:
        extension_counts[path.suffix] = extension_counts.get(path.suffix, 0) + 1
    return {
        "root": str(root.resolve()),
        "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "zero_length_files": sum(path.stat().st_size == 0 for path in files),
        "extension_counts": dict(sorted(extension_counts.items())),
        "timepoints": timepoints,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parent
    parser.add_argument(
        "--source",
        type=Path,
        default=root / "sam_spaghetti/doc/notebook/sam_sequence_detect_quantify_and_align.ipynb",
    )
    parser.add_argument(
        "--executed",
        type=Path,
        default=root / "outputs/historic_notebook/sam_sequence_detect_quantify_and_align.executed.ipynb",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "outputs/historic_notebook/validation.json",
    )
    parser.add_argument(
        "--pipeline-output",
        type=Path,
        default=root / "outputs/historic_nuclei_images",
    )
    args = parser.parse_args()

    author_notebook = load_notebook(args.source)
    run_notebook = load_notebook(args.executed)
    run_code_cells = [
        cell
        for cell in run_notebook["cells"]
        if cell.get("cell_type") == "code" and cell.get("source")
    ]
    error_outputs = [
        output
        for cell in run_code_cells
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]

    author_images = image_outputs(author_notebook)
    run_images = image_outputs(run_notebook)
    comparisons = []
    for key, author_bytes in sorted(author_images.items()):
        run_bytes = run_images.get(key)
        comparison = {
            "cell_index": key[0],
            "output_index": key[1],
            "mime": key[2],
            "present_in_run": run_bytes is not None,
        }
        if run_bytes is not None:
            comparison.update(compare_image(author_bytes, run_bytes))
        comparisons.append(comparison)

    report = {
        "source_notebook": str(args.source.resolve()),
        "executed_notebook": str(args.executed.resolve()),
        "source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
        "executed_sha256": hashlib.sha256(args.executed.read_bytes()).hexdigest(),
        "code_cells": len(run_code_cells),
        "executed_code_cells": sum(
            cell.get("execution_count") is not None for cell in run_code_cells
        ),
        "error_outputs": len(error_outputs),
        "author_embedded_images": len(author_images),
        "run_embedded_images": len(run_images),
        "encoded_images_identical": sum(
            item.get("encoded_bytes_identical", False) for item in comparisons
        ),
        "pixel_images_identical": sum(
            item.get("pixel_values_identical", False) for item in comparisons
        ),
        "image_comparisons": comparisons,
        "pipeline_outputs": pipeline_inventory(args.pipeline_output),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if (
        report["error_outputs"]
        or report["executed_code_cells"] != report["code_cells"]
        or report["pipeline_outputs"]["zero_length_files"]
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
