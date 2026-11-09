"""Phyllotaxis statistics and pattern classification from a primordium log.

Angles are kept signed (0-360) so that handedness reversals are visible; the
folded statistic used in the first spike hid them.
"""
import math
import numpy as np


def sequence(log, skip=1 / 3):
    t = np.array([l[0] for l in log]); x = np.array([l[1] for l in log]); y = np.array([l[2] for l in log])
    th = np.degrees(np.arctan2(y, x)) % 360
    k = int(len(t) * skip)
    return t[k:], th[k:], np.hypot(x, y)[k:]


def circ_stats(deg):
    z = np.exp(1j * np.radians(deg)).mean()
    mean = math.degrees(math.atan2(z.imag, z.real)) % 360
    dev = (np.asarray(deg) - mean + 180) % 360 - 180
    return mean, float(np.sqrt((dev ** 2).mean()))


def lattice_fit(d, tol=30.0):
    """Explain signed divergence angles by one angle alpha and its permutation motifs.

    Swapping the order of two successive organs on a regular spiral turns
    (a, a, a) into (2a, -a, 2a) (Besnard et al. 2014). Returns alpha, the fraction of
    angles equal to alpha, the fraction that are permutation motifs, and the rest.
    """
    d = np.asarray(d) % 360
    hist = np.bincount((d // 10).astype(int) % 36, minlength=36)
    hist = hist + np.roll(hist, 1) + np.roll(hist, -1)
    c = 10 * int(np.argmax(hist)) + 5
    sel = np.abs((d - c + 180) % 360 - 180) < 25
    alpha, _ = circ_stats(d[sel])
    def near(m):
        return np.abs((d - m * alpha + 180) % 360 - 180) < tol
    f1 = near(1)
    fp = (near(2) | near(-1)) & ~f1
    dev = ((d[f1] - alpha + 180) % 360 - 180)
    return alpha, float(f1.mean()), float(fp.mean()), float(1 - f1.mean() - fp.mean()), float(dev.std()) if f1.any() else float("nan")


def nodes(t, th):
    """Group near-simultaneous initiations into nodes (whorls)."""
    gaps = np.diff(t)
    if len(gaps) < 4:
        return [[k] for k in range(len(t))], 0.0
    tau = 0.3 * np.percentile(gaps, 90)
    grp, cur = [], [0]
    for k, g in enumerate(gaps, start=1):
        if g <= tau:
            cur.append(k)
        else:
            grp.append(cur); cur = [k]
    grp.append(cur)
    return grp, tau


def summarize(log, gamma, skip=1 / 3):
    out = dict(n=len(log), pattern="none")
    if len(log) < 12:
        return out
    t, th, rb = sequence(log, skip)
    a, f1, fp, fo, sd1 = lattice_fit(np.diff(th))
    a_fold = min(a, 360 - a)
    gaps = np.diff(t)
    out.update(alpha=a_fold, f_alpha=f1, f_perm=fp, f_other=fo, sd_alpha=sd1,
               gap_cv=float(gaps.std() / gaps.mean()), gap_mean=float(gaps.mean()),
               frac_short=float((gaps < 0.25 * gaps.mean()).mean()))
    grp, tau = nodes(t, th)
    sizes = np.array([len(g) for g in grp])
    jug = int(round(sizes.mean()))
    out.update(jugacy=jug, node_size_mean=float(sizes.mean()), frac_nodes_full=float((sizes == jug).mean()),
               Rb=float(rb.mean()), Rb_sd=float(rb.std()))
    if jug <= 1:
        d = np.diff(th) % 360
        tp = np.diff(t)
        right = d < 180
        hand = right.mean() >= 0.5
        ds = d if hand else 360 - d                    # signed relative to dominant handedness
        mean, sd = circ_stats(ds)
        fold = np.minimum(d, 360 - d)
        flips = int((np.diff(right.astype(int)) != 0).sum())
        good = np.abs(fold - np.median(fold)) < 25
        best = cur = 0
        for a, b, c in zip(good[1:], right[1:], right[:-1]):
            cur = cur + 1 if (a and b == c) else 0
            best = max(best, cur)
        med = float(np.median(fold))
        if a_fold >= 165:
            name = "distichous"
        elif 150 <= a_fold < 165:
            name = "intermediate"
        elif 125 <= a_fold < 150:
            name = "spiral"
        elif 92 <= a_fold <= 108:
            name = "lucas"
        else:
            name = "other"
        # regular = one angle explains the sequence, allowing a few order permutations
        regular = (f1 >= 0.8) and (fo <= 0.12)
        out.update(pattern=name if regular else name + "~", div_mean=mean, div_sd=sd, fold_med=med,
                   fold_sd=float(fold.std()), flips=flips, longest=best, Tp=float(tp.mean()),
                   Tp_cv=float(tp.std() / tp.mean()), G=float(gamma * tp.mean()), ndiv=len(d),
                   seq=np.round(ds[-12:]).astype(int).tolist())
    else:
        full = [g for g in grp if len(g) == jug]
        per = 360.0 / jug
        phase, spacing_err, tn = [], [], []
        for g in full:
            a = np.sort(th[g])
            sp = np.diff(np.r_[a, a[0] + 360])
            spacing_err.append(np.abs(sp - per).max())
            z = np.exp(1j * np.radians(jug * th[g])).mean()
            phase.append((math.degrees(math.atan2(z.imag, z.real)) % 360) / jug)
            tn.append(t[g].mean())
        phase = np.array(phase); tn = np.array(tn)
        rot = (np.diff(phase) % per) / per             # 0.5 = alternating whorls
        rot_fold = np.minimum(rot, 1 - rot)
        tw = np.diff(tn)
        name = {2: "decussate", 3: "tricussate"}.get(jug, f"whorl{jug}")
        alt = float(np.median(rot_fold)) if len(rot_fold) else float("nan")
        regular = (np.median(spacing_err) < 30) and (alt > 0.38) and ((sizes == jug).mean() > 0.7)
        if not regular and 0.15 < alt <= 0.38:
            name = f"multijugate{jug}"
        out.update(pattern=name if regular else name + "~", rot_frac=alt,
                   spacing_err=float(np.median(spacing_err)) if spacing_err else float("nan"),
                   Tp=float(tw.mean()) if len(tw) else float("nan"),
                   Tp_cv=float(tw.std() / tw.mean()) if len(tw) > 1 else float("nan"),
                   G=float(gamma * tw.mean()) if len(tw) else float("nan"), ndiv=len(tw))
    return out


def fmt(s):
    if s.get("pattern") == "none":
        return f"n={s['n']:3d} (too few)"
    if s["jugacy"] <= 1:
        return (f"n={s['n']:3d} {s['pattern']:11s} div={s['div_mean']:6.1f}+-{s['div_sd']:4.1f} "
                f"flips={s['flips']:2d}/{s['ndiv']:2d} run={s['longest']:2d} Tp={s['Tp']:5.2f} cv={s['Tp_cv']:.2f} "
                f"G={s['G']:.3f} Rb={s['Rb']:.1f}+-{s['Rb_sd']:.1f} seq={s['seq']}")
    return (f"n={s['n']:3d} {s['pattern']:11s} jug={s['jugacy']} full={s['frac_nodes_full']:.2f} "
            f"rot={s['rot_frac']:.2f} spacing_err={s['spacing_err']:5.1f} Tp={s['Tp']:5.2f} cv={s['Tp_cv']:.2f} "
            f"G={s['G']:.3f} Rb={s['Rb']:.1f}+-{s['Rb_sd']:.1f}")
