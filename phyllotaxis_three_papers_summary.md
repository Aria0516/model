# 三篇 phyllotaxis 中 auxin-PIN1 模型论文总结

本文总结三篇 2006 年 PNAS 论文中关于茎尖叶序形成的核心思想、模型假设、关键公式和公式来源。

## 论文列表

1. Smith et al. 2006, **A plausible model of phyllotaxis**  
   DOI: https://doi.org/10.1073/pnas.0510457103  
   本地文件: `files/1001/Smith et al. - 2006 - A plausible model of phyllotaxis.pdf`

2. Barbier de Reuille et al. 2006, **Computer simulations reveal properties of the cell-cell signaling network at the shoot apex in Arabidopsis**  
   DOI: https://doi.org/10.1073/pnas.0510130103  
   本地文件: `files/1002/Barbier de Reuille et al. - 2006 - Computer simulations reveal properties of the cell-cell signaling network at the shoot apex in Arabidopsis.pdf`

3. Jonsson et al. 2006, **An auxin-driven polarized transport model for phyllotaxis**  
   DOI: https://doi.org/10.1073/pnas.0509839103  
   本地文件: `files/1003/Jonsson et al. - 2006 - An auxin-driven polarized transport model for phyllotaxis.pdf`

## 统一符号

下文统一使用如下符号：

- \(i,j,k\): 细胞编号。
- \(N_i\): 细胞 \(i\) 的邻居集合。
- \(A_i=[IAA]_i\): 细胞 \(i\) 中 auxin 浓度。
- \(P_i=[PIN]_i\): 细胞 \(i\) 中总 PIN1 或内部 PIN1。
- \(P_{ij}\): 细胞 \(i\) 朝向邻居 \(j\) 那侧膜上的 PIN1。
- \(J_{ij}\) 或 \(F_{ij}\): auxin 从细胞 \(i\) 到细胞 \(j\) 的通量。
- \(D\): 被动扩散强度。
- \(T\): PIN1 介导主动运输强度。
- \(l_{ij}\): 细胞 \(i\) 与 \(j\) 的共享壁长。

三篇论文都可以抽象成一个细胞网络上的质量守恒方程：

```math
\frac{dA_i}{dt}
=
S_i
-\delta_i A_i
+\sum_{j\in N_i} D_{ij}(A_j-A_i)
+\sum_{j\in N_i}(J_{ji}-J_{ij})
-R_i
```

其中 \(S_i\) 是 auxin 来源，\(\delta_iA_i\) 是降解，扩散项来自 Fick 扩散定律的离散形式，主动运输项由 PIN1 决定，\(R_i\) 是原基或维管束等 sink。

---

# 1. Smith et al. 2006: A plausible model of phyllotaxis

## 1.1 核心问题

这篇文章想回答：

> Reinhardt 等人提出的“auxin 由 PIN1 主动运输并在新原基处形成峰值”的概念模型，是否真的能在计算机模拟中产生稳定叶序？

它不是从真实 PIN1 图像直接反推 auxin，也不是从化学渗透理论完整推导，而是构造了一个现象学的离散细胞动力系统。

## 1.2 主要生物假设

1. 叶序模式主要在茎尖 L1 表皮层形成。
2. Auxin 在 L1 中可获得，并通过扩散和 PIN1 主动运输重新分布。
3. Auxin 上调 PIN1 表达。
4. PIN1 在细胞膜上朝 auxin 浓度更高的邻居极化。
5. Auxin 高峰诱导新原基。
6. 原基虽然 auxin 高，但会把 auxin 排入内部组织，因此在 L1 中表现为 sink。
7. 只有 peripheral zone 对 auxin 有形成器官的响应能力。

## 1.3 PIN1 总量动力学

```math
\frac{dP_i}{dt}
=
\alpha_{PIN0}
+
\frac{\alpha_{PIN}A_i}{1+\kappa_{PIN}P_i}
-
\delta_{PIN}P_i
```

含义：

- \(\alpha_{PIN0}\): PIN1 基础生产。
- \(\alpha_{PIN}A_i\): auxin 促进 PIN1 生产。
- \(1+\kappa_{PIN}P_i\): 饱和项，防止 PIN1 无限增加。
- \(\delta_{PIN}P_i\): PIN1 衰减。

