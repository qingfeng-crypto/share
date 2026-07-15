# MATLAB 避坑指南（补偿 AI 的 MATLAB 天生弱势）

本文件提取自 MathWorks 官方帮助中心的广度探索，聚焦 **AI 写 MATLAB 最容易写错/忽略**的点。目的：把 MATLAB 的"脾气"固化成条款，避免凭旧记忆写错。

## 官方文档查阅（拿不准就查）

- **基础入口**：英文权威 `https://www.mathworks.com/help/`；中文站 `https://ww2.mathworks.cn/help/` 为机器翻译，**精确语法/选项名以英文版为准**。
- **规则**：① 拿不准 MATLAB 语法、选项名、版本行为时，**抓取具体函数参考页**（如 `help/optim/ug/intlinprog.html`），不要猜；② 不要抓首页；③ 中文页是机器翻译，关键语法对照英文版。
- **版本基线**：本机 MATLAB 为 **R2024b**，本文所有 MATLAB 写法均按 R2024b 可用能力给出，不依赖 R2025a 及以后版本。

---

## 一、通用铁律

- **约束方向统一为 ≤ / ==**：`linprog` / `intlinprog` 只接受 `A*x <= b`（`≥` 须整体乘 `-1` 翻转）；`fmincon` 非线性约束 `c<=0, ceq==0`。
- **旧算法名已删除**：`linprog` / `intlinprog` 默认 HiGHS 系；指定 `'active-set'` / `'simplex'` / `'dual-simplex-legacy'` 会报错，只能用 `'dual-simplex-highs'` / `'interior-point'` / `'interior-point-legacy'`。
- **随机数可复现**：`kmeans`、PCA 重采样、任何随机初始化前必须 `rng(seed)`，否则结果不可复现。
- **输出是对象，不是裸矩阵**：`fitlm` → `LinearModel`；旧式 ODE → `sol` 结构体（`sol.x` 是时间，**不是 `sol.t`**）；新式 `ode` 对象 → `ODEResults`（`S.Time` / `S.Solution`）；`pdepe` → 3-D 数组 `sol(:,:,k)`。
- **表 vs 矩阵语义相反**（`fitlm`）：表输入"末列即响应"且分类变量自动识别；矩阵输入须显式 `'CategoricalVars'`，否则类别数字被当连续量。
- **版本敏感 API**：区分"经典函数式"与"新对象式"（R2024b 已支持 `ode` 对象工作流），不要混用取值方式。

---

## 二、优化（linprog / intlinprog / fmincon）

- **linprog**：`A*x<=b` 是唯一接受形式；返回的 `lambda` 是影子价格**相反数**，作灵敏度须取负；区间约束用 cell `{bl,b}`。
- **intlinprog（最重要）**：整数变量解**不是精确整数**（落在 `ConstraintTolerance` 内），必须 `x(intcon)=round(x(intcon))` 并复检 `A*x-b` / `Aeq*x-beq` / 边界可行性；默认 `"highs"` 算法；`exitflag==3` 仅相对可行、解可能大不可行，不能当成功；二进制用 `lb=0,ub=1`；`f=[]` 表示只求可行点。
- **求解器输出不可混用**：R2024b 中 `linprog` 可返回 `lambda`，而 `intlinprog` 只返回 `[x,fval,exitflag,output]`，不支持第五个输出参数。不要写 `[x,fval,exitflag,output,lambda] = intlinprog(...)`；整数规划的影子价格不能直接从 `intlinprog` 获取。若需敏感性分析，应另行求解连续 LP 松弛，并明确标注结论来自 LP 松弛而非整数规划。
- **fmincon**：非线性约束函数必须返回 `[c, ceq]`（`c<=0, ceq==0`，无等式时 `ceq=[]`）；`x0` 必填且其形状决定传入 `fun`/`nonlcon` 的 `x` 形状；用符号梯度须 `SpecifyObjectiveGradient=true` 且 `fun` 返回第二输出梯度；无非线性约束也必须显式传 `nonlcon=[]`；边界不一致直接报错并返回 `x0`。

### MATLAB 求解代码运行前质检

在调用 `linprog`、`intlinprog` 或其他求解器前，必须完成以下检查：

