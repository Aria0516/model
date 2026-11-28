"""Inspect the supplied Arabidopsis images and reproduce the reviewed annotations."""

import argparse
import csv
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
HOURS = (0, 5, 10)
STAGES = range(-3, 6)
DIVERGENCE = 137.5

# Reference angle for the sector guide, and the sign from P0 towards P1.
# A guide angle is rounded to the common angular grid; the actual P0 is a detection.
GUIDES = {
    "S01": (0, -1), "S02": (137.5, 1), "S03": (0, 1), "S04": (137.5, 1),
    "S05": (137.5, 1), "S06": (0, 1), "S07": (0, -1), "S08": (-137.5, -1),
    "S09": (0, 1), "S10": (-137.5, -1), "S11": (0, -1), "S12": (0, 1),
    "S13": (-137.5, -1), "S14": (0, 1),
}

# The reviewed decisions. Each line gives P, max_id/confidence at 0, 5 and 10 h,
# then an optional explanation. A dash means that no detection was retained.
# h, m and l stand for high, medium and low, respectively.
REVIEW = {
    "S01": """
    -3    -     -     -
    -2   27l   13l    -    南侧弱峰位置连续，半径比 P−1 大。
    -1   56m   43m   57h
     0   48h   38h   46l
     1   40h   21h   23h
     2   72m   61l   77l   北侧边缘有多个候选峰，后两帧方位逐渐偏移。
     3    5l    -     -    东南边缘有局部信号，只有本帧可辨。
     4   57l   44l   58l   西北侧弱峰沿约 161° 外移，半径与其他外圈编号重叠。
     5   63m   55m   65l   东北侧边缘亮带，末帧范围较宽。
    """,
    "S02": """
    -3    -    39l   47l   北侧内圈弱峰，中央信号较平。
    -2   37m   16m   33m
    -1   41m   26m   39m
     0   53m   42m   49m
     1   17m    9m    9m
     2   60m   49l   58l   东北外围亮带逐渐移到视野边缘。
     3    -     -     -
     4   27l    8l   14l   东南边缘的局部弱峰在三帧靠近同一方位。
     5    -     -     -
    """,
    "S03": """
    -3    -    17l   26l   东南侧为弱峰，后两帧位置相近，半径偏大。
    -2   51l   51l   61l   北侧亮带可连续追踪，但半径接近 P0。
    -1   27h   22h   27h
     0   39h   31h   36h
     1   53h   49h   59h
     2   12h   13m    2m   南侧亮带向外移，末帧已接近边缘。
     3    -     -     -
     4    -    35l   31l   西侧边缘的局部弱峰，偏离理论方位。
     5   26m   19m   15m   三帧都可见东南边缘亮斑。
    """,
    "S04": """
    -3    -     -     -
    -2   26m   21l    -    西南侧峰较宽，5 h 的方位偏西。
    -1   32m   24m    -
     0   39m   39m   39m
     1   19m    9m    -
     2   44m   47l   50l   东北亮带偏北，末帧半径回缩。
     3    -     -     -
     4   20l    8l    -    东南外圈有连续弱峰，末帧同方位外圈红点超出着色区。
     5   55l   49l    -    北侧远端斑点仅在前两帧连续。
    """,
    "S05": """
    -3    -     -     -
    -2   24l   32l   32l   西南侧宽平台上有一列向外移动的弱峰，角度和半径均有偏差。
    -1   38m   44m   49m
     0   57m   64m    -
     1    2m    3m    -
     2   62l    -     -    东北视野边缘的亮斑，仅此帧有着色区内的对应峰。
     3    -     -     -
     4    -     -     -
     5    -    75l    -    北偏西的边缘亮斑，另两帧缺乏可靠对应。
    """,
    "S06": """
    -3    -    20l   28l   东南内圈信号较平，两帧弱峰的方位接近。
    -2   41m   36m   48m
    -1   25h   19h   31m
     0   34h   27h   35h
     1   45h   46h   51m
     2    2m    3m   11l   南侧远端亮带延续，末帧另有东偏的候选峰。
     3    -     -     -
     4   33l   29l   38l   西侧边缘有连续弱峰，已接近视野极限。
     5    4l   12l   16l   东南外圈弱峰，0 h 方位较后两帧偏南。
    """,
    "S07": """
    -3    -     -     -
    -2   13l    2l   13l   南侧信号随时间增强，前两帧半径接近 P0，末帧峰向内偏。
    -1   35h   29h   29h
     0   27h   26h   25h
     1   19h   12h   11h
     2   53m   56m   58m
     3   11l    -     -    东南边缘的局部亮斑只有 0 h 有对应红圈。
     4    -     -     -
     5   46l   55l   52l   东北外圈亮带较宽，对应点方位有偏移。
    """,
    "S08": """
    -3    -    24l   12l   南侧内圈弱峰逐渐外移。
    -2   29l    -    24l   西北侧早晚两帧有内圈峰，5 h 同方向检测偏外。
    -1   20m   30m   20m
     0   15m   21m    9m
     1   42m   49m   45m
     2    3m    8l    -    东南边缘的信号到 5 h 已减弱。
     3    -     -     -
     4    -     -     -
     5    -     -     -
    """,
    "S09": """
    -3    -     -     -
    -2   42m    -    40m   北侧内圈峰在首末帧方位一致，5 h 缺少同层红圈。
    -1    -    27h   23h
     0   33h   42h   31h
     1   48h   53h   44h
     2   13h   12h    2h
     3   54l    -     -    仅 0 h 东北边缘可见小亮斑。
     4    -     -    27l   西侧外圈仅在末帧出现局部弱峰。
     5   23l   22l   19l   东南边缘弱峰，末帧偏南且半径稍小。
    """,
    "S10": """
    -3    -     -    19l   末帧在南偏东内圈出现弱峰。
    -2   44l   27m   37m
    -1   42m   21m   33m
     0   27m   17m   22m
     1   53m   42m   57l
     2   24m    -     -    东南边缘在 0 h 有局部亮斑，后两帧的对应区信号很低。
     3    -     -    40l   西北外围仅末帧出现可分辨的弱峰。
     4   51l    -    44l   东北边缘首末帧角度接近，中间帧分成两支。
     5    9l   11l   11l   南偏西的外圈亮斑位置稳定，同扇区另有偏南的弱峰。
    """,
    "S11": """
    -3   37l    -    50l   东北内圈弱峰仅在首末帧可辨，5 h 的同角度峰偏外。
    -2   14m   17m   16m
    -1   40h   44h   57h
     0   24h   30h   36m
     1   16h   18h   18m
     2   61m   61l   67l   北侧外圈亮带逐渐偏东，后两帧信号较弱。
     3    -     -     -
     4   35l   42l    -    西北边缘的弱峰在前两帧可追踪。
     5   54l   60l   66l   三帧都在约 50° 的外围，比理论方位偏北。
    """,
    "S12": """
    -3    -     -    36l   末帧东南内圈有弱峰，与此前更靠外的红圈相距较远。
    -2   76l   64l   69l   正北亮带在三帧均有位置稳定的峰，但半径比 P−1 大。
    -1   41h   31h   32h
     0   53h   45h   40m
     1   71h   58h   66h
     2    7m    3m    3l   南偏东的外圈亮带，末帧同一扇区有多个弱峰。
     3    -     -     -
     4   47l   41l   38l   西侧弱峰的方位与向外位移连续，半径和 P2 接近。
     5   28m    4m   23m   东南边缘的局部亮带在三帧均可辨。
    """,
    "S13": """
    -3    -     -    29l   末帧南侧内圈出现可分辨的小峰。
    -2   33l   26m   47m
    -1   31m   19h   34m
     0   20h   13h   23h
     1   44h   45h   70m
     2    4m    -     -    东南外圈在 0 h 有清楚亮斑，5 h 的同方位检测落在低信号区。
     3    -     -     -
     4   38m   39l   61m   东北边缘亮带在 5 h 分成两个候选峰。
     5    3l    2l    2l   南侧外围弱峰的方位连续，检测半径略有回缩。
    """,
    "S14": """
    -3    -     -    39l   末帧东南内圈出现弱峰，早期候选过于靠外。
    -2   47m   36m   67m
    -1   29h   18h   34h
     0   35h   29h   47h
     1   50h   43h   66h
     2   18h    2h    8h
     3    -     -     -
     4    -    17l   38l   西侧外圈由暗转亮，后两帧有弱局部峰。
     5   24l    7l    7l   东南边缘有两支亮带，后两帧按较偏南的一支追踪。
    """,
}

