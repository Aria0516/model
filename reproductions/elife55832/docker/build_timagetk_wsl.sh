#!/usr/bin/env bash
set -euo pipefail

context_dir="/mnt/c/Users/xczhang/Desktop/papers/reproductions/elife55832"
dockerfile="${context_dir}/docker/Dockerfile.timagetk"

docker build \
  --network host \
  --build-arg HTTP_PROXY=http://127.0.0.1:7897 \
  --build-arg HTTPS_PROXY=http://127.0.0.1:7897 \
  --tag elife55832-timagetk:2.1.0 \
  --file "${dockerfile}" \
  "${context_dir}"
