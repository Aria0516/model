"""Extract one matching embedded figure from the archived and executed notebooks."""

from __future__ import annotations

import base64
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CELL_INDEX = 28
OUTPUT_INDEX = 1


def extract(notebook_path: Path, output_path: Path) -> None:
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    payload = notebook["cells"][CELL_INDEX]["outputs"][OUTPUT_INDEX]["data"]["image/png"]
    if isinstance(payload, list):
        payload = "".join(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(payload))


def main() -> None:
    output_dir = ROOT / "outputs" / "figure_comparison"
    extract(
        ROOT / "sam_spaghetti" / "doc" / "notebook" / "sam_sequence_detect_quantify_and_align.ipynb",
        output_dir / "official_notebook_primordia_detection.png",
    )
    extract(
        ROOT / "outputs" / "historic_notebook" / "sam_sequence_detect_quantify_and_align.executed.ipynb",
        output_dir / "reproduced_primordia_detection.png",
    )


if __name__ == "__main__":
    main()