公式来源：

```math
\frac{dx}{dt}=\text{production}-\text{decay}
```

再加一个 Michaelis-Menten / Hill 风格的饱和调控项。

## 1.4 PIN1 膜定位公式

```math
P_{ij}
=
P_i
\frac{l_{ij}b^{A_j}}
{\sum_{k\in N_i}l_{ik}b^{A_k}}
```

含义：

- 邻居 \(j\) 的 auxin 越高，细胞 \(i\) 越倾向把 PIN1 放到朝向 \(j\) 的膜上。
- \(l_{ij}\) 修正不同细胞壁长度。
- \(b>1\) 控制极化强度。

这个公式本质类似 softmax / Boltzmann 权重分配：

```math
w_j=\frac{e^{s_j}}{\sum_k e^{s_k}}
```

因为：

```math
b^{A_j}=e^{(\ln b)A_j}
```

所以 Smith 模型中的 PIN1 极化是一个经验性的“指数偏好”规则，不是从明确的分子反应推导出来的。

## 1.5 主动运输通量

```math
F_{ij}
=
T P_{ij}
\frac{A_i^2}{1+\kappa_T A_j^2}
```

含义：

- \(P_{ij}\) 越多，从 \(i\) 到 \(j\) 的运输能力越强。
- 源细胞 \(A_i\) 越高，可被输出的 auxin 越多。
- 目标细胞 \(A_j\) 越高，运输趋于饱和。
- 平方项是经验设定，作者说明它不是直接实验推导，而是在模拟中比线性项更稳定地控制峰值间距。

公式来源：

```math
\text{flux}\propto \text{transporter amount}\times \text{substrate availability}
```

再加饱和项。

## 1.6 Auxin 动力学

```math
\frac{dA_i}{dt}
=
\frac{\alpha_{IAA}}{1+\kappa_{IAA}A_i}
-
\delta_{IAA}A_i
+
\sum_{j\in N_i}D_{ij}(A_j-A_i)
+
\sum_{j\in N_i}(F_{ji}-F_{ij})
```

其中：

- \(\frac{\alpha_{IAA}}{1+\kappa_{IAA}A_i}\): auxin 生产，高浓度时负反馈饱和。
- \(\delta_{IAA}A_i\): 一阶降解。
- \(\sum_jD_{ij}(A_j-A_i)\): 离散 Fick 扩散。
- \(\sum_j(F_{ji}-F_{ij})\): 主动运输流入减流出。

## 1.7 原基附加规则

当 peripheral zone 中相邻细胞 auxin 超过阈值 \(Th\)，模型生成原基。

原基内额外 auxin 生产：

```math
\text{additional production}_i
=
\frac{\alpha_{IAA}^{primordium}}{1+\kappa_{IAA}A_i}
\left(1-\frac{d_i}{r}\right)
```

其中 \(d_i\) 是细胞到原基中心的距离，\(r\) 是原基半径。这个项使原基中心 auxin 生产更强，边缘较弱。

用于增强 PIN1 朝原基中心极化的“等效 auxin”：

```math
A_i^*
=
\max\left(
A_i,\,
A_{max}\left(1-\frac{d_i}{r}\right)
\right)
```

同时，原基中的 auxin 被限制在 \(A_{max}\)，超过部分被视为排入内部组织，启动维管束形成。

## 1.8 推演机制

Smith 模型的反馈链条是：

```math
A_j \text{ 较高}
\Rightarrow
P_{ij} \text{ 增加}
\Rightarrow
F_{ij} \text{ 增加}
\Rightarrow
A_j \text{ 更高}
\Rightarrow
\text{形成 auxin peak}
```

peak 周围的 auxin 被抽走，使附近难以形成第二个 peak。随着茎尖增长，旧原基远离中心，新 peak 在离旧原基较远的位置出现，从而产生 spiral、distichous、decussate、tricussate 等叶序。

---

# 2. Barbier de Reuille et al. 2006: Computer simulations reveal properties of the cell-cell signaling network

## 2.1 核心问题

这篇文章的问题和 Smith 不同：

> 如果把显微镜中观察到的 PIN1 极性网络当作已知输入，这个网络会把 auxin 运到哪里？

