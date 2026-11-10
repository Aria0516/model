"""GTRC (Physcomitrium patens KCHb, Pp3c2_9150) -> Arabidopsis homolog search.

Steps: BLASTP of GTRC against the Arabidopsis proteome, reciprocal BLASTP of the
Arabidopsis KCHs against moss, then a KCH family tree (At / Os / Pp) built with
MAFFT + FastTree, on full-length and motor-domain-only alignments.

Needs: ncbi-blast+, mafft, FastTree, biopython, matplotlib.
Usage:  python3 run_analysis.py <dir with the three Ensembl Plants *.pep.all.fa(.gz)>
"""
import collections
import gzip
import shutil
import subprocess
import sys
from pathlib import Path

from Bio import AlignIO, Phylo, SeqIO

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"            # BLAST databases and temporary files (not committed)
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parents[1]

PROTEOMES = {
    "At": "Arabidopsis_thaliana.TAIR10.pep.all.fa",
    "Pp": "Physcomitrium_patens.Phypa_V3.pep.all.fa",
    "Os": "Oryza_sativa.IRGSP-1.0.pep.all.fa",
}
GTRC = "Pp3c2_9150V3.1"

# Arabidopsis KCH (kinesin-14 with an N-terminal CH domain), found by step 1 below.
AT_KCH = ["AT1G09170", "AT1G63640", "AT2G47500", "AT3G10310",
          "AT3G44730", "AT5G27000", "AT5G41310"]
# Sequences used for the tree (one transcript per gene).
TREE_SET = {
    "At": AT_KCH + ["AT1G73860", "AT1G18410", "AT4G21270", "AT4G05190"],
    "Pp": ["Pp3c2_9150V3.1", "Pp3c14_19550V3.2", "Pp3c17_21780V3.5",
           "Pp3c24_19380V3.1", "Pp3c20_5990V3.1", "Pp3c24_13720V3.3"],
    "Os": ["Os01t0744000-01", "Os05t0521300-04", "Os04t0467901-01",
           "Os12t0547500-01", "Os11t0672400-00", "Os02t0229600-00",
           "Os03t0301800-01", "Os06t0554700-01", "Os01t0243100-01"],
}
# Non-KCH kinesin-14s used to root the tree (ATK1, ATK5 and two moss homologs).
OUTGROUP = {"AT4G21270.1", "AT4G05190.1", "Pp3c20_5990V3.1", "Pp3c24_13720V3.3"}

LABEL = {
    "AT2G47500.1": "At AT2G47500 (KCH3)", "AT5G27000.1": "At AT5G27000 (ATK4)",
    "AT3G44730.1": "At AT3G44730 (KP1)", "AT4G21270.1": "At AT4G21270 ATK1 [outgroup]",
    "AT4G05190.1": "At AT4G05190 ATK5 [outgroup]",
    "AT1G73860.1": "At AT1G73860 (no CH)", "AT1G18410.1": "At AT1G18410 (no CH)",
    "Pp3c2_9150V3.1": "Pp Pp3c2_9150 GTRC/KCHb",
    "Pp3c20_5990V3.1": "Pp Pp3c20_5990 [outgroup]",
    "Pp3c24_13720V3.3": "Pp Pp3c24_13720 [outgroup]",
    "Os12t0547500-01": "Os Os12t0547500 (OsKCH1)",
}
FMT = "6 qseqid sseqid pident length qstart qend sstart send evalue bitscore slen qlen"


def gene_id(seq_id):
    if seq_id.startswith("Pp3c"):
        return seq_id.split("V3")[0]
    if seq_id.startswith("Os"):
        return seq_id.split("-")[0]
    return seq_id.split(".")[0]


def label(seq_id):
    if seq_id in LABEL:
        return LABEL[seq_id]
    prefix = "At" if seq_id.startswith("AT") else seq_id[:2]
    return f"{prefix} {gene_id(seq_id)}"


def run(cmd, out=None):
    with open(out, "w") if out else open("/dev/null", "w") as fh:
        subprocess.run(cmd, check=True, stdout=fh)


