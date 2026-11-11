#!/bin/bash
# build both panel-A decks, then gradients, Chinese fonts, validation and a 200 dpi render
set -e
cd "$(dirname "$0")"
SK=${PPTX_SCRIPTS:?set PPTX_SCRIPTS to the pptx skill scripts dir (validate.py, soffice.py)}
mkdir -p out; python3 sam_geom2.py ../mech.npz sam_shapes.json; node sam_a.js sam_shapes.json out
for l in en zh; do
  f=out/fig1-2A_apex_$l.pptx
  python3 apply_grads.py $f sam_shapes.json
  [ $l = zh ] && python3 fix_fonts.py $f
  python3 $SK/office/validate.py $f | tail -1
  (cd out && timeout 120 python3 $SK/office/soffice.py --headless --convert-to pdf fig1-2A_apex_$l.pptx >/dev/null 2>&1)
  pdftoppm -r 200 -png -singlefile out/fig1-2A_apex_$l.pdf out/fig1-2A_apex_$l
done