因此它不是生成 PIN1 极化，而是使用真实 PIN1 immunolabeling 图像构造细胞网络，并在网络上计算 auxin 稳态分布。

## 2.2 模型输入

1. 从显微图像中分割细胞。
2. 每个细胞作为一个节点。
3. 细胞壁作为无向扩散边。
4. 有 PIN1 标记且可判断方向的膜作为有向主动运输边。
5. 原基中可见的 provascular strand 区域作为 auxin sink。
6. Auxin 可以从 meristem 边界进入，或者由细胞局部产生。

## 2.3 可写成的统一动力学形式

正文没有像 Smith 和 Jonsson 那样列出完整 ODE，但其模拟规则可整理为：

```math
\frac{dA_i}{dt}
=
S_i
-
\gamma A_i
+
\sum_{j\in N_i}D_{ij}(A_j-A_i)
+
\sum_{j\in N_i}(T_{ji}A_j-T_{ij}A_i)
-
R_i
```

其中：

- \(S_i\): 边界输入或局部产生。
- \(\gamma A_i\): 一阶降解。
- \(D_{ij}(A_j-A_i)\): 被动扩散。
- \(T_{ij}A_i\): 由真实 PIN1 方向定义的主动输出。
- \(R_i\): 原基或 provascular strand 的 sink。

若膜上存在从 \(i\) 指向 \(j\) 的 PIN1，则 \(T_{ij}>0\)，否则 \(T_{ij}=0\) 或很小。

## 2.4 稳态假设

论文假设 auxin 分布建立得比生长和细胞分裂快，因此每张静态显微图对应一个近似稳态：

```math
\frac{dA_i}{dt}=0
```

也就是说，它求的是在给定 PIN1 网络下的 stationary auxin distribution。

## 2.5 饱和约束

论文还加入一个规则：

```math
A_i\le A_{sat}
```

即细胞不能无限积累 auxin。超过饱和水平后，细胞不再接受更多 influx。作者指出，这与“高浓度时扩散压过主动运输”的情形在模拟结果上类似。

## 2.6 公式来源

这篇的公式来源最朴素：

1. 细胞网络上的质量守恒：

```math
\frac{dA_i}{dt}=\text{source}-\text{sink}+\text{inflow}-\text{outflow}
```

2. Fick 扩散定律的离散形式：

```math
\text{diffusion}_{ij}=D_{ij}(A_j-A_i)
```

3. 有向图输运：

```math
\text{active flux}_{ij}=T_{ij}A_i
```

4. 一阶降解：

```math
\text{decay}_i=\gamma A_i
```

5. 边界 source 和 sink 条件。

## 2.7 主要发现

模拟不仅在年轻原基处得到 auxin 高值，还预测 meristem summit 会积累 auxin。

这点不容易从 PIN1 图像肉眼看出。作者随后用实验验证：

1. pDR5::GFP 在 summit 不明显响应，说明 summit 对 auxin 的器官发生响应弱或不敏感。
2. auxin immunolabeling 和 GCMS 显示 summit 中确实有 IAA。
3. 模拟中如果把 summit 到达的 auxin 立即降解，I-1 位置的新 auxin maximum 会消失。

因此这篇提出：meristem summit 可能不是器官发生区，但会影响下一个原基位置，类似 auxin 流动中的 reservoir 或 traffic jam。

---

# 3. Jonsson et al. 2006: An auxin-driven polarized transport model for phyllotaxis

## 3.1 核心问题

这篇文章想补上 Smith 和 Barbier de Reuille 都没有完全解决的问题：

> PIN1 为什么会朝某个方向极化？

作者提出：

> 邻近细胞的 auxin 浓度调控本细胞 PIN1 在不同膜面之间的循环和定位。

因此这是一个 auxin-driven PIN polarization model。

## 3.2 简化 auxin 运输模型

在 PIN1 主动运输未饱和的近似下：

```math
\frac{dA_i}{dt}
=
D\sum_{k\in N_i}(A_k-A_i)
+
T\sum_{k\in N_i}(A_kP_{ki}-A_iP_{ik})
```

含义：

- 第一项是被动扩散。
- 第二项是主动运输的流入减流出。
- \(A_kP_{ki}\) 是邻居 \(k\) 通过朝向 \(i\) 的 PIN1 把 auxin 输给 \(i\)。
- \(A_iP_{ik}\) 是 \(i\) 通过朝向 \(k\) 的 PIN1 把 auxin 输给 \(k\)。

