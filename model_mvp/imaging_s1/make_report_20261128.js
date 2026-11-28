// Concise Word report: model adjustment plan, step 1 (A1 secondary inhibitory field), DR5 timing (stage 1, revision 5).
// node make_report_20261128.js ../../汇报_模型调整与DR5时序_20261128.docx
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, HeadingLevel, LevelFormat, BorderStyle, PageBreak,
} = require("docx");

const ROOT = path.resolve(__dirname, "..", "..");
const FIG_A1 = `${ROOT}/model_mvp/ablation_a1/out/fig_A1_paired_ablation.png`;
const FIG_DR5 = `${ROOT}/model_mvp/imaging_s1/out/fig_S1-3_staged_dr5_delay.png`;
const FIG_DIG = `${ROOT}/model_mvp/imaging_s1/ga2020/fig4GH_digitize_check.png`;
const OUT = process.argv[2];

const FONT = { ascii: "Times New Roman", hAnsi: "Times New Roman", eastAsia: "SimSun", cs: "Times New Roman" };
const HFONT = { ascii: "Arial", hAnsi: "Arial", eastAsia: "SimHei", cs: "Arial" };
const GREY = "595959";

function runs(text, opts = {}) {
  return text.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map(t =>
    t.startsWith("**") ? new TextRun({ text: t.slice(2, -2), bold: true, ...opts }) : new TextRun({ text: t, ...opts }));
}
const P = (text) => new Paragraph({ children: runs(text), spacing: { after: 100, line: 300 } });
const B = (text) => new Paragraph({ children: runs(text), numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 290 } });
let numCount = 0;
const numRefs = [];
function newList() { numCount += 1; const r = `num${numCount}`; numRefs.push(r); return (text) =>
  new Paragraph({ children: runs(text), numbering: { reference: r, level: 0 }, spacing: { after: 60, line: 290 } }); }
const H1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
const H2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
const CAP = (text) => new Paragraph({ children: runs(text, { size: 18, color: GREY }), spacing: { after: 200, line: 260 } });
const GAP = () => new Paragraph({ spacing: { after: 100 }, children: [] });

function img(file, wCm) {
  const buf = fs.readFileSync(file);
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);   // PNG header
  const wPx = Math.round(wCm / 2.54 * 96);
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 60 }, keepNext: true,
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: wPx, height: Math.round(wPx * h / w) } })] });
}

const TW = 9070;   // A4, 2.5 cm margins
const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };
// rows: array of arrays of strings; "**x**" = bold; "a\nb" = two lines (second grey, smaller)
function table(rows, colW, { leftCols = [0] } = {}) {
  return new Table({
    width: { size: TW, type: WidthType.DXA }, columnWidths: colW,
    rows: rows.map((r, i) => new TableRow({
      tableHeader: i === 0, cantSplit: true,
      children: r.map((t, j) => {
        const align = leftCols.includes(j) ? AlignmentType.LEFT : AlignmentType.CENTER;
        const parts = t.split("\n");
        return new TableCell({
          width: { size: colW[j], type: WidthType.DXA }, borders,
          shading: i === 0 ? { fill: "E8EEF7", type: ShadingType.CLEAR, color: "auto" } : undefined,
          margins: { top: 50, bottom: 50, left: 90, right: 90 },
          children: parts.map((p, k) => new Paragraph({ alignment: align,
            children: runs(p, k === 0 ? (i === 0 ? { size: 19, bold: true } : { size: 19 }) : { size: 17, color: GREY }) })),
        });
      }),
    })),
  });
}

const L1 = newList(), L2 = newList(), L3 = newList(), L4 = newList();