POINT_NOTES = {
    ("S01", -1, 0): "西北宽亮区有两个红圈。#56 信号较强，其半径和后两帧形成外移序列。",
    ("S01", 0, 10): "东侧仍为强亮区，峰中心较 5 h 向内偏约 10 µm，器官对应有歧义。",
    ("S02", 0, 0): "与东侧 #41 的强度相差 0.002。#53 在中央区外，#41 在圈内。",
    ("S02", -2, 10): "同扇区 #28 半径略大，#33 的局部峰更强。",
    ("S04", 0, 0): "西北 #39 是圈外最强峰，东侧 #32 位于中央区内。",
    ("S04", 0, 10): "沿用 5 h 西北外层峰。相同扇区更亮的 #40 向内偏约 15 µm。",
    ("S05", 0, 0): "西北 #57 方位约 119°，信号强于中央区内缘的东侧 #38。",
    ("S08", 0, 0): "与东侧 #20 的强度相差 0.001。西南 #15 在虚线外，东侧峰在虚线内缘。",
    ("S10", 0, 0): "与东侧 #42 的强度相差 0.001。西南 #27 在虚线外，东侧峰在虚线内缘。",
    ("S10", -2, 0): "候选峰靠近中心，方位较后两帧偏西。",
    ("S10", 1, 10): "北偏东亮带出现两个层次。#57 局部信号较强，但比 5 h 外移约 14 µm。",
    ("S11", 0, 10): "东侧亮区内有多个红圈，本帧峰中心较 5 h 向内偏约 5 µm。",
    ("S12", 0, 10): "东侧亮区的 #40 比同扇区外侧 #52 强，较 5 h 向内偏约 7 µm。",
    ("S13", -2, 0): "内圈 #33 的方位较后两帧偏北，同方位的外层点已达 P0 半径。",
    ("S13", 0, 0): "西南 #20 为本帧最强峰，东侧强峰 #31 位于中央区深处。",
}


