"""Parallel, resumable download of the 21 qDII-CLV3-DR5 meristems (Zenodo record 3737795), MD5-checked.
Meristem by meristem (the order was T0-first until 14:58 on 2026-10-14; restarting resumes partial files).

python download_zenodo_parallel.py [workers] [file-name prefix]
"""
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PREFIX = sys.argv[2] if len(sys.argv) > 2 else "qDII-CLV3-DR5-"        # e.g. qDII-CLV3-PIN1-PI- for the PIN1 meristems
OUT = Path(__file__).resolve().parent / "data" / "zenodo_3737795" / PREFIX.rstrip("-")
LISTING = Path(__file__).resolve().parent / "data" / "zenodo_3737795" / "qDII-CLV3-DR5" / "zenodo_record_3737795.json"


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def order(key):
    """Meristem by meristem (all three time points together) so that processing can start early."""
    t = 2 if "-T5." in key else 1 if "-T10." in key else 0
    return key.replace("-T5.", ".").replace("-T10.", "."), t


def fetch(f):
    target = OUT / f["key"]
    want = f["checksum"].split(":", 1)[1]
    if target.exists() and target.stat().st_size == f["size"] and md5(target) == want:
        return f"done already {f['key']}"
    t0 = time.time()
    for attempt in range(5000):                   # long-lived connections get throttled: drop slow ones and resume
        r = subprocess.run(["curl.exe", "-s", "-L", "--fail", "--retry", "5", "--retry-all-errors", "--retry-delay", "5",
                            "--speed-limit", "200000", "--speed-time", "60",
                            "-C", "-", "--output", str(target), f["links"]["self"]])
        if target.exists() and target.stat().st_size == f["size"]:
            break
    if not target.exists() or target.stat().st_size != f["size"]:
        return f"FAILED size {f['key']}"
    if md5(target) != want:
        target.rename(target.with_suffix(".czi.bad"))
        return f"FAILED md5 {f['key']} (renamed to .bad)"
    s = time.time() - t0
    return f"ok {f['key']}  {f['size'] / 1e6:.0f} MB in {s:.0f} s ({f['size'] / 1e6 / max(s, 1):.2f} MB/s)"


if __name__ == "__main__":
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    OUT.mkdir(parents=True, exist_ok=True)
    files = [f for f in json.load(open(LISTING))["files"] if f["key"].startswith(PREFIX)]
    files.sort(key=lambda f: order(f["key"]))
    print(f"{len(files)} files, {sum(f['size'] for f in files) / 1e9:.2f} GB, {workers} parallel", flush=True)
    with ThreadPoolExecutor(workers) as ex:                 # report each file as soon as it is verified
        for fut in as_completed([ex.submit(fetch, f) for f in files]):
            print(time.strftime("%H:%M:%S"), fut.result(), flush=True)
    print("ALL FILES DOWNLOADED AND MD5-VERIFIED" if all((OUT / f["key"]).exists() for f in files) else "SOME FILES MISSING", flush=True)
