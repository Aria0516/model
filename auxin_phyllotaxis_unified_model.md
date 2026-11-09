# 生长素影响叶序的统一数学模型

## 基于 Smith et al. (2006)、Barbier de Reuille et al. (2006) 与 Jönsson et al. (2006) 的推导

## 0. 结论先行

三篇论文可以被统一成同一条因果链：

\[
\text{邻细胞生长素略高}
\Longrightarrow
\text{朝向它的膜 PIN1 增多}
\Longrightarrow
\text{更多生长素被运入}
\Longrightarrow
\text{局部峰被放大}.
\]

扩散试图抹平浓度差；PIN1 定向运输则可把小扰动放大。当主动运输反馈强于扩散和局部降解时，均匀生长素分布失稳，出现有特征间距的峰。只有外周区对这些峰具有器官发生能力；峰越过阈值后转化为原基。原基随后把 L1 表层中的生长素排入内部组织，形成周围耗竭区。顶端生长把旧原基带离发生环，新峰便在旧原基之间最空的位置出现。峰是同时越过阈值还是逐个越过阈值，决定轮生还是螺旋叶序。

本文构造的统一模型同时保留：

1. Smith 模型的生长几何、器官发生区、原基身份切换和原基汇；
2. Barbier de Reuille 模型的有限受体容量、中央区“有生长素但不触发器官”的储库，以及“强降解”和“物理移除”两种完全不同的边界条件；
3. Jönsson 模型的 PIN1 内部池—膜池循环、Michaelis–Menten 饱和运输和可解析的模式失稳条件。

最重要的解析结论是：在一维外周细胞环、快速 PIN 极化和低浓度非饱和极限下，记

\[
B=TP
\]

为主动运输强度 \(T\) 与每细胞可用膜 PIN 总量 \(P\) 的乘积，则没有生产/降解时，均匀态失稳的条件是

\[
\boxed{\frac{D}{TP}<\frac12}.
\]

若生产—降解对扰动提供速率 \(r_A>0\) 的局部恢复，条件变为

\[
\boxed{
TP\left(\frac12-\frac{D}{TP}\right)^2>r_A,
\qquad TP>2D.
}
\]

最不稳定波数和初始峰间距为

\[
q_*=\arccos\left(\frac12+\frac{D}{TP}\right),
\qquad
\ell_*=\frac{2\pi}{q_*}
\quad\text{（以细胞数计）}.
\]

这给出了从分子运输参数到“峰间距—每圈峰数—叶序类型”的直接桥梁。

---

## 1. 三篇论文分别解决什么问题

| 论文 | 数学对象 | PIN1 如何得到 | 主要输出 | 不能单独解决的问题 |
|---|---|---|---|---|
| Smith et al., 1001 | 生长曲面上的离散细胞图 + auxin/PIN ODE + 原基事件 | 邻胞生长素的壁长加权指数 softmax | 直列、十字对生、三轮生、螺旋及扰动实验 | PIN 极化公式和原基中心吸引是经验设定；仅运输反馈不能稳定地产生螺旋 |
| Barbier de Reuille et al., 1002 | 从显微图像数字化的固定细胞图和固定 PIN 有向边 | 直接由免疫标记给定 | 给定 PIN 网络下的稳态生长素分布、中央储库和 I-1 | 不产生 PIN 极性、不含生长，不能自行生成连续叶序 |
| Jönsson et al., 1003 | 静态/生长细胞图上的 auxin 运输与 PIN 循环 ODE | 邻细胞生长素驱动胞内 PIN 向相应膜定位 | 模式形成、螺旋样/轮生样峰、PIN 极性反转、线性稳定性 | 缺少原基事件和持久原基汇；增长模拟中的峰与叶序不够稳定 |

需要特别澄清：Jönsson 2006 不是以通量为反馈信号的 canalization 模型。它是浓度驱动模型：邻细胞 \(A_j\) 决定 \(P_{ij}\)，通量是结果而不是极化输入。

原始资料：

- [Smith et al., A plausible model of phyllotaxis](C:/Users/xczhang/Desktop/papers/files/1001/Smith%20et%20al.%20-%202006%20-%20A%20plausible%20model%20of%20phyllotaxis.pdf)
- [Barbier de Reuille et al., Computer simulations reveal properties...](C:/Users/xczhang/Desktop/papers/files/1002/Barbier%20de%20Reuille%20et%20al.%20-%202006%20-%20Computer%20simulations%20reveal%20properties%20of%20the%20cell-cell%20signaling%20network%20at%20the%20shoot%20apex%20in%20Arabidopsis.pdf)
- [Jönsson et al., An auxin-driven polarized transport model for phyllotaxis](C:/Users/xczhang/Desktop/papers/files/1003/Jonsson%20et%20al.%20-%202006%20-%20An%20auxin-driven%20polarized%20transport%20model%20for%20phyllotaxis.pdf)

---

## 2. 三篇原模型的数学骨架

### 2.1 Smith：经验极化 + 生长几何 + 原基状态

令 \(A_i=[\mathrm{IAA}]_i\)，\(P_i=[\mathrm{PIN}]_i\)，\(P_{ij}\) 为细胞 \(i\) 朝邻胞 \(j\) 的膜上 PIN 数量。

总 PIN 动力学为

\[
\frac{dP_i}{dt}
=
\frac{\rho_{P0}+\rho_PA_i}{1+\kappa_PP_i}
-\mu_PP_i.
\tag{S1}
\]

注意基础生产与 auxin 诱导生产在同一个饱和分式中。给定 \(A_i\) 后，其正稳态为

\[
P_i^*
=
\frac{-1+\sqrt{1+4\kappa_P(\rho_{P0}+\rho_PA_i)/\mu_P}}
{2\kappa_P}.
\tag{S2}
\]

PIN 在各侧膜上的分配为

\[
P_{ij}
=P_i
\frac{l_{ij}b^{A_j}}
{\sum_{k\in N_i}l_{ik}b^{A_k}}.
\tag{S3}
\]

令 \(\beta=\ln b\)，则 \(b^{A_j}=e^{\beta A_j}\)，所以该式是壁长加权 softmax。两侧膜的相对分配满足

\[
\frac{P_{ij}}{P_{ik}}
=\frac{l_{ij}}{l_{ik}}b^{A_j-A_k},
\tag{S4}
\]

即邻胞的微小浓度差被指数放大。

主动运输采用经验式

\[
F_{i\to j}
=TP_{ij}\frac{A_i^2}{1+\kappa_TA_j^2}.
\tag{S5}
\]

生长素守恒式为

\[
\frac{dA_i}{dt}
=
\frac{\rho_A}{1+\kappa_AA_i}
-\mu_AA_i
+\sum_{j\in N_i}D_{ij}(A_j-A_i)
+\sum_{j\in N_i}(F_{j\to i}-F_{i\to j}).
\tag{S6}
\]

只有外周区有器官发生能力。当两个相邻细胞超过阈值 \(Th\) 时创建原基。原基额外生产生长素，并用一个“等效生长素”场强制 PIN 朝原基中心极化：

