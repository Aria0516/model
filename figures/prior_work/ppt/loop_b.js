// Fig. 1-2 B (regulatory loop) as an editable PowerPoint slide, English and Chinese.
// The slide is twice the panel size (6.34 x 5.6 in) with 14/12 pt text, so that it matches the
// 7/6 pt text of the other panels when placed at half size.
//   node loop_b.js <out_dir>
const pptxgen = require("pptxgenjs");
const path = require("path");

const W = 6.34, H = 5.6;
const INK = "1A1A1A", GREY = "8C8C8C", MUTED = "555555", LABEL = "333333";
const LW = 1.6;                                   // line width (pt) at slide scale
const BW = 0.235, BH = 0.12;                     // box size, fraction of the panel
const XL = 0.125, XM = 0.49, XR = 0.85;
const Y = [0.83, 0.65, 0.47, 0.29, 0.105];

const X = (u) => u * W;                           // panel coordinates (y up) -> inches (y down)
const Yi = (v) => (1 - v) * H;

const TEXT = {
  en: {
    src: [["Peripheral", {}], ["\n", {}], ["synthesis*", {}]],
    A: [[["Auxin ", {}], ["A", { italic: true }]], [["epidermis", {}]]],
    pin: [[["PIN1 polarity", {}]], [["up-gradient", {}]]],
    dr5: [[["DR5", { italic: true }], ["-like ", {}], ["R", { italic: true }]], [["passive read-out", {}]]],
    M: [[["Integration ", {}], ["M", { italic: true }]], [["leaky, ", {}], ["τ", { italic: true }], ["M", { italic: true, subscript: true }]]],
    inh: [[["Secondary", {}]], [["inhibition", {}]]],
    ini: [[["Initiation", {}]], [["M", { italic: true }], [" ≥ ", {}], ["θ", { italic: true }], [" in ring", {}]]],
    pri: [[["Primordium", {}]], [["placed object", {}]]],
    inner: [[["Inner layer*", {}]], [["vascular drainage", {}]]],
    edges: { inward: "inward*", polarizes: "polarizes", transport: "transport", places: "places", drains: "drains",
             sink: "sink", cue: "polarity\ncue", triggers: "triggers", raises: "raises θ" },
  },
  zh: {
    A: [[["生长素 ", {}], ["A", { italic: true }]], [["表皮层", {}]]],
    pin: [[["PIN1极性", {}]], [["朝高浓度", {}]]],
    dr5: [[["DR5", { italic: true }], ["样读出 ", {}], ["R", { italic: true }]], [["被动读出", {}]]],
    M: [[["时间整合 ", {}], ["M", { italic: true }]], [["泄漏积分，", {}], ["τ", { italic: true }], ["M", { italic: true, subscript: true }]]],
    inh: [[["次级", {}]], [["抑制", {}]]],
    ini: [[["原基启动", {}]], [["环内 ", {}], ["M", { italic: true }], [" ≥ ", {}], ["θ", { italic: true }]]],
    pri: [[["原基", {}]], [["放置的对象", {}]]],
    inner: [[["内层*", {}]], [["维管排出", {}]]],
    edges: { inward: "向内*", polarizes: "定极性", transport: "运输", places: "放置", drains: "排出",
             sink: "汇", cue: "极化\n线索", triggers: "触发", raises: "抬高θ" },
  },
};
TEXT.zh.src = [[["外围", {}]], [["合成*", {}]]];
TEXT.en.src = [[["Peripheral", {}]], [["synthesis*", {}]]];

// two-line node: first line title (14 pt), second line sub (12 pt); one-title nodes use 14 pt on both lines
function runs(lines, twoTitles) {
  const out = [];
  lines.forEach((line, i) => {
    line.forEach(([t, o], j) => {
      const size = i === 0 || twoTitles ? 14 : 12;
      const opt = Object.assign({ fontSize: size }, o);
      if (j === line.length - 1 && i < lines.length - 1) opt.breakLine = true;
      out.push({ text: t, options: opt });
    });
  });
  return out;
}

