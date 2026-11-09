# model

生长素–PIN1 叶序建模与相关论文的计算复现。

- [`model_mvp/`](model_mvp/README.md)：模型方程、实验脚本及结果。
- [`model_mvp/frozen_v2/`](model_mvp/frozen_v2/README.md)：冻结的主线模型。
- [`reproductions/`](reproductions/)：相关论文的复现脚本与分析。
- [`reports/`](reports/)、[`figures/`](figures/)：研究报告与图表。
- [`presentation_20260921/`](presentation_20260921/)：汇报材料。

各模型与复现任务的运行方法、环境和数据来源见对应目录的 README。

## 获取代码

```bash
git clone --recurse-submodules https://github.com/Aria0516/model.git
```

`reproductions/elife55832/sam_spaghetti` 以 Git 子模块固定官方代码版本。

## 本地数据

原始显微数据、大型三维图像中间产物、下载的工具与依赖、临时文件和缓存通过 `.gitignore` 排除，保留在本地。
eLife 复现的数据来源与下载方法见 [`reproductions/elife55832/README.md`](reproductions/elife55832/README.md)。