def read_frame(code, hour):
    stem = ROOT / "data" / f"{code}_{hour:02d}h"
    with stem.with_name(stem.name + "_maxima.csv").open(encoding="utf-8-sig") as f:
        points = {int(row["max_id"]): {key: float(value) for key, value in row.items()
                  if key not in ("max_id", "auto_P")} for row in csv.DictReader(f)}
    nuclei = np.genfromtxt(stem.with_name(stem.name + "_nuclei.csv"), delimiter=",", names=True)
    for pt in points.values():
        d2 = (nuclei["x_um"] - pt["x_um"])**2 + (nuclei["y_um"] - pt["y_um"])**2
        nearest = np.argsort(d2)[:6]
        pt["nearest_nucleus_um"] = float(np.sqrt(d2[nearest[0]]))
        pt["local_signal"] = np.average(nuclei["auxin_input"][nearest],
                                        weights=np.exp(-(d2[nearest] - min(d2)) / 72))
        ring = (d2 >= 10**2) & (d2 <= 22**2)
        pt["contrast"] = (pt["local_signal"] - np.median(nuclei["auxin_input"][ring])
                          if np.any(ring) else 0)
    return points


def angular_difference(a, b):
    return (a - b + 180) % 360 - 180


def central_radius(code, hour):
    # Axis ticks on the supplied PNGs: the origin is at pixel (457, 488),
    # and 20 micrometres span about 90 pixels. Count the white dashed arc.
    filename = ROOT / "images" / f"{code}_{hour:02d}h.png"
    with Image.open(filename) as im:
        rgb = np.asarray(im.convert("RGB"))
    y, x = np.ogrid[:rgb.shape[0], :rgb.shape[1]]
    radius_px = np.hypot(x - 457, y - 488)
    mask = (rgb.min(axis=2) >= 247) & (radius_px >= 60) & (radius_px <= 195)
    bins = np.bincount(np.rint(radius_px[mask]).astype(int), minlength=197)
    return int(np.argmax(np.convolve(bins, [1, 1, 1], mode="same"))) / 4.5


