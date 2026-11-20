"""Second round on the user's deck: own background for the closing slide, no references slide, new page header.

Header (all content layouts): section number in brand blue, a thin divider, section name with its English
name below, a four-step progress bar marking the current section, the round logo and school name at the
right, and a hairline closing the header band.
"""
import re, sys, shutil, zipfile
from xml.sax.saxutils import escape
from pathlib import Path
from lxml import etree
from pptx import Presentation
from pptx.util import Inches
from pptx.oxml.ns import qn

SRC, DST = Path(sys.argv[1]), Path(sys.argv[2])
K = Path(__file__).resolve().parent
TMP = DST.with_suffix(".stage.pptx")

prs = Presentation(SRC)
slides = list(prs.slides)

# ---- closing slide: own background photo
end = slides[-1]
old = next(sh for sh in end.shapes if sh.shape_type == 13 and sh.width > Inches(13))
pic = end.shapes.add_picture(str(K / "figs" / "closing_bg.jpg"), 0, 0, width=prs.slide_width, height=prs.slide_height)
sp = end.shapes._spTree
sp.remove(pic._element)
old._element.addprevious(pic._element)
sp.remove(old._element)

# ---- drop the references slide
lst = prs.slides._sldIdLst
for sid in list(lst):
    s = prs.part.related_part(sid.get(qn("r:id")))
    if any(sh.has_text_frame and sh.text_frame.text.strip() == "参考文献" for sh in s.slide.shapes):
        lst.remove(sid)
        prs.part.drop_rel(sid.get(qn("r:id")))
        print("removed references slide")

prs.save(TMP)

# ---- header in the layouts
EMU = 914400
BLUE, INK, SUB, TRACK, LINE = "276A9A", "1F2D3D", "8DA2B8", "D6DEE8", "D5DEE8"
SECTIONS = {"BG": (0, "01", "研究背景", "BACKGROUND"), "SG": (1, "02", "研究意义", "SIGNIFICANCE"),
            "RT": (2, "03", "研究内容与方案", "CONTENT & PLAN"), "RS": (2, "03", "研究内容与方案", "CONTENT & PLAN"),
            "PL": (3, "04", "进度安排", "PLANNING")}


def e(v):
    return int(round(v * EMU))


def tb(sid, name, x, y, w, h, t, size, color, bold, face, spc=0, anchor="ctr"):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr txBox="1"/><p:nvPr userDrawn="1"/></p:nvSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="{anchor}"/><a:lstStyle/><a:p><a:pPr algn="l"/>'
            f'<a:r><a:rPr lang="zh-CN" sz="{int(size * 100)}" b="{1 if bold else 0}" spc="{spc}" dirty="0"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:latin typeface="{face}"/><a:ea typeface="{face}"/><a:cs typeface="{face}"/></a:rPr><a:t>{escape(t)}</a:t></a:r></a:p></p:txBody></p:sp>')


def rect(sid, name, x, y, w, h, fill):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm><a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 50000"/></a:avLst></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr></p:sp>')


def line(sid, name, x0, y0, x1, y1, color, w_pt):
    return (f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvCxnSpPr/><p:nvPr userDrawn="1"/></p:nvCxnSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{e(x0)}" y="{e(y0)}"/><a:ext cx="{e(x1 - x0)}" cy="{e(y1 - y0)}"/></a:xfrm><a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
            f'<a:ln w="{int(w_pt * 12700)}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:ln></p:spPr></p:cxnSp>')


def pic(sid, name, rid, x, y, w, h):
    return (f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr userDrawn="1"/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')


def header(k, num, cn, en):
    parts = [
        tb(400, "Header number", 0.62, 0.26, 0.78, 0.6, num, 30, BLUE, True, "Arial"),
        line(401, "Header divider", 1.44, 0.34, 1.44, 0.80, TRACK, 1.0),
        tb(402, "Header section", 1.62, 0.25, 5.0, 0.36, cn, 17, INK, True, "微软雅黑"),
        tb(403, "Header section en", 1.63, 0.61, 5.0, 0.22, en, 9, SUB, False, "Arial", spc=200),
    ]
    sw, sg, x0 = 0.44, 0.08, 7.55
    for i in range(4):
        parts.append(rect(404 + i, f"Header progress {i + 1}", x0 + i * (sw + sg), 0.53, sw, 0.07, BLUE if i == k else TRACK))
    parts += [
        pic(410, "Header logo", "rId50", 9.92, 0.24, 0.6, 0.6),
        pic(411, "Header school name", "rId51", 10.62, 0.29, 2.09, 0.526),
        line(412, "Header hairline", 0.62, 0.95, 12.71, 0.95, LINE, 0.75),
    ]
    return "".join(parts)


W = DST.with_suffix(".dir")
shutil.rmtree(W, ignore_errors=True)
zipfile.ZipFile(TMP).extractall(W)
L = W / "ppt" / "slideLayouts"
for f in sorted(L.glob("slideLayout*.xml")):
    x = f.read_text(encoding="utf-8")
    m = re.search(r'<p:cSld name="([^"]*)"', x)
    if not m or m.group(1) not in SECTIONS:
        continue
    rels = (L / "_rels" / (f.name + ".rels")).read_text(encoding="utf-8")
    assert 'Id="rId50"' in rels and 'Id="rId51"' in rels, f.name
    shapes = re.findall(r"<p:(?:sp|pic|cxnSp)>.*?</p:(?:sp|pic|cxnSp)>", x, re.S)
    hdr = [s for s in shapes if re.search(r'name="Header[^"]*"', s)]
    first = x.index(hdr[0])
    for s in hdr:
        x = x.replace(s, "", 1)
    k, num, cn, en = SECTIONS[m.group(1)]
    x = x[:first] + header(k, num, cn, en) + x[first:]
    f.write_text(x, encoding="utf-8")
    print("header rebuilt in", f.name, m.group(1))

DST.unlink(missing_ok=True)
with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(W / "[Content_Types].xml", "[Content_Types].xml")
    for p in sorted(W.rglob("*")):
        if p.is_file() and p.name != "[Content_Types].xml":
            z.write(p, p.relative_to(W).as_posix())
shutil.rmtree(W)
TMP.unlink()
print("saved", DST)