- **语法检查**：代码使用半角 ASCII 标点；括号、方括号、花括号和引号成对；矩阵行之间使用分号；不混用 Python 的 `#`、`**`、列表或字典语法。
- **API 检查**：核对当前函数的输入输出签名，不凭 `linprog`、`intlinprog` 或其他求解器的相似名称推断接口；尤其核对输出参数数量。
- **模型检查**：核对 `f`、`A`、`b`、`Aeq`、`beq`、`lb`、`ub` 的维度；确认所有不等式均已整理为 `A*x <= b`；确认 `intcon` 索引与变量数量一致。
- **运行后检查**：先检查 `exitflag`，再检查 `A*x-b`、`Aeq*x-beq`、上下界和整数性，最后才报告目标函数与资源利用率。求解器报错或未成功时，不得把前面打印的利润、方案或资源信息当作最终结果。

---

## 三、符号数学（solve / dsolve / matlabFunction）

- **solve**：多变量必须 `solve(eqns, var1, var2)` **显式指定顺序**，否则解会错位赋给输出变量；方程组返回结构体 `S.x` 取字段；求不出符号解时会自动转 `vpasolve` 且非多项式只给一个数值解（漏解风险）；生成参数不进工作区，须 `ReturnConditions=true` 捕获；`IgnoreAnalyticConstraints` 默认 `false`（严格，与 dsolve 相反）。
- **dsolve**：方程组返回结构体、多输出按**因变量字母序**赋值（非书写顺序）；`IgnoreAnalyticConstraints` 默认 `true`（会套用非全局成立的简化，结果须验证）；导数初值须先 `Dy=diff(y,t)` 再写 `Dy(0)==1`；无显式解转 `ode45` 或 `Implicit=true`。
- **matlabFunction**：`[a,b]`（向量）当一个输出，`a,b`（逗号分隔）才产生两个输出；喂 `fmincon` 须 `'Vars',{x}` 把符号向量映射为单一输入向量；`'Outputs'` / `'Optimize'` 仅在 `'File'` 指定时有效。

---

## 四、微分方程（ode45 / ode15s / pdepe）

- **ode45 / ode15s**：先判刚性——出现"求解极慢/步数爆炸"立即改用 `ode15s`；`odefun` 必须 `(t,y)` 两输入并返回**列向量**，`y0` 为列向量且长度匹配；解结构体用 `sol.x`(时间) / `sol.y`(解)，任意点取值用 `deval(sol, x)`；`tspan` 多元素不控制步长。
- **pdepe**：先化标准型 `c·∂u/∂t = x^(-m)·∂(x^m·f)/∂x + s`，`pdefun` 返回 `[c,f,s]`；边界写 `p + q·f = 0`（`m>0` 时左边界被忽略，求解器自动对称）；`xmesh` / `tspan` 严格递增且长度 ≥3，精度由 `xmesh` 密度主导；取解 `u = sol(:,:,k)`；仅支持 `RelTol` / `AbsTol` / `NormControl` / `InitialStep` / `MaxStep` 等受支持选项（其余 `odeset` 选项会被忽略）。

---

## 五、统计（fitlm / kmeans / pca）

- **fitlm**：优先**表 + 公式**写法显式指定响应变量，避免"末列即响应"默认陷阱；矩阵输入必须显式 `'CategoricalVars'`；结果是 `LinearModel` 对象，用 `mdl.Coefficients` 读系数、`predict(mdl, newdata)` 预测；去截距用公式 `-1`。
- **kmeans**：调用前必须 `rng(seed)` 可复现；设 `'Replicates',5`（或更多）避局部极小；含 NaN 的行被删除且 `idx` 对应位为 NaN，聚类前应插补/清洗；新数据分类用 `pdist2(C, Xtest, 'euclidean', 'Smallest', 1)`，不要重跑 kmeans。
- **pca**：对测试/新数据必须用训练得到的 `coeff` 和 `mu`：`(Xnew - mu) * coeff(:,1:k)`，**禁止重跑 `pca`**；`coeff` 是载荷（列=主成分，方差降序），`score = Xc * coeff`；默认已中心化，`score*coeff'` 重构的是中心化数据（要加回 `mu`）；用 `cumsum(explained)` 决定保留成分数。

---

## 六、图形与专用可视化（含已固化三大痛点）

> 护栏前提：出图默认 **Python（matplotlib）**；MATLAB 仅用于极个别专用图（控制系统频域、Signal Processing、需 `.fig` 等）。以下用于给 MATLAB 专用图兜底。

