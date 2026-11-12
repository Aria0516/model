// Fig. 2-1 technical roadmap as an editable PowerPoint slide (Chinese), drawn at its printed size (13.5 cm wide).
// Scientific question -> three modules (1 -> 2 -> 3, matching research contents (1)-(3)) -> expected model and its use.
//   node roadmap.js <out.pptx>
const pptxgen = require("pptxgenjs");

const W = 5.315, H = 3.0;                        // inches (13.5 cm wide)
const INK = "1A1A1A", FRAME = "7F7F7F";
const FONT = "Times New Roman";                  // East Asian runs are set to 宋体 afterwards (fix_fonts.py)
const FS = 8, FS_H = 8.5, FS_Q = 9.5;
const TINT = ["FCE9D9", "E2EFDA", "DCE6F2"], TOP = "DDF0EE", BOTTOM = "F9DEDC";

const pres = new pptxgen();
pres.defineLayout({ name: "FIG", width: W, height: H });
pres.layout = "FIG";
pres.title = "图2-1 技术路线";
const s = pres.addSlide();

function text(x, y, w, h, runs, o = {}) {
  s.addText(runs, {
    x, y, w, h, fontFace: FONT, fontSize: o.fs || FS, bold: !!o.bold, color: INK, align: o.align || "center",
    valign: "middle", fill: o.fill ? { color: o.fill } : undefined,
    line: o.noline ? { type: "none" } : { color: o.lc || INK, width: o.lw || 0.75, dashType: o.dash || "solid" },
    margin: [1, 2, 1, 2], lineSpacingMultiple: 1.0, objectName: o.name,
  });
}
function seg(x1, y1, x2, y2, name, arrow) {
  const ln = { color: INK, width: 0.8 };
  if (arrow) ln.endArrowType = "triangle";
  s.addShape(pres.ShapeType.line, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.0001), h: Math.max(Math.abs(y2 - y1), 0.0001),
    flipH: x2 < x1, flipV: y2 < y1, line: ln, objectName: name,
  });
}

// top: scientific question
const M = 0.03;
text(M, 0.03, W - 2 * M, 0.3, "生长素信号时间整合对原基启动与叶序的影响",
  { fs: FS_Q, bold: true, fill: TOP, lw: 1.0, name: "question" });

// three module frames
const GAP = 0.15, FW = (W - 2 * M - 2 * GAP) / 3, FY = 0.5, FH = 1.98;
const fx = [M, M + FW + GAP, M + 2 * (FW + GAP)];
const modules = [
  { head: "第一阶段", q: "茎尖生长素与DR5动态定量",
    steps: ["原基阶段划分", "按叶间期排列时间轴", "生长素轨迹与DR5时序"] },
  { head: "第二阶段", q: "生长素运输与细胞响应建模",
    steps: ["运输模型：原基供给、中央与周边差异", "参数抽样，按实测分布筛选", "响应模型：拟合DR5时序"] },
  { head: "第三阶段", q: "启动规则比较与叶序预测",
    steps: ["比较瞬时阈值与时间整合", "留出数据与叶序统计检验", "预测改变生长素处理时长与抑制极性运输后的叶序"] },
];
// tree from the question to the three frames
const qy = 0.33, tyBus = qy + 0.08;
seg(W / 2, qy, W / 2, tyBus, "tree_top");
seg(fx[0] + FW / 2, tyBus, fx[2] + FW / 2, tyBus, "tree_bus");
modules.forEach((m, k) => {
  const x = fx[k], cx = x + FW / 2;
  seg(cx, tyBus, cx, FY, `tree_${k}`, true);
  text(x, FY, FW, FH, "", { fill: TINT[k], lc: FRAME, dash: "dash", lw: 0.75, name: `frame_${k}` });
  text(x, FY + 0.02, FW, 0.2, m.head, { fs: FS_H, bold: true, noline: true, name: `head_${k}` });
  const bx = x + 0.08, bw = FW - 0.16;
  let y = FY + 0.25;
  text(bx, y, bw, 0.28, m.q, { fs: FS, bold: true, fill: "FFFFFF", lw: 0.9, name: `q_${k}` });
  y += 0.28;
  m.steps.forEach((t, j) => {
    seg(cx, y, cx, y + 0.1, `arr_${k}_${j}`, true);
    y += 0.1;
    text(bx, y, bw, 0.35, t, { fill: "FFFFFF", name: `step_${k}_${j}` });
    y += 0.35;
  });
});

// bottom: converge to the expected model and its use
const by = FY + FH, bus2 = by + 0.08, BY = bus2 + 0.08;
modules.forEach((m, k) => seg(fx[k] + FW / 2, by, fx[k] + FW / 2, bus2, `down_${k}`));
seg(fx[0] + FW / 2, bus2, fx[2] + FW / 2, bus2, "bottom_bus");
seg(W / 2, bus2, W / 2, BY, "to_result", true);
text(M, BY, W - 2 * M, H - BY - 0.03, [
  { text: "建立经成像数据约束的生长素-PIN1叶序模型，", options: { breakLine: true } },
  { text: "阐明时间整合对原基启动时序及叶序精度与稳健性的作用", options: {} },
], { fs: FS_H, bold: true, fill: BOTTOM, lw: 1.0, name: "result" });

pres.writeFile({ fileName: process.argv[2] || "roadmap.pptx" }).then((f) => console.log("wrote", f));
