#!/usr/bin/env bash
set -euo pipefail

context_dir="/mnt/c/Users/xczhang/Desktop/papers/reproductions/elife55832/sam_spaghetti"
dockerfile="/mnt/c/Users/xczhang/Desktop/papers/reproductions/elife55832/docker/Dockerfile.original"

if [[ ! -d "${context_dir}/.git" ]]; then
  echo "Official sam_spaghetti checkout not found at ${context_dir}." >&2
  exit 1
fi

if [[ ! -f "${dockerfile}" ]]; then
  echo "Dockerfile not found at ${dockerfile}." >&2
  exit 1
fi

docker build \
  --network host \
  --build-arg HTTP_PROXY=http://127.0.0.1:7897 \
  --build-arg HTTPS_PROXY=http://127.0.0.1:7897 \
  --tag elife55832-sam-spaghetti:original \
  --file "${dockerfile}" \
  "${context_dir}"
