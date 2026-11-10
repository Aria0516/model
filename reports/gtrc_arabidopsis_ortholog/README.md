# GTRC（小立碗藓 KCHb）在拟南芥中的同源基因

## 结论

- **GTRC = Pp3c2_9150（PpKCHb，kinesin-14-II / KCH 亚家族）**，基因号来自 Li et al. 2021 *Nat Commun* 正文。
- **拟南芥中没有一对一的直系同源基因。** 小立碗藓的 4 个 KCH（GTRC、Pp3c14_19550、Pp3c17_21780、Pp3c24_19380）在两棵树里都聚成一个苔藓自己的分支（支持率 1.00 / 0.999），说明它们是苔藓谱系内部复制出来的。因此 GTRC 对应的是拟南芥的整个 KCH 家族（7 个基因），属于“一对多”的关系。
- **序列上最像的**是 AT3G44730（KP1）和 AT2G47500（KCH3），两者分数几乎一样。GTRC 与 KP1 互为最佳命中，但领先幅度可以忽略（624 vs 622 bits）。
- **功能上的对应基因是 KCH3（AT2G47500）和 KCH7**：Niu et al. 2025 *PNAS* 把 PpKCHb（即 GTRC）转入拟南芥 kch3 kch7 双突变体，能够回补其根向重力缺陷。

## 拟南芥 7 个 KCH 基因（GTRC 的 CH 区和马达区都能比上）

| AGI | 备注 | 与 GTRC 最佳比对片段的一致性 |
|---|---|---|
| AT3G44730 | KP1，GTRC 的 BLAST 第 1 名 | 65% |
| **AT2G47500** | **KCH3**（已核实，见下） | 61% |
| AT1G09170 | | 50% |
| AT5G27000 | ATK4，与 KCH3 最近的旁系同源基因 | 60% |
| AT1G63640 | | 43% |
| AT3G10310 | | 50% |
| AT5G41310 | CH 区与 KCH3 差异最大（一致性 16%） | 50% |

另有 AT1G73860、AT1G18410 两个 kinesin-14 能比上 GTRC 的马达区，但没有 CH 区，PNAS 文中的 KCHL1 可能是其中之一（未核实）。

**KCH3 = AT2G47500 的依据**：PNAS 图 4A 给出 KCH3 全长 983 aa，ATP 结合位点 GQTG 位于 481–484。拟南芥蛋白组中只有 AT2G47500.1 同时满足这两点。

**KCH7 对应哪个 AGI，正文无法确定**，需要看 PNAS 的 SI Appendix。尝试过的推断都对不上：
- 按染色体顺序编号：会得出 KCH7 = AT5G41310，但它的 CH 区和 KCH3 差异最大，与文中“KCH7 的 CH 区与 KCH3、PpKCHb 保守”的说法矛盾。
- 按重组蛋白截断位置（KCH3 1–764、KCH7 1–762）比对：没有哪个候选基因能对上。

## 文件

| 文件 | 内容 |
|---|---|
| `1_GTRC_vs_Arabidopsis_blastp.tsv` | GTRC 对拟南芥全蛋白组的 BLASTP，按基因汇总的前 30 名 |
| `2_reciprocal_Arabidopsis_KCH_vs_moss.tsv` | 7 个拟南芥 KCH 反向比对小立碗藓的前 4 名 |
| `3_KCH_sequences.fa` | 建树用的 26 条序列（At / Os / Pp） |
| `3_KCH_*.trimmed.aln`、`3_KCH_*.nwk` | 比对结果（已去除缺口超过 50% 的列）和系统树，分全长和马达区两套 |
| `3_KCH_trees.png` | 两棵树的图（蓝：拟南芥，绿：水稻，红：小立碗藓） |
| `run_analysis.py` | 一键复现全部分析 |

## 方法

- 蛋白组：Ensembl Plants，包括 TAIR10、Phypa_V3、IRGSP-1.0。
- BLASTP（BLAST+ 2.12，E 值 ≤ 1e-5）。查询序列为 Pp3c2_9150V3.1（1365 aa）。
- 建树：MAFFT L-INS-i 比对，去除缺口超过 50% 的列，FastTree 2（LG+Γ）建树，支持率为 SH-like 局部支持值。外类群为 ATK1、ATK5 及两个苔藓非 KCH kinesin-14。马达区按 KCH3 第 390–730 位取比对列。

复现命令（参数为三个 `.pep.all.fa.gz` 所在目录）：

```bash
python3 run_analysis.py /path/to/proteomes
```

## 注意

- `sum_bits` 是同一基因多个 HSP 的分数之和，只用于排序。
- 苔藓分支在两棵树里的姐妹群不同（全长树：AT1G63640/AT5G41310 组；马达区树：KP1/KCH3 组，支持率仅 0.50），所以不能据此认定某个拟南芥基因是“最近的”。
- 部分水稻基因模型不完整（470–560 aa），会影响局部拓扑，但不改变“苔藓 KCH 单系”的结论。
