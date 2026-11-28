const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, HeadingLevel, LevelFormat, BorderStyle,
} = require("docx");

const ROOT = "/home/user/model";
const FIG1 = `${ROOT}/model_mvp/imaging_s1/out/fig_S1-3_staged_dr5_delay.png`;
const FIG2 = `${ROOT}/model_mvp/imaging_s1/ga2020/fig4GH_digitize_check.png`;
const OUT = process.argv[2]; // node make_report_dr5.js ../../汇报_DR5时序_20261128.docx

const FONT = { ascii: "Times New Roman", hAnsi: "Times New Roman", eastAsia: "SimSun", cs: "Times New Roman" };
const HFONT = { ascii: "Arial", hAnsi: "Arial", eastAsia: "SimHei", cs: "Arial" };
const GREY = "595959";

// text with **bold** segments
function runs(text, opts = {}) {
  return text.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map(t =>
    t.startsWith("**") ? new TextRun({ text: t.slice(2, -2), bold: true, ...opts }) : new TextRun({ text: t, ...opts }));
}
const P = (text, opts = {}) => new Paragraph({ children: runs(text), spacing: { after: 100, line: 300 }, ...opts });
const B = (text, level = 0) => new Paragraph({ children: runs(text), numbering: { reference: "bul", level }, spacing: { after: 60, line: 290 } });
const N = (text, ref = "num") => new Paragraph({ children: runs(text), numbering: { reference: ref, level: 0 }, spacing: { after: 60, line: 290 } });
const N2 = (text) => N(text, "num2");
const H1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
const CAP = (text) => new Paragraph({ children: runs(text, { size: 18, color: GREY }), spacing: { after: 200, line: 260 } });

function img(path, wCm, srcW, srcH) {
  const wPx = Math.round(wCm / 2.54 * 96);
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 60, after: 60 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(path), transformation: { width: wPx, height: Math.round(wPx * srcH / srcW) } })],
  });
}