公式来源：

```math
\partial_t A=D\nabla^2 A
```

加上载体介导的有向运输：

```math
J_{ik}\propto P_{ik}A_i
```

## 3.3 Cell-based 饱和运输公式

论文给出的更完整细胞间净通量为：

```math
J_{ij}^{tot}
=
D(A_i-A_j)
+
T\left(
P_{ij}\frac{A_i}{K_A+A_i}
-
P_{ji}\frac{A_j}{K_A+A_j}
\right)
```

这里：

- \(D(A_i-A_j)\): 扩散。
- \(\frac{A_i}{K_A+A_i}\): Michaelis-Menten 饱和项。
- \(P_{ij}\frac{A_i}{K_A+A_i}\): 从 \(i\) 到 \(j\) 的 PIN1 主动外排。
- \(P_{ji}\frac{A_j}{K_A+A_j}\): 反方向主动外排。

公式来源是载体介导运输的 Michaelis-Menten 形式：

```math
v=V_{max}\frac{A}{K_A+A}
```

其中 \(V_{max}\) 被 PIN1 数量 \(P_{ij}\) 调节。

## 3.4 Detailed chemiosmotic transport model

在更详细的模型中，细胞质 compartment 和细胞壁 compartment 分开。细胞 \(i\) 到其相邻细胞壁 compartment \(ij\) 的净通量写为：

```math
J_{i,ij}^{tot}
=
\left(D_{efflux}A_i-D_{influx}A_{ij}\right)
+
P_{ij}
\left(
T_{efflux}\frac{A_i}{K_A+A_i}
-
T_{influx}\frac{A_{ij}}{K_A+A_{ij}}
\right)
```

这个公式来自经典 chemiosmotic auxin transport hypothesis：

1. IAA 是弱酸。
2. 细胞壁 pH 低，细胞质 pH 高。
3. 中性 IAAH 更容易被动穿膜。
4. 阴离子 IAA- 需要 AUX/LAX、PIN 等载体介导跨膜。
5. PIN1 主要影响阴离子形式 auxin 的定向外排。

所以 Jonsson 模型比 Smith 更靠近生物物理运输机制。

## 3.5 PIN1 cycling 模型

作者假设 PIN1 在细胞内部 compartment 和不同膜面之间循环：

```math
\frac{dP_{ij}}{dt}
=
f(A_j)P_i-k_2P_{ij}
```

```math
\frac{dP_i}{dt}
=
\sum_{k\in N_i}
\left(
k_2P_{ik}-f(A_k)P_i
\right)
```

含义：

- \(P_i\): 细胞 \(i\) 内部 PIN1。
- \(P_{ij}\): 细胞 \(i\) 朝向邻居 \(j\) 的膜上 PIN1。
- \(f(A_j)P_i\): 邻居 \(j\) 的 auxin 促进 PIN1 从内部定位到朝向 \(j\) 的膜。
- \(k_2P_{ij}\): 膜上 PIN1 内吞回内部 compartment。

公式来源是 mass-action reaction kinetics：

```math
P_i
\rightleftharpoons
P_{ij}
```

只是 forward rate 被邻居 auxin 通过 \(f(A_j)\) 调节。

## 3.6 反馈函数 \(f(A)\)

论文使用两类形式。

线性反馈：

```math
f(A_j)=k_1A_j
```

Hill 型饱和反馈：

```math
f(A_j)
=
k_1
\frac{A_j^n}{K^n+A_j^n}
```

Hill 型来源于配体响应或信号转导中的饱和非线性。\(n\) 控制协同性和非线性强度。

## 3.7 PIN1 平衡分配的推导

如果 PIN1 cycling 比 auxin 分布变化快，可以令：

```math
\frac{dP_{ij}}{dt}=0
```

于是：

```math
P_{ij}=\frac{f(A_j)}{k_2}P_i
```

又因为总 PIN1 守恒：

```math
P_i^{tot}=P_i+\sum_{k\in N_i}P_{ik}
```

代入可得：

```math
P_{ij}
=
P_i^{tot}
\frac{f(A_j)}
{k_2+\sum_{k\in N_i}f(A_k)}
```