function build(lang, outFile) {
  const pres = new pptxgen();
  pres.defineLayout({ name: "PANEL", width: W, height: H });
  pres.layout = "PANEL";
  pres.title = lang === "zh" ? "图1-2 B 调控回路" : "Fig. 1-2 B regulatory loop";
  const s = pres.addSlide();
  const T = TEXT[lang];
  const font = "Times New Roman";

  const nodes = {
    src: [XL, Y[0], T.src, "solid", true], A: [XM, Y[0], T.A, "solid"], pin: [XR, Y[0], T.pin, "solid"],
    dr5: [XL, Y[1], T.dr5, "solid"], M: [XM, Y[1], T.M, "solid"],
    inh: [XL, Y[2], T.inh, "solid", true], ini: [XM, Y[2], T.ini, "solid"],
    pri: [XM, Y[3], T.pri, "dashed"], inner: [XM, Y[4], T.inner, "solid"],
  };
  for (const [key, [u, v, lines, style, twoTitles]] of Object.entries(nodes)) {
    const color = style === "grey" ? MUTED : INK;
    const r = runs(lines, twoTitles).map((x) => ({ text: x.text, options: Object.assign({ color }, x.options) }));
    s.addText(r, {
      x: X(u - BW / 2), y: Yi(v + BH / 2), w: X(BW), h: H * BH,
      shape: pres.ShapeType.roundRect, rectRadius: 0.09,
      fill: { color: style === "state" ? "E6E6E6" : "FFFFFF" },
      line: { color: style === "grey" ? GREY : INK, width: style === "state" ? 2.6 : LW,
              dashType: style === "dashed" ? "dash" : "solid" },
      fontFace: font, align: "center", valign: "middle", margin: 0, lineSpacingMultiple: 1.0,
      objectName: `node_${key}`,
    });
  }

  // a straight segment in panel coordinates; arrow at its end if requested
  function seg(u1, v1, u2, v2, o = {}) {
    const x1 = X(u1), y1 = Yi(v1), x2 = X(u2), y2 = Yi(v2);
    const line = { color: o.color || INK, width: o.width || LW };
    if (o.arrow) line.endArrowType = "triangle";
    if (o.dash) line.dashType = o.dash;
    s.addShape(pres.ShapeType.line, {
      x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
      flipH: x2 < x1, flipV: y2 < y1, line, objectName: o.name,
    });
  }
  function path(pts, o = {}) {                  // polyline, arrow on the last segment
    for (let k = 0; k < pts.length - 1; k++) {
      seg(pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1], Object.assign({}, o, { arrow: o.arrow && k === pts.length - 2 }));
    }
  }
  function inhibit(pts) {                       // polyline ending in a flat bar
    path(pts, {});
    const [u0, v0] = pts[pts.length - 2], [u1, v1] = pts[pts.length - 1];
    const dx = X(u1) - X(u0), dy = Yi(v1) - Yi(v0), n = Math.hypot(dx, dy);
    const px = (-dy / n) * 0.12, py = (dx / n) * 0.12;             // 0.12 in half-length
    const cx = X(u1), cy = Yi(v1);
    s.addShape(pres.ShapeType.line, {
      x: Math.min(cx - px, cx + px), y: Math.min(cy - py, cy + py), w: Math.abs(2 * px), h: Math.abs(2 * py),
      line: { color: INK, width: 2.6 },
    });
  }
  function label(u, v, text, align, valign) {    // small label anchored at (u, v)
    const w = 1.2, h = text.includes("\n") ? 0.5 : 0.3;
    let x = X(u), y = Yi(v);
    if (align === "center") x -= w / 2; else if (align === "right") x -= w;
    if (valign === "bottom") y -= h; else if (valign === "middle") y -= h / 2;
    s.addText(text, {
      x, y, w, h, fontFace: font, fontSize: 12, color: LABEL, align, valign: valign === "bottom" ? "bottom" : valign === "top" ? "top" : "middle",
      margin: 0, isTextBox: true, lineSpacingMultiple: 0.95,
    });
  }

  const L = (k) => nodes[k][0] - BW / 2, R = (k) => nodes[k][0] + BW / 2;
  const Tp = (k) => nodes[k][1] + BH / 2, B = (k) => nodes[k][1] - BH / 2, ny = (k) => nodes[k][1];
  const E = T.edges;

  // epidermal transport loop
  path([[R("src"), ny("src")], [L("A"), ny("A")]], { arrow: true });
  label((R("src") + L("A")) / 2, ny("A") + 0.012, E.inward, "center", "bottom");
  path([[R("A"), ny("A") + 0.03], [L("pin"), ny("pin") + 0.03]], { arrow: true });
  label((R("A") + L("pin")) / 2, ny("A") + 0.042, E.polarizes, "center", "bottom");
  path([[L("pin"), ny("pin") - 0.03], [R("A"), ny("A") - 0.03]], { arrow: true });
  label((R("A") + L("pin")) / 2, ny("A") - 0.042, E.transport, "center", "top");
  // main chain
  path([[XM, B("A")], [XM, Tp("M")]], { arrow: true });
  path([[XM, B("M")], [XM, Tp("ini")]], { arrow: true });
  path([[XM, B("ini")], [XM, Tp("pri")]], { arrow: true });
  label(XM + 0.015, (B("ini") + Tp("pri")) / 2, E.places, "left", "middle");
  path([[XM, B("pri")], [XM, Tp("inner")]], { arrow: true });
  label(XM + 0.015, (B("pri") + Tp("inner")) / 2, E.drains, "left", "middle");
  path([[L("M"), ny("M")], [R("dr5"), ny("dr5")]], { arrow: true, color: GREY, dash: "sysDot" });
  // primordium feedback
  inhibit([[R("pri"), ny("pri") - 0.03], [0.99, ny("pri") - 0.03], [0.99, 0.94], [XM, 0.94], [XM, Tp("A") + 0.016]]);
  label((XM + 0.99) / 2, 0.945, E.sink, "center", "bottom");
  path([[R("pri"), ny("pri") + 0.03], [XR, ny("pri") + 0.03], [XR, B("pin")]], { arrow: true });
  label(XR + 0.012, (B("pin") + ny("pri")) / 2, E.cue, "left", "middle");
  path([[L("pri"), ny("pri")], [XL, ny("pri")], [XL, B("inh")]], { arrow: true });
  label(XL + 0.012, (B("inh") + ny("pri")) / 2, E.triggers, "left", "middle");
  inhibit([[R("inh"), ny("inh")], [L("ini") - 0.014, ny("ini")]]);
  label((R("inh") + L("ini")) / 2, ny("ini") + 0.012, E.raises, "center", "bottom");

  return pres.writeFile({ fileName: outFile });
}

const out = process.argv[2] || ".";
Promise.all([build("en", path.join(out, "fig1-2B_loop_en.pptx")), build("zh", path.join(out, "fig1-2B_loop_zh.pptx"))])
  .then((f) => console.log("wrote", f.join(", ")));
