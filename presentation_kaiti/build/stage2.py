"""Stage 2: turn the group-meeting deck (stage1.pptx) into the proposal-defence deck (开题汇报.pptx)."""
import copy, re
from pathlib import Path
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

K = Path(__file__).resolve().parent
FIG = Path("/home/user/model/figures/prior_work")
prs = Presentation(K / "stage1.pptx")
S = list(prs.slides)                      # S[0..22] = old slides 1..23, S[23] = copy of the cover
LAY = {l.name: l for l in prs.slide_layouts}

BLUE, GOLD, INK, GREY = RGBColor(0x1F, 0x4E, 0x99), RGBColor(0xB8, 0x97, 0x5A), RGBColor(0x1A, 0x1A, 0x1A), RGBColor(0x59, 0x59, 0x59)
WHITE, CARD, CARD2 = RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0xF1, 0xF4, 0xF9), RGBColor(0xEE, 0xF4, 0xEA)
HEAD, BODY = ("微软雅黑", "微软雅黑"), ("Times New Roman", "宋体")


# ---------------------------------------------------------------- helpers
def style_run(run, size, bold=False, color=INK, face=BODY):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is not None:
            rPr.remove(el)
    for tag, f in (("a:latin", face[0]), ("a:ea", face[1]), ("a:cs", face[0])):
        etree.SubElement(rPr, qn(tag)).set("typeface", f)


def text(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, inset=0.04):
    """paras: list of dicts {runs: [(text, size, bold, color, face)], align, after, line}"""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(inset)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = anchor
    for i, pd in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = pd.get("align", PP_ALIGN.LEFT)
        p.space_after = Pt(pd.get("after", 0))
        if "line" in pd:
            p.line_spacing = pd["line"]
        for t, size, bold, color, face in pd["runs"]:
            r = p.add_run()
            r.text = t
            style_run(r, size, bold, color, face)
    return box


def para(t, size=16, bold=False, color=INK, face=BODY, **kw):
    return dict(runs=[(t, size, bold, color, face)], **kw)


def shape(slide, kind, x, y, w, h, fill=None, line=None, lw=1.0, adj=None):
    sh = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    st = sh._element.find(qn("p:style"))
    if st is not None:
        sh._element.remove(st)
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(lw)
    if adj is not None:
        sh.adjustments[0] = adj
    return sh


def badge(slide, x, y, d, label, size=15):
    o = shape(slide, MSO_SHAPE.OVAL, x, y, d, d, fill=BLUE)
    tf = o.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = label
    style_run(r, size, True, WHITE, HEAD)
    return o


def set_runs(sp_el, lines):
    """Replace the text of a copied text shape, keeping the first run's formatting; lines: [(text, size or None)]."""
    txBody = sp_el.find(qn("p:txBody"))
    ps = txBody.findall(qn("a:p"))
    p0 = ps[0]
    r0 = p0.find(qn("a:r"))
    for p in ps:
        txBody.remove(p)
    for t, size in lines:
        p = copy.deepcopy(p0)
        for r in p.findall(qn("a:r")):
            p.remove(r)
        r = copy.deepcopy(r0)
        r.find(qn("a:t")).text = t
        if size:
            r.find(qn("a:rPr")).set("sz", str(int(size * 100)))
        end = p.find(qn("a:endParaRPr"))
        if end is not None:
            end.addprevious(r)
        else:
            p.append(r)
        txBody.append(p)


TITLE = next(sh for sh in S[1].shapes if sh.name == "Text 9")._element
SLDNUM = next(sh for sh in S[1].shapes if sh.name.startswith("Slide Number"))._element


def new_slide(layout, title=None):
    s = prs.slides.add_slide(LAY[layout])
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    if title is not None:
        t = copy.deepcopy(TITLE)
        s.shapes._spTree.append(t)
        set_runs(t, [(title, None)])
    s.shapes._spTree.append(copy.deepcopy(SLDNUM))
    return s


def notes(s, t):
    s.notes_slide.notes_text_frame.text = t


def renumber(s):
    for i, el in enumerate(s.shapes._spTree.iter(qn("p:cNvPr")), start=2):
        el.set("id", str(i))


def picture(s, path, x, y, w=None, h=None):
    return s.shapes.add_picture(str(path), Inches(x), Inches(y),
                                width=Inches(w) if w else None, height=Inches(h) if h else None)


def source(s, t, y=7.06):
    text(s, 0.5, y, 9.0, 0.3, [para(t, 11, color=GREY)])