若 \(f(A_j)=k_1A_j\)，则：

```math
P_{ij}
=
P_i^{tot}
\frac{A_j}
{k_2/k_1+\sum_{k\in N_i}A_k}
```

如果膜定位占主导，\(k_2/k_1\) 相对很小，则近似为：

```math
P_{ij}
\approx
P_i^{tot}
\frac{A_j}
{\sum_{k\in N_i}A_k}
```

这说明 Jonsson 的 PIN1 极化不是直接写成经验 softmax，而是从 PIN1 内吞-外排循环的平衡态推出来的。

## 3.8 线性稳定性结论

在一维周期细胞列的简化模型中，均匀 auxin 状态：

```math
A_i=A,\quad \forall i
```

可以变得不稳定。论文的简化分析表明，当主动运输相对扩散足够强时，均匀态会破缺，出现有特征波长的 auxin peak-trough pattern。文中给出的量纲组合是 \(D/(TP)\)，其阈值约为 \(0.5\)。

直观解释：

```math
\text{主动运输反馈强}
>
\text{扩散平滑作用}
\Rightarrow
\text{均匀态不稳定}
\Rightarrow
\text{规则 auxin peak 出现}
```

## 3.9 推演机制

Jonsson 模型的核心链条是：

```math
A_j \text{ 较高}
\Rightarrow
f(A_j) \text{ 较高}
\Rightarrow
P_{ij} \text{ 增加}
\Rightarrow
J_{ij} \text{ 增加}
\Rightarrow
A_j \text{ 更高}
```

这也是正反馈，但它比 Smith 多了一层明确的 PIN1 cycling 机制。

---

# 4. 三篇论文的关系

## 4.1 一句话比较

| 论文 | 问题 | PIN1 如何得到 | auxin 如何计算 | 主要结论 |
|---|---|---|---|---|
| Smith et al. | 一个合理的 auxin-PIN1 机制能否产生叶序 | 由 auxin 经验性上调和指数极化 | ODE 动力系统 | auxin-PIN1 正反馈加原基 sink 可产生多种叶序 |
| Barbier de Reuille et al. | 真实 PIN1 网络会把 auxin 运到哪里 | 直接来自显微图像 | 图网络稳态输运 | 真实 PIN1 网络预测原基和 summit auxin 积累 |
| Jonsson et al. | PIN1 极化可否由 auxin 本身驱动 | 由 PIN1 cycling 动力学产生 | chemiosmotic + Michaelis-Menten + ODE | auxin 驱动 PIN1 极化足以产生规则 peak 和叶序 |

## 4.2 三者的模型层级

三篇可以按“PIN1 是否被解释”分成三个层次：

```math
\text{Barbier de Reuille: } P_{ij} \text{ 由实验图像给定}
```

```math
\text{Smith: } P_{ij}=P_i\frac{l_{ij}b^{A_j}}{\sum_k l_{ik}b^{A_k}}
```

```math
\text{Jonsson: } \frac{dP_{ij}}{dt}=f(A_j)P_i-k_2P_{ij}
```

也就是：

1. Barbier de Reuille: 已知 PIN1，求 auxin。
2. Smith: 用经验规则让 auxin 决定 PIN1。
3. Jonsson: 用 PIN1 cycling 机制让 auxin 决定 PIN1。

## 4.3 共同的正反馈结构

三篇都围绕同一个基本反馈：

```math
\text{local auxin maximum}
\Rightarrow
\text{PIN1 points toward it}
\Rightarrow
\text{more auxin flows into it}
\Rightarrow
\text{maximum is reinforced}
```

同时，峰值周围因为 auxin 被抽走或扩散，形成低 auxin 区，产生空间间距：

```math
\text{peak}
\Rightarrow
\text{neighbor depletion}
\Rightarrow
\text{new peak must appear farther away}
```

这就是叶序中“新原基远离旧原基”的动力学版本。

## 4.4 共同基础公式

三篇的公式都可以追溯到以下基础模型。

### 质量守恒

```math
\frac{dA_i}{dt}
=
\text{source}
-
\text{sink}
+
\text{inflow}
-
\text{outflow}
```

### Fick 扩散

连续形式：

```math
\partial_t A=D\nabla^2 A
```

离散形式：