- **导出**：一律 `exportgraphics` 而非 `saveas`；显式 `Resolution`（≥300）或 `ContentType,'vector'`；**不对 JPEG/PNG 传 `ContentType,'vector'`（无效）**；透明背景需 `BackgroundColor,'none'` 且配 `vector`；截整窗（含 App 控件）用 `exportapp`。
- **savefig vs exportgraphics**：`savefig` 存可重开的 `.fig` 工程文件；`exportgraphics` 出成品图。交付论文图用后者。跨机/含中文 `.fig` 用 `"-v7.3"`；R2024b 起 `.fig` 默认紧凑、不兼容 R2014a 前。
- **figure 初始化**：`figure('Color','white','NumberTitle','off')` 去灰底与 "Figure N:" 前缀。
- **colormap**：默认 `parula` / `turbo`，**禁止 `jet`**；单坐标区用 `colormap(ax, map)`；控制颜色范围用 `clim`（**非旧 `caxis`**，R2022a 前才叫 caxis）。
- **bode（控制系统）**：需数值用 `[mag,phase,wout]=bode(sys)`；`mag` 是 3-D 数组，SISO 取 `mag(1,1,k)`；`mag` 是幅值非 dB，须 `20*log10(mag)`；**R2024b 起 `gca` 对 bode 图返回 chart 对象而非 axes**，改外观用 `bodeplot` / `getoptions` / `setoptions`；多行标题用含 `newline` 的单个字符串。
- **fft（频谱）**：必须按"除以 `L` → 取单边 → 正频乘 2（跳过 DC 与奈奎斯特）→ 频率轴 `Fs/L`"四步，禁止裸画 `abs(fft(X))`；相位先阈值清零再 `unwrap(angle(...))`；补零 `n=2^nextpow2(L)` 提分辨率。
- **三大痛点（已固化）**：① `latex` 解释器拒 Unicode/中文，中文标注用默认 `tex` 或 `'none'`；② 去上/右边框 `box off` + 设 `LineWidth`，`grid off`；③ 字号偏小，出图前统一 `set(groot,'DefaultAxesFontSize',11)`。

### 二维线性规划可行域绘图防错

`linprog` 求解成功不代表后续可行域绘图代码正确。二维可行域通常需要枚举约束边界交点，必须先固定矩阵形状约定：约束矩阵 `A` 为 `m×2`，约束向量 `b` 为 `m×1`，单个交点用于矩阵运算时为 `2×1` 列向量，顶点集合用于存储和绘图时为 `N×2` 行矩阵。

- **`contour` / `clabel` 输出不可混用**：同时接收等高线矩阵和句柄；`X`、`Y`、`Z` 必须具有相同二维尺寸；只有在等高线矩阵有效且为标准两行格式时才调用 `clabel`。
  ```matlab
  [X, Y] = meshgrid(x1Grid, x2Grid);
  assert(isequal(size(X), size(Y), size(Z)), ...
      'contour 的 X、Y、Z 必须具有相同的二维尺寸');
  [contourMatrix, contourHandle] = contour(X, Y, Z, levels);
  if ~isempty(contourMatrix) && size(contourMatrix, 1) == 2
      clabel(contourMatrix, contourHandle);
  end
  ```
- **边界交点右端保持列向量**：解 `M*x=rhs` 时，`M` 为 `2×2`、`rhs` 必须为 `2×1`；不要在 `[rhs1; rhs2]` 后追加转置符号，否则会变成 `1×2` 并触发左除维度错误。平行或重合边界先检查 `rank(M)` 或数值秩。
- **顶点集合统一为 `N×2`**：初始化使用 `vertices = zeros(0, 2)`；新增顶点使用 `vertices(end+1,:) = point(:).'`；禁止混合 `1×2` 和 `2×1` 顶点后直接纵向拼接，否则会触发 `vertcat` 维度错误。
- **矩阵乘法统一使用列向量**：从顶点矩阵取点后写 `v = vertices(k,:).'`，再用 `A*v <= b + tol` 检查可行性；不要根据变量当前形状交替使用 `A*v` 和 `A*v'`。
- **绘图失败与求解失败分开处理**：若 `exitflag > 0` 而 `plot_feasible_region` 报错，应保留并报告 LP 求解结果，只修复绘图函数；不得把可视化异常误判为模型或 `linprog` 求解失败。