// table
const TW = 9070; // A4 with 2.5 cm margins: 11906 - 2*1418
const colW = [3170, 1300, 1300, 1700, 1600];
const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };
function cell(text, w, { head = false, bold = false, align = AlignmentType.CENTER } = {}) {
  return new TableCell({
    width: { size: w, type: WidthType.DXA }, borders,
    shading: head ? { fill: "E8EEF7", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ alignment: align, children: [new TextRun({ text, bold: head || bold, size: 19 })] })],
  });
}
const rows = [
  ["数据与算法", "t50 输入", "t50 DR5", "DR5 延迟", "性质"],
  ["发表曲线，输入按 1 − qDII", "−14.6 h", "−0.9 h", "+13.7 h", "正式目标"],
  ["发表曲线，输入按 −ln qDII", "−9.2 h", "−0.9 h", "+8.4 h", "正式目标"],
  ["开发组 14 个茎尖，主分析", "−12.2 h", "−5.7 h", "+6.5 h\n[−6.4, +11.4]", "探索性"],
  ["开发组，10 项敏感性分析", "—", "—", "−5.7 ～ +8.8 h", "2 项区间 > 0"],
];
const table = new Table({
  width: { size: TW, type: WidthType.DXA }, columnWidths: colW,
  rows: rows.map((r, i) => new TableRow({
    tableHeader: i === 0,
    children: r.map((t, j) => {
      if (t.includes("\n")) {
        const [a, b] = t.split("\n");
        return new TableCell({
          width: { size: colW[j], type: WidthType.DXA }, borders, margins: { top: 60, bottom: 60, left: 100, right: 100 },
          children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: a, size: 19, bold: true })] }),
                     new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: b, size: 17, color: GREY })] })],
        });
      }
      return cell(t, colW[j], { head: i === 0, align: j === 0 ? AlignmentType.LEFT : AlignmentType.CENTER, bold: j === 3 && i > 0 && i < 3 });
    }),
  })),
});

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { font: HFONT, size: 32, bold: true },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 0, after: 80 }, keepNext: true } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: HFONT, size: 25, bold: true, color: "1F3864" },
        paragraph: { spacing: { before: 260, after: 100 }, keepNext: true, outlineLevel: 0 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] },
      ...["num", "num2"].map(r => ({ reference: r, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 400, hanging: 300 } } } }] })),
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1418, bottom: 1418, left: 1418, right: 1418 } } },
    children: [
      new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("分阶段生长素输入与 DR5 读出的时间差")] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
        children: [new TextRun({ text: "第一阶段（成像定量）进展汇报 · 2026-11-28", size: 20, color: GREY })] }),

      H1("一、要回答的问题"),
      P("生长素输入（qDII 下降）升高之后，DR5 读出要隔多久才升高？这个时间差是实施方案第 10 步“读出对照”要模型复现的量：模型里 DR5 由积分变量 M 驱动，若数据中存在明显延迟，就支持输入与读出之间有一个慢过程。"),

      H1("二、做了什么"),
      B("原计划逐个位点重建发育时间轴，但两次触发事先写定的停止规则：可信茎尖数用作者编号时 4 / 14，用 Codex 校正编号时 3 / 14，规则要求至少 8 个。"),
      B("因此改做两件事。方案（修订五）在读取任何 DR5 之前写定并提交。"),
      B("**正式目标：**把原研究（Galvan-Ampudia 等，2020）图 4G、4H 的箱线图逐格数字化（N = 21 个茎尖），按统一规则算 DR5 相对输入的延迟。", 0),
      B("**探索性分析：**开发组 14 个茎尖，用 Codex 编号逐帧定阶段，发育时间 τ = 12·k + h（k 为原基编号，h = 0、5、10 h）。各位点减去同帧背景，用同一规则算延迟，对茎尖自助抽样 1000 次给出区间。"),
      B("**延迟的算法：**每条曲线以早期各格的中位数为基线，最高一格为平台，取首次越过两者中点的时刻为 t50。延迟 = t50(DR5) − t50(输入)。"),

      H1("三、结果"),
      P("各数据与算法下的 DR5 延迟见下表，曲线和全部敏感性分析见图 1。"),
      table,
      new Paragraph({ spacing: { after: 120 }, children: [] }),
      N("**方向一致：**发表曲线和开发组都是输入先升、DR5 后升，DR5 在 P0 到 P1 处于平台。"),
      N("**发表曲线的延迟取决于输入的换算：**按 1 − qDII 为 +13.7 h，按 −ln qDII 为 +8.4 h，相差约 5 h。所以模型与数据比较时，必须使用同一种 DII 换算。"),
      N("**开发组的延迟不确定：**主分析为 +6.5 h，但 95% 区间（−6.4 到 +11.4 h）包含 0。按事先规则，结论是“在这一分辨率下看不出延迟”。结果不稳的原因是：输入曲线在 P−1 有一个台阶，正好落在中点附近，基线稍有变化，t50 就会跳动十几个小时。"),
      N("**绝对尺度不同：**我们重跑作者管线得到的 DR5 约为发表图的 2 倍，1 − qDII 也普遍偏高，原因尚未查清。因此两边只比较时间量，不比较数值。"),
      N("**P1 以后的 DR5 走向取决于编号：**用作者编号时 P1 的 DR5 仍然高，改用 Codex 编号后很快回落。"),

      img(FIG1, 15, 2125, 1913),
      CAP("图 1　A：原研究发表的曲线（正式目标）。B：开发组 14 个茎尖（探索性）。两条曲线都换算为“0 = 基线、1 = 平台”，虚线为各自的 t50，箭头为 DR5 延迟。C：各种算法下的 DR5 延迟，横线为 95% 自助区间。"),
      img(FIG2, 13.5, 2727, 1410),
      CAP("图 2　数字化核对：红线为读出的四分位，橙线为中位数，叠在原图 4G（左，生长素输入）和 4H（右，DR5）上，误差小于 1 像素。原图引自 Galvan-Ampudia et al., eLife 2020;9:e55832（CC BY 4.0）。"),

      H1("四、结论"),
      B("第 10 步读出对照的**正式目标已经确定**：DR5 延迟 +13.7 h（1 − qDII）或 +8.4 h（−ln qDII）。模型延迟与目标相差不超过 6 h，且 DR5 峰落在同一阶段，即判为一致。这一目标只用于比较，不用于调参。"),
      B("开发组的探索性曲线与发表曲线方向一致，但区间太宽，不能作为独立证据；也不用它来设定积分时间 τ_M。"),

      H1("五、需要确认的两点"),
      N2("“DR5 峰落在同一阶段”这一判据，在发表曲线上本身判得不稳：P0 5 h 到 P1 5 h 的四格几乎一样高。建议改为“DR5 在 P0 内升过一半”。"),
      N2("P1 以后的 DR5 走向随编号而变，建议第 10 步不拿它作为比较项。"),

      H1("六、局限"),
      B("每个茎尖只有 0、5、10 h 三帧，短于一个叶间期（约 12 h）；逐帧定阶段还带有至多半个叶间期的相位误差。小于约 5 h 的延迟分辨不出来。"),
      B("开发组的编号由 Codex 校正，没有经过人工复核。"),
      B("这里测的是“输入升高与 DR5 升高之间的时间差”，不是原基起始决定的时刻。"),
      new Paragraph({ spacing: { before: 200 }, children: [new TextRun({
        text: "详细数据与方案：model_mvp/imaging_s1/RESULTS.md 第 16 节、PROTOCOL.md 修订五。", size: 18, color: GREY })] }),
    ],
  }],
});

Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUT, b); console.log("written", OUT); });