def prepare():
    WORK.mkdir(exist_ok=True)
    db = {}
    for sp, name in PROTEOMES.items():
        fa = WORK / name
        if not fa.exists():
            src = SRC / name
            src_gz = SRC / (name + ".gz")
            if src.exists():
                shutil.copy(src, fa)
            else:
                with gzip.open(src_gz, "rb") as fi, open(fa, "wb") as fo:
                    shutil.copyfileobj(fi, fo)
        prefix = str(fa)[:-3]
        if not Path(prefix + ".pin").exists() and not Path(prefix + ".00.pin").exists():
            run(["makeblastdb", "-in", str(fa), "-dbtype", "prot", "-parse_seqids", "-out", prefix])
        db[sp] = prefix
    return db


def blast(query, db, out, max_targets=500):
    run(["blastp", "-query", str(query), "-db", db, "-evalue", "1e-5",
         "-max_target_seqs", str(max_targets), "-num_threads", "4", "-outfmt", FMT], out)
    return [line.rstrip("\n").split("\t") for line in open(out)]


def gene_summary(rows, qlen):
    """Per subject gene: summed bitscore of the best transcript, query coverage, HSP list."""
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for q, s, pid, ln, qs, qe, ss, se, ev, bs, sl, ql in rows:
        by[gene_id(s)][s].append((float(bs), float(pid), int(qs), int(qe), float(ev), int(sl)))
    out = []
    for g, tx in by.items():
        t, h = max(tx.items(), key=lambda kv: sum(x[0] for x in kv[1]))
        covered = set()
        for x in h:
            covered.update(range(x[2], x[3] + 1))
        best = max(h)
        hsps = ";".join(f"{x[2]}-{x[3]}({x[1]:.0f}%)" for x in sorted(h, key=lambda y: y[2]))
        out.append(dict(gene=g, transcript=t, sum_bits=round(sum(x[0] for x in h)),
                        best_hsp_identity=round(best[1], 1), best_evalue=best[4],
                        query_cov=round(len(covered) / qlen * 100), subject_len=best[5],
                        has_CH_region=any(x[2] < 230 and x[3] > 120 for x in h), hsps=hsps))
    return sorted(out, key=lambda d: -d["sum_bits"])


def write_tsv(rows, path, n=None):
    rows = rows[:n] if n else rows
    with open(path, "w") as fh:
        fh.write("\t".join(rows[0].keys()) + "\n")
        for r in rows:
            fh.write("\t".join(str(v) for v in r.values()) + "\n")


def trim(aln, path, columns=None, max_gap=0.5):
    n = len(aln)
    cols = columns if columns is not None else range(aln.get_alignment_length())
    keep = [i for i in cols if sum(r.seq[i] == "-" for r in aln) / n <= max_gap]
    with open(path, "w") as fh:
        for r in aln:
            fh.write(f">{r.id}\n{''.join(r.seq[i] for i in keep)}\n")
    return len(keep)


def rooted(tree_file):
    t = Phylo.read(tree_file, "newick")
    t.root_with_outgroup(t.common_ancestor([c for c in t.get_terminals() if c.name in OUTGROUP]))
    t.ladderize()
    return t


