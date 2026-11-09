#!/bin/bash
f=$(/opt/conda/envs/sam_spaghetti/bin/python -c 'import tissue_nukem_3d.growth_estimation as g; print(g.__file__)' 2>/dev/null)
n=$(grep -n "def $1" "$f" | cut -d: -f1)
sed -n "${n},$((n+${2:-40}))p" "$f"
