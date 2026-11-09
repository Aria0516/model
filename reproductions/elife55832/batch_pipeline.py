"""Run the authors' notebook (doc/notebook/sam_sequence_detect_quantify_and_align.ipynb, historic Docker image)
on each meristem separately. Only two parameter cells are changed: cell 7 (experiment, sam_id) and cell 9 (which
steps run). The repository's batch script is not used: it passes `sam_orientation` to `detect_organ_primordia`,
which does not accept it, and it is not the code path that was validated in August.

python batch_pipeline.py validate              # E27/SAM7: authors' crops (orientation -1) and automatic crops (orientation decided automatically)
python batch_pipeline.py run [n_parallel]     # the 21 Zenodo meristems whose three time points are downloaded and MD5-verified

Per meristem: configuration .csv files mounted over the image's share/data copies; input directory with RAW/
(hard links to the CZI files) and TIF-No-organs/ (crops, see docker/make_crop.py and calib_v2/PROTOCOL.md
revision 2). Handedness is not published for these meristems: pass 1 uses +1, handedness.py decides from the
aligned data, and if the sign must flip, pass 2 re-runs only the alignment cells with -1.
"""
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import handedness

HERE = Path(__file__).resolve().parent
ZEN = HERE / "data" / "zenodo_3737795" / "qDII-CLV3-DR5"
WORK = HERE / "work_batch"
NOTEBOOK = HERE / "sam_spaghetti" / "doc" / "notebook" / "sam_sequence_detect_quantify_and_align.ipynb"
IMAGE = "elife55832-historic:2020"
SHARE = "/opt/sam_spaghetti/share/data"
CONDA = "/opt/conda/envs/sam_spaghetti/bin"
CROP_R = "60"
DATES = {"E25": "170811", "E27": "170817", "E31": "171102", "E33": "171106", "DR5-TEST": "170226"}
CHANNELS = "['DIIV','DR5','TagBFP','CLV3']"
PAT = re.compile(r"qDII-CLV3-DR5-(?:(E\d+)-)?LD-SAM(\d+)(?:-T(\d+))?\.czi$")


def wsl(path):
    p = str(Path(path).resolve()).replace("\\", "/")
    return "/mnt/" + p[0].lower() + p[2:]


def exp_name(exp):
    return f"qDII-DR5-CLV3-LD_{exp}_{DATES[exp]}"


def sequence_name(exp, sam):
    return f"{exp_name(exp)}_sam{int(sam):02d}"


def verified_files():
    log = HERE / "data" / "download_dr5_log.txt"
    ok = set()
    if log.exists():
        for line in open(log, encoding="utf-8-sig", errors="ignore"):
            m = re.search(r"(?:ok|done already) (\S+\.czi)", line)
            if m:
                ok.add(m.group(1))
    return ok


def meristems(files):
    seqs = {}
    for f in files:
        m = PAT.match(Path(f).name)
        if m:
            seqs.setdefault((m.group(1) or "DR5-TEST", int(m.group(2))), []).append((int(m.group(3) or 0), Path(f)))
    return seqs


def run(cmd, log):
    with open(log, "a", encoding="utf-8") as f:
        f.write("\n$ " + " ".join(cmd) + "\n")
        f.flush()
        return subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT).returncode


def prepare(exp, sam, files, root, crops, authors_tifs=None):
    seq = sequence_name(exp, sam)
    base = root / seq
    cfg, expdir = base / "cfg", base / "mic" / exp_name(exp)
    raw, tif = expdir / "RAW", expdir / "TIF-No-organs"
    for d in (cfg, raw, tif, base / "nb"):
        d.mkdir(parents=True, exist_ok=True)
    (cfg / "experiment_info.csv").write_text(
        "experiment;experiment_name;microscopy_directory;channel_names;reference_name\n"
        f"{exp};{exp_name(exp)};{exp_name(exp)};{CHANNELS};TagBFP\n")
    (cfg / "nomenclature.csv").write_text(
        "filename;experiment;sam_id;hour_time\n" + "".join(f"{p.name};{exp};{sam};{h}\n" for h, p in sorted(files)))
    for _, p in files:
        if not (raw / p.name).exists():
            os.link(p, raw / p.name)
        t = tif / (p.name[:-4] + "-No-organs.tif")
        if t.exists():
            continue
        if crops == "authors":
            os.link(authors_tifs / t.name, t)
        else:
            code = run(["wsl.exe", "-u", "root", "-d", "Ubuntu", "--", "docker", "run", "--rm",
                        "-v", f"{wsl(raw)}:/in:ro", "-v", f"{wsl(tif)}:/out", "-v", f"{wsl(HERE / 'docker')}:/tools:ro", IMAGE,
                        f"{CONDA}/python", "/tools/make_crop.py", "crop", f"/in/{p.name}", f"/out/{t.name}", CROP_R], base / "log.txt")
            if code != 0:
                raise RuntimeError(f"crop failed for {p.name}")
    return seq, base


def notebook(base, exp, sam, orientation, steps):
    (base / "cfg" / "nuclei_image_sam_orientation.csv").write_text(f"experiment;sam_id;orientation\n{exp};{sam};{orientation}\n")
    nb = json.load(open(NOTEBOOK, encoding="utf-8"))
    assert "".join(nb["cells"][7]["source"]).startswith("experiment = ") and "detection" in "".join(nb["cells"][9]["source"])
    nb["cells"][7]["source"] = [f"experiment = '{exp}'\n", f"sam_id = {sam}"]
    nb["cells"][9]["source"] = [f"detection = {steps}\n", f"registration = {steps}\n", "primordia_alignment = True"]
    name = f"pass_{'full' if steps else 'align'}_{orientation:+d}.ipynb"
    json.dump(nb, open(base / "nb" / name, "w", encoding="utf-8"))
    return name


