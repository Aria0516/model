// Fig. 2-1 technical roadmap as an editable PowerPoint slide (Chinese), drawn at its printed size (15 cm wide).
// Topic -> three stage sub-problems; parallel tracks inside each stage; each stage's result feeds the next -> one conclusion.
//   node roadmap.js <out.pptx>
const pptxgen = require("pptxgenjs");

const W = 5.906, H = 3.13;                        // inches (15 cm wide)
const INK = "1A1A1A", FRAME = "44546A", RES = "2F5597";   // text/lines, stage frame border, result text
const FONT = "Times New Roman";                  // East Asian runs are set to 宋体 afterwards (fix_fonts.py)
const FS = 7.5, FS_H = 8.5, FS_T = 9.5;
const TINT = ["FEE8D6", "C8E5B2", "B6C7EA"];        // stage frames
const FILL = ["FFF0CB", "E3F3D9", "D9E5F1"];        // boxes inside each stage
const TOP = "D2F5F0", BOTTOM = "FADCDF";

const pres = new pptxgen();
pres.defineLayout({ name: "FIG", width: W, height: H });
pres.layout = "FIG";
pres.title = "图2-1 技术路线";
const s = pres.addSlide();

function box(x, y, w, h, runs, o = {}) {
  s.addText(runs, {
    x, y, w, h, shape: o.round ? pres.ShapeType.roundRect : undefined, rectRadius: o.round, fontFace: FONT, fontSize: o.fs || FS, bold: !!o.bold, color: o.color || INK, align: "center", valign: "middle",
    fill: o.fill ? { color: o.fill, transparency: o.transp || 0 } : undefined,
    line: o.noline ? { type: "none" } : { color: o.lc || INK, width: o.lw || 0.75, dashType: o.dash || "solid" },
    margin: [1, 1.5, 1, 1.5], lineSpacingMultiple: 0.95, objectName: o.name,
  });
}
function seg(x1, y1, x2, y2, arrow, lw) {
  const ln = { color: INK, width: lw || 0.75 };
  if (arrow) ln.endArrowType = "triangle";
  s.addShape(pres.ShapeType.line, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.0001), h: Math.max(Math.abs(y2 - y1), 0.0001),
    flipH: x2 < x1, flipV: y2 < y1, line: ln,
  });
}
// one parent (bottom centre px, py) to several children (centres xs, top cy): plain tree, as a problem is broken down
function split(px, py, xs, cy) {
  const by = py + (cy - py) / 2;
  seg(px, py, px, by);
  seg(Math.min(...xs, px), by, Math.max(...xs, px), by);
  xs.forEach((x) => seg(x, by, x, cy));
}
// several children (centres xs, bottom ys) to one parent (centre px, top py)
function merge(xs, ys, px, py) {
  const by = py - (py - Math.max(...ys)) / 2;
  xs.forEach((x, i) => seg(x, ys[i], x, by));
  seg(Math.min(...xs, px), by, Math.max(...xs, px), by);
  seg(px, by, px, py, true);
}
function chain(x, y, w, texts, h, gap, fill) {    // vertical chain of boxes; returns bottom y
  texts.forEach((t, j) => {
    if (j > 0) { seg(x + w / 2, y, x + w / 2, y + gap, true); y += gap; }
    box(x, y, w, h, t, { fill });
    y += h;
  });
  return y;
}

const M = 0.03, BH = 0.28, TG = 0.14;              // margin, box height, gap of a split/merge
const FS_Q = 8;                                    // stage sub-problem boxes
box(M, 0.03, W - 2 * M, 0.25, "生长素信号时间整合对原基启动与叶序的影响", { fs: FS_T, bold: true, fill: TOP, name: "topic" });

const GAP = 0.18, FW = (W - 2 * M - 2 * GAP) / 3, FY = 0.43;
const HH = 0.25, IN = FY + 0.2;                   // sub-problem box height and top
const BODY = HH + TG + BH + TG + BH + TG + BH + TG + BH;
const FH = 0.2 + BODY + 0.06;
const OY = IN + BODY - HH;                         // row of the stage results (stages 1 and 2)
const fx = [M, M + FW + GAP, M + 2 * (FW + GAP)];
const PAD = 0.05, TS = 0.06;                       // frame inner padding, space between two tracks
split(W / 2, 0.28, fx.map((x) => x + FW / 2), FY);

// frame: tinted stage band with "stage: approach" on top and the stage's sub-problem in the white box
function frame(k, name, problem) {
  const x = fx[k];
  box(x, FY, FW, FH, "", { fill: TINT[k], lc: FRAME, lw: 0.9, dash: "dash", round: 0.08, name: `frame_${k}` });
  box(x, FY + 0.02, FW, 0.17, name, { fs: FS_H, bold: true, noline: true });
  box(x + PAD, IN, FW - 2 * PAD, HH, problem, { fs: FS_Q, fill: FILL[k], name: `problem_${k}` });
  const hx = x + PAD, hw = FW - 2 * PAD, tw = (hw - TS) / 2;
  return { cx: x + FW / 2, hx, hw, tw, tx: [hx, hx + tw + TS], mids: [hx + tw / 2, hx + tw + TS + tw / 2] };
}
const ty = IN + HH + TG;                           // top of the first row of track boxes
const AG = (OY - TG - ty - 3 * BH) / 2;           // arrow gap inside a three-step track

