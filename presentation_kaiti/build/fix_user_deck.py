"""Apply the agreed fixes to the user's own deck (开题汇报_张希程_研究目的与意义优化版.pptx).

1. slide 15: drop the Chinese names under the three pattern maps (keep the English titles in the figures);
   colour bar and legend line moved up into the freed space
2. Latin text in Song-typeface captions (slides 13-17) set to Times New Roman; spaces between CJK and Latin removed
3. slide 14 B legend: the initiation criterion switches between instant threshold and temporal integration
4. speaker notes of slides 11 and 13-16 rewritten for the current figures
5. SVG panels: full-page white background rectangles removed (they were cut at the panel edge and showed as
   faint frame lines in WPS)
"""
import re, sys, zipfile, shutil
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches
from pptx.oxml.ns import qn
from lxml import etree

SRC, DST = Path(sys.argv[1]), Path(sys.argv[2])
TMP = DST.with_suffix(".stage.pptx")
prs = Presentation(SRC)
S = prs.slides

CJK = r"[　-〿一-鿿＀-￯]"


def tidy(t):
    t = re.sub(rf"({CJK}) +([A-Za-z0-9θ])", r"\1\2", t)
    t = re.sub(rf"([A-Za-z0-9θ°.]) +({CJK})", r"\1\2", t)
    return t


def walk(shapes):
    for sh in shapes:
        if sh.shape_type == 6:
            yield from walk(sh.shapes)
        else:
            yield sh


# ---- 2. fonts
changed = 0
for i in (13, 14, 15, 16, 17):
    for sh in walk(S[i - 1].shapes):
        if not sh.has_text_frame:
            continue
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                rPr = r._r.find(qn("a:rPr"))
                if rPr is None:
                    continue
                lat = rPr.find(qn("a:latin"))
                if lat is not None and lat.get("typeface") == "宋体":
                    lat.set("typeface", "Times New Roman")
                    cs = rPr.find(qn("a:cs"))
                    if cs is not None:
                        cs.set("typeface", "Times New Roman")
                    new = tidy(r.text)
                    if new != r.text:
                        r.text = new
                    changed += 1
print("runs set to Times New Roman:", changed)

# ---- 1. slide 15
s15 = S[14]
for sh in list(s15.shapes):
    if sh.name in ("二列互生", "螺旋", "交互对生"):
        sh._element.getparent().remove(sh._element)
for sh in s15.shapes:
    if sh.name.startswith("15bar"):
        sh.top = Inches(5.2)
    if sh.has_text_frame and sh.text_frame.text.startswith("改变发生环中线半径"):
        sh.top = Inches(6.0)

# ---- 3. slide 14 B legend
for sh in S[13].shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith("发生环内的整合量"):
        runs = sh.text_frame.paragraphs[0].runs
        runs[0].text = "启动判据可在瞬时阈值与时间整合（M达到阈值θ）之间切换。"
        for r in runs[1:]:
            r._r.getparent().remove(r._r)

