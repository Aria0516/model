"""Stage 1b: restyle the group-meeting deck's header layouts after the reference defence deck.

Header: dark-blue numbered tab with a light slanted stripe, section name, a thin blue rule, the round school
logo and the school name at the right. Five header layouts:
  BG 01 研究背景 | SG 02 研究意义 (new) | RT 03 已有工作积累 | RS 04 研究内容与方案 | PL 05 预期结果与进度 (new)
Writes base.pptx (still holding the 23 original slides, which stage3 drops).
"""
import re, shutil, zipfile
from pathlib import Path

K = Path(__file__).resolve().parent
W = K / "work_b"
shutil.rmtree(W, ignore_errors=True)
W.mkdir()
zipfile.ZipFile(K / "src" / "group.pptx").extractall(W)
L = W / "ppt" / "slideLayouts"
EMU = 914400
DARK, LIGHT, RULE = "376092", "95B3D7", "276A9A"


def e(v):
    return int(round(v * EMU))


def poly(sid, name, pts, fill):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    cx, cy = e(x1 - x0), e(y1 - y0)
    path = "".join(("<a:moveTo>" if i == 0 else "<a:lnTo>") + f'<a:pt x="{e(x - x0)}" y="{e(y - y0)}"/>' + ("</a:moveTo>" if i == 0 else "</a:lnTo>")
                   for i, (x, y) in enumerate(pts))
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{e(x0)}" y="{e(y0)}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/><a:rect l="0" t="0" r="r" b="b"/>'
            f'<a:pathLst><a:path w="{cx}" h="{cy}">{path}<a:close/></a:path></a:pathLst></a:custGeom>'
            f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr></p:sp>')


def tbox(sid, name, x, y, w, h, t, size, color, bold, face, algn="l"):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr txBox="1"/><p:nvPr userDrawn="1"/></p:nvSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"/><a:lstStyle/><a:p><a:pPr algn="{algn}"/>'
            f'<a:r><a:rPr lang="zh-CN" sz="{int(size * 100)}" b="{1 if bold else 0}" dirty="0"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:latin typeface="{face}"/><a:ea typeface="{face}"/><a:cs typeface="{face}"/></a:rPr><a:t>{t}</a:t></a:r></a:p></p:txBody></p:sp>')


def rule(sid, x0, x1, y, w_pt):
    return (f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{sid}" name="Header rule"/><p:cNvCxnSpPr/><p:nvPr userDrawn="1"/></p:nvCxnSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{e(x0)}" y="{e(y)}"/><a:ext cx="{e(x1 - x0)}" cy="0"/></a:xfrm><a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
            f'<a:ln w="{int(w_pt * 12700)}"><a:solidFill><a:srgbClr val="{RULE}"/></a:solidFill></a:ln></p:spPr></p:cxnSp>')


def pic(sid, name, rid, x, y, w, h):
    return (f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr userDrawn="1"/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')


def header(num, label):
    return "".join([
        poly(300, "Header tab", [(0.62, 0.34), (1.74, 0.34), (1.57, 0.88), (0.62, 0.88)], DARK),
        poly(301, "Header stripe", [(1.82, 0.34), (2.04, 0.34), (1.87, 0.88), (1.65, 0.88)], LIGHT),
        tbox(302, "Header number", 0.62, 0.34, 1.0, 0.54, num, 20, "FFFFFF", True, "Arial", "ctr"),
        tbox(303, "Header section", 2.3, 0.34, 5.0, 0.54, label, 20, RULE, False, "微软雅黑"),
        rule(304, 0.62, 8.62, 0.885, 2.25),
        pic(305, "Header logo", "rId50", 8.7, 0.22, 0.76, 0.76),
        pic(306, "Header school name", "rId51", 9.55, 0.29, 3.0, 0.755),
    ])


# new layouts 6 (SG) and 7 (PL) are copies of layout 4
mrels = W / "ppt" / "slideMasters" / "_rels" / "slideMaster1.xml.rels"
mx = W / "ppt" / "slideMasters" / "slideMaster1.xml"
ct = W / "[Content_Types].xml"
for n, nm in ((6, "SG"), (7, "PL")):
    shutil.copy(L / "slideLayout4.xml", L / f"slideLayout{n}.xml")
    shutil.copy(L / "_rels" / "slideLayout4.xml.rels", L / "_rels" / f"slideLayout{n}.xml.rels")
    x = (L / f"slideLayout{n}.xml").read_text(encoding="utf-8").replace('<p:cSld name="RS">', f'<p:cSld name="{nm}">')
    (L / f"slideLayout{n}.xml").write_text(x, encoding="utf-8")
    r = mrels.read_text(encoding="utf-8")
    rid = "rId" + str(max(int(v) for v in re.findall(r'Id="rId(\d+)"', r)) + 1)
    mrels.write_text(r.replace("</Relationships>", f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout{n}.xml"/></Relationships>'), encoding="utf-8")
    m = mx.read_text(encoding="utf-8")
    used = [int(v) for v in re.findall(r'<p:sldLayoutId id="(\d+)"', m)] + [int(v) for v in re.findall(r'<p:sldMasterId id="(\d+)"', (W / "ppt" / "presentation.xml").read_text(encoding="utf-8"))]
    mx.write_text(m.replace("</p:sldLayoutIdLst>", f'<p:sldLayoutId id="{max(used) + 1}" r:id="{rid}"/></p:sldLayoutIdLst>'), encoding="utf-8")
    ct.write_text(ct.read_text(encoding="utf-8").replace("</Types>", f'<Override PartName="/ppt/slideLayouts/slideLayout{n}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/></Types>'), encoding="utf-8")

for n, num, label in ((2, "01", "研究背景"), (6, "02", "研究意义"), (3, "03", "已有工作积累"), (4, "04", "研究内容与方案"), (7, "05", "预期结果与进度")):
    p = L / f"slideLayout{n}.xml"
    x = p.read_text(encoding="utf-8")
    tree_end = x.index("</p:spTree>")
    body = x[:tree_end]
    keep = []
    for m in re.finditer(r"<p:(sp|pic|cxnSp)>.*?</p:\1>", body, re.S):
        if '<p:ph type="sldNum"' in m.group(0):
            keep.append(m.group(0))
    first = re.search(r"<p:(sp|pic|cxnSp)>", body).start()
    x = body[:first] + header(num, label) + "".join(keep) + x[tree_end:]
    p.write_text(x, encoding="utf-8")
    rp = L / "_rels" / f"slideLayout{n}.xml.rels"
    r = rp.read_text(encoding="utf-8")
    r = r.replace("</Relationships>",
                  '<Relationship Id="rId50" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image4.png"/>'
                  '<Relationship Id="rId51" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image3.png"/></Relationships>')
    rp.write_text(r, encoding="utf-8")

dst = K / "base.pptx"
dst.unlink(missing_ok=True)
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(W / "[Content_Types].xml", "[Content_Types].xml")
    for f in sorted(W.rglob("*")):
        if f.is_file() and f.name != "[Content_Types].xml":
            z.write(f, f.relative_to(W).as_posix())
print("wrote", dst)
