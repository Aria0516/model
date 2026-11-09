"""Run the authors' membrane-segmentation / wall-polarity script on each PIN1 meristem separately
(noise_v3/PROTOCOL.md revision 2). Unmodified script; per-meristem configuration and output directories.

python pin1_pipeline.py test            # E35/SAM4 only
python pin1_pipeline.py run [n]         # all 4 meristems

Configuration differences from the DR5 runs: 5 channels; the reference (membrane) channel is PI, which the
script uses for segmentation; a `signal_names` column (['PIN1']) that the wall-polarity step reads but the
repository's example experiment_info.csv lacks.
"""
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from batch_pipeline import CONDA, IMAGE, run, wsl

HERE = Path(__file__).resolve().parent
ZEN = HERE / "data" / "zenodo_3737795" / "qDII-CLV3-PIN1-PI"
WORK = HERE / "work_pin1"
OUT = HERE / "outputs" / "pin1"
SCRIPT = "/opt/sam_spaghetti/src/sam_spaghetti/scripts/sam_experiment_segment_and_quantify_polarities.py"
DATES = {"E35": "171110", "E37": "171113"}
CHANNELS = ["DIIV", "PIN1", "PI", "TagBFP", "CLV3"]
PAT = re.compile(r"qDII-CLV3-PIN1-PI-(E\d+)-LD-SAM(\d+)(?:-T(\d+))?\.czi$")
PATCHES = HERE / "docker" / "patches" / "sam_spaghetti"          # Python 3 compatibility patches, see docker/patches/PATCHES.md


def patch_mounts():
    m = []
    for f in sorted(PATCHES.glob("*.py")):
        m += ["-v", f"{wsl(f)}:/opt/sam_spaghetti/src/sam_spaghetti/{f.name}:ro"]
    return m


def exp_name(exp):
    return f"qDII-CLV3-PIN1-PI-LD_{exp}_{DATES[exp]}"


def meristems():
    seqs = {}
    for f in ZEN.glob("*.czi"):
        m = PAT.match(f.name)
        if m:
            seqs.setdefault((m.group(1), int(m.group(2))), []).append((int(m.group(3) or 0), f))
    return seqs


def process(exp, sam, files):
    seq = f"{exp_name(exp)}_sam{sam:02d}"
    base = WORK / seq
    cfg, expdir = base / "cfg", base / "mic" / exp_name(exp)
    raw, tif = expdir / "RAW", expdir / "TIF-No-organs"
    for d in (cfg, raw, tif):
        d.mkdir(parents=True, exist_ok=True)
    (cfg / "experiment_info.csv").write_text(
        "experiment;experiment_name;microscopy_directory;channel_names;reference_name;signal_names\n"
        f"{exp};{exp_name(exp)};{exp_name(exp)};{CHANNELS};PI;['PIN1']\n")
    (cfg / "nomenclature.csv").write_text(
        "filename;experiment;sam_id;hour_time\n" + "".join(f"{p.name};{exp};{sam};{h}\n" for h, p in sorted(files)))
    log = base / "log.txt"
    for _, p in files:
        if not (raw / p.name).exists():
            os.link(p, raw / p.name)
        t = tif / (p.name[:-4] + "-No-organs.tif")
        if not t.exists():
            code = run(["wsl.exe", "-u", "root", "-d", "Ubuntu", "--", "docker", "run", "--rm",
                        "-v", f"{wsl(raw)}:/in:ro", "-v", f"{wsl(tif)}:/out", "-v", f"{wsl(HERE / 'docker')}:/tools:ro", IMAGE,
                        f"{CONDA}/python", "/tools/make_crop.py", "crop", f"/in/{p.name}", f"/out/{t.name}", "60", ",".join(CHANNELS)], log)
            if code != 0:
                return seq, f"crop failed for {p.name}"
    out = OUT / seq
    out.mkdir(parents=True, exist_ok=True)
    code = run(["wsl.exe", "-u", "root", "-d", "Ubuntu", "--", "docker", "run", "--rm", "--shm-size=2g",
                "-v", f"{wsl(cfg)}:/cfg:ro", "-v", f"{wsl(base / 'mic')}:/mic:ro", "-v", f"{wsl(out)}:/out"] + patch_mounts() + [IMAGE,
                f"{CONDA}/python", SCRIPT, "-e", exp, "-dir", "/cfg", "-Mdir", "/mic", "-o", "/out", "-S", "-s", "-W", "-P", "-v"], log)
    walls = sorted(out.rglob("*_walls.csv"))
    (out / "status.txt").write_text(f"exit {code}; wall tables {len(walls)}\n")
    return seq, f"exit {code}; wall tables {len(walls)}"


