// Fig. 2-1 technical roadmap, three columns: scientific question -> three stages (sub-problem, parallel tracks, result;
// each result feeds the next stage) -> answer. Drawn 15 cm wide as an editable PowerPoint slide (Chinese).
//   node roadmap.js <out.pptx>
const pptxgen = require("pptxgenjs");

const W = 5.906, H = 3.84;                          // inches
const INK = "1A1A1A", FRAME = "7F7F7F";
const FONT = "Times New Roman";                     // East Asian runs are set to 宋体 afterwards (fix_fonts.py)
const FS = 7.5, FS_L = 8.5, FS_Q = 8, FS_T = 9.5;
const TINT = ["FCE9D9", "E2EFDA", "DCE6F2"], TOP = "DDF0EE", BOTTOM = "F9DEDC";

const pres = new pptxgen();
pres.defineLayout({ name: "FIG", width: W, height: H });
pres.layout = "FIG";
pres.title = "图2-1 技术路线";
const s = pres.addSlide();

function box(x, y, w, h, text, o = {}) {
  s.addText(text, {
    x, y, w, h, fontFace: FONT, fontSize: o.fs || FS, bold: !!o.bold, color: INK, align: "center", valign: "middle",
    fill: o.fill === null ? undefined : { color: o.fill || "FFFFFF" },
    line: o.noline ? { type: "none" } : { color: o.lc || INK, width: o.lw || 0.5, dashType: o.dash || "solid" },
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
const split = (px, py, xs, cy, arrow) => {          // parent (centre px, bottom py) -> children tops at cy (number or list)
  const cys = Array.isArray(cy) ? cy : xs.map(() => cy);
  const by = py + (Math.min(...cys) - py) * (arrow ? 0.3 : 0.5);   // bus nearer the parent: arrows stay long
  seg(px, py, px, by); seg(Math.min(...xs, px), by, Math.max(...xs, px), by);
  xs.forEach((x, i) => seg(x, by, x, cys[i], arrow));
};
const merge = (xs, ys, px, py) => {                 // children bottoms -> parent top; bus nearer the children
  const by = Math.max(...ys) + (py - Math.max(...ys)) * 0.3;
  xs.forEach((x, i) => seg(x, ys[i], x, by));
  seg(Math.min(...xs, px), by, Math.max(...xs, px), by); seg(px, by, px, py, true);
};
const chain = (x, y, w, texts, h, gap) => {         // vertical chain of steps; returns the bottom
  texts.forEach((t, j) => {
    if (j > 0) { seg(x + w / 2, y, x + w / 2, y + gap, true); y += gap; }
    box(x, y, w, h, t); y += h;
  });
  return y;
};

const M = 0.03, BH = 0.28, TG = 0.17, PAD = 0.05, TS = 0.15;
box(M, 0.03, W - 2 * M, 0.26, "在拟南芥茎尖中，细胞对生长素信号的时间整合如何影响原基启动与叶序形成？",
    { fs: FS_T, bold: true, fill: TOP, lw: 0.9, name: "question" });

const GAP = 0.18, FW = (W - 2 * M - 2 * GAP) / 3, FY = 0.42;
const HH = 0.34, IN = FY + 0.21, RB = 0.2, NB = 0.3, TB = 0.38, RH = 0.28;   // sub-problem, rule, common, test, result
const BODY = HH + 5 * TG + RB + NB + TB + RH + RH;   // stage 3 is the tallest column
const FH = 0.21 + BODY + 0.06, OY = IN + BODY - RH;
const fx = [M, M + FW + GAP, M + 2 * (FW + GAP)];
split(W / 2, 0.29, fx.map((x) => x + FW / 2), FY);

function frame(k, label, problem) {
  const x = fx[k];
  box(x, FY, FW, FH, "", { fill: TINT[k], lc: FRAME, lw: 0.75, dash: "dash", name: `frame_${k}` });
  box(x, FY + 0.02, FW, 0.17, label, { fs: FS_L, noline: true, fill: null });
  box(x + PAD, IN, FW - 2 * PAD, HH, problem, { fs: FS_Q, bold: true, lw: 0.75, name: `problem_${k}` });
  const hx = x + PAD, hw = FW - 2 * PAD, tw = (hw - TS) / 2;
  return { cx: x + FW / 2, hx, hw, tw, tx: [hx, hx + tw + TS], mids: [hx + tw / 2, hx + tw + TS + tw / 2] };
}
const ty = IN + HH + TG;                            // first row of track boxes (stages 1, 2)
const AG = (OY - TG - ty - 4 * BH) / 3;             // arrow gap in a four-step track

// stage 1: time course (left), two parallel imaging measurements on one card (right)
{
  const f = frame(0, "第一阶段：成像定量", "茎尖生长素输入的时空分布\n与DR5响应时序");
  const b = chain(f.tx[0], ty, f.tw, ["以P0为参照\n按叶间期对齐", "输入升高与\nDR5激活先后", "估计细胞移动", "外推细胞\n生长素轨迹"], BH, AG);
  // two parallel measurements on one snug card; the arrows meet the card, not the boxes
  const CP = 0.05, P1 = 0.34, P2 = 0.46, PG = 0.09, ch = CP + P1 + PG + P2 + CP, cy = ty + (b - ty - ch) / 2;
  split(f.cx, IN + HH, f.mids, [ty, cy], true);
  box(f.tx[1], cy, f.tw, ch, "", { fill: "F6D5BC", noline: true, name: "imaging_card" });
  box(f.tx[1] + 0.045, cy + CP, f.tw - 0.09, P1, "PIN1成像：\n极性方向");
  box(f.tx[1] + 0.045, cy + CP + P1 + PG, f.tw - 0.09, P2, "qDII成像：\n低生长素区及\n区域输入比值");
  merge(f.mids, [b, cy + ch], f.cx, OY);
  box(f.hx, OY, f.hw, RH, "生长素轨迹、DR5时序与空间分布", { lw: 0.75, name: "result_0" });
}

// stage 2: transport model (left) first; once it reproduces the input distribution the response parameters are fixed
{
  const f = frame(1, "第二阶段：机制建模", "空间分布与响应延迟\n的形成机制");
  split(f.cx, IN + HH, f.mids, ty, true);
  const bl = chain(f.tx[0], ty, f.tw, ["扩展已有表皮层\n与内层运输模型", "纳入原基对\n生长素的供给", "参数抽样，按\n分布与极性筛选", "再现生长素\n输入分布"], BH, AG);
  const br = chain(f.tx[1], ty, f.tw, ["细胞生长素轨迹\n输入响应模型", "区分中央与\n周边的响应", "经报告信号换算\n对照DR5变化", "确定响应参数"], BH, AG);
  seg(f.tx[0] + f.tw, bl - BH / 2, f.tx[1], bl - BH / 2, true);   // transport reproduces input -> response fixed
  merge(f.mids, [bl, br], f.cx, OY);
  box(f.hx, OY, f.hw, RH, "运输与响应模型\n及参数取值范围", { lw: 0.75, name: "result_1" });
}

// stage 3: both rules -> one common setting -> both tests -> result -> predictions that follow from it
{
  const f = frame(2, "第三阶段：规则检验", "时间整合对原基启动\n与叶序的作用");
  let y = ty;
  split(f.cx, IN + HH, f.mids, y, true);
  box(f.tx[0], y, f.tw, RB, "瞬时阈值规则");
  box(f.tx[1], y, f.tw, RB, "时间整合规则");
  merge(f.mids, [y + RB, y + RB], f.cx, y + RB + TG);
  y += RB + TG;
  box(f.hx, y, f.hw, NB, "相同运输、生长与\n信号换算设定下比较", { name: "common_setting" });
  split(f.cx, y + NB, f.mids, y + NB + TG, true);
  y += NB + TG;
  box(f.tx[0], y, f.tw, TB, "留出茎尖信号：\nDR5延迟、\n平均发生间隔");
  box(f.tx[1], y, f.tw, TB, "成熟茎叶序：\n发散角变异、\n发生顺序");
  merge(f.mids, [y + TB, y + TB], f.cx, y + TB + TG);
  y += TB + TG;
  box(f.hx, y, f.hw, RH, "两类规则的解释力\n及其预测出现差异的条件", { lw: 0.75, name: "result_2" });
  seg(f.cx, y + RH, f.cx, y + RH + TG, true);
  y += RH + TG;
  box(f.hx, y, f.hw, RH, "可检验预测：改变处理时长、\n抑制极性运输后的叶序", { dash: "dash", name: "predictions" });
}

// each stage's result goes along the gutter into the next stage's sub-problem
[0, 1].forEach((k) => {
  const x0 = fx[k] + FW - PAD, gx = fx[k] + FW + GAP / 2, x1 = fx[k + 1] + PAD;
  const y0 = OY + RH / 2, y1 = IN + HH / 2;
  seg(x0, y0, gx, y0, false, 1.0); seg(gx, y0, gx, y1, false, 1.0); seg(gx, y1, x1, y1, true, 1.0);
});

// the model obtained (cell response left open: threshold or integration) and the answer to the question on top
const fb = FY + FH, RY = fb + 0.17;
merge(fx.map((x) => x + FW / 2), [fb, fb, fb], W / 2, RY);
box(M, RY, W - 2 * M, H - RY - 0.03, "构建“生长素输入 → 细胞响应 → 原基启动 → 叶序形成”的生长素-PIN1模型\n明确生长素信号的时间整合在何种条件下影响原基启动时序、叶序精度与稳健性",
    { fs: FS_L, bold: true, fill: BOTTOM, lw: 0.9, name: "answer" });
console.log("answer box", RY.toFixed(3), (H - RY - 0.03).toFixed(3), "AG", AG.toFixed(3));
pres.writeFile({ fileName: process.argv[2] || "roadmap4.pptx" }).then((f) => console.log("wrote", f));
