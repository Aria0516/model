#!/usr/bin/env bash
set -euo pipefail

repro_root="/mnt/c/Users/xczhang/Desktop/papers/reproductions/elife55832"
input_dir="${repro_root}/data/E27_SAM7/original_layout"
result_dir="${repro_root}/outputs/historic_notebook"
nuclei_dir="${repro_root}/outputs/historic_nuclei_images"
experiment_dir="/opt/sam_spaghetti/share/data/microscopy/20170817 MS-E27 LD qDII-CLV3-DR5"
notebook="/opt/sam_spaghetti/doc/notebook/sam_sequence_detect_quantify_and_align.ipynb"

mkdir -p "${result_dir}" "${nuclei_dir}"

docker run --rm \
  --shm-size=2g \
  --volume "${input_dir}:${experiment_dir}:ro" \
  --volume "${nuclei_dir}:/opt/sam_spaghetti/share/data/nuclei_images" \
  --volume "${result_dir}:/work" \
  elife55832-historic:2020 \
  /opt/conda/envs/sam_spaghetti/bin/jupyter nbconvert \
    --to notebook \
    --execute "${notebook}" \
    --ExecutePreprocessor.timeout=-1 \
    --ExecutePreprocessor.kernel_name=python3 \
    --output-dir=/work \
    --output=sam_sequence_detect_quantify_and_align.executed.ipynb