def walls_single(exp, sam, hour, files):
    """Wall extraction and PIN1 quantification for one time point at a time (the whole sequence at once needs
    more than the 15 GB WSL memory). Reuses the segmentation of the full run through hard links."""
    seq = f"{exp_name(exp)}_sam{sam:02d}"
    frame = f"{seq}_t{hour:02d}"
    src = OUT / seq / seq / frame
    base = WORK / seq / f"single_t{hour:02d}"
    cfg, out = base / "cfg", OUT.parent / "pin1_single" / frame
    (out / seq / frame).mkdir(parents=True, exist_ok=True)
    cfg.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.name.endswith((".inr.gz", "_cell_data.csv")) and not (out / seq / frame / f.name).exists():
            os.link(f, out / seq / frame / f.name)
    czi = [p for h, p in files if h == hour][0]
    (cfg / "experiment_info.csv").write_text((WORK / seq / "cfg" / "experiment_info.csv").read_text())
    (cfg / "nomenclature.csv").write_text(f"filename;experiment;sam_id;hour_time\n{czi.name};{exp};{sam};{hour}\n")
    code = run(["wsl.exe", "-u", "root", "-d", "Ubuntu", "--", "docker", "run", "--rm", "--shm-size=2g",
                "-v", f"{wsl(cfg)}:/cfg:ro", "-v", f"{wsl(out)}:/out"] + patch_mounts() + [IMAGE,
                f"{CONDA}/python", SCRIPT, "-e", exp, "-dir", "/cfg", "-o", "/out", "-W", "-P", "-v"], base / "log.txt")
    walls = sorted(out.rglob("*_walls.csv"))
    (out / "status.txt").write_text(f"exit {code}; wall tables {len(walls)}\n")
    return frame, f"exit {code}; wall tables {len(walls)}"


def process_frame(exp, sam, hour, files):
    """Segmentation, wall extraction and PIN1 quantification for one time point (noise_v3 PROTOCOL revision 5)."""
    seq = f"{exp_name(exp)}_sam{sam:02d}"
    frame = f"{seq}_t{hour:02d}"
    base = WORK / seq / f"frame_t{hour:02d}"
    cfg, expdir = base / "cfg", base / "mic" / exp_name(exp)
    raw, tif = expdir / "RAW", expdir / "TIF-No-organs"
    for d in (cfg, raw, tif):
        d.mkdir(parents=True, exist_ok=True)
    czi = [p for h, p in files if h == hour][0]
    (cfg / "experiment_info.csv").write_text(
        "experiment;experiment_name;microscopy_directory;channel_names;reference_name;signal_names\n"
        f"{exp};{exp_name(exp)};{exp_name(exp)};{CHANNELS};PI;['PIN1']\n")
    (cfg / "nomenclature.csv").write_text("filename;experiment;sam_id;hour_time\n" + f"{czi.name};{exp};{sam};{hour}\n")
    log = base / "log.txt"
    if not (raw / czi.name).exists():
        os.link(czi, raw / czi.name)
    t = tif / (czi.name[:-4] + "-No-organs.tif")
    if not t.exists():
        code = run(["wsl.exe", "-u", "root", "-d", "Ubuntu", "--", "docker", "run", "--rm",
                    "-v", f"{wsl(raw)}:/in:ro", "-v", f"{wsl(tif)}:/out", "-v", f"{wsl(HERE / 'docker')}:/tools:ro", IMAGE,
                    f"{CONDA}/python", "/tools/make_crop.py", "crop", f"/in/{czi.name}", f"/out/{t.name}", "60", ",".join(CHANNELS)], log)
        if code != 0:
            return frame, f"crop failed"
    out = OUT.parent / "pin1_single" / frame
    out.mkdir(parents=True, exist_ok=True)
    code = run(["wsl.exe", "-u", "root", "-d", "Ubuntu", "--", "docker", "run", "--rm", "--shm-size=2g",
                "-v", f"{wsl(cfg)}:/cfg:ro", "-v", f"{wsl(base / 'mic')}:/mic:ro", "-v", f"{wsl(out)}:/out"] + patch_mounts() + [IMAGE,
                f"{CONDA}/python", SCRIPT, "-e", exp, "-dir", "/cfg", "-Mdir", "/mic", "-o", "/out", "-S", "-s", "-W", "-P", "-v"], log)
    walls = sorted(out.rglob("*_walls.csv"))
    (out / "status.txt").write_text(f"exit {code}; wall tables {len(walls)}\n")
    return frame, f"exit {code}; wall tables {len(walls)}"


if __name__ == "__main__":
    seqs = meristems()
    if sys.argv[1] == "single":
        e, s_, h = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
        print(*walls_single(e, s_, h, seqs[(e, s_)]), flush=True)
        sys.exit(0)
    if sys.argv[1] == "frames0":                     # revision 5: 0 h of every meristem, one at a time (memory)
        import time
        for (e, s_), f in sorted(seqs.items()):
            frame = f"{exp_name(e)}_sam{s_:02d}_t00"
            if (OUT.parent / "pin1_single" / frame / "status.txt").exists():
                print(time.strftime("%H:%M:%S"), frame, "already done", flush=True)
                continue
            print(time.strftime("%H:%M:%S"), *process_frame(e, s_, 0, f), flush=True)
        sys.exit(0)
    if sys.argv[1] == "test":
        print(*process("E35", 4, seqs[("E35", 4)]), flush=True)
    else:
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        todo = [(e, s, f) for (e, s), f in sorted(seqs.items()) if not (OUT / f"{exp_name(e)}_sam{s:02d}" / "status.txt").exists()]
        with ThreadPoolExecutor(n) as ex:
            for r in ex.map(lambda t: process(*t), todo):
                print(*r, flush=True)