\[
A_i'=\max\left\{A_i,A_{\max}\left(1-\frac{d_i}{r}\right)\right\}.
\tag{S7}
\]

原基真实浓度被硬截断在 \(A_{\max}\)，超出的量被解释为排入内部组织。

Smith 模型最关键的发现不是某一组参数，而是：仅有 S3–S6 的运输反馈只能产生近似等距峰，不能稳定地产生螺旋叶序；必须加入原基身份、原基汇和组织生长。

### 2.2 Barbier de Reuille：给定 PIN 网络后的稳态运输

这篇论文的 PIN 图来自显微图像，不随时间改变。令 \(a_c\) 为细胞 \(c\) 的浓度，\(V_c\) 为体积，\(\mathcal P_i(c)\) 和 \(\mathcal P_o(c)\) 分别为 PIN 输入和输出邻居。

被动扩散为

\[
\gamma_{c\leftarrow n}=\Gamma(a_n-a_c).
\tag{B1}
\]

主动运输含供体可用性和受体剩余容量：

\[
\psi_{c\leftarrow n}
=\Psi
\left(1-e^{-\alpha a_n}\right)
\left[1-e^{-\alpha(\sigma-a_c)}\right]_+.
\tag{B2}
\]

这里 \([x]_+=\max(x,0)\)。加截断是必要的；论文原式若在 \(a_c>\sigma\) 时不截断会产生非物理的负运输。

原基向深层的排出为

\[
\psi_{c\downarrow}
=\beta_c\Psi\left(1-e^{-\alpha a_c}\right).
\tag{B3}
\]

其中 \(E_c\in\{0,1\}\) 表示该细胞是否存在朝向深层/维管前体的 PIN1 泵，
\(\beta_c\) 是该泵的相对效率（原基中心最大，向外减小）。因此真正的向下流出为
\(J_c^{\mathrm{down}}=E_c\psi_{c\downarrow}\)。

守恒式为

\[
\frac{da_c}{dt}
=\frac1{V_c}
\left[
\sum_{n\in\mathcal N(c)}\gamma_{c\leftarrow n}
+\sum_{n\in\mathcal P_i(c)}\psi_{c\leftarrow n}
-\sum_{n\in\mathcal P_o(c)}\psi_{n\leftarrow c}
-E_c\psi_{c\downarrow}
\right]
-\delta a_c.
\tag{B4}
\]

B4 是由原文 Eq. (5) 与 Eq. (7) 直接合并得到的守恒形式。论文的展开式
Eq. (8) 疑似漏掉了 B3 中的 \(\beta_c\)，因此统一模型应以 B3–B4 为准。

该模型最独特的结论是：

- 顶端中央区可以积累生长素，但不对器官发生作出 DR5 型响应；
- 中央有限容量使流入在其边缘形成“交通堵塞”，I-1 出现在最强流入走廊与中央区交界处；
- 把中央区设为强降解汇会消除中央峰和 I-1；
- 删除中央区及其连接相当于无通量空洞，反而仍可在上游形成 I-1。

因此“中央降解”和“中央移除”在数学上不能混为一谈。

### 2.3 Jönsson：PIN 循环 + 生物物理运输 + 失稳分析

非饱和细胞模型为

\[
\frac{dA_i}{dt}
=D\sum_{k\in N_i}(A_k-A_i)
+T\sum_{k\in N_i}(A_kP_{ki}-A_iP_{ik}).
\tag{J1}
\]

带 Michaelis–Menten 饱和的成对净通量为

\[
J_{i\to j}^{\mathrm{tot}}
=D(A_i-A_j)
+T\left[
P_{ij}\frac{A_i}{K_A+A_i}
-P_{ji}\frac{A_j}{K_A+A_j}
\right].
\tag{J2}
\]

详细模型将胞质和细胞壁/质外体分开：

\[
J_{i\to ij}^{\mathrm{tot}}
=D_{\mathrm{efflux}}A_i-D_{\mathrm{influx}}A_{ij}
+P_{ij}\left[
T_{\mathrm{efflux}}\frac{A_i}{K_A+A_i}
-T_{\mathrm{influx}}\frac{A_{ij}}{K_A+A_{ij}}
\right].
\tag{J3}
\]

PIN1 在胞内池 \(P_i^c\) 与朝向邻胞 \(j\) 的膜池 \(P_{ij}\) 之间循环：

\[
\frac{dP_{ij}}{dt}=f(A_j)P_i^c-k_2P_{ij},
\tag{J4}
\]

\[
\frac{dP_i^c}{dt}
=\sum_{k\in N_i}\left(k_2P_{ik}-f(A_k)P_i^c\right).
\tag{J5}
\]

可取线性反馈 \(f(A)=k_1A\)，也可取 Hill 反馈

\[
f(A)=k_1\frac{A^n}{K_F^n+A^n}.
\tag{J6}
\]

若 PIN 循环比生长素变化快，令 J4 为零并利用每细胞总 PIN 守恒，可得

\[
P_{ij}^*
=P_i^{\mathrm{tot}}
\frac{f(A_j)}{k_2+\sum_{k\in N_i}f(A_k)}.
\tag{J7}
\]

在线性反馈下，等价于

\[
P_{ij}^*
=P_i^{\mathrm{tot}}
\frac{A_j}{k_2/k_1+\sum_{k\in N_i}A_k}.
\tag{J8}
\]

这为 Smith 的经验 softmax 提供了一个机制化替代。

---

## 3. 统一模型的建模对象与变量

只显式模拟茎尖表皮 L1。它在时刻 \(t\) 是一个随生长变化的细胞图

\[
G(t)=(\mathcal V(t),\mathcal E(t)).
\]

对细胞 \(i\) 定义：

| 符号 | 含义 |
|---|---|
| \(V_i(t)\) | 细胞有效体积或 L1 面积乘统一厚度 |
| \(A_i(t)\) | 生长素浓度 |
| \(N_i^A=V_iA_i\) | 生长素量；数值积分的守恒变量 |
| \(P_i^T\) | 每细胞总 PIN1 有效量；合成参数按每细胞计 |
| \(P_i^c\) | 胞内 PIN1 有效量 |
| \(P_{ij}\) | 细胞 \(i\) 朝邻胞 \(j\) 的膜 PIN1 有效量 |
| \(l_{ij}\) | 共享壁长 |
| \(d_{ij}\) | 两细胞中心距离 |
| \(s_i\in[0,1]\) | 原基身份/向内部排出能力 |
| \(\chi_C,\chi_P,\chi_X\) | 中央区、外周器官发生区、近基部区指示函数 |

约束为

\[
P_i^T=P_i^c+\sum_{j\in N_i}P_{ij}.
\tag{U1}
\]

中央区允许 \(A_i\) 较高，但原基触发函数中令 \(\chi_P=0\)。这正是“有生长素但器官响应弱”的数学表达。

---

## 4. 统一模型的完整方程

