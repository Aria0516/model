// Fig. 2-1 technical roadmap, matrix layout: row labels on the left, one tinted dashed frame per research content,
// short two-line white boxes, black lines, one font size throughout; palette after the NSFC multicolour scheme
// (grey / orange / green / blue / purple). Drawn 15 cm wide as an editable PowerPoint slide (Chinese).
//   node roadmap.js <out.pptx>
const pptxgen = require("pptxgenjs");

const W = 5.906, H = 3.7;                          // inches
const INK = "000000", ARROW = "6B7B8C";
const GREY = ["F4F6F8", "DDE3E8"], PURPLE = ["EEE4F4", "D8C3E6"];
const MOD = [["FBEAD4", "EDC48F"], ["E4F0D7", "BCD79F"], ["DDEAF6", "B7D1EA"]];   // [frame tint, header fill]
const FONT = "Times New Roman";                     // East Asian runs are set to 宋体 afterwards (fix_fonts.py)
const FS = 8;                                       // one size for every box

const pres = new pptxgen();
pres.defineLayout({ name: "FIG", width: W, height: H });
pres.layout = "FIG";
pres.title = "图2-1 技术路线";
const s = pres.addSlide();

function box(x, y, w, h, text, o = {}) {
  s.addText(text, {
    x, y, w, h, fontFace: FONT, fontSize: FS, color: INK, align: "center", valign: "middle",
    fill: { color: o.fill || "FFFFFF" },
    line: { color: INK, width: o.lw || 0.75, dashType: o.dash || "solid" },
    margin: [1, 2, 1, 2], lineSpacingMultiple: 1.0, objectName: o.name,
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

// geometry
const LX = 0.03, LW = 0.36;                         // row-label column
const AX0 = 0.5, AX1 = W - 0.03, GAPM = 0.28;       // module area and the space between modules (sequence arrows)
const FW = (AX1 - AX0 - 2 * GAPM) / 3, BW = FW - 0.22;
const fx = [0, 1, 2].map((k) => AX0 + k * (FW + GAPM));
const cx = fx.map((x) => x + FW / 2), MID = (AX0 + AX1) / 2;
const FY = 0.5, HB = 0.3, BH = 0.38, AG = 0.15;
const rows = [FY + 0.08];                           // header row, then four content rows
for (let i = 1; i < 5; i++) rows.push(rows[i - 1] + (i === 1 ? HB : BH) + AG);
const FB = rows[4] + BH + 0.08, FH = FB - FY;

// top: the thesis title, broken down into the three research contents
box(MID - 1.75, 0.03, 3.5, 0.3, "拟南芥叶序形成中生长素时间整合的建模研究", { fill: GREY[1], name: "title" });

// module frames first (so lines and boxes sit on top)
MOD.forEach(([tint], k) => box(fx[k], FY, FW, FH, "", { fill: tint, dash: "dash", lw: 1.0, name: `frame_${k}` }));

const bus0 = 0.42;
seg(MID, 0.33, MID, bus0); seg(cx[0], bus0, cx[2], bus0);
cx.forEach((c) => seg(c, bus0, c, rows[0], true));

// row labels
const LABELS = ["研究\n内容", "数据\n材料", "关键\n方法", "定量\n检验", "阶段\n产出"];
LABELS.forEach((t, i) => {
  const h = i === 0 ? HB : BH, y = rows[i] + h / 2 - 0.19;
  box(LX, y, LW, 0.38, t, { fill: GREY[1], name: `label_${i}` });
});

const CELLS = [
  ["成像数据定量", "21个茎尖qDII与DR5\n4个茎尖PIN1成像", "以P0为参照对齐阶段\n结合细胞移动估计轨迹",
   "PIN1极性与低生长素区\nDR5激活时序", "细胞生长素轨迹\nDR5时序与空间分布"],
  ["模型建立与检验", "前期表皮层与内层模型\n生长素轨迹与空间分布", "纳入原基供给\n与中央周边差异",
   "参数抽样与筛选\n经换算对照DR5", "运输与响应模型\n及参数取值范围"],
  ["启动规则比较", "相同运输与生长设定\n文献叶序与留出茎尖", "瞬时阈值规则\n时间整合规则",
   "DR5延迟、平均发生间隔\n发散角与发生顺序", "两类规则的解释力\n处理后叶序预测"],
];
CELLS.forEach((col, k) => {
  col.forEach((t, i) => {
    const h = i === 0 ? HB : BH, w = i === 0 ? BW * 0.86 : BW;
    box(cx[k] - w / 2, rows[i], w, h, t, { fill: i === 0 ? MOD[k][1] : "FFFFFF", name: `cell_${k}_${i}` });
    if (i > 0) seg(cx[k], rows[i - 1] + (i === 1 ? HB : BH), cx[k], rows[i], true);
  });
});

// sequence between research contents: the result of one is used by the next
[0, 1].forEach((k) => {
  s.addShape(pres.ShapeType.rightArrow, {
    x: fx[k] + FW + 0.04, y: FY + FH / 2 - 0.13, w: GAPM - 0.08, h: 0.26,
    fill: { color: ARROW }, line: { type: "none" }, objectName: `sequence_${k}`,
  });
});

// bottom: research goal
const bus1 = FB + 0.1, GY = FB + 0.22, GH = H - 0.03 - GY;
cx.forEach((c) => seg(c, rows[4] + BH, c, bus1));
seg(cx[0], bus1, cx[2], bus1); seg(MID, bus1, MID, GY, true);
box(LX, GY + GH / 2 - 0.19, LW, 0.38, "研究\n目标", { fill: GREY[1], name: "label_goal" });
box(MID - 2.0, GY, 4.0, GH, "构建“生长素输入 → 时间整合 → 原基启动 → 叶序形成”的生长素-PIN1模型\n明确时间整合影响叶序精度与稳健性的条件",
    { fill: PURPLE[1], name: "goal" });
console.log("goal box", GY.toFixed(3), GH.toFixed(3));

pres.writeFile({ fileName: process.argv[2] || "roadmap3.pptx" }).then((f) => console.log("wrote", f));
