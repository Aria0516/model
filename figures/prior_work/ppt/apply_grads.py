"""Swap the solid fill of named shapes for native PowerPoint gradient fills (pptxgenjs cannot write gradients).
    python apply_grads.py deck.pptx sam_shapes.json
Gradient spec per shape: {"type": "path"|"lin", "focus": [x%, y%] (path), "ang": deg (lin),
                          "stops": [[pos%, "RRGGBB", transparency%], ...]}
"""
import json, re, shutil, sys, zipfile
from xml.sax.saxutils import quoteattr

deck, spec = sys.argv[1], json.load(open(sys.argv[2]))
grads = {s["name"]: s["grad"] for s in spec["shapes"] if s.get("grad")}


def grad_xml(g):
    gs = "".join(f'<a:gs pos="{int(p * 1000)}"><a:srgbClr val="{c}"><a:alpha val="{int((100 - t) * 1000)}"/>'
                 f"</a:srgbClr></a:gs>" for p, c, t in g["stops"])
    if g["type"] == "lin":
        tail = f'<a:lin ang="{int(g["ang"] * 60000)}" scaled="0"/>'
    else:
        fx, fy = g["focus"]
        tail = (f'<a:path path="circle"><a:fillToRect l="{fx * 1000}" t="{fy * 1000}" r="{(100 - fx) * 1000}" '
                f'b="{(100 - fy) * 1000}"/></a:path>')
    return f'<a:gradFill rotWithShape="1"><a:gsLst>{gs}</a:gsLst>{tail}</a:gradFill>'


tmp = deck + ".tmp"
n = 0
with zipfile.ZipFile(deck) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if re.match(r"ppt/slides/slide\d+\.xml$", item.filename):
            x = data.decode("utf-8")

            def fix(m):
                global n
                sp = m.group(0)
                nm = re.search(r'<p:cNvPr [^>]*name="([^"]*)"', sp)
                if nm and nm.group(1) in grads:
                    sp2 = re.sub(r"<a:solidFill>.*?</a:solidFill>", lambda _: grad_xml(grads[nm.group(1)]), sp,
                                 count=1, flags=re.S)
                    n += sp2 != sp
                    return sp2
                return sp
            x = re.sub(r"<p:sp>.*?</p:sp>", fix, x, flags=re.S)
            data = x.encode("utf-8")
        zout.writestr(item, data)
shutil.move(tmp, deck)
print(f"{deck}: {n} gradient fills (of {len(grads)})")