def main():
    db = prepare()
    seqs = {sp: SeqIO.to_dict(SeqIO.parse(WORK / name, "fasta")) for sp, name in PROTEOMES.items()}
    gtrc = seqs["Pp"][GTRC]
    SeqIO.write([gtrc], WORK / "GTRC.fa", "fasta")

    # 1. GTRC vs Arabidopsis
    rows = blast(WORK / "GTRC.fa", db["At"], WORK / "gtrc_vs_at.tsv")
    summ = gene_summary(rows, len(gtrc))
    for r in summ:
        desc = seqs["At"][r["transcript"]].description
        r["annotation"] = desc.split("description:")[-1].split(" [Source")[0] if "description:" in desc else ""
    write_tsv(summ, HERE / "1_GTRC_vs_Arabidopsis_blastp.tsv", 30)

    # 2. Reciprocal: each Arabidopsis KCH vs moss
    at_q = [seqs["At"][g + ".1"] for g in AT_KCH]
    SeqIO.write(at_q, WORK / "at_kch.fa", "fasta")
    rows = blast(WORK / "at_kch.fa", db["Pp"], WORK / "at_vs_pp.tsv", 50)
    best = collections.defaultdict(dict)
    for q, s, pid, *_rest in rows:
        bs = float(_rest[6])
        g = gene_id(s)
        if bs > best[q].get(g, (0, 0))[0]:
            best[q][g] = (bs, float(pid))
    rec = []
    for q in sorted(best):
        top = sorted(best[q].items(), key=lambda kv: -kv[1][0])[:4]
        rec.append(dict(arabidopsis=q, best_moss_gene=top[0][0],
                        best_is_GTRC=top[0][0] == "Pp3c2_9150",
                        top4=" | ".join(f"{g} {b:.0f}bits {p:.0f}%" for g, (b, p) in top)))
    write_tsv(rec, HERE / "2_reciprocal_Arabidopsis_KCH_vs_moss.tsv")

    # 3. KCH family tree
    records = []
    for sp, ids in TREE_SET.items():
        for sid in ids:
            sid = sid if sid in seqs[sp] else sid + ".1"
            r = seqs[sp][sid]
            r.seq = r.seq.rstrip("*")
            r.description = ""
            records.append(r)
    SeqIO.write(records, HERE / "3_KCH_sequences.fa", "fasta")
    run(["mafft", "--quiet", "--maxiterate", "1000", "--localpair", "--thread", "4",
         str(HERE / "3_KCH_sequences.fa")], WORK / "kch.aln")
    aln = AlignIO.read(WORK / "kch.aln", "fasta")
    trim(aln, HERE / "3_KCH_fulllength.trimmed.aln")
    # motor domain = KCH3 (AT2G47500) residues 390-730 (Niu et al. 2025, Fig. 4A: motor 399-724)
    k3 = next(r for r in aln if r.id == "AT2G47500.1")
    pos, motor_cols = 0, []
    for i, ch in enumerate(str(k3.seq)):
        pos += ch != "-"
        if 390 <= pos <= 730:
            motor_cols.append(i)
    trim(aln, HERE / "3_KCH_motor.trimmed.aln", motor_cols)
    for tag in ("fulllength", "motor"):
        run(["FastTree", "-lg", "-gamma", "-quiet", str(HERE / f"3_KCH_{tag}.trimmed.aln")],
            HERE / f"3_KCH_{tag}.nwk")

    draw_trees()


def draw_trees():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"At": "#1f6fb4", "Pp": "#c0392b", "Os": "#2e8b57"}
    fig, axes = plt.subplots(1, 2, figsize=(17, 9.5))
    for ax, tag, title in zip(axes, ("fulllength", "motor"),
                              ("Full-length alignment", "Motor domain only")):
        t = rooted(HERE / f"3_KCH_{tag}.nwk")
        for c in t.get_nonterminals():
            c.name = None
        for c in t.get_terminals():
            sp = "Pp" if c.name.startswith("Pp") else ("Os" if c.name.startswith("Os") else "At")
            c.color = colors[sp]
            c.name = label(c.name)
        Phylo.draw(t, axes=ax, do_show=False,
                   branch_labels=lambda c: f"{c.confidence:.2f}" if c.confidence is not None
                   and not c.is_terminal() and c.confidence < 1.0 and len(c.get_terminals()) > 1 else "",
                   label_colors=lambda n: next((col for k, col in colors.items() if n.startswith(k)), "black"))
        ax.set_title(f"KCH kinesins (FastTree LG+G, SH-like support) - {title}", fontsize=10)
        ax.set_ylabel("")
        ax.set_yticks([])
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(HERE / "3_KCH_trees.png", dpi=150)


if __name__ == "__main__":
    main()
