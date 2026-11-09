# eLife 55832 计算复现

复现对象：Galvan-Ampudia, Cerutti et al. (2020), *Temporal integration of auxin information for the regulation of patterning*, eLife 9:e55832。论文 DOI：<https://doi.org/10.7554/eLife.55832>。

## 复现范围

本目录把“复现”分成两个可以审计的层级：

1. **附录 2 几何随机模型**：使用现代 NumPy 独立重实现式 (24)–(34)，扫描发散角噪声和 plastochron 噪声，输出原基簇可分性与模拟点云。
2. **真实图像的最小检验**：使用作者下载脚本指定的 E27/SAM7 预处理 TIFF（0、5、10 h），在最大投影上近似检测细胞核、计算 qDII/auxin proxy、CLV3 中心和连续极坐标图，对照 Figure 1 的“时间推进约等价于图样旋转”结论。

这不是湿实验复现，也不冒充完整的论文图形再生成。论文的完整统计还需要 21 个 qDII–DR5 SAM、PIN1 数据、核检测、非线性配准、L1 曲面、跨样本对齐、人工原基校正和群体平均。

## 已固定的来源

- 官方论文：<https://elifesciences.org/articles/55832>
- 原始 CZI 数据：<https://doi.org/10.5281/zenodo.3737795>（34.3 GB）
- 处理数据浏览器：<https://flower.ens-lyon.fr/sam_patterning/>
- 官方代码归档：<https://github.com/elifesciences-publications/sam_spaghetti>
- 本地官方代码快照：[`sam_spaghetti/`](./sam_spaghetti/)，commit `40915058f8b044c4ee235433e2c2c6c57b7df7e5`

## 两条复现轨道

1. **官方历史轨道（已完成）**：在 WSL2 + Docker 中重建 Python 3.7/Mosaic 依赖环境，使用三份原始 CZI 和三份裁剪 TIFF，未修改地执行官方 E27/SAM7 notebook。15/15 个代码单元成功、0 个错误；详见 [`HISTORIC_REPRODUCTION.md`](HISTORIC_REPRODUCTION.md)。
2. **现代最小轨道**：不依赖停更组件，独立重实现附录 2 几何模型，并在预处理 TIFF 上做投影级时间旋转检验。这条轨道便于理解和快速重跑，但不等于完整三维管线。

## 运行

历史官方 notebook：

```powershell
& .\download_e27_sam7.ps1 -IncludeRawCzi
wsl.exe -u root -d Ubuntu -- bash /mnt/c/Users/xczhang/Desktop/papers/reproductions/elife55832/docker/run_historic_notebook_wsl.sh
```

现代最小复现：

当前 Codex Python 已含 NumPy、Pandas 和 Pillow，可运行：

```powershell
& .\download_e27_sam7.ps1
& .\run_reproduction.ps1
```

也可以分开运行：

```powershell
$python = 'C:\Users\xczhang\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $python .\reproduce_appendix2.py --output .\outputs
& $python .\reproduce_e27_sequence.py --data .\data\E27_SAM7 --output .\outputs
```

## 输出

- `outputs/historic_notebook/sam_sequence_detect_quantify_and_align.executed.ipynb`：官方 notebook 的完整新执行副本。
- `outputs/historic_notebook/validation.json`：与作者保存的 11 张 notebook 图逐图比较的哈希和像素差。
- `outputs/historic_nuclei_images/`：完整核检测、信号定量、配准、对齐和原基检测产物（64 个文件，约 1.37 GiB）。

- `outputs/appendix2_summary.json`：附录模型参数、角度离散和可分性摘要。
- `outputs/appendix2_rank_deviations.csv`：各原基序号的角度/半径标准差。
- `outputs/appendix2_separability.csv`、`outputs/appendix2_separability.svg`：噪声相图。
- `outputs/appendix2_population.svg`：论文估计噪声下的模拟原基点云。
- `outputs/e27_sam7_auxin_proxy.png`：三帧真实数据的像素级 auxin proxy。
- `outputs/e27_sam7_rotation_curve.csv`、`.svg`、`.png`：旋转角—相似度曲线。
- `outputs/e27_sam7_summary.json`：图像元数据、中心估计和最佳旋转角。
- `outputs/verification.json`：输入 SHA-256、输出结构和关键数值断言。

## 重要实现决定

1. 附录式 (30) 把 `r_p-r_{p-1}` 写成指数随机量，与式 (26)–(29) 及量纲不一致。这里采用一致的乘法递推 `r_p=r_{p-1} exp(beta Normal(1,sigma_tau))`，并在 JSON 中记录。
2. 论文未公开附录 2 的模拟脚本，也没有说明 k-means 中角度与半径的尺度化。本复现显式使用 `wrapped(theta)/alpha` 与 `log(r/R)/beta` 两个无量纲特征；因此可分性数值属于透明的合理重实现，不宣称逐位复刻作者私有代码。
3. 图像轨道在最大强度投影上用局部极值和非极大值抑制近似检测细胞核，并在这些位置计算 DII/TagBFP 比值。论文正式分析使用三维尺度空间核检测、L1 曲面提取和非线性配准；两者应分别称为“投影核最小检验”和“完整三维管线”。
4. 输入 TIFF 必须与作者服务器报告的字节数完全一致，否则脚本拒绝运行，防止把中断下载当成数据。

## 本次运行结果

- 附录模型在论文估计的 `sigma_alpha=3.6°`、`sigma_tau=0.22` 下，P1–P5 平均角度标准差为 `6.11°`，接近论文报告的观测标准差 `6.7°`；透明重实现下的簇可分性为 `96.6%`。
- 三个 TIFF 均为 `1024×1024×45×4`、16-bit ImageJ hyperstack，横向像素尺寸约 `0.2076 µm`；投影检测得到 701、755、822 个核。
- T0 与 T10 连续 auxin proxy 场的全局最佳旋转为 `-140°`，相关系数 `0.789`。符号来自图像手性/坐标约定，其绝对值与论文发散角 `137.5°` 相差 `2.5°`；在 `-138°`（2° 网格中最接近 `-137.5°`）时相关系数仍为 `0.780`。
- T0 与 T5 的全局最佳值在 `4°`，说明“一个 plastochron 对应一次发散角旋转”不能被机械地线性插值为“半个 plastochron 对应半个发散角”；论文也没有提出这种连续刚体旋转定律。

## 仍未覆盖的下一层

E27/SAM7 单序列官方 notebook 已完整复跑。若要复现论文全部群体统计和全部主图，仍需下载约 34.3 GB 的完整 CZI 数据集，对 21 个 qDII–DR5 SAM 及 PIN1 数据执行批处理，并复现论文中的人工原基校正与跨样本统计。
