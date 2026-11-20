"""Vector PDFs (English) of the figures on slides 13-16, recomposed like the slides.
Panels are clipped from the original vector figure PDFs and placed with pypdf; nothing is rasterised here."""
from pathlib import Path
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from pypdf.generic import ContentStream, FloatObject, NameObject, ArrayObject
import shutil

F = Path("/home/user/model/figures/prior_work")
OUT = F / "slides_en"   # run: python3 compose_slides_en.py
PX = 72 / 300          # PNG pixel (300 dpi) -> PDF point


def panel(src, box, keep_images=False):
    """Source page clipped to box = (x0, y0, x1, y1) in PNG pixels of the source figure."""
    r = PdfReader(str(F / src))
    pg = r.pages[0]
    Hpt = float(pg.mediabox.height)
    x0, y0, x1, y1 = box
    rx, ry, rw, rh = x0 * PX, Hpt - y1 * PX, (x1 - x0) * PX, (y1 - y0) * PX
    cs = ContentStream(pg.get_contents(), r)
    # drop raster images that this panel does not show (the rendered Fig. 1-2 A), so they are not copied along
    xo = pg["/Resources"].get_object().get("/XObject")
    imgs = set()
    if xo is not None and not keep_images:
        xo = xo.get_object()
        imgs = {k for k in list(xo.keys()) if xo[k].get_object().get("/Subtype") == "/Image"}
        for k in imgs:
            del xo[k]
    ops = [(o, op) for o, op in cs.operations if not (op == b"Do" and o and o[0] in imgs)]
    clip = [([FloatObject(v) for v in (rx, ry, rw, rh)], b"re"), ([], b"W"), ([], b"n")]
    cs.operations = clip + ops
    pg[NameObject("/Contents")] = cs
    return pg, (rx, ry, rw, rh)


def compose(name, W, H, items):
    """items: (src, box, X, Y, scale) with X, Y the top-left corner in output pixels."""
    out = PageObject.create_blank_page(width=W * PX, height=H * PX)
    for src, box, X, Y, s in items:
        pg, (rx, ry, rw, rh) = panel(src, box, keep_images=(name.startswith("slide14")))
        dx, dy = X * PX, (H - Y) * PX - rh * s
        out.merge_transformed_page(pg, Transformation().translate(-rx, -ry).scale(s, s).translate(dx, dy))
    w = PdfWriter(); w.add_page(out)
    with open(OUT / name, "wb") as fh:
        w.write(fh)
    print("wrote", name, round(W * PX), "x", round(H * PX), "pt")


g = 24
# ---- slide 13: Fig. 1-1, A and B large, C and D top right, E below
f1 = "fig1_data.pdf"
A, B = (24, 40, 924, 1074), (966, 40, 1866, 1074)
C, D, E = (0, 1144, 502, 1815), (502, 1144, 1183, 1815), (1183, 1144, 1890, 1815)
Hab = A[3] - A[1]
Wr = 900
wcd = (C[2] - C[0]) + g + (D[2] - D[0]); scd = Wr / wcd; hcd = (C[3] - C[1]) * scd
he = Hab - hcd - g; se = he / (E[3] - E[1]); we = (E[2] - E[0]) * se
x0 = 900 + g + 900 + 2 * g
compose("slide13_fig1-1_imaging.pdf", x0 + Wr, Hab, [
    (f1, A, 0, 0, 1), (f1, B, 900 + g, 0, 1),
    (f1, C, x0, 0, scd), (f1, D, x0 + ((C[2] - C[0]) + g) * scd, 0, scd),
    (f1, E, x0 + (Wr - we) / 2, hcd + g, se)])

# ---- slide 14: Fig. 1-2 A and B
f2 = "fig2_model_pptB_rt.pdf"
compose("slide14_fig1-2AB_model.pdf", 1890, 834, [(f2, (0, 0, 1890, 834), 0, 0, 1)])

# ---- slide 15: Fig. 1-2 C-E (2x2 with colour bar), F over G at the right
c, d, e = (0, 991, 570, 1580), (672, 991, 1218, 1580), (1320, 991, 1890, 1580)
cb = (672, 1595, 1218, 1685)
Fp, Gp = (0, 1700, 1025, 2355), (1025, 1700, 1890, 2355)
cw, ch = 570, 589
gw, gh = 2 * cw + g, 2 * ch + g
sF = None
wr = round((gh - g) / ((Fp[3] - Fp[1]) / (Fp[2] - Fp[0]) + (Gp[3] - Gp[1]) / (Gp[2] - Gp[0])))
sf, sg = wr / (Fp[2] - Fp[0]), wr / (Gp[2] - Gp[0])
scb = cw * 0.95 / (cb[2] - cb[0])
compose("slide15_fig1-2C-G_patterns.pdf", gw + 2 * g + wr, gh, [
    (f2, c, 0, 0, 1), (f2, d, cw + g + (cw - 546) / 2, 0, 1), (f2, e, 0, ch + g, 1),
    (f2, cb, cw + g + (cw - (cb[2] - cb[0]) * scb) / 2, ch + g + (ch - (cb[3] - cb[1]) * scb) / 2, scb),
    (f2, Fp, gw + 2 * g, 0, sf), (f2, Gp, gw + 2 * g, (Fp[3] - Fp[1]) * sf + g, sg)])

# ---- slide 16: Fig. 1-3 unchanged
shutil.copy(F / "fig3_tests.pdf", OUT / "slide16_fig1-3_tests.pdf")
print("wrote slide16_fig1-3_tests.pdf (copy)")
