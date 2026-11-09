# 尺度标定：状态

**已完成（2026-10-14 21:30）。** 结果见 `RESULTS.md`。

经过：18:25 应用户要求暂停（当时 58/63 个文件已校验、12/21 个茎尖已处理，残缺输出已删除），19:47 按原步骤恢复，
19:57 全部 63 个文件下载并通过 MD5 校验，21:02 21 个茎尖全部处理完，随后完成测量汇总、几何换算和模型运行。

恢复与重跑用的命令（在 `reproductions\elife55832` 目录下，PowerShell）：

```powershell
& 'C:\Users\xczhang\software\Conda\python.exe' -u download_zenodo_parallel.py 6
& 'C:\Users\xczhang\software\Conda\python.exe' -u batch_pipeline.py watch 3
```

模型侧（在 `model_mvp\calib_v2` 目录下）：`measure.py ..\..\reproductions\elife55832\outputs\nuclei_21`，然后 `run.py calib`、`run.py run`、`run.py report`。
`out/interim_measure_12.*` 是暂停时只含 12 个茎尖的中间结果，未用于任何分析。
