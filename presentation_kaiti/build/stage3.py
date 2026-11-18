"""Stage 3: proposal-defence deck in the reference style (built from base.pptx; all original slides are dropped)."""
import copy, re
from pathlib import Path
from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

K = Path(__file__).resolve().parent
FIG = Path("/home/user/model/figures/prior_work")
BGF = K / "bgfig"
DBG = K / "deckbg"
prs = Presentation(K / "base.pptx")
S = list(prs.slides)
LAY = {l.name: l for l in prs.slide_layouts}

BLUE, GOLD, INK, GREY = RGBColor(0x1F, 0x4E, 0x99), RGBColor(0xB8, 0x97, 0x5A), RGBColor(0x1A, 0x1A, 0x1A), RGBColor(0x59, 0x59, 0x59)
WHITE, CARD, CARD2 = RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0xF1, 0xF4, 0xF9), RGBColor(0xEE, 0xF4, 0xEA)
RULE, NAVY, PALE = RGBColor(0x27, 0x6A, 0x9A), RGBColor(0x37, 0x60, 0x92), RGBColor(0x6E, 0x9A, 0xB9)
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



# ---------------------------------------------------------------- overrides for the new style
TITLE = next(sh for sh in S[1].shapes if sh.name == "Text 9")._element
SLDNUM = next(sh for sh in S[1].shapes if sh.name.startswith("Slide Number"))._element


def new_slide(layout, title=None):
    s = prs.slides.add_slide(LAY[layout])
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    if title is not None:
        t = copy.deepcopy(TITLE)
        s.shapes._spTree.append(t)
        set_runs(t, [(title, 24)])
        sh = s.shapes[-1]
        sh.left, sh.top, sh.width, sh.height = Inches(0.62), Inches(1.0), Inches(12.1), Inches(0.56)
    if layout != "DEFAULT":
        s.shapes._spTree.append(copy.deepcopy(SLDNUM))
    return s


def source(s, t, y=7.06):
    text(s, 0.62, y, 9.0, 0.3, [para(t, 10, color=GREY)])


def aspect(path):
    w, h = Image.open(path).size
    return w / h


def figs(s, items, y0, hmax, x0=0.62, x1=12.71, gap=0.4):
    """A row of figures scaled to one height; each item (file, caption, source). Returns the bottom of the captions."""
    paths = [BGF / f for f, _, _ in items]
    ars = [aspect(p) for p in paths]
    h = min(hmax, (x1 - x0 - gap * (len(items) - 1)) / sum(ars))
    total = h * sum(ars) + gap * (len(items) - 1)
    x = x0 + (x1 - x0 - total) / 2
    for p, a, (_, cap, src) in zip(paths, ars, items):
        w = a * h
        picture(s, p, x, y0, h=h)
        cw = max(w + gap - 0.06, 2.6)
        text(s, x + w / 2 - cw / 2, y0 + h + 0.06, cw, 0.32, [para(cap, 13, align=PP_ALIGN.CENTER)])
        text(s, x + w / 2 - cw / 2, y0 + h + 0.36, cw, 0.26, [para(src, 10, color=GREY, align=PP_ALIGN.CENTER)])
        x += w + gap
    return y0 + h + 0.62


def fig_at(s, f, x, y, w=None, h=None, cap=None, src=None, cw=None):
    p = BGF / f
    a = aspect(p)
    if w is None:
        w = a * h
    h = w / a
    picture(s, p, x, y, w=w)
    cw = cw or max(w, 2.6)
    if cap:
        text(s, x + w / 2 - cw / 2, y + h + 0.06, cw, 0.32, [para(cap, 13, align=PP_ALIGN.CENTER)])
    if src:
        text(s, x + w / 2 - cw / 2, y + h + 0.36, cw, 0.26, [para(src, 10, color=GREY, align=PP_ALIGN.CENTER)])
    return y + h + 0.62