const children = [
  new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("模型调整与成像定量进展汇报")] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
    children: [new TextRun({ text: "拟南芥叶序形成中生长素时间整合的建模研究 · 2026-11-28", size: 20, color: GREY })] }),

  H1("一、本期要点"),
  B("**模型调整第一步（次级抑制场）完成：**去掉它会使原基位置变散约 3°，不能判为“可忽略”，因此保留，模型这一步不改。"),
  B("**DR5 给模型定了一把尺子：**原研究中，DR5 比生长素晚 8–14 小时亮起来，之后用它检验模型。"),
  B("**我们自己的数据太粗（只拍了 0、5、10 小时），定不下这个时间差。**"),

  H1("二、模型调整构想"),
  P("目标是让模型中每个参数都能由常规实验（计算实验或领域常用的湿实验）、拟合或借用文献来确定。四条约束：实测量作为输入；叶序统计只用于检验，不用来调参数；每次只改一处结构，运行前写定方案与判据；暂不纳入 CLV3/WUS。"),
  table([
    ["方向", "做什么", "目前进展"],
    ["精简结构\n计算实验 A1–A5", "对没有测量值的结构做配对消融：去掉后叶序统计不变，就删去或固定；有影响，就保留并给出范围", "A1 次级抑制场：已完成，保留\n下一步 A2：本地产生、产生饱和能否取 0"],
    ["用成像数据定参数\nB1–B3、B6", "PIN1 分配、中央区 PIN1 倍数、低生长素区宽度、组织生长率：能测的用测量值，测不准的只报范围", "中央区 PIN1 信号约为外周的 0.5–0.66 倍（模型 0.19，映射未确认前不改）\n生长率估计方法验证未通过，时间单位暂不锁定"],
    ["检验核心假说\n第 10 步", "读出对照：模型的 DR5 能否复现输入到读出的延迟\n起始对照：原基起始是否依赖积分", "读出对照的目标已定（本期，第四节）\n起始对照：形态盲标一致性不足（κ = 0.09），用现有数据不做"],
    ["冻结与留出检验\n第 11 步", "模型冻结后，在 7 个留出茎尖上做一次性检验", "留出组至今未读取"],
  ], [1900, 3570, 3600], { leftCols: [0, 1, 2] }),
  GAP(),

  new Paragraph({ children: [new PageBreak()] }),
  H1("三、模型调整第一步：次级抑制场能不能删（A1）"),
  P("**问题：**v3 中模仿 AHP6 的次级抑制场带有 4 个没有测量值的参数。去掉它，叶序统计会不会变？"),
  P("**做法：**v3 的 120 组参数 × 2 个随机种子，场开、场关各跑一遍，共 480 次，逐组比较。差值的 95% 区间完全落在事先定的等效范围内，才判为“可忽略”；只有全部指标都可忽略，才删去这个场。"),
  img(FIG_A1, 15.5),
  CAP("图 1　去掉次级抑制场前后的配对差值（场关 − 场开）。点为参数组均值，横线为 95% 自助区间，灰带为事先写定的等效范围。"),
  table([
    ["指标（全部 120 组）", "场关 − 场开", "等效范围", "判定"],
    ["同时起始比例", "+0.019\n[+0.004, +0.034]", "±0.05", "可忽略"],
    ["原基间隔变异系数", "−0.016\n[−0.044, +0.010]", "±0.05", "可忽略"],
    ["P1–P5 方位离散", "+3.3°\n[+1.3, +5.4]", "±2°", "**证据不足**"],
    ["平均发散角", "−1.7°\n[−8.4, +4.8]", "±2°", "**证据不足**"],
    ["叶序类型改变", "68% 的参数组", "≤ 5%", "有实质影响 *"],
  ], [2770, 2300, 1700, 2300]),
  GAP(),
  L1("**结论：次级抑制场保留，模型这一步不改。**它的 4 个参数继续作为范围参数。"),
  L1("去掉它，原基位置的离散增大约 3°（受运输限制的参数组约 5°），说明它对位置精度有小幅贡献。同时起始比例略增 1.9 个百分点，方向与 ahp6 突变体一致，幅度小。"),
  L1("* 类型改变率（68%）与同一参数组两个种子之间的差别（54%）相近，主要反映不规则运行的轨迹分叉，不能归因于场本身。"),
  L1("480 次运行全部正常起始，没有停摆或事件不足。"),

  new Paragraph({ children: [new PageBreak()] }),
  H1("四、生长素升高后，DR5 要隔多久才亮起来"),
  P("**目标：**生长素升高后，DR5（显示生长素作用的报告基因）要隔多久才亮起来？这个时间差用来检验模型。"),
  P("**方法：**"),
  L2("从原研究发表的图上，读出各阶段原基处的生长素和 DR5 强度（21 个茎尖）。"),
  L2("**标注原基：**作者管线自动给出的原基编号在 0、5、10 小时之间前后对不上，因此由 Codex 对我们 14 个茎尖、每个 3 个时刻的生长素极大点重新标注原基编号（P−3 到 P5，数字越大越老），并让同一编号在三个时刻指向同一个原基，共标注 271 个位点。"),
  L2("按标注的编号排出各原基的发育先后，在每个原基处读出生长素和 DR5 强度。"),
  L2("分别找出两条曲线“升到一半”的时刻，相减得到时间差。"),
  P("**结论：**"),
  L4("**原研究：DR5 比生长素晚 8–14 小时亮起来。**这作为模型的对照目标：不调参数运行模型，看能否算出同样的时间差。"),
  img(FIG_DIG, 12.5),
  CAP("图 2　原研究的生长素（左）和 DR5（右）随原基阶段的变化；红线、橙线为我们从图上读出的数值。原图引自 Galvan-Ampudia et al., eLife 2020（CC BY 4.0）。"),
  L4("**我们的数据：也是生长素先升、DR5 后亮，但定不下晚多少。**每个茎尖只拍了 0、5、10 小时三张，太粗。"),
  img(FIG_DR5, 14.5),
  CAP("图 3　A 原研究、B 我们的数据：橙色为生长素，蓝色为 DR5，箭头为 DR5 晚了多少。C 各种算法下的时间差，横线越长越不确定。"),
  L4("**这个延迟只说明“生长素 → DR5”这一段慢，不能说明原基起始也需要累积生长素。**"),

  H1("五、需要确认的事项"),
  L3("“DR5 峰落在同一阶段”这一判据，在发表曲线上本身判得不稳（P0 5 h 到 P1 5 h 的四格几乎一样高）。建议改为“DR5 在 P0 内升过一半”。"),
  L3("P1 以后的 DR5 走向随编号而变，建议第 10 步不拿它作为比较项。"),
  L3("是否开始模型调整第二步 A2（本地产生、产生饱和能否取 0）。方案与判据会先写好给你看，再运行。"),

  H1("六、局限"),
  B("A1 的结论只在 v3 的参数抽样范围内成立；类型改变、平均发散角两项主要受轨迹分叉影响。"),
  B("每个茎尖只有 0、5、10 h 三帧，短于一个叶间期；逐帧定阶段还带有至多半个叶间期的相位误差，小于约 5 h 的延迟分辨不出来。"),
  B("开发组的编号由 Codex 校正，没有经过人工复核。DR5 部分测的是“输入升高与读出升高之间的时间差”，不是原基起始决定的时刻。"),
  new Paragraph({ spacing: { before: 200 }, children: [new TextRun({ size: 18, color: GREY,
    text: "详细材料：model_mvp/ablation_a1/RESULTS.md；model_mvp/imaging_s1/RESULTS.md 第 16 节、PROTOCOL.md 修订五；模型改进实施方案.md。" })] }),
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { font: HFONT, size: 32, bold: true },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 0, after: 80 }, keepNext: true } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: HFONT, size: 25, bold: true, color: "1F3864" },
        paragraph: { spacing: { before: 260, after: 100 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: HFONT, size: 22, bold: true, color: "1F3864" },
        paragraph: { spacing: { before: 180, after: 80 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] },
      ...numRefs.map(r => ({ reference: r, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 400, hanging: 300 } } } }] })),
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1418, bottom: 1418, left: 1418, right: 1418 } } },
    children,
  }],
});

Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUT, b); console.log("written", OUT); });