```math
\sum_{j\in N_i}D_{ij}(A_j-A_i)
```

### 载体介导运输

线性形式：

```math
J_{ij}=T P_{ij}A_i
```

饱和形式：

```math
J_{ij}=T P_{ij}\frac{A_i}{K_A+A_i}
```

### 生产-降解动力学

```math
\frac{dx}{dt}=\alpha-\delta x
```

带负反馈饱和：

```math
\text{production}
=
\frac{\alpha}{1+\kappa x}
```

### Hill 型响应

```math
f(A)=k\frac{A^n}{K^n+A^n}
```

### PIN1 膜循环

```math
\frac{dP_{ij}}{dt}
=
\text{recruitment to membrane}
-
\text{internalization}
```

在 Jonsson 中具体写为：

```math
\frac{dP_{ij}}{dt}=f(A_j)P_i-k_2P_{ij}
```

## 4.5 从公式到叶序的统一推演

可以把三篇统一成以下过程：

1. L1 细胞层中存在 auxin。
2. auxin 可扩散，也可由 PIN1 主动运输。
3. 某处 auxin 稍高时，周围细胞的 PIN1 会指向它。
4. 该点获得更多 auxin，形成 peak。
5. peak 诱导原基。
6. 原基成为 sink 或把 auxin 排入内部组织。
7. 附近 auxin 被耗尽，新 peak 不能贴着旧 peak 出现。
8. 茎尖生长改变空间关系，新 peak 在远离旧原基的位置出现。
9. 长期迭代后形成稳定叶序，如 spiral phyllotaxis 和接近黄金角的发散角。

## 4.6 关键差异

### Smith 的特点

- 强调能否从一组合理规则生成叶序。
- PIN1 分配公式是经验性的指数权重。
- 原基规则和 sink 规则对稳定叶序很关键。
- 适合理解“为什么 auxin-PIN1 feedback 可以产生几何模式”。

### Barbier de Reuille 的特点

- 不解释 PIN1 极性如何产生。
- 使用真实 PIN1 图像作为网络输入。
- 强调稳态 auxin 分布和 meristem summit 的功能。
- 适合理解“真实 PIN1 网络实际意味着什么 auxin 流场”。

### Jonsson 的特点

- 明确提出 auxin 调控 PIN1 cycling。
- 使用 Michaelis-Menten 和 chemiosmotic auxin transport。
- 给出从 PIN1 cycling 到膜分配的推导。
- 适合理解“PIN1 极化本身怎样由 auxin 浓度差产生”。

## 4.7 最简统一模型

如果只保留最核心结构，可以写成：

```math
\frac{dA_i}{dt}
=
S_i-\delta A_i
+\sum_{j\in N_i}D_{ij}(A_j-A_i)
+\sum_{j\in N_i}
\left[
T P_{ji}g(A_j)
-
T P_{ij}g(A_i)
\right]
-R_i
```

其中：

```math
g(A)=A
```

或：

```math
g(A)=\frac{A}{K_A+A}
```

三篇的主要差异就在 \(P_{ij}\) 怎么定义。

Barbier de Reuille:

```math
P_{ij}=\text{observed PIN1 polarity from image}
```

Smith:

```math
P_{ij}
=
P_i
\frac{l_{ij}b^{A_j}}
{\sum_{k\in N_i}l_{ik}b^{A_k}}
```

Jonsson:

```math
\frac{dP_{ij}}{dt}
=
f(A_j)P_i-k_2P_{ij}
```

所以三篇可以看成同一个框架下对 \(P_{ij}\) 的三种处理方式。

## 4.8 对阅读和复现的建议

如果要复现模型，可以按难度从低到高：

1. 先复现 Barbier de Reuille 型图网络稳态输运：给定有向边，求 \(A_i\) 稳态。
2. 再加入 Smith 型 PIN1 指数极化：让 \(P_{ij}\) 随 \(A_j\) 更新。
3. 最后实现 Jonsson 型 PIN1 cycling：显式模拟 \(P_i\) 和 \(P_{ij}\) 的转化。

如果目标是理解叶序生成，最重要的是抓住一个统一观点：

```math
\text{叶序不是直接由黄金角公式指定的，}
\text{而是 auxin-PIN1 feedback 在生长组织上自组织出来的空间模式。}
```