### 4.1 细胞间净通量

先定义几何扩散电导

\[
D_{ij}=D_0\frac{l_{ij}}{d_{ij}}=D_{ji}.
\tag{U2}
\]

定义供体饱和函数和受体容量函数

\[
u(A)=\frac{A}{K_A+A},
\qquad
v_\sigma(A)=\left[1-e^{-\alpha(\sigma-A)}\right]_+.
\tag{U3}
\]

从 \(i\) 到 \(j\) 的净通量取为

\[
\boxed{
J_{ij}
=D_{ij}(A_i-A_j)
+T\left[
P_{ij}u(A_i)v_\sigma(A_j)
-P_{ji}u(A_j)v_\sigma(A_i)
\right].
}
\tag{U4}
\]

显然

\[
J_{ji}=-J_{ij}.
\tag{U5}
\]

U4 同时继承：

- Smith 的“目标浓度过高时流入饱和”；
- Barbier de Reuille 的“受体容量有限”；
- Jönsson 的“PIN 数量乘供体 Michaelis–Menten 可用性”。

若只研究模式起始，可令 \(v_\sigma=1\)，并在线性低浓度极限用 \(u(A)\simeq A/K_A\)。

### 4.2 生长素量守恒

令区域和原基依赖的生产上限为

\[
\rho_i
=\rho_C\chi_C(i)+\rho_{\mathrm{PZ}}\chi_P(i)+\rho_X\chi_X(i)+\rho_s s_i.
\tag{U6}
\]

外围未显式组织还可通过边界输入 \(B_i v_\sigma(A_i)\) 提供生长素。原基向深层的连续排出采用饱和汇

\[
R_i^{\mathrm{prim}}
=\eta_sV_is_i\frac{A_i}{K_s+A_i}.
\tag{U7}
\]

这里 \(\eta_s\) 是最大体积归一化排出率，量纲为“浓度/时间”。
由于 U6 同时允许原基额外生产 \(\rho_ss_i\)，原基并不会仅凭
\(s_i>0\) 就自动成为净汇。忽略极化引起的额外流入时，在背景浓度
\(A_0\) 附近产生局部耗竭至少需要

\[
\boxed{
\eta_s\frac{A_0}{K_s+A_0}
>
\frac{\rho_s}{1+\kappa_AA_0}.
}
\tag{U7a}
\]

若 \(A_q>0\) 把周围运输继续引向原基，U7a 只是必要的局部比较；完整净汇
条件还必须把跨边净流入计入。

完整生长素量方程为

\[
\boxed{
\frac{dN_i^A}{dt}
=
V_i\frac{\rho_i}{1+\kappa_AA_i}
+B_iv_\sigma(A_i)
-\mu_AN_i^A
-R_i^{\mathrm{prim}}
-\sum_{j\in N_i}J_{ij}.
}
\tag{U8}
\]

它把 Smith 的硬截断 \(A\le A_{\max}\) 改为连续汇 U7，因此可以做稳定性分析，也不会在一个时间步中凭空删除不明数量的生长素。

由于 \(N_i^A=V_iA_i\)，浓度形式自动包含生长稀释：

\[
\frac{dA_i}{dt}
=\frac1{V_i}\frac{dN_i^A}{dt}
-\frac{A_i}{V_i}\frac{dV_i}{dt}.
\tag{U9}
\]

Smith 和 Jönsson 的增长模拟都未清楚纳入 U9 的稀释项；统一模型应显式保留它。

### 4.3 总 PIN1 的生产与降解

定义 PIN1 的每细胞合成率

\[
G_i^P(A_i,P_i^T)
=\frac{\rho_{P0}+\rho_PA_i}{1+\kappa_PP_i^T}.
\]

则 Smith 的总 PIN 动力学可写为

\[
\boxed{
\frac{dP_i^T}{dt}=G_i^P-\mu_PP_i^T.
}
\tag{U10}
\]

若数据不足，也可固定 \(P_i^T=P_0\)。下面把合成、降解和膜循环写成一个
显式守恒系统；对该系统求和会自动恢复 U10，实际积分时不应再把 U10
作为独立方程重复积分。Smith 的敏感性分析说明总 PIN 方程的精确形式不是
螺旋维持的核心，关键是膜分配对邻胞浓度的非线性响应。

### 4.4 PIN1 循环与极化

定义一个与原基身份有关、但与真实生长素分开的极化信号

\[
C_j=A_j+A_qs_j.
\tag{U11}
\]

\(A_q\) 表示原基形成后可能由发育状态、力学或其他信号产生的持久极化线索；设 \(A_q=0\) 即检验是否可以完全由真实生长素维持极化。这样比把它称为“等效生长素”更清楚。

取

\[
F(C)=F_0+F_1\frac{C^n}{K_F^n+C^n}.
\tag{U12}
\]

PIN 循环方程为

\[
\boxed{
\begin{aligned}
\frac{dP_{ij}}{dt}
={}&k_{\mathrm{on}}l_{ij}F(C_j)P_i^c
-(k_{\mathrm{off}}+\mu_P)P_{ij},\\
\frac{dP_i^c}{dt}
={}&G_i^P-\mu_PP_i^c\\
&-\sum_{k\in N_i}
\left[
k_{\mathrm{on}}l_{ik}F(C_k)P_i^c
-k_{\mathrm{off}}P_{ik}
\right].
\end{aligned}
}
\tag{U13}
\]

U13 保证每细胞有限 PIN 池在不同膜之间竞争，并保持
\(P_i^c,P_{ij}\ge0\)。把胞内池与所有膜池相加，膜化/内吞项严格抵消，
得到 U10。

若 PIN 循环快，令 \(dP_{ij}/dt=0\)，记

\[
\rho=\frac{k_{\mathrm{off}}+\mu_P}{k_{\mathrm{on}}},
\]

则

\[
\boxed{
P_{ij}^*
=P_i^T
\frac{l_{ij}F(C_j)}
{\rho+\sum_{k\in N_i}l_{ik}F(C_k)}.
}
\tag{U14}
\]

U14 同时包含两篇论文的极化闭合式：

- 取 \(\rho\to0\)、\(F(C)=e^{\beta C}=b^C\)，得到 Smith 的壁长加权 softmax；
- 取 \(l_{ij}=1\)、\(F(A)=A\)、\(k_{\mathrm{on}}=k_1\)、
  \(k_{\mathrm{off}}=k_2\)、\(\mu_P=0\)，并固定 \(P_i^T\)，得到 Jönsson
  的准稳态式。

### 4.5 原基触发、身份场与汇

在时刻 \(t\)，若细胞 \(i\) 同时满足

\[
\chi_P(i)=1,
\qquad
A_i\ge A_{\mathrm{on}},
\qquad
A_i\ge A_j\quad\forall j\in N_i,
\tag{U15}
\]

且它不在已有原基的锁定半径内，则创建新原基 \(m\)，记录位置、时间和方位角

\[
(\mathbf x_m,t_m,\theta_m).
\]