def execute(base, exp, out, name):
    cfg = base / "cfg"
    mounts = []
    for f in ("experiment_info.csv", "nomenclature.csv", "nuclei_image_sam_orientation.csv"):
        mounts += ["-v", f"{wsl(cfg / f)}:{SHARE}/{f}:ro"]
    mounts += ["-v", f"{wsl(base / 'mic' / exp_name(exp))}:{SHARE}/microscopy/{exp_name(exp)}:ro",
               "-v", f"{wsl(out)}:{SHARE}/nuclei_images", "-v", f"{wsl(base / 'nb')}:/work"]
    return run(["wsl.exe", "-u", "root", "-d", "Ubuntu", "--", "docker", "run", "--rm", "--shm-size=2g"] + mounts +
               [IMAGE, f"{CONDA}/jupyter", "nbconvert", "--to", "notebook", "--execute", f"/work/{name}",
                "--ExecutePreprocessor.timeout=-1", "--ExecutePreprocessor.kernel_name=python3",
                "--output-dir=/work", f"--output=executed_{name}"], base / "log.txt")


def process(exp, sam, files, root, out, crops, orientation=None, authors_tifs=None):
    """orientation=None: decide automatically (pass 1 with +1, flip if handedness.py says so)."""
    seq, base = prepare(exp, sam, files, root, crops, authors_tifs)
    # every meristem gets its own nuclei_images directory: compile_signal_data([experiment]) rewrites the files of
    # every sequence of the experiment it finds there, which corrupts meristems of the same experiment running in
    # parallel (normalisation is per image, so isolation does not change any result)
    seq_out = out / seq
    seq_out.mkdir(parents=True, exist_ok=True)
    first = orientation if orientation is not None else 1
    code = execute(base, exp, seq_out, notebook(base, exp, sam, first, True))
    if code != 0:
        return seq, f"pass 1 exit {code}"
    total, frames = handedness.score_sequence(seq_out / seq)
    decision = f"score {total:+.2f} with orientation {first:+d}"
    if orientation is None and total < 0:
        code = execute(base, exp, seq_out, notebook(base, exp, sam, -first, False))
        t2, _ = handedness.score_sequence(seq_out / seq)
        decision += f"; flipped to {-first:+d}, score now {t2:+.2f}, exit {code}"
    (seq_out / "handedness.txt").write_text(decision + "\n" + "\n".join(f"{n} {s:+.2f} n={k}" for n, s, k in frames) + "\n")
    return seq, decision


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "validate":
        raw = HERE / "data" / "E27_SAM7" / "original_layout"
        files = meristems((raw / "RAW").glob("*.czi"))[("E27", 7)]
        jobs = [("authors", -1, HERE / "outputs" / "validate_authors_crop"), ("auto", None, HERE / "outputs" / "validate_auto_crop")]
        with ThreadPoolExecutor(2) as ex:
            res = ex.map(lambda j: process("E27", 7, files, WORK / f"validate_{j[0]}", j[2], j[0], j[1], raw / "TIF-No-organs"), jobs)
            for (kind, _, _), r in zip(jobs, res):
                print(kind, r, flush=True)
    elif mode == "watch":                      # keep processing meristems as their downloads complete, until all 21 are done
        import time
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        out = HERE / "outputs" / "nuclei_21"
        listing = json.load(open(ZEN / "zenodo_record_3737795.json"))["files"]
        expected = {k for k in meristems(ZEN / f["key"] for f in listing if f["key"].startswith("qDII-CLV3-DR5-"))}
        started, running = set(), {}
        with ThreadPoolExecutor(n) as ex:
            while True:
                seqs = {k: v for k, v in meristems(ZEN / f for f in verified_files()).items() if len(v) == 3}
                for k, f in sorted(seqs.items()):
                    if k not in started and not (out / sequence_name(*k) / "handedness.txt").exists() and len(running) < n:
                        started.add(k)
                        running[k] = ex.submit(process, k[0], k[1], f, WORK / "run", out, "auto")
                for k in [k for k, fut in running.items() if fut.done()]:
                    try:
                        print(time.strftime("%H:%M:%S"), *running.pop(k).result(), flush=True)
                    except Exception as exc:                      # noqa: BLE001
                        print(time.strftime("%H:%M:%S"), sequence_name(*k), "FAILED", repr(exc), flush=True)
                done = {k for k in expected if (out / sequence_name(*k) / "handedness.txt").exists()}
                if not running and (done | started) >= expected:
                    print(f"finished: {len(done)} of {len(expected)} meristems processed", flush=True)
                    break
                time.sleep(60)
    elif mode == "run":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        seqs = {k: v for k, v in meristems(ZEN / f for f in verified_files()).items() if len(v) == 3}
        out = HERE / "outputs" / "nuclei_21"
        todo = [(e, s, f) for (e, s), f in sorted(seqs.items()) if not (out / sequence_name(e, s) / "handedness.txt").exists()]
        print(f"{len(seqs)} complete meristems, {len(todo)} to process", flush=True)
        with ThreadPoolExecutor(n) as ex:
            for r in ex.map(lambda t: process(t[0], t[1], t[2], WORK / "run", out, "auto"), todo):
                print(*r, flush=True)