def takeaway(s, t, y=6.62):
    text(s, 0.62, y, 12.09, 0.4, [para(t, 16, True, RULE, HEAD, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)


def frame_lines(s, color=WHITE):
    """Corner brackets and a rule, as on the reference cover."""
    for x0, x1, y in ((1.37, 2.45, 0.82), (10.88, 11.96, 0.82)):
        shape(s, MSO_SHAPE.RECTANGLE, x0, y, x1 - x0, 0.035, fill=color)
    for x in (1.37, 11.925):
        shape(s, MSO_SHAPE.RECTANGLE, x, 0.82, 0.035, 1.1, fill=color)
    shape(s, MSO_SHAPE.RECTANGLE, 2.35, 1.37, 8.65, 0.012, fill=color)


def logo_disc(s, cx, cy, d):
    shape(s, MSO_SHAPE.OVAL, cx - d / 2, cy - d / 2, d, d, fill=WHITE)
    picture(s, K / "work_b" / "ppt" / "media" / "image4.png", cx - d * 0.45, cy - d * 0.45, w=d * 0.9, h=d * 0.9)


# ---------------------------------------------------------------- cover
CV = new_slide("DEFAULT")
picture(CV, DBG / "cover_bg.jpg", 0, 0, w=13.333, h=7.5)
frame_lines(CV)
text(CV, 4.1, 0.55, 2.4, 0.5, [para("公诚勇毅", 18, True, WHITE, HEAD, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
text(CV, 6.85, 0.55, 2.4, 0.5, [para("三实一新", 18, True, WHITE, HEAD, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
text(CV, 1.0, 1.75, 11.33, 0.5, [para("硕士学位论文开题报告", 22, False, WHITE, HEAD, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
text(CV, 1.0, 2.35, 11.33, 2.2, [para("拟南芥叶序形成中", 46, True, WHITE, HEAD, align=PP_ALIGN.CENTER),
                                   para("生长素时间整合的建模研究", 46, True, WHITE, HEAD, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
logo_disc(CV, 6.667, 6.3, 1.55)
text(CV, 0.7, 5.8, 3.4, 0.45, [para("汇报人：张希程", 20, False, RULE, HEAD)])
text(CV, 0.7, 6.45, 3.4, 0.45, [para("导　师：齐继艳 教授", 20, False, RULE, HEAD)])
text(CV, 9.23, 5.8, 3.4, 0.45, [para("生命科学与技术学院", 20, False, RULE, HEAD, align=PP_ALIGN.RIGHT)])
text(CV, 8.83, 6.45, 3.8, 0.45, [para("答辩时间：2026年11月", 20, False, RULE, HEAD, align=PP_ALIGN.RIGHT)])
notes(CV, "各位老师好，我是生命科学与技术学院生物技术与工程专业的张希程，导师是齐继艳教授。我的论文题目是《拟南芥叶序形成中生长素时间整合的建模研究》。下面从研究背景、研究意义、已有工作积累、研究内容与方案、预期结果与进度五个方面汇报。")

# ---------------------------------------------------------------- contents
CO = new_slide("DEFAULT")
picture(CO, DBG / "contents_bg.jpg", 0, 0, w=13.333, h=7.5)
shape(CO, MSO_SHAPE.RECTANGLE, 1.37, 0.82, 1.08, 0.035, fill=WHITE)
shape(CO, MSO_SHAPE.RECTANGLE, 1.37, 0.82, 0.035, 1.1, fill=WHITE)
shape(CO, MSO_SHAPE.RECTANGLE, 0.95, 1.95, 0.012, 3.15, fill=WHITE)
text(CO, 1.6, 4.05, 2.6, 0.5, [dict(runs=[("/CONTENT", 24, False, WHITE, ("Times New Roman", "Times New Roman"))])])
logo_disc(CO, 5.0, 3.72, 1.42)
SECTIONS = [("01", "研究背景", "BACKGROUND"), ("02", "研究意义", "SIGNIFICANCE"), ("03", "已有工作积累", "PRIOR WORK"),
            ("04", "研究内容与方案", "RESEARCH PLAN"), ("05", "预期结果与进度", "OUTCOMES & SCHEDULE")]
for i, (n, cn, en) in enumerate(SECTIONS):
    y = 0.8 + i * 1.25
    text(CO, 6.75, y, 1.3, 0.75, [dict(runs=[(n, 36, False, RULE, ("Times New Roman", "Times New Roman"))])], anchor=MSO_ANCHOR.MIDDLE)
    text(CO, 8.55, y, 4.3, 0.5, [para(cn, 24, False, RULE, HEAD)], anchor=MSO_ANCHOR.MIDDLE)
    text(CO, 8.55, y + 0.5, 4.3, 0.36, [dict(runs=[(en, 14, False, PALE, ("Times New Roman", "Times New Roman"))])])
notes(CO, "汇报分五部分：先介绍研究背景和本研究的意义，然后是前期已经完成的工作，接着是研究内容、技术路线以及可能遇到的问题和解决措施，最后是预期结果与进度安排。")

# ---------------------------------------------------------------- 01 research background
B1 = new_slide("BG", "叶序：侧生器官绕茎轴的规则排列")
figs(B1, [("s02_1.png", "二列互生、螺旋、交互对生与轮生", "Kuhlemeier C. Trends Plant Sci. (2007)"),
          ("s02_2.png", "拟南芥野生型与ahp6的花序及茎尖", "Refahi Y., et al. eLife (2016)")], 1.75, 4.0)
takeaway(B1, "螺旋叶序中相继器官多以接近137.5°的发散角排列；这些器官来自茎尖周边依次发生的原基")
notes(B1, "首先介绍叶序。叶片、花等侧生器官绕植物茎轴的排列方式称为叶序，常见类型包括二列、螺旋、交互对生和轮生，左图来自Kuhlemeier的综述，下方的圆环是对应的横切示意。最常见的是螺旋叶序，相继发生的器官多以接近137.5°的发散角依次排列，呈现出规则的几何结构。右图是拟南芥花序：野生型的长角果沿茎呈规则的螺旋排列，ahp6突变体的排列明显不规则；最右是茎尖的电镜照片，原基按发生先后编号。这些器官都由茎尖分生组织周边的原基发育而来，原基之间的局部相互作用与茎尖的形态、生长共同影响新原基发生的位置和时间，螺旋叶序就在这一过程中逐步形成。（Kuhlemeier, 2007；Refahi et al., 2016；Godin et al., 2020）")

B2 = new_slide("BG", "茎尖分生组织：原基在周边区依次发生")
figs(B2, [("s03_1.png", "A 中央区（CZ）与周边区（PZ）；B 生长素传感器与CLV3；C 茎尖生长素分布", "Galvan-Ampudia C.S., et al. eLife (2020)")], 1.85, 4.05)
takeaway(B2, "原基之间的局部相互作用与茎尖的形态、生长共同决定新原基发生的位置与时间")
notes(B2, "叶序中的器官都来自茎尖分生组织。图中是拟南芥花序茎尖的俯视图。A中洋红色是中央区，里面是干细胞；青色是周边区，新的花原基就在周边区的特定位置逐个产生。B同时显示了生长素传感器和干细胞标记CLV3，图上按发生次序给原基编号：P0是正在发生的原基，P-1、P-2是接下来将要发生的位置，P1、P2、P3依次更老。C是由B换算出的生长素分布。可以看到，在茎尖上已经能在细胞分辨率下同时看到原基的位置和生长素的分布。生长素是介导原基之间相互作用的重要信号，下面先看它如何决定原基发生的位置。（Galvan-Ampudia et al., 2020）")

B3 = new_slide("BG", "生长素的局部积累诱导原基发生")
figs(B3, [("s04_1.png", "pin1：花序轴顶端不形成花芽", "Okada K., et al. Plant Cell (1991)"),
          ("s04_2.png", "番茄：在预定位点施加IAA", "Reinhardt D., et al. Plant Cell (2000)"),
          ("s04_3.png", "pin1：局部施加IAA诱导花芽", "Reinhardt D., et al. Plant Cell (2000)")], 1.9, 3.9)
takeaway(B3, "生长素的局部积累是原基发生的重要条件，并决定侧生器官的径向位置")
notes(B3, "生长素的局部积累是原基发生的重要条件。左图来自Okada等1991年：极性运输严重受损的拟南芥pin-formed1，也就是pin1突变体，花序轴顶端不形成花芽，呈针状；用极性运输抑制剂处理野生型也得到相同表型。中图和右图来自Reinhardt等2000年：在番茄茎尖将要发生原基的位点施加IAA，可以诱导出原基；在pin1花序顶端的侧面局部施加IAA，就能在施加位点所在的径向位置诱导出花芽。作者据此提出，生长素决定侧生器官的径向位置。那么在野生型茎尖中，这种局部高浓度是怎样产生的？（Okada et al., 1991；Reinhardt et al., 2000）")

B4 = new_slide("BG", "PIN1极性运输塑造生长素的分布")
figs(B4, [("s05_1.png", "PIN1在原基及位点I1–I3富集", "Reinhardt D., et al. Nature (2003)"),
          ("s05_2.png", "PIN1极性指向I1", "Heisler M.G., et al. Curr. Biol. (2005)"),
          ("s05_3.png", "极性运输模型：已有原基作为汇", "Reinhardt D., et al. Nature (2003)")], 1.75, 4.15)
takeaway(B4, "生长素持续流向已有原基，新的积累只出现在与已有原基保持一定距离的位置")
notes(B4, "在野生型茎尖中，局部高浓度由生长素外排载体PIN1介导的定向运输产生。左图来自Reinhardt等2003年，PIN1信号集中在各原基的中心，以及将要发生原基的位点I1到I3。中图来自Heisler等2005年的活体成像，箭头表示PIN1在细胞中的极性：周围细胞都把PIN1指向I1，生长素在I1汇聚；他们还发现生长素水平随原基发育经历积累与消退的循环。右图是Reinhardt等提出的模型：已有原基像汇一样吸走生长素，在它周围形成生长素较低的区域，因此新的积累只出现在与已有原基保持一定最小间距的位置，并在那里诱导新原基。不过，生长素的积累并不等于细胞的响应。（Reinhardt et al., 2003；Heisler et al., 2005）")

B5 = new_slide("BG", "生长素积累不等于转录响应，响应又反过来调节运输")
fig_at(B5, "vernoux5BD.png", 0.62, 2.35, w=7.75, cap="茎尖中的DII-VENUS（B）、不可降解对照mDII（C）与DR5（D）", src="Vernoux T., et al. Mol. Syst. Biol. (2011)")
fig_at(B5, "bhatia_ga.png", 8.83, 1.72, w=3.88, cap="MONOPTEROS经正反馈调节PIN1极性", src="Bhatia N., et al. Curr. Biol. (2016)")
takeaway(B5, "原基定位既取决于生长素被运往何处，也取决于细胞如何响应：运输与响应相互耦合")
notes(B5, "生长素并不只在原基处出现。左图来自Vernoux等2011年，B是生长素传感器DII-VENUS，信号越弱表示生长素越高；C是不受生长素降解的对照mDII；D是由生长素响应元件串联构成的合成启动子DR5驱动的转录报告。可以看到，茎尖中央同样存在生长素积累，但DR5信号很弱，主要出现在原基处，说明积累并不等同于响应。这与中央区和周边区的生长素信号网络组分不同有关，WUSCHEL也被发现能在干细胞中调节生长素响应。右图来自Bhatia等2016年：生长素响应因子MONOPTEROS能调节PIN1极性，反过来影响运输方向，形成正反馈。因此，原基定位既取决于生长素被运往何处，也取决于细胞如何响应，运输与响应在这一过程中相互耦合。（Vernoux et al., 2011；Ma et al., 2019；Bhatia et al., 2016）")

B6 = new_slide("BG", "经典运输模型：PIN1朝高浓度极化，叶序自发形成")
figs(B6, [("s06_1.png", "螺旋与交互对生", "Jönsson H., et al. PNAS (2006)"),
          ("s06_2.png", "二列、交互对生、三叶轮生与螺旋", "Smith R.S., et al. PNAS (2006)"),
          ("s06_3.png", "实测（蓝）与模拟（红）的发散角", "Smith R.S., et al. PNAS (2006)")], 1.85, 3.95)
takeaway(B6, "不需要预设137.5°，模型在实测误差范围内再现了拟南芥幼苗的发散角")
notes(B6, "经典的叶序运输模型主要刻画运输过程。Jönsson等和Smith等在2006年假设PIN1优先朝向生长素浓度较高的相邻细胞极化，使生长素进一步向这些细胞汇聚；这一极化规则是模型假设。左图是Jönsson模型，在半球面上自发形成螺旋和交互对生的生长素峰；中图是Smith模型在生长的茎尖上模拟出的二列互生、交互对生、三叶轮生和螺旋；右图比较了实测（蓝）和模拟（红）的发散角，模型在实测误差范围内再现了拟南芥幼苗的发散角。也就是说，不需要预先设定137.5°，叶序就能从生长素运输的自组织中产生。不过这些模拟主要在表层展开，原基形成后生长素向内部组织的输送只以简化的排出规则表示。（Jönsson et al., 2006；Smith et al., 2006）")

B7 = new_slide("BG", "模型由表层汇聚扩展到向内运输")
figs(B7, [("bayer_mid.png", "双极化模型：原基定位与中脉形成", "Bayer E.M., et al. Genes Dev. (2009)"),
          ("deb_abl.png", "番茄：消融原基中脉前后", "Deb Y., et al. Development (2015)"),
          ("hartmann3d.png", "三维模型：表层汇聚与向内运输", "Hartmann F.P., et al. PLoS Comput. Biol. (2019)")], 1.85, 3.95)
takeaway(B7, "原基形成后生长素经中脉向内排出，这一排出有助于维持叶序间隔的稳定")
notes(B7, "为描述表层汇聚与内部运输之间的联系，Bayer等2009年提出双极化模型，让朝向高浓度和沿通量的两种PIN1极化同时起作用，再现了原基定位与中脉形成过程中观测到的PIN1定位动态，左图下方是他们的示意。中图来自Deb等2015年的番茄消融实验：消融原基中脉后，原基的生长素排出受阻，叶序间隔的稳定性下降，支持原基经中脉向内排出生长素。右图是Hartmann等2019年的三维模型，把表层汇聚与向内运输放在同一组织中模拟，再现了茎尖中大部分PIN1极化动态。这些模型刻画了生长素在茎尖中的分配，而原基何时启动，则由模型中另设的规则决定。（Bayer et al., 2009；Deb et al., 2015；Hartmann et al., 2019）")

B8 = new_slide("BG", "原基启动规则：浓度阈值、抑制场与随机发生")
def rule_card(s, x, y, w, h, head, body):
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=CARD, adj=0.08)
    text(s, x + 0.2, y + 0.08, w - 0.4, h - 0.16, [para(head, 17, True, NAVY, HEAD, after=3), para(body, 14, line=1.08)], anchor=MSO_ANCHOR.MIDDLE)
rule_card(B8, 0.62, 1.72, 5.75, 1.05, "① 浓度阈值", "相邻两细胞的生长素浓度达到预设阈值即启动原基（Smith et al., 2006）")
rule_card(B8, 0.62, 2.95, 5.75, 1.05, "③ 随机发生", "发生率随局部抑制水平变化的随机事件（Refahi et al., 2016）")
fig_at(B8, "s07_2.png", 0.62, 4.15, w=5.75, cap="随机多细胞模型模拟的发散角与发生间隔", src="Refahi Y., et al. eLife (2016)")
rule_card(B8, 6.96, 1.72, 5.75, 1.05, "② 细胞分裂素抑制场", "原基中的AHP6向周围移动形成抑制场，规定器官发生的时间顺序（Besnard et al., 2014）")
fig_at(B8, "besnard4de.png", 7.28, 2.95, w=5.1, cap="野生型（d）与ahp6（e）：DR5（品红）与TCS（绿）", src="Besnard F., et al. Nature (2014)", cw=5.75)
takeaway(B8, "这些规则只依据当前状态，细胞所经历的生长素变化如何引发原基启动，尚无模型刻画")
notes(B8, "在这些模型里，原基什么时候启动由另设的规则决定，已有规则大致三类。第一类是浓度阈值，在再现发散角的Smith模型中，相邻两个细胞的生长素浓度达到预设阈值时启动原基，这一规则只依据当前的生长素浓度。第二类来自实验：Besnard等2014年发现，原基中表达的细胞分裂素信号抑制因子AHP6向周围移动形成抑制场，为器官发生规定了时间顺序，使叶序更为稳健；右图中，野生型的细胞分裂素信号TCS在预定位点之间呈规则分布，ahp6中这种分布被打乱。第三类是在抑制场基础上，Refahi等的随机多细胞模型把原基启动看作发生率随局部抑制水平变化的随机事件，左下是模拟的发散角与发生间隔。这些规则分别从生长素浓度、器官间抑制和随机性描述原基启动，而细胞所经历的生长素变化如何经转录响应引发原基启动，还需要借助定量成像来回答。（Smith et al., 2006；Besnard et al., 2014；Refahi et al., 2016）")

B9 = new_slide("BG", "定量成像：在细胞水平分别读出生长素输入与转录输出")
figs(B9, [("s09_1.png", "DII-VENUS显示生长素积累", "Brunoud G., et al. Nature (2012)"),
          ("s09_2.png", "21个茎尖对齐叠加：10 h（E）与0 h旋转137.5°（F）几乎相同", "Galvan-Ampudia C.S., et al. eLife (2020)")], 1.85, 3.95)
takeaway(B9, "独立采集的茎尖对齐后生长素输入分布高度一致，可按叶间期重建平均的发育过程")
notes(B9, "要在茎尖中追踪细胞所经历的生长素变化，需要能在细胞水平分别读出信号输入与转录输出的报告系统。左图来自Brunoud等2012年：DII-VENUS由可被生长素降解的结构域与荧光蛋白融合而成，在生长素作用下迅速降解，可以在细胞分辨率上反映相对的生长素分布；箭头所指的新原基位点信号逐渐消失。此后的比率型报告R2D2以不可降解的mDII为参照作归一化，DR5v2则报告转录输出。右图来自本课题的核心文献Galvan-Ampudia等2020年：21个独立采集的茎尖按原基位置对齐后叠加，10小时的平均分布与0小时分布旋转137.5°后几乎相同。据此，在识别原基阶段后，可以把不同阶段的空间图像按一个叶间期的间隔排在同一时间轴上，重建平均的发育过程。（Brunoud et al., 2012；Liao et al., 2015；Galvan-Ampudia et al., 2020）")

B10 = new_slide("BG", "生长素输入最大区向外推进，PIN1总体指向茎尖中心")
yb = fig_at(B10, "s08_1.png", 0.9, 1.72, w=5.6, cap="最大区不附着于固定细胞（0、5、10 h）")
fig_at(B10, "s08_2.png", 1.4, yb - 0.25, w=4.6, cap="最大区外移快于细胞")
fig_at(B10, "s08_3.png", 7.55, 1.72, h=4.25, cap="PIN1极性指向茎尖中心", src="Galvan-Ampudia C.S., et al. eLife (2020)")
takeaway(B10, "最大区以离心波的形式穿过组织，不同位置的细胞因而经历不同的生长素变化历程")
notes(B10, "同一研究还发现，生长素输入最大区并不固定在特定细胞上。左上追踪了0、5、10小时的细胞核，绿圈是最大区，被追踪的细胞生长素分别迅速下降或上升；左下比较了最大区和细胞的径向位置，最大区起始于茎尖中央的高生长素区，以离心波的形式向外推进，在P1到P4阶段的平均径向速度可以超过细胞的移动速度，所以不同位置的细胞经历不同的生长素变化历程。右图是4个茎尖的PIN1极性矢量：在组织尺度上PIN1总体指向茎尖中心，并在最大区离开中央区时局部偏转。生长素合成基因YUC1、YUC4在较老原基与茎尖的交界处表达，提示较老原基还可能向茎尖供给生长素；侧生器官也会通过竞争下游运输影响茎尖的生长素输出和大小。（Galvan-Ampudia et al., 2020；Shi et al., 2018）")

B11 = new_slide("BG", "转录响应滞后近一个叶间期：细胞对生长素进行时间整合")
figs(B11, [("s10_1.png", "各阶段生长素输入（G）与DR5转录输出（H）", "Galvan-Ampudia C.S., et al. eLife (2020)"),
           ("s10_2.png", "IAA处理30、120、300 min后的DR5", "Galvan-Ampudia C.S., et al. eLife (2020)")], 1.9, 3.9)
takeaway(B11, "转录响应取决于生长素浓度与作用时长的共同作用——时间整合")
notes(B11, "最关键的发现是时间整合。左图G和H分别是各原基阶段的生长素输入和DR5转录输出：在原基形成的位置，生长素输入升高后，DR5要再过近一个叶间期才开始表达；同样的生长素水平在不同细胞中引起的DR5响应也不相同，与细胞此前的经历有关。右图是外施IAA的实验：各处理都使周边区的生长素输入普遍升高，但短时处理主要在已经接触过生长素的位点增强DR5，延长处理时间后周边区大多数细胞才出现响应；浓度较低而时间较长的处理，可以引起与浓度较高而时间较短的处理相当甚至更强的响应。可见转录响应取决于生长素浓度与作用时长的共同作用，这被称为时间整合。它可能依赖ARF介导的核内信号通路，arf3突变体的叶序也出现异常；每日限时施加IAA同样会改变叶序。这说明时间整合参与叶序调控，但它如何影响原基的发生间隔、发散角和发生顺序，目前还不清楚。（Galvan-Ampudia et al., 2020）")

B12 = new_slide("BG", "叶序的变异：同时起始与次序颠倒")
yb = fig_at(B12, "s12_1.png", 1.0, 1.72, w=5.0, cap="时序成像：野生型（e）与ahp6（f）的器官起始")
fig_at(B12, "s12_2.png", 1.35, yb - 0.25, w=4.3, cap="同时起始、次序颠倒与发散角分布", src="Besnard F., et al. Nature (2014)")
fig_at(B12, "s12_3.png", 7.3, 1.72, h=4.2, cap="发散角序列：野生型与ahp6（黑线实测，蓝线模型）", src="Refahi Y., et al. eLife (2016)", cw=5.4)
takeaway(B12, "变异的类型与频率反映原基启动的规则，可用来反推控制叶序动态的参数")
notes(B12, "叶序并不完美。原基的发生间隔、发散角和发生顺序并非固定不变：即使在野生型拟南芥中，相邻原基的发生间隔也会波动，茎上器官的次序时有颠倒。左侧来自Besnard等2014年，上方是每12小时一帧的时序成像，星号表示同时起始的器官；下方统计显示，相邻器官同时起始是次序颠倒的主要来源，ahp6中这类同时起始明显增多。Mirabet等的理论分析表明，在抑制场模型中加入随机性后，螺旋叶序会出现手性反转、器官同时起始和二列发散角三类缺陷。右图来自Refahi等2016年，是相邻长角果之间的发散角序列，黑线实测、蓝线模型预测；他们指出这些异常可以用来反推控制叶序动态的参数。所以，叶序的稳健性不仅体现在平均发散角上，也体现在发生间隔和发生顺序的稳定程度上。（Besnard et al., 2014；Mirabet et al., 2012；Refahi et al., 2016）")

B13 = new_slide("BG", "茎尖大小、生长素信号与叶序")
figs(B13, [("s11_1.png", "茎尖越大，次序颠倒越多", "Landrein B., et al. J. Exp. Bot. (2015)"),
           ("s11_2.png", "玉米abph1：茎尖增大，叶序变为交互对生", "Giulini A., et al. Nature (2004)"),
           ("lee_scheme.png", "生长素、ZmPIN1a与ABPH1的相互作用", "Lee B.H., et al. Plant Physiol. (2009)")], 1.95, 3.6)
takeaway(B13, "实验中茎尖大小与生长素信号往往同时改变，模型可以分别改变二者，区分各自的作用")
notes(B13, "茎尖大小也与叶序的稳健性和类型有关。左图来自Landrein等2015年：缩短日照使茎尖变大，器官位置的异常增多，这些异常多与器官出现节律的改变有关，原基起始的空间位置并未改变；示意中茎尖越大，可供原基发生的圆周越长，次序颠倒越多。中图来自Giulini等2004年：玉米aberrant phyllotaxy1，即abph1突变体的茎尖增大，叶序由二列互生转为交互对生；但用细胞分裂素使培养胚的茎尖扩大到相近程度，却没有观察到叶序改变。右图来自Lee等2009年的进一步研究：该突变体叶原基起始处的PIN1表达出现较晚，胚中的生长素水平也较低，据此推测生长素和PIN1水平降低推迟了叶原基起始，进而促成茎尖扩大和叶序改变。可见实验中茎尖大小与生长素信号往往同时改变，模型可以分别改变二者，区分各自对叶序的作用。（Landrein et al., 2015；Giulini et al., 2004；Lee et al., 2009）")

# ---------------------------------------------------------------- 02 significance
G1 = new_slide("SG", "现有研究的不足")
fig_at(G1, "ga_fig6.png", 2.2, 1.68, w=8.9, cap="生长素水平、通量与转录响应随原基发育（P-2→P3）的变化示意", src="Galvan-Ampudia C.S., et al. eLife (2020)", cw=8.9)
GAPS = [("时间整合尚未纳入叶序模型", "运输模型以瞬时浓度阈值启动原基，随机发生模型不含生长素运输"),
        ("运输与响应未与成像系统对照", "中央区高输入、位点输入逐步升高与转录滞后近一个叶间期，能否被同时解释"),
        ("两类启动规则缺乏定量比较", "平均发散角可能相近，需要用发生间隔、发生顺序与变异来区分")]
for i, (h, b) in enumerate(GAPS):
    x = 0.62 + i * 4.15
    shape(G1, MSO_SHAPE.ROUNDED_RECTANGLE, x, 5.42, 3.95, 1.55, fill=CARD, adj=0.08)
    badge(G1, x + 0.18, 5.6, 0.42, str(i + 1), 15)
    text(G1, x + 0.72, 5.55, 3.1, 0.5, [para(h, 16, True, NAVY, HEAD)], anchor=MSO_ANCHOR.MIDDLE)
    text(G1, x + 0.2, 6.1, 3.6, 0.85, [para(b, 14, line=1.08)])
notes(G1, "综合以上背景，现有研究有三点不足。上图是Galvan-Ampudia等对时间整合的概括：随着原基从P-2发育到P3，生长素水平先在起始位点逐步升高，转录响应则要滞后一段时间才出现。第一，生长素信号的时间整合虽有成像实验支持，现有叶序模型却尚未纳入这一过程：经典运输模型以某一时刻的浓度阈值触发原基，随机发生模型虽按局部抑制水平累积发生概率，却不包含生长素运输，时间整合因而没有与PIN1运输和原基启动联系起来。第二，成像显示茎尖中央的生长素输入较高、原基起始位点处的输入逐步升高、周边细胞的转录激活滞后近一个叶间期，现有运输规则与细胞响应过程结合后能否同时解释这些现象，尚未得到系统检验。第三，瞬时阈值与时间整合两类规则缺乏统一框架下的定量比较，二者可能给出相近的平均发散角，而在信号响应、发生间隔和发生顺序上不同，因此时间整合对叶序精度与稳健性的作用需要依据这些指标来判断。")

G2 = new_slide("SG", "研究目的与意义")
fig_at(G2, "model_scheme.png", 0.75, 1.72, h=4.55, cap="本研究的生长素–PIN1模型结构（开题报告图1-2 B）", cw=5.4)
AIMS = ["以反映时间整合的细胞响应衔接生长素输入、转录响应与原基启动，检验时间整合能否解释原基依次发生的节律",
        "用茎尖定量成像确定模型参数，检验模型能否同时再现中央区高输入、起始位点输入逐步升高与延迟出现的转录激活",
        "在同一模型中比较瞬时阈值与时间整合，分析时间整合在什么条件下影响叶序的精度与稳健性"]
paras_ = [para("研究目的", 20, True, NAVY, HEAD, after=6)]
for i, a in enumerate(AIMS):
    paras_.append(dict(runs=[(f"{i + 1}. ", 16, True, RULE, BODY), (a, 16, False, INK, BODY)], line=1.15, after=8))
text(G2, 6.55, 1.75, 6.15, 3.6, paras_)
shape(G2, MSO_SHAPE.ROUNDED_RECTANGLE, 6.55, 5.3, 6.16, 1.65, fill=NAVY, adj=0.08)
text(G2, 6.8, 5.35, 5.7, 1.55, [para("研究意义", 18, True, WHITE, HEAD, after=4),
                                 para("从细胞读取生长素信号的方式解释组织尺度的叶序格局；模型预测可为后续实验的观测指标、成像时间和处理条件提供依据", 15, color=WHITE, line=1.12)],
     anchor=MSO_ANCHOR.MIDDLE)
notes(G2, "针对上述不足，本研究旨在通过生长素–PIN1模型，分析生长素浓度与作用时长如何共同影响原基启动。左图是本研究的模型结构，生长素在表皮层经PIN1运输，细胞对生长素的时间整合M决定原基启动，原基又反过来作为汇和极化线索。研究目的有三点：第一，以反映时间整合的细胞响应把生长素输入、转录响应和原基启动衔接起来，从细胞读取生长素信号的方式出发，检验时间整合能否解释原基依次发生的节律。第二，分析原基对生长素的排出与供给以及茎尖中央与周边响应差异的作用，用茎尖定量成像确定模型参数及其合理取值范围，考察模型能否同时再现中央区的高输入、起始位点处输入的逐步升高以及延迟出现的转录激活，解释持续生长的茎尖中原基定位与启动时间如何协调。第三，在同一模型中比较瞬时阈值与时间整合两类启动规则，并分别改变茎尖大小与生长素信号，分析时间整合在什么条件下影响叶序的精度与稳健性；若两类规则给出相近的平均排列而变异不同，便可比较哪类规则更能解释实测的叶序变异。总之，本研究把生长素时空动态、细胞响应与器官排列放在同一模型中，从细胞读取生长素信号的方式解释组织尺度的叶序格局，模型参数由茎尖定量成像确定，模拟结果直接与观测比较，其预测也可用于确定后续实验的观测指标、成像时间和处理条件。")


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



# ---------------------------------------------------------------- references (full list of the proposal, two columns)
import html
RF = new_slide("PL", "参考文献")
_t = (K.parent / "v2" / "final_p.txt").read_text(encoding="utf-8", errors="replace")
_i = _t.find("5 参考文献"); _j = _t.find("二、", _i)
REFS = []
for _line in _t[_i:_j].split("\n"):
    _m = re.match(r"\s*\[(\d+)\](.*)", _line)
    if _m:
        REFS.append("[" + _m.group(1) + "] " + html.unescape(_m.group(2).strip()).replace("Proceedings of the National Academy of Sciences of the United States of America", "PNAS"))
assert len(REFS) == 25, len(REFS)
for col, chunk in enumerate((REFS[:13], REFS[13:])):
    text(RF, 0.62 + col * 6.15, 1.7, 5.95, 5.35, [para(r, 10, line=1.0, after=3.5) for r in chunk])
notes(RF, "这是开题报告的全部参考文献，编号与报告一致，背景部分的图均取自其中的原文。")

# ---------------------------------------------------------------- closing slide
EN = new_slide("DEFAULT")
picture(EN, DBG / "cover_bg.jpg", 0, 0, w=13.333, h=7.5)
frame_lines(EN)
text(EN, 4.1, 0.55, 2.4, 0.5, [para("公诚勇毅", 18, True, WHITE, HEAD, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
text(EN, 6.85, 0.55, 2.4, 0.5, [para("三实一新", 18, True, WHITE, HEAD, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
text(EN, 1.0, 2.5, 11.33, 1.6, [para("敬请各位老师批评指正", 50, True, WHITE, HEAD, align=PP_ALIGN.CENTER)], anchor=MSO_ANCHOR.MIDDLE)
logo_disc(EN, 6.667, 6.3, 1.55)
text(EN, 0.7, 5.8, 3.4, 0.45, [para("汇报人：张希程", 20, False, RULE, HEAD)])
text(EN, 0.7, 6.45, 3.4, 0.45, [para("导　师：齐继艳 教授", 20, False, RULE, HEAD)])
text(EN, 9.23, 5.8, 3.4, 0.45, [para("生命科学与技术学院", 20, False, RULE, HEAD, align=PP_ALIGN.RIGHT)])
text(EN, 8.83, 6.45, 3.8, 0.45, [para("答辩时间：2026年11月", 20, False, RULE, HEAD, align=PP_ALIGN.RIGHT)])
notes(EN, "以上是我的开题汇报，恳请各位老师批评指正，谢谢。")

# ---------------------------------------------------------------- order, drop the original slides
NEW_ORDER = [CV, CO, B1, B2, B3, B4, B5, B6, B7, B8, B9, B10, B11, B12, B13, G1, G2,
             W1, W2, W3, CT, RD, PB, EX, SC, RF, EN]
lst = prs.slides._sldIdLst
by_part = {prs.part.related_part(sid.get(qn("r:id"))): sid for sid in list(lst)}
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