def inspect(code, angle, sign):
    frames = [read_frame(code, hour) for hour in HOURS]
    print(code, "CLV3 radius (um)", [round(central_radius(code, h), 1) for h in HOURS])
    print("Candidates: id:radius/theta/maxima signal/local nuclear signal/"
          "local contrast/distance to nearest nucleus.")
    for p in STAGES:
        target = angular_difference(angle + sign * p * DIVERGENCE, 0)
        print(f"P{p:2d} ({target:+.0f} deg)")
        for hour, points in zip(HOURS, frames):
            candidates = [(i, pt) for i, pt in points.items()
                          if abs(angular_difference(pt["theta_deg"], target)) < 30]
            candidates.sort(key=lambda item: item[1]["r_um"])
            print(f" {hour:2}h " + " ".join(
                f"{i}:{pt['r_um']:.0f}/{pt['theta_deg']:.0f}/"
                f"{pt['auxin_input_normalized']:.2f}/{pt['local_signal']:.2f}/"
                f"{pt['contrast']:+.2f}/{pt['nearest_nucleus_um']:.1f}"
                for i, pt in candidates))


LABEL_FIELDS = ("code", "hour", "P", "max_id", "confidence", "note")
DIRECTION_FIELDS = ("code", "direction", "confidence")
CONFIDENCE = {"h": "high", "m": "medium", "l": "low"}


def reviewed_rows():
    labels = []
    directions = []
    codes = {p.name.split("_")[0] for p in (ROOT / "data").glob("*_maxima.csv")}
    if set(REVIEW) != codes or set(GUIDES) != codes:
        raise ValueError("Review and input specimen codes differ")
    for code, tracks in REVIEW.items():
        sign = GUIDES[code][1]
        directions.append((code, "counterclockwise" if sign == 1 else "clockwise", "high"))
        frames = {h: read_frame(code, h) for h in HOURS}
        used_ids = {h: set() for h in HOURS}
        stages_seen = set()
        for line in tracks.strip().splitlines():
            stage, t0, t5, t10, *explanation = line.split(maxsplit=4)
            p = int(stage)
            if p in stages_seen:
                raise ValueError(f"Repeated P{p} in {code}")
            stages_seen.add(p)
            previous = None
            for h, selection in zip(HOURS, (t0, t5, t10)):
                if selection == "-":
                    continue
                ident = int(selection[:-1])
                confidence = CONFIDENCE[selection[-1]]
                if ident not in frames[h] or ident in used_ids[h]:
                    raise ValueError(f"Unknown or reused max_id {ident} in {code} {h} h")
                used_ids[h].add(ident)
                note = POINT_NOTES.get((code, p, h), explanation[0] if explanation else "")
                if previous is not None:
                    previous_h, previous_id = previous
                    note = f"前次标注为 {previous_h} h #{previous_id}。" + note
                labels.append((code, h, p, ident, confidence, note))
                previous = (h, ident)
        if stages_seen != set(STAGES):
            raise ValueError(f"Incomplete review of P stages for {code}")
    return sorted(labels), sorted(directions)


def deliver(write):
    labels, directions = reviewed_rows()
    for filename, fields, rows in (("labels.csv", LABEL_FIELDS, labels),
                                   ("handedness.csv", DIRECTION_FIELDS, directions)):
        path = ROOT / filename
        if write:
            with path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(fields)
                writer.writerows(rows)
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            expected = [list(map(str, row)) for row in rows]
            if next(reader) != list(fields) or list(reader) != expected:
                raise ValueError(f"File differs from reviewed choices: {filename}")
        print(f"{filename}: {len(rows)} rows verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--inspect", choices=sorted(GUIDES), metavar="CODE",
                      help="show candidate detections in the nine angular sectors")
    mode.add_argument("--write", action="store_true", help="regenerate the two reviewed CSVs")
    parser.add_argument("--angle", type=float, help="override the P0 guide angle for inspection")
    parser.add_argument("--sign", choices=(-1, 1), type=int, help="override the sign for inspection")
    args = parser.parse_args()
    if args.inspect:
        angle, sign = GUIDES[args.inspect]
        inspect(args.inspect, angle if args.angle is None else args.angle,
                sign if args.sign is None else args.sign)
    else:
        deliver(args.write)