# ---------------------------------------------------------------- cover and closing slide
def cover(s, main, sub, line1, line2):
    sh = {x.name: x for x in s.shapes}
    t = sh["文本框 9"]
    t.left, t.top, t.width, t.height = Inches(0.5), Inches(3.62), Inches(12.33), Inches(2.0)
    t.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    set_runs(t._element, ([(sub, 26)] if sub else []) + [(main, 40 if sub else 54)])
    for p in t.text_frame.paragraphs:
        p.alignment = PP_ALIGN.CENTER
    for name, tx, y in (("文本框 10", line1, 5.9), ("文本框 11", line2, 6.45)):
        b = sh[name]
        b.left, b.top, b.width, b.height = Inches(0.5), Inches(y), Inches(12.33), Inches(0.46)
        set_runs(b._element, [(tx, 20)])
        b.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER


cover(S[0], "拟南芥叶序形成中生长素时间整合的建模研究", "硕士学位论文开题报告",
      "汇报人：张希程　　　　指导教师：齐继艳 教授", "生命科学与技术学院　·　生物技术与工程　·　2026年11月")
notes(S[0], "各位老师好，我是生命科学与技术学院生物技术与工程专业的张希程，导师是齐继艳教授。我的论文题目是《拟南芥叶序形成中生长素时间整合的建模研究》。下面从选题依据、已有工作积累、研究内容与研究方案、预期结果与进度安排四个方面汇报。")
cover(S[23], "敬请各位老师批评指正", None,
      "汇报人：张希程　　　　指导教师：齐继艳 教授", "生命科学与技术学院　·　生物技术与工程　·　2026年11月")
notes(S[23], "以上是我的开题汇报，恳请各位老师批评指正，谢谢。")

# ---------------------------------------------------------------- retained background slides
for s in S[1:12]:
    for sh in s.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if "时间积分" in r.text:
                        r.text = r.text.replace("时间积分", "时间整合")
    if s.has_notes_slide:
        tf = s.notes_slide.notes_text_frame
        for p in tf.paragraphs:
            for r in p.runs:
                r.text = r.text.replace("时间积分", "时间整合")
notes(S[7], "同一研究还有两点发现。第一，生长素最大区并不固定在某些细胞上。左上追踪了P1区域0、5、10小时的细胞核，绿圈是生长素最大区，白圈和红圈是被追踪的细胞，它们的生长素分别迅速下降或上升。左下比较了最大区（彩色线）和细胞（灰线）的径向位置随时间的变化，最大区向外移动得比细胞快。这意味着不同位置的细胞经历着不同的生长素时间历程，这正是本研究要追踪细胞、推算细胞所经历生长素变化的原因。第二，右图是4个茎尖的PIN1极性矢量叠加在生长素分布上：在组织尺度上，PIN1强烈指向茎尖中心，茎尖中央的生长素输入也较高。这些空间特征与经典模型中“原基处汇聚、周边耗竭”的图景不完全一致，本研究将用这些空间分布检验运输模型。（Galvan-Ampudia et al., 2020）")

# ---------------------------------------------------------------- outline
OUT = new_slide("DEFAULT")
shape(OUT, MSO_SHAPE.RECTANGLE, 0, 0, 4.3, 7.5, fill=BLUE)
text(OUT, 0.55, 2.75, 3.3, 1.0, [para("汇报提纲", 40, True, WHITE, HEAD)])
text(OUT, 0.6, 3.75, 3.3, 0.5, [dict(runs=[("CONTENTS", 18, False, RGBColor(0xC9, 0xD6, 0xEA), ("Arial", "Arial"))])])
shape(OUT, MSO_SHAPE.RECTANGLE, 0.6, 4.35, 0.9, 0.05, fill=GOLD)
ITEMS = [("01", "选题依据", "研究背景与现状 · 现有研究不足 · 研究目的与意义"),
         ("02", "已有工作积累", "成像数据处理与测量 · 生长素–PIN1模型 · 模型检验"),
         ("03", "研究内容与研究方案", "研究内容 · 技术路线 · 存在问题及解决措施"),
         ("04", "预期结果与进度安排", "预期结果与应用价值 · 工作量与进度 · 主要参考文献")]
for i, (n, t, sub) in enumerate(ITEMS):
    y = 1.05 + i * 1.5
    badge(OUT, 5.0, y + 0.1, 0.8, n, 20)
    text(OUT, 6.1, y, 6.7, 0.55, [para(t, 24, True, INK, HEAD)])
    text(OUT, 6.1, y + 0.58, 6.7, 0.45, [para(sub, 16, color=GREY)])
notes(OUT, "汇报分四部分：先介绍选题依据，包括研究背景、现有研究的不足和本研究的目的；然后是前期已经完成的工作；接着是研究内容、技术路线以及可能遇到的问题和解决措施；最后是预期结果、工作量与进度安排。")

