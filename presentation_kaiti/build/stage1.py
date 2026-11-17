"""Stage 1 of the proposal-defence deck: work on an unpacked copy of the group-meeting deck.

- four navigation tabs (选题依据 | 已有工作 | 研究方案 | 预期与进度) in the header layouts; layout 2/3/4 highlight
  tabs 1/2/3 and a new layout 6 (copy of 4) highlights tab 4
- duplicate slide 1 (cover) as the closing slide
Writes stage1.pptx.
"""
import re, shutil, subprocess, zipfile
from pathlib import Path

K = Path(__file__).resolve().parent
SK = Path("/root/.claude/skills/synced/7f5327c6-5f1c-4411-ac43-2617029bb6a2_533e3339-3eeb-414a-9f6e-ae2cfcdf911e/pptx/scripts")
W = K / "work"
shutil.rmtree(W, ignore_errors=True)
W.mkdir()
zipfile.ZipFile(K / "src" / "group.pptx").extractall(W)

TABS = ["选题依据", "已有工作", "研究方案", "预期与进度"]
X0, TW, H = 3429000, 1783080, 749808
L = W / "ppt" / "slideLayouts"

# --- new layout 6 = copy of layout 4 -------------------------------------------------------------
shutil.copy(L / "slideLayout4.xml", L / "slideLayout6.xml")
shutil.copy(L / "_rels" / "slideLayout4.xml.rels", L / "_rels" / "slideLayout6.xml.rels")
x6 = (L / "slideLayout6.xml").read_text(encoding="utf-8").replace('<p:cSld name="RS">', '<p:cSld name="PL">')
(L / "slideLayout6.xml").write_text(x6, encoding="utf-8")
mrels = W / "ppt" / "slideMasters" / "_rels" / "slideMaster1.xml.rels"
r = mrels.read_text(encoding="utf-8")
ids = [int(v) for v in re.findall(r'Id="rId(\d+)"', r)]
rid = f"rId{max(ids) + 1}"
r = r.replace("</Relationships>", f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout6.xml"/></Relationships>')
mrels.write_text(r, encoding="utf-8")
mx = W / "ppt" / "slideMasters" / "slideMaster1.xml"
m = mx.read_text(encoding="utf-8")
used = [int(v) for v in re.findall(r'<p:sldLayoutId id="(\d+)"', m)] + [int(v) for v in re.findall(r'<p:sldMasterId id="(\d+)"', (W / "ppt" / "presentation.xml").read_text(encoding="utf-8"))]
new_id = max(used) + 1
m = m.replace("</p:sldLayoutIdLst>", f'<p:sldLayoutId id="{new_id}" r:id="{rid}"/></p:sldLayoutIdLst>')
mx.write_text(m, encoding="utf-8")
ct = W / "[Content_Types].xml"
c = ct.read_text(encoding="utf-8")
c = c.replace("</Types>", '<Override PartName="/ppt/slideLayouts/slideLayout6.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/></Types>')
ct.write_text(c, encoding="utf-8")

# --- rebuild the tab block in the four header layouts ---------------------------------------------
FONT = ('<a:latin typeface="微软雅黑" panose="020B0503020204020204" pitchFamily="34" charset="-122"/>'
        '<a:ea typeface="微软雅黑" panose="020B0503020204020204" pitchFamily="34" charset="-122"/>'
        '<a:cs typeface="微软雅黑" panose="020B0503020204020204" pitchFamily="34" charset="-120"/>')


def tab_text(i, sid, label, active):
    col = "FFFFFF" if active else "808080"
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Tab {i + 1}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{X0 + i * TW}" y="0"/><a:ext cx="{TW}" cy="{H}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" rtlCol="0" anchor="ctr"/><a:lstStyle/>'
            f'<a:p><a:pPr marL="0" indent="0" algn="ctr"><a:buNone/></a:pPr><a:r><a:rPr lang="zh-CN" sz="1700" b="1" kern="0" spc="300" dirty="0">'
            f'<a:solidFill><a:srgbClr val="{col}"/></a:solidFill>{FONT}</a:rPr><a:t>{label}</a:t></a:r><a:endParaRPr lang="zh-CN" sz="1700" dirty="0"/></a:p></p:txBody></p:sp>')


def tab_fill(i, sid):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Tab fill"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{X0 + i * TW}" y="0"/><a:ext cx="{TW}" cy="{H}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="1F4E99"/></a:solidFill><a:ln w="12700"><a:solidFill><a:srgbClr val="1F4E99"/></a:solidFill></a:ln></p:spPr></p:sp>')


def divider(i, sid):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Tab divider"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{X0 + i * TW}" y="219456"/><a:ext cx="0" cy="310896"/></a:xfrm><a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
            f'<a:noFill/><a:ln w="12700"><a:solidFill><a:srgbClr val="C8C8C8"/></a:solidFill></a:ln></p:spPr></p:sp>')


for n, active in ((2, 0), (3, 1), (4, 2), (6, 3)):
    p = L / f"slideLayout{n}.xml"
    x = p.read_text(encoding="utf-8")
    shapes = re.findall(r"<p:sp>.*?</p:sp>", x, re.S)
    old = []
    for sp in shapes:
        off = re.search(r'<a:off x="(\d+)" y="(\d+)"/>', sp)
        if off and X0 <= int(off.group(1)) < 12_000_000 and int(off.group(2)) <= 219456:
            old.append(sp)
    assert len(old) in (4, 5), (n, len(old))
    anchor = x.index(old[0])
    for sp in old:
        x = x.replace(sp, "", 1)
    new, sid = [], 200
    new.append(tab_fill(active, sid)); sid += 1
    for i, lab in enumerate(TABS):
        new.append(tab_text(i, sid, lab, i == active)); sid += 1
    for i in range(1, len(TABS)):
        if active not in (i - 1, i):
            new.append(divider(i, sid)); sid += 1
    x = x[:anchor] + "".join(new) + x[anchor:]
    p.write_text(x, encoding="utf-8")

# --- closing slide: copy of the cover -------------------------------------------------------------
out = subprocess.run(["python3", str(SK / "add_slide.py"), str(W), "slide1.xml"], capture_output=True, text=True)
print(out.stdout.strip(), out.stderr.strip())

dst = K / "stage1.pptx"
dst.unlink(missing_ok=True)
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
    ct_first = W / "[Content_Types].xml"
    z.write(ct_first, "[Content_Types].xml")
    for f in sorted(W.rglob("*")):
        if f.is_file() and f != ct_first:
            z.write(f, f.relative_to(W).as_posix())
print("wrote", dst)