// stage 1: time course (left) and two parallel imaging measurements (right, grouped, no arrows between them)
{
  const f = frame(0, "第一阶段：成像定量", "原基生长素输入与DR5响应时序");
  split(f.cx, IN + HH, f.mids, ty);
  const b0 = chain(f.tx[0], ty, f.tw, ["以P0为参照\n按叶间期对齐", "输入升高与\nDR5激活先后", "结合细胞移动\n估计生长素轨迹"], BH, AG, FILL[0]);
  const gh = b0 - ty, gx = f.tx[1];
  box(gx, ty, f.tw, gh, "", { lc: FRAME, lw: 0.6, dash: "sysDash", name: "imaging_group" });
  const ih = (gh - 0.04 * 2 - 0.08) / 2;
  box(gx + 0.04, ty + 0.04, f.tw - 0.08, ih, "PIN1成像\n极性方向", { fill: FILL[0] });
  box(gx + 0.04, ty + 0.04 + ih + 0.08, f.tw - 0.08, ih, "qDII成像\n低生长素区与\n区域输入比值", { fill: FILL[0] });
  merge(f.mids, [b0, b0], f.cx, OY);
  box(f.hx, OY, f.hw, HH, "生长素轨迹、DR5时序与空间分布", { color: RES, fill: FILL[0], name: "result_0" });
}

// stage 2: transport model (left) and response model (right)
{
  const f = frame(1, "第二阶段：机制建模", "空间分布与响应延迟的形成机制");
  split(f.cx, IN + HH, f.mids, ty);
  const b = [chain(f.tx[0], ty, f.tw, ["纳入原基供给与\n中央周边差异", "参数抽样，按\n分布与极性筛选", "再现生长素\n输入分布"], BH, AG, FILL[1]),
             chain(f.tx[1], ty, f.tw, ["细胞生长素轨迹\n输入响应模型", "经报告信号换算\n对照DR5变化", "确定响应参数"], BH, AG, FILL[1])];
  merge(f.mids, b, f.cx, OY);
  box(f.hx, OY, f.hw, HH, "经数据约束的运输与响应模型", { color: RES, fill: FILL[1], name: "result_1" });
}

// stage 3: both rules go through both tests -> judgement -> predictions that follow from it
{
  const f = frame(2, "第三阶段：规则检验", "时间整合对启动与叶序的作用");
  let y = ty;
  split(f.cx, IN + HH, f.mids, y);
  const RB = 0.2, TB = 2 * BH - RB;                // one-line rule boxes, three-line test boxes
  box(f.tx[0], y, f.tw, RB, "瞬时阈值规则", { fill: FILL[2] });
  box(f.tx[1], y, f.tw, RB, "时间整合规则", { fill: FILL[2] });
  const by = y + RB + TG / 2;                      // both rules go through both tests
  f.mids.forEach((m) => seg(m, y + RB, m, by));
  seg(f.mids[0], by, f.mids[1], by);
  y += RB + TG;
  f.mids.forEach((m) => seg(m, by, m, y, true));
  box(f.tx[0], y, f.tw, TB, "留出茎尖检验：\nDR5延迟激活与\n平均发生间隔", { fill: FILL[2] });
  box(f.tx[1], y, f.tw, TB, "文献叶序检验：\n发散角变异与\n发生顺序", { fill: FILL[2] });
  merge(f.mids, [y + TB, y + TB], f.cx, y + TB + TG);
  y += TB + TG;
  box(f.hx, y, f.hw, BH, "两类规则对观测的解释力\n及预测出现差异的条件", { color: RES, fill: FILL[2], name: "result_2" });
  seg(f.cx, y + BH, f.cx, y + BH + TG, true);
  y += BH + TG;
  box(f.hx, y, f.hw, BH, "可检验预测：改变处理时长、\n抑制极性运输后的叶序", { color: RES, fill: FILL[2], dash: "dash", name: "predictions" });
}

// links between stages: each stage's result goes along the gutter into the next stage's sub-problem box
[0, 1].forEach((k) => {
  const x0 = fx[k] + FW - PAD, gx = fx[k] + FW + GAP / 2, x1 = fx[k + 1] + PAD;
  const y0 = OY + HH / 2, y1 = IN + HH / 2;
  seg(x0, y0, gx, y0, false, 1.0);
  seg(gx, y0, gx, y1, false, 1.0);
  seg(gx, y1, x1, y1, true, 1.0);
});

// conclusion
const fb = FY + FH, RY = fb + 0.15;
merge(fx.map((x) => x + FW / 2), [fb, fb, fb], W / 2, RY);
box(M, RY, W - 2 * M, H - RY - 0.03, [
  { text: "建立经成像数据约束的生长素-PIN1叶序模型，", options: { breakLine: true } },
  { text: "明确时间整合在何种条件下影响原基启动时序、叶序精度与稳健性", options: {} },
], { fs: FS_H, bold: true, fill: BOTTOM, name: "conclusion" });

pres.writeFile({ fileName: process.argv[2] || "roadmap.pptx" }).then((f) => console.log("wrote", f));