# ---------------------------------------------------------------- gaps and aims
GAP = new_slide("BG", "现有研究的不足与本研究的目的")
shape(GAP, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5, 1.75, 7.25, 5.25, fill=CARD, adj=0.03)
text(GAP, 0.8, 1.92, 6.7, 0.5, [para("现有研究不足", 20, True, BLUE, HEAD)])
G = ["时间整合已有成像证据，但叶序模型尚未纳入：运输模型以某一时刻的浓度阈值触发原基，随机发生模型不含生长素运输。",
     "茎尖中央输入较高、起始位点输入逐步升高、转录激活滞后近一个叶间期，运输与细胞响应结合后能否同时解释，尚未系统检验。",
     "瞬时阈值与时间整合缺乏统一框架下的定量比较；两者平均发散角可能相近，需要用发生间隔、发生顺序和变异来区分。"]
for i, g in enumerate(G):
    y = 2.6 + i * 1.42
    badge(GAP, 0.85, y + 0.05, 0.42, str(i + 1), 15)
    text(GAP, 1.45, y, 6.05, 1.3, [para(g, 16, line=1.15)])
shape(GAP, MSO_SHAPE.ROUNDED_RECTANGLE, 8.0, 1.75, 4.83, 5.25, fill=BLUE, adj=0.03)
text(GAP, 8.3, 1.92, 4.3, 5.0, [
    para("研究目的", 20, True, WHITE, HEAD, after=6),
    para("在生长素–PIN1模型中，以反映时间整合的细胞响应衔接生长素输入、转录响应与原基启动；用茎尖定量成像确定模型，比较瞬时阈值与时间整合两类启动规则，明确时间整合在何种条件下影响叶序精度与稳健性。", 16, color=WHITE, line=1.15, after=16),
    para("研究意义", 20, True, WHITE, HEAD, after=6),
    para("从细胞读取生长素信号的方式解释组织尺度的叶序格局，并为后续实验的观测指标与处理条件提供可检验的预测。", 16, color=WHITE, line=1.15)])
notes(GAP, "综合以上背景，现有研究有三点不足。第一，生长素信号的时间整合虽有成像实验支持，现有叶序模型却尚未纳入：经典运输模型以某一时刻的浓度阈值触发原基，随机发生模型虽按局部抑制水平累积发生概率，却不包含生长素运输。第二，成像显示茎尖中央的生长素输入较高、原基起始位点处的输入逐步升高、周边细胞的转录激活滞后近一个叶间期，现有运输规则与细胞响应结合后能否同时解释这些现象，尚未系统检验。第三，瞬时阈值与时间整合两类规则缺乏统一框架下的定量比较，它们可能给出相近的平均发散角，而在信号响应、发生间隔和发生顺序上不同。因此，本研究的目的是在生长素–PIN1模型中，以反映时间整合的细胞响应把生长素输入、转录响应和原基启动衔接起来，用茎尖定量成像确定模型，在同一框架下比较两类启动规则，明确时间整合在什么条件下影响叶序的精度与稳健性。")

# ---------------------------------------------------------------- prior work
def keypoints(s, x, y, w, h, pts, size=16):
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=CARD, adj=0.03)
    paras = []
    for tag, t in pts:
        paras.append(dict(runs=[(tag + "  ", size, True, BLUE, HEAD), (t, size, False, INK, BODY)], line=1.15, after=10))
    text(s, x + 0.25, y + 0.15, w - 0.5, h - 0.3, paras, anchor=MSO_ANCHOR.MIDDLE)


W1 = new_slide("RT", "处理21个茎尖的公开成像，得到模型所需的几何参数")
picture(W1, FIG / "fig1_data_zh.png", 0.5, 1.68, h=5.32)
keypoints(W1, 6.3, 1.75, 6.53, 5.25, [
    ("A、B", "重建原作者处理流程并改进批处理，稳定处理全部21个茎尖，得到L1层细胞核位置、生长素输入、DR5与CLV3信号和原基阶段"),
    ("C、D", "细胞核最近邻间距4.53 µm、CLV3表达区半径27.3 µm，茎尖间差异约2%，作为模型的几何输入"),
    ("E", "4个茎尖的细胞间PIN1量差异（对数标准差0.08）远小于模型产生文献报道非规范发散角比例所需的水平")])
