import sys, re
from tissue_nukem_3d.microscopy_images import czifile
for f in sys.argv[1:]:
    with czifile.CziFile(f) as c:
        md = c.metadata
    md = md() if callable(md) else md
    if not isinstance(md, str):
        import xml.etree.ElementTree as ET
        md = ET.tostring(md, encoding='unicode')
    names = re.findall(r'<Channel Id="Channel:\d+" Name="([^"]*)"', md)
    dyes = re.findall(r'<DyeName>([^<]*)</DyeName>', md)
    em = re.findall(r'<EmissionWavelength>([^<]*)</EmissionWavelength>', md)
    ex = re.findall(r'<ExcitationWavelength>([^<]*)</ExcitationWavelength>', md)
    sizes = {k: v for k, v in re.findall(r'<Size([XYZCT])>(\d+)</Size[XYZCT]>', md)}
    print(f.split('/')[-1], '| channels', names[:6], '| dyes', dyes[:6], '| ex', ex[:6], '| em', em[:6], '| sizes', sizes)