原基身份场可取

\[
s_i(t)
=\min\left\{
1,
\sum_m
\exp\left[-\frac{d_s(\mathbf x_i,\mathbf x_m(t))^2}
{2w_m(t)^2}\right]
\right\},
\tag{U16}
\]

其中 \(d_s\) 是曲面测地距离，\(w_m(t)\) 是随原基年龄增长的身份场宽度。
U16 随即激活：

- 额外生产 \(\rho_ss_i\)；
- 向内部排出 U7；
- 可选的持久极化线索 U11。

用局部极大值而不是“任意两相邻超阈值细胞”触发，可避免 Smith 原规则中的配对歧义。数值上还应使用 \(A_{\mathrm{on}}>A_{\mathrm{off}}\) 的滞后或最短锁定时间，防止峰在阈值附近反复触发。
若若干相邻细胞形成完全相等的超阈值平台，U15 中的非严格不等号会使它们
都成为局部极大；实现时应把平台视为一个连通分量，只选一个代表点，或使用
带最小间距的非极大抑制，避免结果依赖细胞遍历顺序。

### 4.6 生长与细胞分裂

可采用两种替代分辨率：

1. 几何精细层：使用 Smith 的旋转曲面和相对基本伸长率 RERG，或 Jönsson 的半球—圆柱表面、细胞球增长和排斥弹簧；
2. 叶序约化层：只追踪原基相对发生环的径向外移。

约化层令原基形成于半径 \(R_g\) 的发生环，之后

\[
R_m(t)=R_g e^{\gamma_g(t-t_m)},
\qquad
\dot\theta_m=0.
\tag{U17}
\]

细胞分裂时必须按量而非浓度守恒地重映射所有池。若子细胞体积比例为
\(\omega\) 和 \(1-\omega\)，则分别继承 \(\omega N_i^A\) 与
\((1-\omega)N_i^A\)；\(P_i^c\) 同样按体积比分配。旧外膜上的 \(P_{ij}\)
按两子细胞继承的壁长比例分配，新生姐妹壁的膜池可置零或从胞内池等量转入。
更新后必须同时检查总 PIN 守恒和 U1，不能只拆分 \(P_i^T\) 而忽略各膜池。

---

## 5. 质量守恒、非负性与时间尺度

### 5.1 质量守恒

对全部细胞求和。由于 U5，内部边通量两两抵消：

\[
\sum_i\sum_{j\in N_i}J_{ij}=0.
\]

因此

\[
\frac{d}{dt}\sum_iN_i^A
=\sum_i
\left[
V_i\frac{\rho_i}{1+\kappa_AA_i}
+B_iv_\sigma(A_i)
-\mu_AN_i^A
-R_i^{\mathrm{prim}}
\right].
\tag{U18}
\]

关闭生产、边界输入、降解和原基汇后，总生长素严格守恒。这是实现时最重要的单元测试。

### 5.2 非负性

U3 满足 \(u(0)=0\)，目标容量函数被截断为非负，扩散在 \(A_i=0\) 时只会向细胞 \(i\) 输入。连续系统因此在非负正交体内不变。数值上可用 BDF/Radau
处理刚性，但这两类方法本身不自动保证正性；还应配合非负约束、对数变量、
正性保持离散或受限步长。不要直接使用过大的显式 Euler 步长。
对 PIN 池也一样：当 \(P_{ij}=0\) 时 U13 的膜化项非负；当 \(P_i^c=0\)
时，合成和内吞项非负。因此显式胞内/膜池写法不会产生负 PIN。

### 5.3 快慢分离

1002 假设运输建立稳态的时间远短于生长和分裂。统一模型可写成

\[
\tau_A,\tau_P\ll\tau_g,\tau_{\mathrm{plastochron}}.
\tag{U19}
\]

若 U19 成立，可在每个几何更新时间内把 U8 与 U13 积分至准稳态，并用
U10 检查 PIN 总池；若不成立，就必须同时积分化学和生长，不能直接套用
固定 PIN 的稳态结论。

---

## 6. 均匀稳态

在没有原基、无边界输入、区域均一且所有细胞相同的情形，所有内部通量为零。生长素稳态满足

\[
\frac{\rho_A}{1+\kappa_AA_0}=\mu_AA_0.
\tag{E1}
\]

正根为

\[
\boxed{
A_0
=\frac{-1+\sqrt{1+4\kappa_A\rho_A/\mu_A}}
{2\kappa_A}.
}
\tag{E2}
\]

若 \(\kappa_A\to0\)，则 \(A_0=\rho_A/\mu_A\)。

给定 \(A_0\)，总 PIN 稳态满足

\[
\frac{\rho_{P0}+\rho_PA_0}{1+\kappa_PP_0}=\mu_PP_0,
\]

故

\[
\boxed{
P_0
=\frac{-1+\sqrt{1+4\kappa_P(\rho_{P0}+\rho_PA_0)/\mu_P}}
{2\kappa_P}.
}
\tag{E3}
\]

若每个细胞有 \(z\) 个等长邻边，快速 PIN 循环给出每侧均匀膜 PIN

\[
P_{ij,0}
=P_0\frac{lF(A_0)}{\rho+zlF(A_0)}.
\tag{E4}
\]

---

## 7. 一维外周环的线性稳定性：完整推导

这一节给出从运输方程到峰间距的解析桥梁。

### 7.1 约化假设

考虑 \(N\) 个等大细胞组成的周期环，每个细胞只有左右两个邻居。取：

- 快速 PIN 循环；
- 线性反馈 \(F(A)=A\)；
- 大部分 PIN 位于膜上，故每细胞可用膜 PIN 总量为常数 \(P\)；
- 主动运输未饱和；
- 暂时忽略原基和几何生长。

本节把 U4 除以共同细胞体积，并将低浓度线性化
\(u(A)\simeq A/K_A\) 中的 \(1/K_A\)（以及取定的容量因子）吸收到
系数 \(T\) 里。因此这里的 \(D\) 和 \(TP\) 都是浓度方程中的有效
一阶速率；它们不是未经换算的 U4 有量纲参数。

于是

\[
P_{i,i+1}
=P\frac{A_{i+1}}{A_{i-1}+A_{i+1}},
\qquad
P_{i,i-1}
=P\frac{A_{i-1}}{A_{i-1}+A_{i+1}}.
\tag{L1}
\]

显然

\[
P_{i,i-1}+P_{i,i+1}=P.
\tag{L2}
\]

生长素方程为

\[
\begin{aligned}
\dot A_i={}&R(A_i)
+D(A_{i-1}+A_{i+1}-2A_i)\\
&+T\left(
A_{i-1}P_{i-1,i}
+A_{i+1}P_{i+1,i}
-A_iP
\right),
\end{aligned}
\tag{L3}
\]

其中 \(R(A)\) 是生产—降解净反应。

### 7.2 在线性阶展开 PIN

令

\[
A_i=A_0+a_i,
\qquad |a_i|\ll A_0.
\]

