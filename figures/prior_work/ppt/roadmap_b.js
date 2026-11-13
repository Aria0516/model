// Fig. 2-1 variant B, goal-progression layout: inputs -> three stages headed by goal phrases (grey with pink/green
// parallel tracks, blue with model <-> data feedback, orange) -> research goal (purple). Black lines, one font size.
//   node roadmap_b.js <out.pptx>
const { make, PAL } = require("./rm_lib");
const W = 5.906, H = 4.32, FS = 7.5;
const { box, seg, frame, plus, split, merge, write } = make(W, H, FS);
const M = 0.03, BH = 0.2, CX = W / 2;
const bw = (t) => 0.22 + t.length * 0.108;          // box width that fits a one-line label

// inputs
const IN = ["茎尖成像数据", "前期生长素-PIN1模型"], iw = IN.map(bw), IG = 0.42;
const ifw = iw[0] + iw[1] + IG + 0.16, ifx = CX - ifw / 2;
frame(ifx, M, ifw, BH + 0.1, PAL.grey[0], { lw: 1.0 });
const ix = [ifx + 0.08, ifx + 0.08 + iw[0] + IG];
IN.forEach((t, k) => box(ix[k], M + 0.05, iw[k], BH, t));
plus(ix[0] + iw[0] + IG / 2, M + 0.05 + BH / 2, 0.2);
let y = M + BH + 0.1;
merge([ix[0] + iw[0] / 2, ix[1] + iw[1] / 2], [M + 0.05 + BH, M + 0.05 + BH], CX, y + 0.14, 0.6);
y += 0.14;

// stage 1: grey band, goal header, two parallel tracks (pink, green)
const S1H = 0.05 + BH + 0.14 + (0.04 + BH + 0.11 + BH + 0.04) + 0.05;
frame(M, y, W - 2 * M, S1H, PAL.grey[0], { lw: 1.0 });
const h1 = "辨析生长素输入与DR5响应时序";
box(CX - bw(h1) / 2, y + 0.05, bw(h1), BH, h1, { fill: PAL.grey[1] });
const TW = 1.95, tx = [CX - 0.3 - TW, CX + 0.3], ty = y + 0.05 + BH + 0.14, TH = 0.04 + BH + 0.11 + BH + 0.04;
const tc = tx.map((x) => x + TW / 2);
split(CX, y + 0.05 + BH, tc, ty + 0.04);
const TR = [["以P0为参照对齐阶段", "估计细胞生长素轨迹"], ["qDII空间分布定量", "低生长素区与输入比值"]];
[PAL.pink[0], PAL.green[0]].forEach((f, k) => {
  frame(tx[k], ty, TW, TH, f, { lw: 0.75 });
  const [a, b] = TR[k];
  box(tc[k] - bw(a) / 2, ty + 0.04, bw(a), BH, a);
  seg(tc[k], ty + 0.04 + BH, tc[k], ty + 0.15 + BH, true);
  box(tc[k] - bw(b) / 2, ty + 0.15 + BH, bw(b), BH, b);
});
plus(CX, ty + TH / 2, 0.22);
const t1end = ty + 0.15 + 2 * BH;
y += S1H;
merge(tc, [t1end, t1end], CX, y + 0.14, 0.75);
y += 0.14;

// stage 2: blue band; mechanisms and data feed the model; model <-> parameter screening (dashed: parameters updated)
const S2H = 0.05 + BH + 0.12 + BH + 0.12 + BH + 0.05;
frame(M, y, W - 2 * M, S2H, PAL.blue[0], { lw: 1.0 });
const h2 = "建立运输与响应模型";
box(CX - bw(h2) / 2, y + 0.05, bw(h2), BH, h2, { fill: PAL.blue[1] });
const lx = 1.75, rx = 4.25, r1 = y + 0.05 + BH + 0.12, r2 = r1 + BH + 0.12;
const A = "原基供给与中央周边差异", B = "PIN1极性与DR5时序", Cm = "运输与响应模型", D = "参数抽样与筛选";
seg(CX, y + 0.05 + BH, CX, y + 0.05 + BH + 0.06); seg(lx, y + 0.05 + BH + 0.06, CX, y + 0.05 + BH + 0.06);
seg(lx, y + 0.05 + BH + 0.06, lx, r1, true);
box(lx - bw(A) / 2, r1, bw(A), BH, A);
box(rx - bw(B) / 2, r1, bw(B), BH, B);
seg(lx, r1 + BH, lx, r2, true);
seg(rx, r1 + BH, rx, r1 + BH + 0.06); seg(lx, r1 + BH + 0.06, rx, r1 + BH + 0.06);
box(lx - bw(Cm) / 2, r2, bw(Cm), BH, Cm, { name: "model" });
box(rx - bw(D) / 2, r2, bw(D), BH, D, { name: "screening" });
seg(lx + bw(Cm) / 2, r2 + BH * 0.32, rx - bw(D) / 2, r2 + BH * 0.32, true);
seg(rx - bw(D) / 2, r2 + BH * 0.7, lx + bw(Cm) / 2, r2 + BH * 0.7, true, true);
const s2model = r2 + BH;
y += S2H;
seg(lx, s2model, lx, y + 0.07); seg(lx, y + 0.07, CX, y + 0.07); seg(CX, y + 0.07, CX, y + 0.14 + 0.05, true);
y += 0.14;

// stage 3: orange band; two rules in parallel -> tests -> predictions
const S3H = 0.05 + BH + 0.12 + BH + 0.12 + BH + 0.11 + BH + 0.05;
frame(M, y, W - 2 * M, S3H, PAL.orange[0], { lw: 1.0 });
const h3 = "检验时间整合的作用";
box(CX - bw(h3) / 2, y + 0.05, bw(h3), BH, h3, { fill: PAL.orange[1] });
const R = ["瞬时阈值规则", "时间整合规则"], rcx = [CX - 1.1, CX + 1.1], q1 = y + 0.05 + BH + 0.12;
split(CX, y + 0.05 + BH, rcx, q1, 0.5);
R.forEach((t, k) => box(rcx[k] - bw(t) / 2, q1, bw(t), BH, t));
plus(CX, q1 + BH / 2, 0.18);
const q2 = q1 + BH + 0.12, T = "留出茎尖与文献叶序检验", P = "处理后叶序预测";
merge(rcx, [q1 + BH, q1 + BH], CX, q2, 0.5);
box(CX - bw(T) / 2, q2, bw(T), BH, T);
seg(CX, q2 + BH, CX, q2 + BH + 0.11, true);
box(CX - bw(P) / 2, q2 + BH + 0.11, bw(P), BH, P);
y += S3H;

// research goal
seg(CX, q2 + 2 * BH + 0.11, CX, y + 0.12, true);
const G = "明确时间整合影响叶序精度与稳健性的条件";
box(CX - bw(G) / 2 - 0.05, y + 0.12, bw(G) + 0.1, H - M - y - 0.12, G, { fill: PAL.purple[1], name: "goal" });
console.log("goal box", (y + 0.12).toFixed(3), (H - M - y - 0.12).toFixed(3));
write(process.argv[2] || "roadmap_b.pptx");
