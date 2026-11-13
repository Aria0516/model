// Fig. 2-1 technical roadmap, layered layout (title -> starting point -> materials -> three research contents -> model),
// drawn at 15 cm wide as an editable PowerPoint slide (Chinese).
//   RH=3.82 node roadmap.js <out.pptx>   (RH: slide height in inches)
const pptxgen = require("pptxgenjs");

const W = 5.906, H = Number(process.env.RH || 4.0);  // inches
const INK = "1A1A1A", DASH = "8C8C8C";
const PINK = "FFD8D7", BLUE = "E2EBFF";
const FONT = "Times New Roman";                    // East Asian runs are set to 宋体 afterwards (fix_fonts.py)
const FS = 7.5, FS_H = 8, FS_T = 9.5, FS_C = 8.5;

const pres = new pptxgen();
pres.defineLayout({ name: "FIG", width: W, height: H });
pres.layout = "FIG";
pres.title = "图2-1 技术路线";
const s = pres.addSlide();

function box(x, y, w, h, runs, o = {}) {
  s.addText(runs, {
    x, y, w, h, fontFace: FONT, fontSize: o.fs || FS, bold: !!o.bold, color: INK, align: "center", valign: "middle",
    fill: { color: o.fill || BLUE }, line: { color: INK, width: 0.75 },
    margin: [1, 2, 1, 2], lineSpacingMultiple: 0.95, objectName: o.name,
  });
}
function seg(x1, y1, x2, y2, arrow) {
  const ln = { color: INK, width: 0.75 };
  if (arrow) ln.endArrowType = "triangle";
  s.addShape(pres.ShapeType.line, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.0001), h: Math.max(Math.abs(y2 - y1), 0.0001),
    flipH: x2 < x1, flipV: y2 < y1, line: ln,
  });
}
function rule(y) {                                   // dashed separator between layers
  s.addShape(pres.ShapeType.line, { x: 0.02, y, w: W - 0.04, h: 0.0001, line: { color: DASH, width: 0.75, dashType: "dash" } });
}
const lines = (...t) => t.map((x, i) => ({ text: x, options: i < t.length - 1 ? { breakLine: true } : {} }));

const M = 0.03, G = 0.2, CW = (W - 2 * M - 2 * G) / 3;
const cx = [0, 1, 2].map((k) => M + k * (CW + G) + CW / 2);
const CX = W / 2;

// title and starting point
let y = 0.03;
box(CX - 2.1, y, 4.2, 0.26, "拟南芥叶序形成中生长素时间整合的建模研究", { fs: FS_T, bold: true, fill: PINK, name: "title" });
y += 0.26;
seg(CX, y, CX, y + 0.15, true); y += 0.15;
box(CX - 1.85, y, 3.7, 0.34, lines("成像观测：原基处生长素输入逐步升高，DR5激活滞后近一个叶间期",
                                    "前期模拟：启动积分时间常数接近一个叶间期时，规则螺旋比例下降"), { name: "start" });
y += 0.34;
rule(y + 0.07);
seg(CX, y, CX, y + 0.15, true); y += 0.15;

// materials
box(CX - 0.55, y, 1.1, 0.2, "研究材料", { fs: FS_H, fill: PINK, name: "materials" });
y += 0.2;
const bus1 = y + 0.08;
seg(CX, y, CX, bus1); seg(cx[0], bus1, cx[2], bus1);
y += 0.17;
cx.forEach((c) => seg(c, bus1, c, y, true));
const MAT = [
  lines("茎尖成像数据：21个茎尖", "qDII与DR5时序，4个茎尖PIN1"),
  lines("前期模型：表皮层与内层", "生长素-PIN1模型及检验流程"),
  lines("文献叶序测量：成熟茎的", "发散角与发生顺序"),
];
MAT.forEach((t, k) => box(cx[k] - CW / 2, y, CW, 0.34, t, { name: `material_${k}` }));
y += 0.34;
rule(y + 0.08);
cx.forEach((c) => seg(c, y, c, y + 0.17, true));
y += 0.17;

// three research contents: heading -> approach -> result; each result also feeds the next content
const HEAD = ["茎尖成像数据的定量分析", "生长素-PIN1模型的建立与检验", "两类启动规则的比较与叶序预测"];   // = 研究内容（1）–（3）
const WAY = [
  lines("以P0为参照按叶间期对齐阶段，", "结合细胞移动估计生长素轨迹，", "定量PIN1极性、低生长素区", "与区域输入比值"),
  lines("纳入原基供给与中央、周边差异，", "参数抽样后按分布与极性筛选；", "将生长素轨迹输入响应模型，", "经报告信号换算对照DR5"),
  lines("相同设定下比较瞬时阈值与", "时间整合规则；留出茎尖检验", "DR5延迟激活与平均发生间隔，", "文献叶序检验发散角与发生顺序"),
];
const RES = [
  lines("生长素轨迹、DR5激活时序", "与空间分布"),
  lines("经数据约束的运输", "与响应模型"),
  lines("两类规则的解释力与出现差异的", "条件；处理后叶序的可检验预测"),
];
const HW = CW, WH = 0.53, RH = 0.34, AG = 0.14;
HEAD.forEach((t, k) => box(cx[k] - HW / 2, y, HW, 0.22, t, { fs: FS_H, fill: PINK, name: `content_${k}` }));
y += 0.22;
cx.forEach((c) => seg(c, y, c, y + AG, true));
y += AG;
const wy = y;
WAY.forEach((t, k) => box(cx[k] - CW / 2, y, CW, WH, t, { name: `approach_${k}` }));
y += WH;
cx.forEach((c) => seg(c, y, c, y + AG, true));
y += AG;
const ry = y;
RES.forEach((t, k) => box(cx[k] - CW / 2, y, CW, RH, t, { name: `result_${k}` }));
y += RH;
[0, 1].forEach((k) => {                              // result k -> approach k+1, along the gutter
  const x0 = cx[k] + CW / 2, gx = x0 + G / 2, x1 = cx[k + 1] - CW / 2;
  const y0 = ry + RH / 2, y1 = wy + WH / 2;
  seg(x0, y0, gx, y0); seg(gx, y0, gx, y1); seg(gx, y1, x1, y1, true);
});
rule(y + 0.08);

// model
const bus2 = y + 0.12;
cx.forEach((c) => seg(c, y, c, bus2));
seg(cx[0], bus2, cx[2], bus2);
y = bus2 + 0.13;
seg(CX, bus2, CX, y, true);
box(M, y, W - 2 * M, H - 0.03 - y, lines("构建经成像数据约束的“生长素输入 → 时间整合 → 原基启动 → 叶序形成”生长素-PIN1模型",
                                         "明确时间整合在何种条件下影响原基启动时序、叶序精度与稳健性"),
    { fs: FS_C, bold: true, fill: PINK, name: "model" });
console.log("bottom box top", y.toFixed(3), "height", (H - 0.03 - y).toFixed(3));

pres.writeFile({ fileName: process.argv[2] || "roadmap2.pptx" }).then((f) => console.log("wrote", f));
