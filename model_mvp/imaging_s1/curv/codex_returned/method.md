# 标注方法

逐张查看 M01–M14 的原始图页，先在各时间点沿圆顶侧面寻找局部向外鼓出的等高线，再对照同处是否有成片的正高度残差。平均曲率图用于辨认凸面及邻近凹沟。圆顶顶部、孤立高点、仅沿裁剪线延伸的一排暖色点均略去。

沿 0、5、10 h 对照同一侧的凸肩及邻近凹沟，记录首次能单独辨出该隆起的一帧。匹配时允许组织向外生长，也参考各帧圆顶的位置，尤其是 M01 和 M06 的 10 h 图。坐标按首次可见图中的凸面中心估读，取整至 1 µm。起始时间难定时记为 `unclear`，并在备注中写出最早看到的形态。顶端被截断时，坐标取最早一帧可见凸肩的中部。

轮廓与高度起伏清楚且跨帧对应稳定时记为 `high`。凸面较浅但可定位时记为 `medium`。轮廓微弱、跨帧不稳定或中心受裁剪影响时记为 `low`。约 55 µm 的半径用于提示裁剪风险，同时检查每帧实际的采样边界。

<details>
<summary>用于复核浅肩和裁剪位置的叠图代码</summary>

此图用包内细胞核坐标重绘高度残差，并叠加每 2 µm 的绝对高度等高线。网格间距为 1 µm，线性插值后作标准差 3 µm 的高斯平滑，只显示采样凸包内的结果。最终位置和时点由原图目视核定。以下代码在包的根目录运行，修改 `code` 可查看其他样本。

```python
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter

def draw(ax, path):
    d = np.genfromtxt(path, delimiter=",", names=True)
    x, y, z = (d[k] for k in ("x_um", "y_um", "z_um"))
    r2 = x*x + y*y
    A = np.column_stack((np.ones(len(x)), x, y, r2))
    use = r2 <= 50**2
    b = np.linalg.lstsq(A[use], z[use], rcond=None)[0]
    axis = np.arange(-62, 63)
    X, Y = np.meshgrid(axis, axis)
    def surface(v):
        g = griddata((x, y), v, (X, Y), method="linear")
        valid = np.isfinite(g)
        weight = gaussian_filter(valid.astype(float), 3)
        sm = gaussian_filter(np.nan_to_num(g), 3) / np.maximum(weight, 1e-10)
        return np.where(valid, sm, np.nan)
    ax.pcolormesh(X, Y, surface(z-A@b), cmap="PuOr_r", vmin=-3, vmax=3, shading="nearest")
    ax.contour(X, Y, surface(z), levels=np.arange(-100, 101, 2), colors="black", linewidths=.45, alpha=.6)
    ax.add_patch(plt.Circle((0, 0), 55, color="#168273", fill=False, linestyle="--", lw=1.2))
    ax.set(aspect="equal", xticks=np.arange(-60, 61, 10), yticks=np.arange(-60, 61, 10))
    ax.grid(lw=.35, alpha=.4)
    ax.tick_params(labelsize=7)
    ax.set_title(path.stem)

code = "M01"
fig, axes = plt.subplots(1, 3, figsize=(12, 4.1), layout="constrained")
for ax, hour in zip(axes, (0, 5, 10)):
    draw(ax, Path("data") / f"{code}_{hour:02}h.csv")
plt.show()
```

</details>