source(W1, "数据：Galvan-Ampudia et al., eLife (2020)")
notes(W1, "前期工作的第一部分是成像数据。材料是已发表的21个拟南芥花序茎尖0、5、10小时的时间序列，以及另外4个茎尖的PIN1成像。我在重建的原作者软件环境中复现了他们的处理结果，再改进了批处理流程，稳定处理了全部21个茎尖，得到每个茎尖表皮层细胞核的位置、生长素输入、DR5与CLV3信号，以及原基阶段（A、B）。可以看到，茎尖中央的生长素输入较高而DR5很弱，DR5主要见于原基。在此基础上测量了茎尖形态：细胞核最近邻间距中位数4.53微米，CLV3表达区半径27.3微米，茎尖间差异约2%，这两项已作为模型的几何输入（C、D）。另外，用细胞壁分割流程处理4个茎尖的PIN1图像，细胞间PIN1量差异的对数标准差约0.08；模型中要达到文献报道的非规范发散角比例，所需差异是实测值的4到6倍，说明实测幅度的PIN1量差异不足以产生这一比例（E）。")

W2 = new_slide("RT", "生长素–PIN1模型自发产生二列互生、螺旋与交互对生")
KF = K / "figs"
picture(W2, KF / "f12_AB.png", 0.5, 1.7, w=6.1)
picture(W2, KF / "f12_CDE.png", 0.5, 1.7 + 2.71 + 0.15, w=6.1)
picture(W2, KF / "f12_FG.png", 6.85, 1.7, w=5.98)
keypoints(W2, 6.85, 3.75, 5.98, 3.25, [
    ("A、B", "生长素经扩散和PIN1极性运输移动；原基既是汇，也是极化线索；启动判据可在瞬时阈值与时间整合间切换"),
    ("C–F", "叶序由模拟自发产生：只改变发生环与原基作用范围之比，得到二列互生、螺旋和交互对生"),
    ("改进", "加入外围合成与内层排出（*）后，阻断运输即不产生原基，起始半径与实测P0重叠"),
    ("G", "积分时间常数接近一个叶间期时规则螺旋减少，需分别刻画转录响应与原基启动")], size=15)
notes(W2, "第二部分是模型。我参照已有的叶序运输模型，在生长、分裂的表皮细胞层上建立了细胞水平的生长素–PIN1模型（A、B）。生长素经扩散和PIN1极性运输在细胞间移动，每个细胞的PIN1总量有限，按相邻细胞的生长素浓度在各膜面间分配；原基形成后既是生长素的汇，也是PIN1极化方向的线索。原基在周边的发生环内依据生长素水平启动，启动判据可以在瞬时阈值和泄漏积分形式的时间整合之间切换。发散角、发生间隔和手性都由模拟自发产生。只改变发生环半径与原基作用范围之比，模型依次产生二列互生、螺旋和交互对生（C到F）。按事先写定的判定标准核查文献现象后，我做了两处改进，就是图中带星号的部分：生长素主要在外围合成，以及加入内层，原基把生长素排入内层后经维管排出。改进后关闭极性运输就不再产生原基，原基起始半径与实测P0半径范围重叠。G图显示，积分时间常数接近一个叶间期时规则螺旋比例下降，所以本研究要把转录响应和原基启动分开刻画。")

W3 = new_slide("RT", "以文献参数检验：叶序是否有序取决于低生长素区与向心运输")
picture(W3, FIG / "fig3_tests_zh.png", 0.45, 1.75, w=7.95)
keypoints(W3, 8.65, 1.75, 4.18, 5.25, [
    ("设定", "PIN1极化强度和次级抑制取自文献，积分时间常数范围依据外施IAA实验；15个参数抽样120组"),
    ("A", "规则螺旋均出现在原基启动受极性运输限制的参数组；有序与否主要取决于w、η与κc"),
    ("B", "主导发散角中位数141°；发生间隔13.8 h，与文献约12 h接近"),
    ("下一步", "用qDII低生长素区与PIN1极性数据约束这些参数")], size=15)
notes(W3, "第三部分是用文献参数检验模型。PIN1极化强度和幼原基周围的次级抑制取自文献，积分时间常数的抽样范围依据外施IAA的实验确定，去掉位点微调后，对15个缺乏测量值的参数抽样120组，每组2个随机种子。结果是，26次规则螺旋都出现在原基启动受极性运输限制的参数组；规则螺旋的主导发散角中位数为141°，换算后的发生间隔为13.8小时，与文献报道的约12小时接近（B）。叶序是否有序主要取决于三个参数：原基作用范围w、汇强度η和向心运输偏置κc（A），它们分别对应低生长素区的范围、深度和PIN1的向心极性。所以下一步要先用qDII的低生长素区和PIN1极性数据约束这些参数，再比较两类启动规则。")