由 L1，

\[
P_{i,i+1}
=\frac P2+\frac{P}{4A_0}(a_{i+1}-a_{i-1})+O(a^2),
\tag{L4}
\]

\[
P_{i,i-1}
=\frac P2+\frac{P}{4A_0}(a_{i-1}-a_{i+1})+O(a^2).
\tag{L5}
\]

从左邻胞流入 \(i\) 的主动运输线性化为

\[
TA_{i-1}P_{i-1,i}
=TP\left[
\frac{A_0}{2}
+\frac{a_{i-1}}2
+\frac{a_i-a_{i-2}}4
\right]+O(a^2).
\tag{L6}
\]

右邻胞相同地给出

\[
TA_{i+1}P_{i+1,i}
=TP\left[
\frac{A_0}{2}
+\frac{a_{i+1}}2
+\frac{a_i-a_{i+2}}4
\right]+O(a^2).
\tag{L7}
\]

总主动输出是

\[
TA_iP=TP(A_0+a_i).
\tag{L8}
\]

因此主动运输的线性扰动为

\[
TP\left[
\frac{a_{i-1}+a_{i+1}}2
-\frac{a_i}{2}
-\frac{a_{i-2}+a_{i+2}}4
\right].
\tag{L9}
\]

若

\[
R'(A_0)=-r_A<0,
\]

则线性系统的 Jacobian 非零元为

\[
J_{i,i\pm2}=-\frac{TP}{4},
\tag{L10}
\]

\[
J_{i,i\pm1}=D+\frac{TP}{2},
\tag{L11}
\]

\[
J_{ii}=-r_A-2D-\frac{TP}{2}.
\tag{L12}
\]

当 \(r_A=0\) 时，这正是 Jönsson 补充材料的 Jacobian。

### 7.3 Fourier 模式与色散关系

取

\[
a_i=\hat a\,e^{\lambda t+\mathrm{i}qi}.
\tag{L13}
\]

利用

\[
a_{i-1}+a_{i+1}=2\cos q\,a_i,
\qquad
a_{i-2}+a_{i+2}=2\cos 2q\,a_i,
\]

得到

\[
\lambda(q)
=-r_A-2D+(2D+TP)\cos q-TP\cos^2q.
\tag{L14}
\]

令 \(c=\cos q\)、\(B=TP\)，则

\[
\boxed{
\lambda(q)
=-r_A+(1-c)(Bc-2D).
}
\tag{L15}
\]

L15 是线性极化与线性供体运输的特例。更一般地，在膜占据接近 1、
受体容量 \(v_\sigma(A)\simeq v_0\) 可视为常数时，定义两个对数弹性

