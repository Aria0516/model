# eLife 55832 官方 notebook 历史环境复现

## 结论

2026-08-18 已在 WSL2 + Docker 中成功执行官方仓库的
`doc/notebook/sam_sequence_detect_quantify_and_align.ipynb`。官方 notebook 和算法源码均未修改；
15/15 个非空代码单元执行完成，错误输出为 0。

这属于**源码级原样复跑**，不是对作者 2020 年机器的二进制镜像恢复。作者没有发布完整的
显式 Conda 锁文件，Mosaic 频道中的部分历史构建也已下线，因此 `timagetk 2.1.0` 是从官方
tag 源码用当年的 Python/GCC 组合重建的，Jupyter 辅助栈则按 2020 年兼容版本补充锁定。

## 固定对象

| 对象 | 固定值 |
|---|---|
| `sam_spaghetti` | commit `40915058f8b044c4ee235433e2c2c6c57b7df7e5`，clean |
| `timagetk` | tag `2.1.0` / commit `2a809e5f513fd7fc08fa95c1f768a148cbb755e0`，clean |
| 历史运行镜像 | `elife55832-historic:2020` |
| 镜像 ID | `sha256:82c97cfbe5c6a46c19c83d4ff08f16b4e74f130a51b32ddebf8a5d59393be9b4` |
| 镜像大小 | 1,283,586,103 bytes |
| 原 notebook SHA-256 | `45e2e39a83d9f1443ed073dd252de784de7e7fa8c86c52567631e17665a98d17` |
| 执行 notebook SHA-256 | `6d2cee4fc70ee44769bf1be645b665d32672a80596c524d14e46a2c6d29cb24e` |

输入是作者下载脚本指定的 E27/SAM7 三份原始 CZI 和三份 `No-organs` TIFF；字节数及
SHA-256 见 [`data/E27_SAM7/input_manifest.json`](data/E27_SAM7/input_manifest.json)。历史 CZI
读取器实测得到四个 `1024 × 1024 × 45`、`uint16` 通道，体素大小为
`(0.208, 0.208, 1.171) µm`。

## 关键环境版本

- Python 3.7.6；NumPy 1.18.1；SciPy 1.4.1；Pandas 1.0.1。
- scikit-image 0.16.2；scikit-learn 0.22.1；Matplotlib 3.1.3；VTK 8.2.0。
- `cellcomplex 1.0.0`、`tissue_analysis 0.10.0`、`tissue_nukem_3d 0.11.0`、
  `tissue_paredes 0.9.0`、`sam_spaghetti 0.1.0`。
- Notebook 6.0.3；nbconvert 5.6.1；nbformat 5.0.4；ipykernel 5.1.4；
  jupyter_client 5.3.4；traitlets 4.3.3。

`timagetk` 的旧打包脚本会把 distribution version 显示为 `0.0.0`；源码和构建输入实际固定在
官方 `2.1.0` tag，不能把这个元数据缺陷误读为使用了未知源码。

## 执行结果

- 观察到的文件生成阶段耗时约 22.75 分钟；原算法的三维核检测为单核计算。
- `t00 / t05 / t10` 分别检测到 `1627 / 1517 / 1500` 个核。
- 对齐后的 L1 数据分别包含 `574 / 564 / 538` 个细胞。
- 自动原基极值表分别包含 `13 / 11 / 13` 行。
- 结果目录包含 64 个非空文件，共 1,471,392,644 bytes：32 个 `.inr.gz`、22 个 CSV、
  6 个 PLY、3 个 PNG 和 1 个 JPG。
- 执行后的 notebook 为 48,015,979 bytes，并包含 11 张内嵌图。

与作者提交在官方 notebook 中的 11 张历史图逐一比较：4 张 PNG 在编码字节和像素上完全
一致，分别来自原始信号图、配准、SAM 对齐和原基检测单元。另 2 张图只有 1 像素的画布宽度
差异；其余 5 张同尺寸图的 RGBA 平均绝对差为 `0.22–0.51/255`。完整逐图哈希及像素差见
[`outputs/historic_notebook/validation.json`](outputs/historic_notebook/validation.json)。因此结果足以
证明主计算管线被真实重放，但不应声称 11 张图全部逐字节一致。

## 复跑命令

在 Windows PowerShell 中：

```powershell
& C:\Users\xczhang\Desktop\papers\reproductions\elife55832\download_e27_sam7.ps1 -IncludeRawCzi
wsl.exe -u root -d Ubuntu -- bash /mnt/c/Users/xczhang/Desktop/papers/reproductions/elife55832/docker/build_timagetk_wsl.sh
wsl.exe -u root -d Ubuntu -- bash /mnt/c/Users/xczhang/Desktop/papers/reproductions/elife55832/docker/build_historic_runtime_wsl.sh
wsl.exe -u root -d Ubuntu -- bash /mnt/c/Users/xczhang/Desktop/papers/reproductions/elife55832/docker/run_historic_notebook_wsl.sh
```

执行产物：

- [`outputs/historic_notebook/sam_sequence_detect_quantify_and_align.executed.ipynb`](outputs/historic_notebook/sam_sequence_detect_quantify_and_align.executed.ipynb)
- [`outputs/historic_nuclei_images/`](outputs/historic_nuclei_images/)
- [`outputs/historic_notebook/validation.json`](outputs/historic_notebook/validation.json)

验证执行副本：

```powershell
python .\validate_historic_notebook.py
```

## 兼容性处理（未改算法源码）

1. 官方 `timagetk 2.1.0` tag 用 Python 3.7.6、NumPy 1.18.1、GCC 7.3 重建为本地 Conda 包。
2. 四个 Mosaic 依赖使用其官方历史 Conda 包离线安装。
3. VTK 8.2.0 需要 `tbb 2020.0`、`jsoncpp 1.8.4` 和 Debian Buster 的 GL/X11 运行库。
4. 仓库自身 CI 使用 `python setup.py develop`；必须沿用此方式，普通 egg 安装会遗漏
   `share/data/colormaps` 等运行资源。
5. 宽松的原始环境文件在今天会混入新 Jinja2/Jupyter API，因此显式锁定 2020 年 notebook
   执行栈。所有版本都记录在 [`docker/Dockerfile.historic-runtime`](docker/Dockerfile.historic-runtime)。
