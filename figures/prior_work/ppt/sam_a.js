// Fig. 1-2 A (shoot apex with a wedge cut away) as an editable PowerPoint slide, English and Chinese.
// Geometry comes from sam_geom2.py (sam_shapes.json); apply_grads.py then adds the gradient fills; every shape is a native freeform, so colours,
// lines and labels can be changed in PowerPoint. Slide = 2x panel size, text 14 pt (7 pt when placed).
//   node sam_a.js sam_shapes.json <out_dir>
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const G = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OUT = process.argv[3] || ".";
const [W, H] = G.slide;
const INK = "1A1A1A";

const LABELS = {
  en: { cz: "Central zone", ring: "Competent\nring", prim: "Primordium", L1: "L1\nepidermis",
        inner: "Inner\nlayer*", strand: "Vascular\nstrand*" },
  zh: { cz: "中央区", ring: "发生环", prim: "原基", L1: "L1层", inner: "内层*", strand: "维管束*" },
};

function freeform(s, pts, opts) {
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const x0 = Math.min(...xs), y0 = Math.min(...ys);
  const w = Math.max(Math.max(...xs) - x0, 0.001), h = Math.max(Math.max(...ys) - y0, 0.001);
  const points = pts.map((p, i) => ({ x: p[0] - x0, y: p[1] - y0, moveTo: i === 0 }));
  if (opts.closed) points.push({ close: true });
  s.addShape("custGeom", Object.assign({ x: x0, y: y0, w, h, points }, opts.shape));
}

function build(lang, outFile) {
  const pres = new pptxgen();
  pres.defineLayout({ name: "PANEL", width: W, height: H });
  pres.layout = "PANEL";
  pres.title = lang === "zh" ? "图1-2 A 茎尖示意" : "Fig. 1-2 A shoot apex";
  const s = pres.addSlide();

  for (const g of G.shapes) {
    if (g.kind === "poly") {
      const shape = { fill: { color: g.fill, transparency: g.transparency || 0 }, objectName: g.name };
      if (g.grad) delete shape.fill.transparency;
      shape.line = g.line ? { color: g.line, width: g.lw } : { type: "none" };
      freeform(s, g.pts, { closed: true, shape });
    } else {
      const line = { color: g.color, width: g.lw };
      if (g.dash) line.dashType = g.dash;
      if (g.arrow) { line.endArrowType = "triangle"; }
      freeform(s, g.pts, { closed: false, shape: { line, objectName: g.name } });
    }
  }

  // labels: "Central zone" above the apex, the rest in two columns ordered by height so leaders do not cross
  const T = LABELS[lang], A = G.anchors;
  const lead = (x1, y1, x2, y2) => freeform(s, [[x1, y1], [x2, y2]], { closed: false,
    shape: { line: { color: INK, width: 1.0 }, objectName: "leader" } });
  const text = (t, x, y, w, h, align) => s.addText(t, { x, y, w, h, fontFace: "Times New Roman", fontSize: 14,
    color: INK, align, valign: "middle", margin: 0, isTextBox: true, lineSpacingMultiple: 0.9 });

  const [cx, cy] = A.cz;
  text(T.cz, cx - 1.0, 0.18, 2.0, 0.32, "center");
  lead(cx, 0.52, cx, cy - 0.03);

  const tw = (t) => Math.max(...t.split("\n").map((l) =>      // rough text width (in) at 14 pt
    [...l].reduce((a, c) => a + (/[\u4e00-\u9fff]/.test(c) ? 0.2 : 0.095), 0)));
  const mid = W / 2;
  const items = ["ring", "prim", "L1", "inner", "strand"].map((k) => ({ k, p: A[k] }));
  for (const side of ["L", "R"]) {
    const col = items.filter((it) => (it.p[0] < mid) === (side === "L")).sort((a, b) => a.p[1] - b.p[1]);
    const n = col.length, top = 1.05, bot = H - 0.75;
    col.forEach((it, i) => {
      const ty = n > 1 ? top + (i * (bot - top)) / (n - 1) : 0.45 * H;
      const two = T[it.k].includes("\n"), h = two ? 0.52 : 0.3, w = 1.15;
      if (side === "L") {
        text(T[it.k], 0.08, ty - h / 2, w, h, "left");
        lead(0.08 + tw(T[it.k]) + 0.07, ty, it.p[0], it.p[1]);
      } else {
        text(T[it.k], W - 0.08 - w, ty - h / 2, w, h, "right");
        lead(W - 0.08 - tw(T[it.k]) - 0.07, ty, it.p[0], it.p[1]);
      }
    });
  }
  return pres.writeFile({ fileName: outFile });
}

Promise.all([build("en", path.join(OUT, "fig1-2A_apex_en.pptx")), build("zh", path.join(OUT, "fig1-2A_apex_zh.pptx"))])
  .then((f) => console.log("wrote", f.join(", ")));
