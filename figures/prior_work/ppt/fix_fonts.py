"""Chinese runs in a pptxgenjs deck: East Asian font 宋体, Latin stays Times New Roman."""
import re, sys, zipfile, shutil
src = sys.argv[1]; tmp = src + ".tmp"
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if re.match(r"ppt/slides/slide\d+\.xml$", item.filename):
            x = data.decode("utf-8")
            def fix(m):
                r = m.group(0)
                t = "".join(re.findall(r"<a:t>([^<]*)</a:t>", r))
                if any("一" <= c <= "鿿" or "＀" <= c <= "￯" for c in t):
                    r = r.replace('<a:ea typeface="Times New Roman" pitchFamily="34" charset="-122"/>',
                                  '<a:ea typeface="宋体" pitchFamily="2" charset="-122"/>')
                    r = r.replace('lang="en-US"', 'lang="zh-CN" altLang="en-US"', 1)
                return r
            x = re.sub(r"<a:r>.*?</a:r>", fix, x, flags=re.S)
            data = x.encode("utf-8")
        zout.writestr(item, data)
shutil.move(tmp, src)
print("fixed", src)
