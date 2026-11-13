// Shared drawing helpers for the Fig. 2-1 roadmap variants (black lines, one font size, NSFC multicolour palette).
const pptxgen = require("pptxgenjs");

const PAL = {
  grey: ["F4F6F8", "DDE3E8"], pink: ["F7DEDF", "E8B4B8"], green: ["E4F0D7", "BCD79F"],
  blue: ["DDEAF6", "B7D1EA"], orange: ["FBEAD4", "EDC48F"], purple: ["EEE4F4", "D8C3E6"], lavender: ["EEEAF4", "EEEAF4"],
};
const INK = "000000", PLUS = "64717E";

function make(W, H, FS) {
  const pres = new pptxgen();
  pres.defineLayout({ name: "FIG", width: W, height: H });
  pres.layout = "FIG";
  pres.title = "图2-1 技术路线";
  const s = pres.addSlide();
  const box = (x, y, w, h, text, o = {}) => s.addText(text, {
    x, y, w, h, fontFace: "Times New Roman", fontSize: FS, color: INK, align: "center", valign: "middle",
    fill: o.fill === null ? undefined : { color: o.fill || "FFFFFF" },
    line: o.noline ? { type: "none" } : { color: INK, width: o.lw || 0.75, dashType: o.dash || "solid" },
    margin: [1, 2, 1, 2], lineSpacingMultiple: 1.0, objectName: o.name,
  });
  const seg = (x1, y1, x2, y2, arrow, dash) => {
    const ln = { color: INK, width: 0.75 };
    if (arrow) ln.endArrowType = "triangle";
    if (dash) ln.dashType = "dash";
    s.addShape(pres.ShapeType.line, {
      x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.0001), h: Math.max(Math.abs(y2 - y1), 0.0001),
      flipH: x2 < x1, flipV: y2 < y1, line: ln,
    });
  };
  const frame = (x, y, w, h, fill, o = {}) => box(x, y, w, h, "", { fill: fill || null, dash: "dash", lw: o.lw || 1.0, name: o.name });
  const plus = (cx, cy, d) => s.addShape(pres.ShapeType.mathPlus, {
    x: cx - d / 2, y: cy - d / 2, w: d, h: d, fill: { color: PLUS }, line: { type: "none" }, objectName: "plus",
  });
  // one parent (centre px, bottom py) to children (centres xs) whose tops are at cy
  const split = (px, py, xs, cy, f = 0.5) => {
    const by = py + (cy - py) * f;
    seg(px, py, px, by); seg(Math.min(...xs, px), by, Math.max(...xs, px), by);
    xs.forEach((x) => seg(x, by, x, cy, true));
  };
  // children (centres xs, bottoms ys) to one parent (centre px, top py)
  const merge = (xs, ys, px, py, f = 0.4) => {
    const by = Math.max(...ys) + (py - Math.max(...ys)) * f;
    xs.forEach((x, i) => seg(x, ys[i], x, by));
    seg(Math.min(...xs, px), by, Math.max(...xs, px), by); seg(px, by, px, py, true);
  };
  const write = (file) => pres.writeFile({ fileName: file }).then((f) => console.log("wrote", f));
  return { pres, s, box, seg, frame, plus, split, merge, write };
}
module.exports = { make, PAL };