\[
\varepsilon_F=\frac{A_0F'(A_0)}{F(A_0)},
\qquad
\varepsilon_u=\frac{A_0u'(A_0)}{u(A_0)},
\]

以及

\[
D_L=\frac{D_{ij}}{V_0},
\qquad
B_0=\frac{T P_{\mathrm{mem},0}v_0u(A_0)}{V_0A_0}.
\]

重复 L4–L14 的一阶展开可得

\[
\boxed{
\lambda(q)
=-r_A+(1-c)
\left\{
B_0\left[\varepsilon_F(1+c)-\varepsilon_u\right]-2D_L
\right\}.
}
\tag{L15a}
\]

因此完整非线性函数的判据应写成

\[
\max_{-1\le c<1}
(1-c)
\left\{
B_0[\varepsilon_F(1+c)-\varepsilon_u]-2D_L
\right\}
>r_A.
\tag{L15b}
\]

取 \(F(A)=A\)、\(u(A)\simeq A/K_A\) 时
\(\varepsilon_F=\varepsilon_u=1\)，且
\(B_0=TP_{\mathrm{mem},0}v_0/(V_0K_A)\)；把这些常数吸收到第 7.1 节的
\(T,P,D\) 后，L15a 正好退化为 L15。由此也可看出，
\(TP>2D\) 不是未经线性化的 U4 的普适阈值。

### 7.4 无反应时的阈值

先令 \(r_A=0\)。非均匀模式满足 \(q\ne0\)，故 \(1-c>0\)。存在 \(\lambda>0\) 当且仅当存在 \(c<1\) 使

\[
Bc-2D>0.
\]

由于 \(c\) 可任意接近 1，条件为

\[
\boxed{B>2D}
\quad\Longleftrightarrow\quad
\boxed{\frac{D}{TP}<\frac12}.
\tag{L16}
\]

L16 是无限链或大 \(N\) 环的连续波数极限。有限细胞环上不能令
\(q\) 任意接近零，严格条件是至少存在一个允许波数
\(q_m=2\pi m/N\) 使 \(\lambda(q_m)>0\)。

### 7.5 有生产—降解恢复时的阈值

对 \(c\) 最大化

\[
f(c)=(1-c)(Bc-2D).
\]

有

\[
c_*=\frac12+\frac{D}{B},
\qquad B>2D,
\tag{L17}
\]

并且

\[
f_{\max}
=B\left(\frac12-\frac{D}{B}\right)^2.
\tag{L18}
\]

故模式形成条件为

\[
\boxed{
B\left(\frac12-\frac{D}{B}\right)^2>r_A,
\qquad B>2D.
}
\tag{L19}
\]

等价写成

\[
\boxed{(B-2D)^2>4Br_A,\qquad B>2D.}
\tag{L20}
\]

对统一模型的生产函数，

\[
R(A)=\frac{\rho_A}{1+\kappa_AA}-\mu_AA,
\]

因此

\[
r_A
=\mu_A+
\frac{\rho_A\kappa_A}{(1+\kappa_AA_0)^2}.
\tag{L21}
\]

### 7.6 最不稳定波长

由 L17，

\[
\boxed{
q_*=\arccos\left(\frac12+\frac{D}{TP}\right),
\qquad
\ell_*=\frac{2\pi}{q_*}.
}
\tag{L22}
\]

当 \(D/(TP)=0\) 时，\(q_*=\pi/3\)，故最短初始峰间距是 6 个细胞；当 \(D/(TP)\to1/2\) 时，\(q_*\to0\)，峰间距趋于无穷。这解释了为什么增强主动运输会增加峰数，而增强扩散会减少峰数或完全消除模式。

在有限 \(N\) 细胞环上，只允许

\[
q_m=\frac{2\pi m}{N},
\qquad m=1,\ldots,\lfloor N/2\rfloor.
\tag{L23}
\]

实际初始峰数应取

\[
m_*=\arg\max_m\lambda(q_m).
\tag{L24}
\]

### 7.7 一个具体数值例子

令

\[
TP=1,\qquad D=0.2,\qquad r_A=0.02.
\]

则

\[
\frac{D}{TP}=0.2<0.5,
\]

\[
q_*=\arccos(0.7)\approx0.795,
\qquad
\ell_*\approx7.90\text{ 个细胞},
\]

\[
\lambda_{\max}=0.09-0.02=0.07>0.
\]

若外周环有 \(N=24\) 个细胞，则

\[
N/\ell_*\approx3.0,
\]

而有限环的允许模中

\[
\lambda(q_3=\pi/4)\approx0.06995
>
\lambda(q_2)\approx0.04244,
\qquad
\lambda(q_4)=0.03.
\]

因此三峰结论也通过离散谱而不只是连续波长近似得到确认。若三个峰近同时
越过原基阈值，倾向三轮生；若阈值、原基汇和增长使它们按时间分开越过
阈值，则可能进入逐个产生的螺旋序列。

### 7.8 连续极限的直觉

在小 \(q\) 处展开 L14：

\[
\lambda(q)
\simeq
-r_A
+\frac{TP-2D}{2}q^2
-\frac{7TP-2D}{24}q^4+O(q^6).
\tag{L25}
\]

二阶项在 \(TP>2D\) 时表现为反扩散，放大长波扰动；四阶项抑制过短波长，于是留下有限特征尺度。这不是经典的两化学物质 Turing 反应—扩散，而是由定向运输反馈产生的有限波长失稳。

---

## 8. 从峰间距到叶序类型

### 8.1 同时形成还是依次形成

线性稳定性只决定最先增长的空间模式，不决定峰何时跨过器官阈值。
对 U7，在 \(s_i=1\) 的背景浓度 \(A_0\) 附近，有两个不同的时间尺度。
若先忽略额外生产和流入，把浓度从 \(A_0\) 排空的特征时间约为

\[
\tau_{\mathrm{drain}}
\sim\frac{K_s+A_0}{\eta_s}.
\tag{P0}
\]

而已建立状态附近的微小浓度扰动受到一阶阻尼

\[
\displaystyle
r_s(A_0)=\frac{\eta_sK_s}{(K_s+A_0)^2}.
\tag{P0b}
\]

决定“同时触发还是依次触发”的三个主时间尺度可写为

\[
\tau_{\mathrm{chem}}\sim\lambda_{\max}^{-1},
\qquad
\tau_{\mathrm{sink}}\sim\tau_{\mathrm{drain}},
\qquad
\tau_g\sim\gamma_g^{-1}.
\]

- 若多个峰在原基汇建立前同时达到 \(A_{\mathrm{on}}\)，得到轮生；
- 若第一个峰一旦触发就迅速建立汇并压低其他候选峰，得到逐个产生的螺旋；
- 若 \(TP\) 太弱或 \(D,r_A\) 太强，均匀态稳定，不形成原基；
- 若汇太弱或阈值太低，会形成过密、无规则或近环状的原基。

不能直接写 \(\eta_s^{-1}\)，因为 \(\eta_s\) 的量纲是浓度/时间；
\(r_s^{-1}\) 描述局部扰动松弛，也不等同于触发后的整体排空时间。

### 8.2 每圈可容纳的峰数

若发生环周长为 \(2\pi R_g\)，细胞平均切向尺度为 \(a_c\)，则物理峰间距约为

\[
L_*=a_c\ell_*.
\tag{P1}
\]

每圈可容纳的峰数约为

\[
M\simeq\frac{2\pi R_g}{L_*}.
\tag{P2}
\]

因此扩大中央区或发生环半径、增强主动运输、减弱扩散，都会提高 \(M\)，使系统更易出现高阶轮生；相反则减少峰数。Jönsson 改变中央区尺寸得到螺旋样和十字对生样模式，正符合这一尺度竞争。

---

## 9. 原基耗竭、发散角与黄金角

### 9.1 原基为何排斥附近的新峰

原基形成后，U7 把生长素从 L1 排向内部。在线性、定常和一维近似下，设背景浓度为 \(\bar A\)，点状原基汇位于 \(x=0\)，则扰动 \(a=A-\bar A\) 满足

\[
D_{\mathrm{eff}}a''-\mu_{\mathrm{eff}}a
=Q_s\bar A\,\delta(x).
\tag{P3}
\]

其解为

\[
a(x)
=-
\frac{Q_s\bar A}
{2\sqrt{D_{\mathrm{eff}}\mu_{\mathrm{eff}}}}
e^{-|x|/\ell_d},
\qquad
\ell_d=\sqrt{\frac{D_{\mathrm{eff}}}{\mu_{\mathrm{eff}}}}.
\tag{P4}
\]

所以原基周围自然产生尺度为 \(\ell_d\) 的耗竭区。这就是经典“旧原基抑制新原基”的生长素运输版本。
这里要求 \(D_{\mathrm{eff}}>0,\mu_{\mathrm{eff}}>0\)：P3 是对已形成原基
外围耗竭包络的现象学粗粒化，可代表被动扩散、深层排出和饱和后的稳定响应。
它不能直接从 L25 的“反扩散”失稳区推出；完整 auxin–PIN 系统中的耗竭
形状应由 U4–U14 数值求得。

### 9.2 发散角的约化选择方程

令新原基总在半径 \(R_g\) 处产生，旧原基以每个 plastochron 的径向比

\[
\varrho=e^{\gamma_gT_p}>1
\tag{P5}
\]

向外移。为了写出“逐个放置”的动力学，令最近的旧原基
\(\theta_{n-1}=0\)，既有序列的相邻发散角为 \(\Delta\)，而待放置新原基的
候选角为 \(\delta\)。第 \(k\) 个旧原基满足

\[
R_{n-k}=R_g\varrho^k,
\qquad
\theta_{n-k}=-(k-1)\Delta,
\qquad
\theta_n=\delta.
\tag{P6}
\]

二者距离为

\[
d_k^2(\delta\mid\Delta)
=R_g^2\left[
1+\varrho^{2k}
-2\varrho^k\cos\!\left(\delta+(k-1)\Delta\right)
\right].
\tag{P7}
\]

把已有原基的耗竭足迹近似为 Gaussian，候选位置的总抑制为

\[
E_{\mathrm{cand}}(\delta\mid\Delta)
=\sum_{k=1}^{K}
\exp\left[-\frac{d_k^2(\delta\mid\Delta)}{2\ell_d^2}\right].
\tag{P8}
\]

Gaussian 是为了得到光滑、易微分的二维抑制核，并不是 P4 指数核的精确延拓；
改用 \(\exp[-d_k/\ell_d]\) 会给出同类最优响应方程，但数值角度会改变。

若每一步把新原基放在 \(E_{\mathrm{cand}}\) 的局部最小值，恒定发散角
\(\Delta\) 必须是这个逐步映射的固定点，即最优候选角满足
\(\delta_*=\Delta\)。记

\[
\bar d_k^2(\Delta)
=d_k^2(\Delta\mid\Delta)
=R_g^2\left[
1+\varrho^{2k}-2\varrho^k\cos(k\Delta)
\right],
\]

则固定点条件为

\[
\boxed{
\sum_{k=1}^{K}
\varrho^k\sin(k\Delta)
\exp\left[-\frac{\bar d_k^2(\Delta)}{2\ell_d^2}\right]
=0,
\qquad
\left.
\frac{\partial^2E_{\mathrm{cand}}}{\partial\delta^2}
\right|_{\delta=\Delta}>0.
}
\tag{P9}
\]

P9 必须对给定 \(\varrho\) 和 \(\ell_d/R_g\) 数值求解。若改为比较
“整族理想螺旋”的全局代价 \(E(\Delta)\)，求导会多出一个 \(k\) 因子；
那不是逐个原基放置的固定点条件。P9 说明发散角不是由一个预先写入的
黄金角常数决定，而是由生长速度、plastochron、发生环半径和耗竭长度共同选择。
在“所有历史间隔都由同一个 \(\Delta\) 表示”的一维约化下，还可检验
\(\left|d\delta_*/d\Delta\right|<1\)。真实历史包含最近 \(K-1\) 个角增量；
其严格历时稳定性要构造相应延迟映射，并要求 Jacobian 的谱半径小于 1。
P9 本身只给出局部极小固定点。

### 9.3 为什么常接近黄金角

在“一次一个原基、需要长期避免与所有旧原基对齐”的参数区间，若

\[
\alpha_\theta=\frac{\Delta}{2\pi}
\]

接近低分母有理数 \(p/q\)，那么第 \(q\) 个原基会与较早原基近似同列，导致 P8 中出现很小的距离和强抑制。最难被有理数逼近的数与黄金比例有关：

\[
\alpha_g=\frac{3-\sqrt5}{2}\approx0.381966,
\]

从而

\[
\Delta_g=2\pi\alpha_g\approx137.508^\circ.
\tag{P10}
\]

其连分数收敛分母为

\[
2,3,5,8,13,\ldots,
\]

即 Fibonacci 数，因此出现 Fibonacci 副螺旋。

但必须强调：黄金角不是 U8–U17 的严格普适解析解。完整模型可随参数产生
\(180^\circ\)、成对轮生、三轮生或其他序列；P9 只描述“一次一个原基”
的恒定角分支，不能单独描述同时出现的轮生。Smith 的长时模拟后期发散角
均值约 \(132.9^\circ\)、总体标准差约 \(8.3^\circ\)。这是根据其补充材料
Table 2 中第 11–40 个原基的 30 个角二次计算所得，并非论文正文直接报告的
统计量。该离散度说明细胞几何和噪声会造成显著偏离；评估模型时应比较
角度分布，而不是要求每一步恰好 \(137.5^\circ\)。

---

## 10. 中央区储库的数学作用

统一模型把中央区定义为

\[
\chi_P=0,
\qquad
A_i\text{ 可积累},
\qquad
v_\sigma(A_i)\text{ 随接近容量而下降}.
\tag{C1}
\]

于是中央区可以接收生长素，却不因高 \(A\) 直接形成器官。当某条原基间走廊向中央输送最多生长素时，中央受体容量下降，流在入口上游积累，形成 I-1。

两个干预有不同数学实现：

| 干预 | 模型操作 | 连续边界类比 | 对 I-1 的预测 |
|---|---|---|---|
| 中央强降解 | 保留节点和入边，令 \(\mu_C\to\infty\) | 吸收/近 Dirichlet 边界 | 流仍被吞噬；中央峰和 I-1 消失 |
| 中央物理移除 | 删除中央节点及相关边 | 无通量/反射边界 | 流不能进入空洞；上游仍堵塞，I-1 可保留 |

这一区分是 1002 对统一模型最重要的贡献。

---

## 11. 无量纲控制参数

取生长素尺度 \(A_0\)、时间尺度 \(\mu_A^{-1}\)、细胞尺度 \(a_c\)、PIN 尺度
\(P_0\)。从 U4 的原始参数出发时，先按 L15a 定义浓度方程中的有效扩散率
\(D_L\) 和主动运输率 \(B_0\)。均匀态真正参与运输的是膜总池

\[
P_{\mathrm{mem},0}
=zP_{ij,0}
=P_0\frac{zlF(A_0)}{\rho+zlF(A_0)},
\tag{N1}
\]

而不一定是总 PIN \(P_0\)。最关键的无量纲组合为：

| 无量纲数 | 定义 | 控制作用 |
|---|---|---|
| 运输—扩散比 | \(\Pi_T=B_0/D_L\) | 是否越过模式形成阈值；L15 特例要求 \(\Pi_T>2\) |
| 反应阻尼 | \(\Pi_R=r_A/B_0\) | 生产/降解对浓度扰动的恢复强度 |
| 极化弹性 | \(\Pi_F=A_0F'(A_0)/F(A_0)\) | 邻胞浓度扰动被膜 PIN 分配放大的线性增益 |
| 供体弹性 | \(\Pi_u=A_0u'(A_0)/u(A_0)\) | 本细胞浓度扰动改变主动输出的线性增益 |
| PIN 极化快慢 | \(\varepsilon_P=\mu_A/(k_{\mathrm{off}}+\mu_P)\) | \(\varepsilon_P\ll1\) 是快速重极化的必要尺度条件 |
| 膜化比例 | \(\Pi_M=\rho/[lF(A_0)]\) | 大时 PIN 多在胞内，小时时接近 Smith/Jönsson 的归一化膜分配 |
| 发生环容量 | \(\Pi_C=2\pi R_g/L_*\) | 同时可容纳的峰数/轮生阶数 |
| 生长—化学比 | \(\Pi_G=\gamma_g/\lambda_{\max}\) | 仅在 \(\lambda_{\max}>0\) 区有直接时间尺度意义；小时化学准稳态 |
| 原基汇强度 | \(\Pi_S=\eta_s/[\mu_A(K_s+A_0)]\) | 相对背景周转的排空速度和新峰时间分离 |
| 阈值 | \(\Pi_\Theta=A_{\mathrm{on}}/A_0\) | plastochron 与同时/依次触发 |
| 中央区大小 | \(\Pi_Z=R_C/R_g\) | 发生环周长、储库容量和叶序转变 |

膜总占据模态的松弛率还包含
\(k_{\mathrm{on}}zlF(A_0)\)，但膜间重极化可能受
\(k_{\mathrm{off}}+\mu_P\) 限制；两种模态都应快于 auxin 动力学，才能安全使用
U14。与其逐个拟合大量有量纲参数，优先扫描
\((\Pi_T,\Pi_R,\Pi_F,\Pi_u,\Pi_C,\Pi_G,\Pi_S,\Pi_\Theta,\Pi_Z)\)
更容易得到可解释的相图。
这组数主要控制均匀态附近与器官触发；它并不完备。非线性峰的幅值和饱和
形状还需固定或扫描
\(K_A/A_0,K_s/A_0,K_F/A_0,\sigma/A_0,\alpha A_0,
\kappa_AA_0,\kappa_PP_0,A_q/A_0,n,F_0/F_1\)。

---

## 12. 数值实现方案

### 12.1 最小可行版本

1. 在半球或圆盘上生成近六边形/Voronoi L1 细胞图；标记中央区和外周区。
2. 初始化

   \[
   A_i=A_0(1+10^{-3}\xi_i),
   \]

   其中 \(\xi_i\) 是零均值小噪声；令 \(P_i^T=P_0\)，按 U14 初始化膜 PIN。
3. 在固定几何上积分 U8 与 U13，以 U10 检查 PIN 总池；化学刚性较强时用 BDF 或 Radau。
4. 监测 U15。出现候选局部峰时创建原基并更新 U16。
5. 每隔较慢的几何时间步更新细胞位置、体积和邻接；分裂时守恒分配生长素量和 PIN 量。
6. 记录每个原基的 \((t_m,R_m,\theta_m)\)，计算

   \[
   \Delta_m=\operatorname{mod}(\theta_m-\theta_{m-1},2\pi),
   \qquad
   T_m=t_m-t_{m-1}.
   \]

7. 扫描无量纲参数并分类为：无模式、直列、十字对生、三轮生、螺旋、混合/不稳定。

### 12.2 推荐的验证顺序

先验证数学，再验证生物现象：

1. 关闭源汇后，检查 \(\sum_iN_i^A\) 的相对漂移是否接近求解器误差；
2. 在规则一维环上复现 L14、L16 和 L22；
3. 网格加密后检查物理峰间距而非“细胞数峰间距”是否收敛；
4. 旋转细胞网格，确认叶序统计不依赖网格方向；
5. 重复随机种子，报告发散角和 plastochron 的分布；
6. 再做 pin1/NPA、外源 auxin、原基消融、中央降解和中央移除模拟。

### 12.3 可观测量

- 生长素峰的数目、幅值、宽度和间距；
- PIN1 极化方向与极性反转；
- 原基方位角、发散角、plastochron 和径向比；
- 中央区、I-1 和原基的生长素量；
- 从外围到中央/I-1/原基的通量路径；
- 对参数扰动和几何噪声的鲁棒性。

---

## 13. 模型的可检验预测

1. 降低 PIN1 总量或主动运输 \(T\)

   \(TP\) 下降，先使峰间距增大，随后在 L19 处失去模式；预测原基减少，最终出现无器官的近均匀/环状生长素分布。

2. 增强被动扩散

   \(D\) 上升使 \(q_*\) 下降、峰间距增大；过强扩散抹平全部峰。

3. 提高极化弹性 \(\varepsilon_F\) 或降低内吞比 \(\rho\)

   L15a 预测线性极化增益提高，或因 \(\rho\) 下降而使
   \(P_{\mathrm{mem},0}\) 增加，通常会缩短峰间距并增加每圈候选峰。
   对 Hill 函数，增大 \(n\) 只有在 \(A_0\) 位于 \(K_F\) 附近且
   \(F_0\) 较小时才通常提高 \(\varepsilon_F\)；远离转折区时反而可能降低
   局部斜率。过强极化还会使结果对细胞几何和噪声更敏感。

4. 增大中央区/发生环半径

   \(\Pi_C\) 增大，更容易由单峰依次出现转向成对或多峰同时出现，即螺旋向轮生转变。

5. 增强原基向内部排出 \(\eta_s\)

   耗竭区加深，候选峰之间的时间分离增强；中等强度有利于规则螺旋，过强会延长 plastochron 或抑制新原基。

6. 中央特异降解与中央消融

   前者应消除 I-1，后者短期内可保留 I-1。若实验结果相同，则 1002 的有限容量储库机制需要修正。

7. 去掉持久原基极化线索 \(A_q\)

   若螺旋仍稳定，说明真实 auxin 峰和向内部汇已足以维持 PIN；若原基形成后 PIN 很快改向并使序列崩溃，则需要独立的发育/力学线索。

---

## 14. 局限与不能过度声称的部分

1. 三篇论文和统一模型都把叶序主要压缩到 L1 二维表面；真实三维下层运输和维管形成只被原基汇代表。
2. 邻胞生长素如何被本细胞感知并控制 PIN 膜化，仍是核心闭合假设。
3. U11 的持久原基线索是明确标注的现象学项，不应被误当作已识别分子。
4. 黄金角不是线性稳定性直接推出的唯一解；其出现依赖增长、阈值、汇和历史原基共同选择。
5. Smith 的指数极化、Barbier de Reuille 的容量尺度和 Jönsson 的中央区 \(X\) 场都含较强经验性；参数不宜跨论文直接等值搬用。
6. 1002 的 PIN 网络固定，因此它验证的是“观察到的极性能否支持所推断的生长素分布”，不是因果地产生极性。
7. Jönsson 的一维阈值只适用于均匀周期链附近；真实不规则、生长图上的阈值应由完整 Jacobian 或数值谱重新计算。
8. 叶序分类必须报告多随机种子、角度分布和持续时间；短暂的螺旋样快照不足以证明稳定螺旋。

---

## 15. 最终模型的最简表达

若只保留实现所需的核心，统一模型可压缩为

\[
\boxed{
\begin{aligned}
\dot N_i^A
={}&S_i(A_i,s_i)-\mu_AN_i^A-R_i^{\mathrm{prim}}
-\sum_jJ_{ij},\\
J_{ij}
={}&D_{ij}(A_i-A_j)
+T[P_{ij}u(A_i)v(A_j)-P_{ji}u(A_j)v(A_i)],\\
G_i^P
={}&\frac{\rho_{P0}+\rho_PA_i}{1+\kappa_PP_i^T},\qquad
P_i^T=P_i^c+\sum_jP_{ij},\\
\dot P_{ij}
={}&k_{\mathrm{on}}l_{ij}F(A_j+A_qs_j)P_i^c
-(k_{\mathrm{off}}+\mu_P)P_{ij},\\
\dot P_i^c
={}&G_i^P-\mu_PP_i^c
-\sum_j\!\left[
k_{\mathrm{on}}l_{ij}F(A_j+A_qs_j)P_i^c-k_{\mathrm{off}}P_{ij}
\right],\\
\text{new primordium}
\Longleftrightarrow{}&
\chi_P=1,\ A_i\text{ 为局部极大且 }A_i\ge A_{\mathrm{on}}.
\end{aligned}
}
\tag{M}
\]

这组方程的逻辑是：

\[
\boxed{
\text{运输失稳产生峰}
\;\to\;
\text{外周峰越阈值形成原基}
\;\to\;
\text{原基向内部排出生长素并制造耗竭区}
\;\to\;
\text{生长把旧原基带走}
\;\to\;
\text{新峰在剩余最大空隙中出现}.
}
\]

这也是三篇 2006 年论文能够被统一的最简数学陈述。

## 自测问题

1. 为什么 \(D/(TP)<1/2\) 只说明均匀态会形成空间峰，却不能单独保证得到稳定黄金角螺旋？
2. 为什么中央区“强降解”和“物理移除”对 I-1 的预测相反？
3. 若实验中减弱 PIN1 后观察到峰间距增大但尚未完全消失，模型中是哪一个色散关系参数在变化？