# ---- 4. notes
NOTES = {
    11: "针对上述不足，本研究关心的问题是：生长素输入的持续时间如何影响原基启动。左图以发生环内的一个细胞为例，假设两种输入同时升高、峰值相同。如果细胞按瞬时阈值读取信号，只看当前的输入，那么无论输入是短时的还是持续的，输入一升高就会启动。如果细胞对生长素做时间整合，累积此前的输入，那么短时输入达不到阈值，不会启动；持续输入则在累积到阈值后较晚启动。两类规则对同样的输入给出不同的启动时刻，因此会预测出不同的原基发生间隔、发生顺序和发散角变异，这正是可以用叶序数据区分它们的依据。基于此，本研究拟在生长素–PIN1模型中，以反映时间整合的细胞响应衔接生长素输入、转录响应和原基启动，用茎尖定量成像确定模型参数，检验模型能否同时再现中央区的高输入、起始位点处输入的逐步升高以及延迟出现的转录激活；进而在同一模型中比较瞬时阈值与时间整合两类启动规则，分析时间整合在什么条件下影响叶序的精度与稳健性。这一工作可以从细胞读取生长素信号的方式解释组织尺度的叶序格局，其预测也可为后续实验的观测指标、成像时间和处理条件提供依据。",
    13: "下面介绍已经完成的工作。第一项是茎尖成像数据的处理与测量。材料是已发表的21个拟南芥花序茎尖0、5、10小时的时间序列成像，以及另外4个茎尖的PIN1成像。我在重建的原作者软件环境中复现了他们的处理结果，再改进批处理流程，稳定处理了全部21个茎尖。左边是茎尖的生长素输入与转录响应：A是生长素输入，B是DR5转录输出，可以看到茎尖中央的生长素输入较高，DR5却很弱，DR5主要见于原基。右边是茎尖形态与细胞间PIN1变异：表皮层细胞核间距的中位数为4.53微米，CLV3表达区半径为27.3微米，茎尖间差异约2%，这两项已作为模型的几何输入（C、D）；4个茎尖细胞间PIN1量差异的对数标准差约0.08，模型要产生文献报道的非规范发散角比例，所需差异是实测值的4到6倍（E）。接下来要以P0为参照按叶间期对齐原基阶段，确定DR5的激活时序和平均发生间隔，提取PIN1极性，定量原基周围的低生长素区，并追踪细胞位置的变化，推算每个细胞经历的生长素变化。",
    14: "第二项是生长素–PIN1模型的建立。左图是茎尖组织与运输路径：模型在生长、分裂的表皮层上计算生长素运输，原基形成后把生长素排入内层，再经维管束外排，图中带星号的是核查文献现象后做的两处改进，即外围合成和内层排出；改进后关闭极性运输就不再产生原基，原基起始半径与实测P0半径范围重叠。右图是生长素运输、时间整合与原基启动之间的关系：生长素经扩散和PIN1极性运输在细胞间移动，PIN1按相邻细胞的生长素浓度极化；原基在发生环内启动，启动判据可以在瞬时阈值和时间整合之间切换，时间整合用泄漏积分M表示，M达到阈值θ时启动；原基形成后既是生长素的汇，也是PIN1极化的线索，并触发次级抑制；另设被动的DR5样读出，用来和成像中的DR5对照。",
    15: "这个模型不预设角度，发散角、发生间隔和手性都由模拟自发产生。左边是原基在茎尖周边的排列：只改变发生环中线半径与原基作用范围之比，模型依次产生二列互生、螺旋和交互对生（C到E）。右上的F图是这一尺度比与相邻原基夹角的关系：比值较小时为约175°的二列互生，增大后为134°到142°的螺旋，再增大则为相邻两节约转87°的交互对生。右下的G图是积分时间与规则螺旋比例：在当前模型中，原基启动的积分时间常数接近一个叶间期时，规则螺旋的比例下降。因此本研究要把转录响应和原基启动分开刻画，这也是第三项研究比较瞬时阈值与时间整合两类启动规则的出发点。",
    16: "最后是用文献参数检验模型。PIN1极化强度和幼原基周围的次级抑制取自文献，积分时间常数的抽样范围依据外施IAA实验确定，对15个缺乏测量值的参数抽样120组，每组2个随机种子。A是120组参数的抽样结果：实心点是形成规则螺旋的参数组，它们都出现在原基启动受极性运输限制的范围内，叶序是否有序主要取决于原基作用范围w、汇强度η和向心运输偏置κc，分别对应低生长素区的范围、深度和PIN1的向心极性。B是四项叶序指标与文献实测值的对照，每项都比较全部模拟和形成规则螺旋的模拟：规则螺旋的主导发散角中位数为141°，换算后的发生间隔为13.8小时，与文献报道的约12小时接近。所以接下来，先用第一项研究得到的低生长素区和PIN1极性数据约束这三个参数，再把模型与两类启动规则衔接，进入第三项研究的比较与预测。",
}
for i, t in NOTES.items():
    S[i - 1].notes_slide.notes_text_frame.text = t

prs.save(TMP)

# ---- 5. SVG backgrounds
FULL = re.compile(r'<path(?=[^>]*fill="#ffffff")(?=[^>]*\sd="M-?[\d.]+ -?[\d.]+H-?[\d.]+V-?[\d.]+H-?[\d.]+Z")(?![^>]*stroke=)[^>]*/>')
removed = 0
with zipfile.ZipFile(TMP) as zin, zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as zout:
    for it in zin.infolist():
        data = zin.read(it.filename)
        if re.match(r"ppt/media/progress_.*\.svg$", it.filename):
            s = data.decode("utf-8")
            s2, n = FULL.subn("", s)
            removed += n
            data = s2.encode("utf-8")
        zout.writestr(it, data)
TMP.unlink()
print("white background rectangles removed from SVGs:", removed)
print("saved", DST)