# ---------------------------------------------------------------- research contents
CT = new_slide("RS", "研究内容")
shape(CT, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5, 1.72, 12.33, 0.66, fill=RGBColor(0xDD, 0xF0, 0xEE), line=RGBColor(0x2E, 0x7D, 0x78), lw=1.0, adj=0.15)
text(CT, 0.6, 1.72, 12.13, 0.66, [dict(runs=[("科学问题：", 18, True, BLUE, HEAD), ("在拟南芥茎尖中，细胞对生长素信号的时间整合如何影响原基启动与叶序形成？", 18, True, INK, HEAD)], align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
CARDS = [("（1）茎尖成像数据的定量分析", "原基处生长素输入怎样变化，DR5响应何时出现？",
          ["以P0为参照，按叶间期对齐原基阶段", "定量生长素升高与DR5激活时间、低生长素区与PIN1极性", "追踪细胞随茎尖生长的位置变化，推算细胞经历的生长素变化"]),
         ("（2）生长素–PIN1模型的建立与检验", "运输与响应能否解释空间分布和响应延迟？",
          ["基于已有表皮层与内层模型，比较模拟与实测空间分布，优化运输模型", "将细胞生长素轨迹输入响应模型，区分中央与周边的响应", "经报告信号换算对照DR5，确定响应模型"]),
         ("（3）两类启动规则的比较与叶序预测", "时间整合能否更好地解释启动节律与叶序变异？",
          ["相同运输、生长与信号换算设定下比较瞬时阈值与时间整合", "留出茎尖检验DR5延迟与平均发生间隔；文献叶序检验发散角变异与发生顺序", "分析茎尖大小的影响，预测改变处理时长、抑制极性运输后的叶序"])]
CW, CG, CY, CH = 3.93, 0.27, 2.62, 4.4
for k, (head, q, items) in enumerate(CARDS):
    x = 0.5 + k * (CW + CG)
    shape(CT, MSO_SHAPE.ROUNDED_RECTANGLE, x, CY, CW, CH, fill=CARD, adj=0.03)
    shape(CT, MSO_SHAPE.ROUNDED_RECTANGLE, x, CY, CW, 0.6, fill=BLUE, adj=0.12)
    text(CT, x, CY, CW, 0.6, [para(head, 16, True, WHITE, HEAD, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
    paras = [para(q, 15, True, BLUE, HEAD, after=8, line=1.1)]
    for it in items:
        paras.append(dict(runs=[("▪ ", 14, False, GOLD, BODY), (it, 15, False, INK, BODY)], after=6, line=1.12))
    text(CT, x + 0.18, CY + 0.75, CW - 0.36, CH - 0.85, paras)
    if k < 2:
        a = shape(CT, MSO_SHAPE.RIGHT_ARROW, x + CW + 0.02, CY + 0.17, CG - 0.04, 0.26, fill=RGBColor(0x8C, 0x9B, 0xB0))
notes(CT, "本研究围绕一个科学问题：在拟南芥茎尖中，细胞对生长素信号的时间整合如何影响原基启动与叶序形成。把它拆成三个依次推进的研究内容。第一，茎尖成像数据的定量分析，回答原基处生长素输入怎样变化、DR5响应何时出现：以P0为参照按叶间期对齐原基阶段，定量生长素升高与DR5激活的时间、低生长素区和PIN1极性，再追踪细胞位置，推算每个细胞经历的生长素变化。第二，生长素–PIN1模型的建立与检验，回答运输与响应能否解释观测到的空间分布和响应延迟：在已有表皮层与内层模型上比较模拟与实测的空间分布、优化运输模型；把细胞生长素轨迹输入响应模型，区分中央与周边的响应，经报告信号换算后对照DR5确定响应模型。第三，两类启动规则的比较与叶序预测，回答时间整合能否更好地解释启动节律与叶序变异：在相同设定下比较瞬时阈值与时间整合，用留出的茎尖和文献叶序分别检验，并预测改变生长素处理时长和抑制极性运输后的叶序变化。")

RD = new_slide("RS", "技术路线")
pic = picture(RD, FIG / "fig2-1_roadmap.png", 0, 1.62, h=5.3)
pic.left = int((prs.slide_width - pic.width) / 2)
text(RD, 0.5, 6.95, 12.33, 0.3, [para("栏间箭头表示前一阶段的产出用于后一阶段；虚线框为可供实验检验的预测。", 12, color=GREY, align=PP_ALIGN.CENTER)])
notes(RD, "技术路线从顶部的科学问题出发，分三个阶段依次推进，栏间的箭头表示前一阶段的产出交给后一阶段。第一阶段是成像定量，回答茎尖生长素输入的时空分布与DR5响应时序：左支对齐原基阶段、追踪细胞并推算细胞经历的生长素变化，右支是PIN1成像和qDII成像两项并行测量，得到生长素轨迹、DR5时序与空间分布。第二阶段是机制建模，回答空间分布与响应延迟的形成机制：左支优化运输模型直到再现生长素输入分布，右支建立区分中央与周边的响应模型，经报告信号换算对照DR5，二者衔接得到运输与响应模型。第三阶段是规则检验：瞬时阈值和时间整合两类规则在相同设定下比较，分别用留出茎尖信号和成熟茎叶序检验，得到两类规则的解释力及其预测出现差异的条件，并由此给出可检验的预测。最终构建从生长素输入、细胞响应、原基启动到叶序形成的生长素–PIN1模型，明确时间整合在何种条件下影响原基启动时序、叶序精度与稳健性。")

# ---------------------------------------------------------------- problems and measures
PB = new_slide("RS", "存在问题及拟采取的解决措施")
ROWS = [("报告信号与模型变量不能直接对应", "DII在生长素较高时饱和；DR5荧光蛋白成熟慢、不带降解信号会累积，易被误当作时间整合",
         "建立报告信号换算模型：生长素水平换算为DII信号，转录响应经报告蛋白合成、成熟和降解换算为DR5信号；在报告蛋白寿命的合理范围内评估时间整合参数，标出接近饱和的区域"),
        ("原基阶段自动标注可信度不足", "较早的预定位点和较老原基的自动标注不可靠，影响时序重建",
         "优先采用可信度高的位点，其余结合表面曲率人工核对；用0、5、10 h时间序列中同一位点的变化衔接相邻阶段，检验以叶间期为阶段间隔是否合理"),
        ("参数难以分别确定", "合成、运输和排出强度的不同组合可给出相近的空间分布",
         "实测参数与适用的文献参数直接取值；相互影响的参数在预定范围内抽样，按低生长素区、PIN1极性和区域输入比值等多种数据筛选；叶序统计不参与筛选，留作最终检验")]
RH, RG = 1.55, 0.17
for i, (t, d, m) in enumerate(ROWS):
    y = 1.98 + i * (RH + RG)
    shape(PB, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5, y, 4.95, RH, fill=CARD, adj=0.06)
    badge(PB, 0.7, y + 0.2, 0.42, str(i + 1), 15)
    text(PB, 1.25, y + 0.12, 4.1, RH - 0.2, [para(t, 16, True, INK, HEAD, after=4), para(d, 13, color=GREY, line=1.1)])
    shape(PB, MSO_SHAPE.RIGHT_ARROW, 5.58, y + RH / 2 - 0.17, 0.42, 0.34, fill=RGBColor(0x8C, 0x9B, 0xB0))
    shape(PB, MSO_SHAPE.ROUNDED_RECTANGLE, 6.13, y, 6.7, RH, fill=CARD2, adj=0.06)
    text(PB, 6.35, y + 0.1, 6.3, RH - 0.2, [para(m, 15, line=1.12)], anchor=MSO_ANCHOR.MIDDLE)
text(PB, 6.13, 1.62, 6.7, 0.35, [para("拟采取的措施", 14, True, RGBColor(0x38, 0x6C, 0x2E), HEAD)])
text(PB, 0.5, 1.62, 4.95, 0.35, [para("可能存在的问题", 14, True, BLUE, HEAD)])
notes(PB, "研究中可能存在三个问题。第一，报告信号与模型变量不能直接对应：DII类报告在生长素较高时接近饱和；DR5报告的荧光蛋白需要时间成熟，又不带降解信号，会在细胞中持续积累，这种积累本身就有时间上的累积效应，可能被误当作细胞对生长素的时间整合。对此拟建立报告信号的换算模型，在报告蛋白寿命的合理范围内评估时间整合参数的变化。第二，原基阶段的自动标注可信度不足，拟优先采用可信度高的位点，其余结合表面曲率人工核对，并用0、5、10小时同一位点的变化衔接相邻阶段。第三，参数难以分别确定：不同参数组合可能给出相近的空间分布。拟将实测和适用的文献参数直接取值，相互影响的参数在预定范围内抽样，用多种空间数据筛选；叶序统计不参与筛选，留作最终检验。")

# ---------------------------------------------------------------- expected results
EX = new_slide("PL", "预期结果与应用价值")
text(EX, 0.5, 1.68, 6.0, 0.45, [para("预期结果", 20, True, BLUE, HEAD)])
EXP = [("模型", "建立以细胞响应衔接时间整合的生长素–PIN1叶序模型，由茎尖定量成像数据给出其参数取值范围"),
       ("规则比较", "定量比较瞬时阈值与时间整合在发生间隔、发散角变异和发生顺序上的差异，明确时间整合起作用的条件"),
       ("可检验预测", "预测延长或缩短生长素处理、抑制极性运输后的叶序变化，供实验检验")]
EW, EG = 3.93, 0.27
for k, (h, t) in enumerate(EXP):
    x = 0.5 + k * (EW + EG)
    shape(EX, MSO_SHAPE.ROUNDED_RECTANGLE, x, 2.2, EW, 2.75, fill=CARD, adj=0.04)
    badge(EX, x + 0.25, 2.42, 0.5, str(k + 1), 17)
    text(EX, x + 0.9, 2.42, EW - 1.05, 0.5, [para(h, 18, True, INK, HEAD)], anchor=MSO_ANCHOR.MIDDLE)
    text(EX, x + 0.25, 3.1, EW - 0.5, 1.75, [para(t, 16, line=1.15)])
text(EX, 0.5, 5.15, 6.0, 0.45, [para("应用价值", 20, True, BLUE, HEAD)])
shape(EX, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5, 5.65, 12.33, 1.35, fill=BLUE, adj=0.08)
text(EX, 0.8, 5.65, 11.73, 1.35, [
    dict(runs=[("▪ ", 15, False, GOLD, BODY), ("模型预测用于确定后续实验的观测指标、成像时间和处理条件", 16, False, WHITE, BODY)], after=6),
    dict(runs=[("▪ ", 15, False, GOLD, BODY), ("模型及配套的成像定量和叶序统计流程可用于其他突变体和作物的叶序分析", 16, False, WHITE, BODY)])],
    anchor=MSO_ANCHOR.MIDDLE)
notes(EX, "本研究预期得到三方面结果。一是建立以细胞响应衔接时间整合的生长素–PIN1叶序模型，并由茎尖定量成像数据给出其参数取值范围。二是在同一模型中定量比较瞬时阈值与时间整合两类启动规则产生的发生间隔、发散角变异和发生顺序，明确时间整合起作用的条件。三是预测延长或缩短生长素处理、抑制极性运输后叶序的变化，供实验检验。在应用上，这些预测可用于确定后续实验的观测指标、成像时间和处理条件；模型及配套的成像定量和叶序统计流程，也可用于其他突变体和作物的叶序分析。")

# ---------------------------------------------------------------- workload and schedule (Gantt)
SC = new_slide("PL", "工作量估计与进度安排")
GX0, GX1, GY0 = 4.15, 12.83, 1.72
MONTHS = ["11", "12", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "1"]
MW = (GX1 - GX0) / len(MONTHS)
for (lab, a, b) in (("2026", 0, 2), ("2027", 2, 14), ("2028", 14, 15)):
    shape(SC, MSO_SHAPE.RECTANGLE, GX0 + a * MW + 0.01, GY0, (b - a) * MW - 0.02, 0.36, fill=BLUE)
    text(SC, GX0 + a * MW, GY0, (b - a) * MW, 0.36, [para(lab, 14, True, WHITE, ("Times New Roman", "宋体"), align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE, inset=0)
for i, mth in enumerate(MONTHS):
    shape(SC, MSO_SHAPE.RECTANGLE, GX0 + i * MW + 0.01, GY0 + 0.4, MW - 0.02, 0.32, fill=RGBColor(0xDC, 0xE4, 0xF0))
    text(SC, GX0 + i * MW, GY0 + 0.4, MW, 0.32, [para(mth, 13, color=INK, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE, inset=0)
TASKS = [("成像数据定量", "约3个月", 0, 3, RGBColor(0xC5, 0x5A, 0x11), "阶段信号曲线、低生长素区范围与深度、细胞生长素轨迹"),
         ("模型完善与检验", "约6个月", 3, 9, RGBColor(0x54, 0x82, 0x35), "运输与响应模型代码及检验结果"),
         ("规则比较与叶序预测", "约3个月", 9, 12, RGBColor(0x2F, 0x55, 0x97), "两类规则的比较结果与可检验预测"),
         ("论文撰写", "约3个月", 12, 15, RGBColor(0x7F, 0x7F, 0x7F), "学位论文")]
TY0, TR = GY0 + 0.95, 1.02
for i, (name, dur, a, b, col, out) in enumerate(TASKS):
    y = TY0 + i * TR
    if i % 2 == 0:
        shape(SC, MSO_SHAPE.RECTANGLE, 0.5, y - 0.06, GX1 - 0.5, TR - 0.06, fill=RGBColor(0xF6, 0xF8, 0xFB))
    text(SC, 0.6, y, 3.5, 0.42, [para(name, 17, True, INK, HEAD)])
    text(SC, 0.6, y + 0.42, 3.5, 0.45, [para("产出：" + out, 12, color=GREY, line=1.05)])
    shape(SC, MSO_SHAPE.ROUNDED_RECTANGLE, GX0 + a * MW + 0.04, y + 0.12, (b - a) * MW - 0.08, 0.5, fill=col, adj=0.3)
    text(SC, GX0 + a * MW, y + 0.12, (b - a) * MW, 0.5, [para(dur, 14, True, WHITE, HEAD, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE, inset=0)
text(SC, 0.5, 6.78, 12.3, 0.35, [dict(runs=[("已完成：", 13, True, BLUE, HEAD), ("图像处理与茎尖形态测量；生长素–PIN1基础模型、改进与文献参数检验；数据处理与检验流程", 13, False, GREY, BODY)])])
notes(SC, "工作量和进度安排如下。第一项成像数据定量约3个月，2026年11月到2027年1月：核对原基阶段，提取PIN1极性，定量原基周围低生长素区，确定DR5的激活时序和平均发生间隔，推算细胞经历的生长素变化。第二项模型完善与检验约6个月，2027年2月到7月：优化运输模型并检验，建立响应模型，与两类启动规则衔接。第三项规则比较与叶序预测约3个月，2027年8月到10月。最后3个月整理结果、撰写学位论文。图像处理、茎尖形态测量和基础模型都已完成，后续工作都在前期建立的数据流程、模型代码和检验流程上开展。")

# ---------------------------------------------------------------- references
RF = new_slide("PL", "主要参考文献")
REFS = [
    "[1] KUHLEMEIER C. Phyllotaxis[J]. Trends in Plant Science, 2007, 12(4): 143-150.",
    "[2] VERNOUX T, BRUNOUD G, FARCOT E, et al. The auxin signalling network translates dynamic input into robust patterning at the shoot apex[J]. Molecular Systems Biology, 2011, 7: 508.",
    "[4] REINHARDT D, PESCE E R, STIEGER P, et al. Regulation of phyllotaxis by polar auxin transport[J]. Nature, 2003, 426(6964): 255-260.",
    "[11] JÖNSSON H, HEISLER M G, SHAPIRO B E, et al. An auxin-driven polarized transport model for phyllotaxis[J]. PNAS, 2006, 103(5): 1633-1638.",
    "[12] SMITH R S, GUYOMARC’H S, MANDEL T, et al. A plausible model of phyllotaxis[J]. PNAS, 2006, 103(5): 1301-1306.",
    "[16] BESNARD F, REFAHI Y, MORIN V, et al. Cytokinin signalling inhibitory fields provide robustness to phyllotaxis[J]. Nature, 2014, 505(7483): 417-421.",
    "[17] REFAHI Y, BRUNOUD G, FARCOT E, et al. A stochastic multicellular model identifies biological watermarks from disorders in self-organized patterns of phyllotaxis[J]. eLife, 2016, 5: e14093.",
    "[18] BRUNOUD G, WELLS D M, OLIVA M, et al. A novel sensor to map auxin response and distribution at high spatio-temporal resolution[J]. Nature, 2012, 482(7383): 103-106.",
    "[20] GALVAN-AMPUDIA C S, CERUTTI G, LEGRAND J, et al. Temporal integration of auxin information for the regulation of patterning[J]. eLife, 2020, 9: e55832.",
    "[22] MIRABET V, BESNARD F, VERNOUX T, et al. Noise and robustness in phyllotaxis[J]. PLoS Computational Biology, 2012, 8(2): e1002389.",
]
text(RF, 0.6, 1.75, 12.1, 5.2, [para(r, 13, line=1.05, after=5) for r in REFS])
text(RF, 0.6, 6.95, 12.1, 0.3, [para("编号与开题报告参考文献列表一致；完整列表（共25篇）见开题报告。", 11, color=GREY)])
notes(RF, "这是汇报中引用的主要参考文献，编号与开题报告一致，完整列表见开题报告。")

# ---------------------------------------------------------------- order, drop the rest
NEW_ORDER = [S[0], OUT, S[1], S[2], S[3], S[4], S[5], S[6], S[8], S[9], S[7], S[10], S[11],
             GAP, W1, W2, W3, CT, RD, PB, EX, SC, RF, S[23]]
lst = prs.slides._sldIdLst
by_part = {}
for sid in list(lst):
    by_part[prs.part.related_part(sid.get(qn("r:id")))] = sid
keep = [by_part[s.part] for s in NEW_ORDER]
for sid in list(lst):
    lst.remove(sid)
    if sid not in keep:
        prs.part.drop_rel(sid.get(qn("r:id")))
for sid in keep:
    lst.append(sid)
for s in NEW_ORDER:
    renumber(s)
out = K / "开题汇报_张希程.pptx"
prs.save(out)
print("saved", out, len(prs.slides), "slides")
