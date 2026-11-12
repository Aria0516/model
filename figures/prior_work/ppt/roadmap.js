// Fig. 2-1 technical roadmap as an editable PowerPoint slide (Chinese), drawn at its printed size (15 cm wide).
// Topic -> three stages; inside each stage parallel tracks that merge -> one conclusion.
//   node roadmap.js <out.pptx>
const pptxgen = require("pptxgenjs");

const W = 5.906, H = 3.13;                        // inches (15 cm wide)
const INK = "1A1A1A", FRAME = "7F7F7F";
const FONT = "Times New Roman";                  // East Asian runs are set to 宋体 afterwards (fix_fonts.py)
const FS = 7.5, FS_H = 8.5, FS_T = 9.5;
const TINT = ["FCE9D9", "E2EFDA", "DCE6F2"], TOP = "DDF0EE", BOTTOM = "F9DEDC";

const pres = new pptxgen();
pres.defineLayout({ name: "FIG", width: W, height: H });
pres.layout = "FIG";
pres.title = "图2-1 技术路线";
const s = pres.addSlide();

function box(x, y, w, h, runs, o = {}) {
  s.addText(runs, {
    x, y, w, h, fontFace: FONT, fontSize: o.fs || FS, bold: !!o.bold, color: INK, align: "center", valign: "middle",
    fill: o.fill ? { color: o.fill } : undefined,
    line: o.noline ? { type: "none" } : { color: o.lc || INK, width: o.lw || 0.6, dashType: o.dash || "solid" },
    margin: [1, 1.5, 1, 1.5], lineSpacingMultiple: 0.95, objectName: o.name,
  });
}
function seg(x1, y1, x2, y2, arrow) {
  const ln = { color: INK, width: 0.7 };
  if (arrow) ln.endArrowType = "triangle";
  s.addShape(pres.ShapeType.line, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.0001), h: Math.max(Math.abs(y2 - y1), 0.0001),
    flipH: x2 < x1, flipV: y2 < y1, line: ln,
  });
}
// one parent (bottom centre px, py) to several children (centres xs, top cy): tree with arrows
function split(px, py, xs, cy) {
  const by = py + (cy - py) / 2;
  seg(px, py, px, by);
  seg(Math.min(...xs, px), by, Math.max(...xs, px), by);
  xs.forEach((x) => seg(x, by, x, cy, true));
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
box(M, 0.03, W - 2 * M, 0.25, "生长素信号时间整合对原基启动与叶序的影响", { fs: FS_T, bold: true, fill: TOP, lw: 0.9, name: "topic" });

const GAP = 0.12, FW = (W - 2 * M - 2 * GAP) / 3, FY = 0.43;
const HH = 0.25, IN = FY + 0.2;                   // stage theme box height and top
const BODY = HH + TG + BH + TG + BH + TG + BH + TG + BH;   // stage 3 is the tallest column
const FH = 0.2 + BODY + 0.06;
const fx = [M, M + FW + GAP, M + 2 * (FW + GAP)];
split(W / 2, 0.28, fx.map((x) => x + FW / 2), FY);

function frame(k, name, head) {
  const x = fx[k];
  box(x, FY, FW, FH, "", { fill: TINT[k], lc: FRAME, dash: "dash", name: `frame_${k}` });
  box(x, FY + 0.02, FW, 0.17, name, { fs: FS_H, bold: true, noline: true });
  box(x + 0.07, IN, FW - 0.14, HH, head, { fs: FS_H, bold: true, fill: "FFFFFF", lw: 0.8 });
  const hx = x + 0.07, hw = FW - 0.14, tw = (hw - 0.08) / 2;
  return { cx: x + FW / 2, hx, hw, tw, tx: [hx, hx + tw + 0.08] };
}

// stages 1 and 2: two parallel tracks of three steps that merge into the stage's result
const stages = [
  { name: "第一阶段", head: "茎尖生长素与DR5动态定量",
    tracks: [["以P0为参照\n划分原基阶段", "各阶段按叶间期\n排在同一时间轴", "DR5激活时序与\n细胞生长素轨迹"],
             ["提取PIN1极性", "定量原基周围\n低生长素区", "中央区与发生环\n生长素比值"]],
    out: "生长素轨迹、DR5时序与空间分布" },
  { name: "第二阶段", head: "生长素运输与细胞响应建模",
    tracks: [["纳入原基供给与\n中央周边差异", "参数抽样，按\n空间分布筛选", "再现生长素\n输入分布"],
             ["细胞生长素轨迹\n输入响应模型", "经报告信号换算\n对照DR5变化", "确定响应参数"]],
    out: "经数据约束的运输与响应模型" },
];
stages.forEach((st, k) => {
  const f = frame(k, st.name, st.head);
  const ty = IN + HH + TG, oy = IN + BODY - HH;    // result box sits on the frame's last row
  const ag = (oy - TG - ty - 3 * BH) / 2;
  split(f.cx, IN + HH, f.tx.map((t) => t + f.tw / 2), ty);
  const bottoms = st.tracks.map((tr, j) => chain(f.tx[j], ty, f.tw, tr, BH, ag, "FFFFFF"));
  merge(f.tx.map((t) => t + f.tw / 2), bottoms, f.cx, oy);
  box(f.hx, oy, f.hw, HH, st.out, { bold: true, fill: "FFFFFF", lw: 0.8 });
});

// stage 3: two rules in parallel -> comparison -> two tests in parallel -> prediction
{
  const f = frame(2, "第三阶段", "启动规则比较与叶序预测");
  const mids = f.tx.map((t) => t + f.tw / 2);
  let y = IN + HH + TG;
  split(f.cx, IN + HH, mids, y);
  box(f.tx[0], y, f.tw, BH, "瞬时阈值启动", { fill: "FFFFFF" });
  box(f.tx[1], y, f.tw, BH, "时间整合启动", { fill: "FFFFFF" });
  merge(mids, [y + BH, y + BH], f.cx, y + BH + TG);
  y += BH + TG;
  box(f.hx, y, f.hw, BH, "比较DR5延迟、发生间隔、\n发散角变异与发生顺序", { fill: "FFFFFF" });
  split(f.cx, y + BH, mids, y + BH + TG);
  y += BH + TG;
  box(f.tx[0], y, f.tw, BH, "按批次留出的\n茎尖信号检验", { fill: "FFFFFF" });
  box(f.tx[1], y, f.tw, BH, "文献成熟茎\n叶序测量检验", { fill: "FFFFFF" });
  merge(mids, [y + BH, y + BH], f.cx, y + BH + TG);
  y += BH + TG;
  box(f.hx, y, f.hw, BH, "预测改变处理时长、抑制\n极性运输后的叶序变化", { bold: true, fill: "FFFFFF", lw: 0.8 });
}

// conclusion
const fb = FY + FH, RY = fb + 0.15;
merge(fx.map((x) => x + FW / 2), [fb, fb, fb], W / 2, RY);
box(M, RY, W - 2 * M, H - RY - 0.03, [
  { text: "建立经成像数据约束的生长素-PIN1叶序模型，", options: { breakLine: true } },
  { text: "阐明时间整合对原基启动时序及叶序精度与稳健性的作用", options: {} },
], { fs: FS_H, bold: true, fill: BOTTOM, lw: 0.9, name: "conclusion" });

pres.writeFile({ fileName: process.argv[2] || "roadmap.pptx" }).then((f) => console.log("wrote", f));
