#!/usr/bin/env python3
"""Deterministic checks for the eLife 55832 reproduction outputs."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"


def read_json(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def validate_checksums() -> list[dict[str, object]]:
    results = []
    for line in (ROOT / "data_checksums.sha256").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split(maxsplit=1)
        path = ROOT / relative.strip()
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                digest.update(block)
        actual = digest.hexdigest()
        assert actual == expected, f"SHA256 mismatch: {path.name}"
        results.append({"file": relative.strip(), "bytes": path.stat().st_size, "sha256": actual})
    return results


def main() -> None:
    appendix = read_json("appendix2_summary.json")
    angular_sd = float(appendix["mean_angular_sd_ranks_1_to_5_deg"])
    observed_sd = float(appendix["paper_observed_angular_sd_deg"])
    assert abs(angular_sd - observed_sd) < 1.0
    assert float(appendix["separability_at_inferred_noise"]) >= 0.90

    image_result = read_json("e27_sam7_summary.json")
    best_t10 = float(image_result["best_rotation_deg"]["10"])
    corr_t10 = float(image_result["best_correlation"]["10"])
    assert abs(abs(best_t10) - 137.5) <= 5.0
    assert corr_t10 >= 0.70
    golden = image_result["correlation_at_paper_divergence_angle"]["10"]
    assert max(float(golden["+137.5_deg"]), float(golden["-137.5_deg"])) >= 0.70
    for time in ["0", "5", "10"]:
        metadata = image_result["metadata"][time]
        assert int(metadata["imagej"]["images"]) == 180
        assert int(metadata["imagej"]["channels"]) == 4
        assert int(metadata["imagej"]["slices"]) == 45
        assert int(metadata["projected_nuclei"]) >= 500

    for svg_name in ["appendix2_separability.svg", "appendix2_population.svg", "e27_sam7_rotation_curve.svg"]:
        ET.parse(OUTPUT / svg_name)
    for png_name, expected_size in [("e27_sam7_auxin_proxy.png", (1536, 560)), ("e27_sam7_rotation_curve.png", (900, 540))]:
        with Image.open(OUTPUT / png_name) as image:
            assert image.size == expected_size
            image.verify()

    verification = {
        "status": "PASS",
        "appendix2": {
            "simulated_mean_angular_sd_deg": angular_sd,
            "paper_observed_angular_sd_deg": observed_sd,
            "separability": appendix["separability_at_inferred_noise"],
        },
        "e27_sam7": {
            "best_t0_t10_rotation_deg": best_t10,
            "best_t0_t10_correlation": corr_t10,
        },
        "inputs": validate_checksums(),
    }
    (OUTPUT / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
