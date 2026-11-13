// Fig. 2-1 variant A, evidence-progression layout: question + hypothesis -> parallel tasks -> evidence pooled ->
// rule comparison and independent tests -> expected understanding. Lavender monochrome, black lines, one font size.
//   node roadmap_a.js <out.pptx>
const { make, PAL } = require("./rm_lib");
const W = 5.906, H = 4.26, FS = 7.5;
const SG = 0.11;                                     // gap for the arrow between two steps
const { box, seg, frame, split, merge, write } = make(W, H, FS);
const L = PAL.lavender[0], M = 0.03, BH = 0.2;

// question and hypothesis side by side
const QW = 2.62, QH = 0.36, qx = [M, W - M - QW];
box(qx[0], M, QW, QH, "科学问题\n生长素信号的时间整合如何影响原基启动与叶序？", { fill: L, name: "question" });
box(qx[1], M, QW, QH, "待检验假设\n原基启动取决于细胞对生长素信号的时间整合", { name: "hypothesis" });
seg(qx[0] + QW, M + QH / 2, qx[1], M + QH / 2, true);

// a dashed block: header, then inner dashed frames each with a header and two steps; returns block bottom and the
// bottom centres of the last steps
function block(y, head, tasks) {
  const n = tasks.length, IG = 0.1, IW = (W - 2 * M - 0.12 - (n - 1) * IG) / n, ix0 = M + 0.06;
  const IFH = 0.04 + BH + SG + BH + SG + BH + 0.04, top = y + 0.05 + BH + 0.14, BHt = 0.05 + BH + 0.14 + IFH + 0.05;
  frame(M, y, W - 2 * M, BHt, null, { lw: 1.25, name: `block_${head}` });
  box(W / 2 - 0.8, y + 0.05, 1.6, BH, head, { fill: L });
  const cxs = tasks.map((_, k) => ix0 + k * (IW + IG) + IW / 2);
  split(W / 2, y + 0.05 + BH, cxs, top + 0.04);
  const ends = [];
  tasks.forEach(([h, a, b], k) => {
    const x = ix0 + k * (IW + IG), c = cxs[k];
    frame(x, top, IW, IFH, null, { lw: 0.75 });
    const hw = Math.min(IW - 0.3, 0.2 + h.length * 0.115), aw = Math.min(IW - 0.16, 0.2 + a.length * 0.11), bw = Math.min(IW - 0.16, 0.2 + b.length * 0.11);
    let yy = top + 0.04;
    box(c - hw / 2, yy, hw, BH, h, { fill: L }); yy += BH;
    seg(c, yy, c, yy + SG, true); yy += SG;
    box(c - aw / 2, yy, aw, BH, a); yy += BH;
    seg(c, yy, c, yy + SG, true); yy += SG;
    box(c - bw / 2, yy, bw, BH, b); yy += BH;
    ends.push([c, yy]);
  });
  return { bottom: y + BHt, ends };
}

let y = M + QH + 0.12;
merge([qx[0] + QW / 2, qx[1] + QW / 2], [M + QH, M + QH], W / 2, y, 0.5);
const b1 = block(y, "数据定量与模型建立", [
  ["成像定量", "以P0为参照对齐阶段", "估计细胞生长素轨迹"],
  ["运输模型", "纳入原基供给与中央差异", "按空间分布与极性筛选"],
  ["响应模型", "经报告信号换算", "对照DR5确定响应参数"],
]);
y = b1.bottom + 0.12;
merge(b1.ends.map((e) => e[0]), b1.ends.map((e) => e[1]), W / 2, y, 0.55);
box(W / 2 - 1.2, y, 2.4, 0.34, "证据汇聚\n运输与响应模型及参数范围", { fill: L, name: "pooled" });
y += 0.34;
seg(W / 2, y, W / 2, y + 0.12, true); y += 0.12;
const b2 = block(y, "规则比较与独立检验", [
  ["规则比较", "瞬时阈值与时间整合规则", "DR5延迟与平均发生间隔"],
  ["独立检验", "留出茎尖信号", "文献叶序统计"],
]);
y = b2.bottom + 0.12;
merge(b2.ends.map((e) => e[0]), b2.ends.map((e) => e[1]), W / 2, y, 0.55);
box(W / 2 - 1.45, y, 2.9, H - M - y, "预期认识\n明确时间整合影响叶序精度与稳健性的条件", { fill: L, name: "expected" });
console.log("expected box", y.toFixed(3), (H - M - y).toFixed(3));
write(process.argv[2] || "roadmap_a.pptx");
