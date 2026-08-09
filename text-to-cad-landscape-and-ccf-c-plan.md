# Text-to-CAD 调研与 CCF C 投稿方案

更新时间：2026-08-08

## 结论摘要

当前项目不算过时，但属于第一代 agentic、code-first text-to-CAD 架构：大模型生成参数化 Python 代码，本地 CAD 内核执行并反馈错误、几何指标和渲染图。

对于本地、可审计、可编辑的单零件建模，这仍然是合理路线。若以研究前沿或工业级 CAD 为目标，现有实现还缺少结构化设计规格、主动澄清、特征级修复、工程验收测试、多视图评审、装配表示和专门训练。

如果目标是发表 CCF C 级别会议，建议不要尝试把所有前沿方向都堆进一个系统。最可行的路线是将当前项目扩展为：

> 用结构化 DesignSpec 同时驱动 CAD 代码生成、可执行验收测试与特征级局部修复的可靠 text-to-parametric-CAD 框架。

## 一、当前 text-to-CAD 的技术路线

截至 2026-08-08，公开研究和实践大致汇聚为以下流程：

```text
自然语言 / 图片
    ↓
需求解析与主动澄清
    ↓
结构化 Design Spec / CAD-IR / 装配图
    ↓
检索已有零件、技能和 CAD API
    ↓
分层规划特征树与参数
    ↓
生成 CAD 代码或原生 B-Rep
    ↓
CAD 内核执行
    ↓
几何测试 + 多视图视觉检查 + 工程规则检查
    ↓
局部修复 / 重新规划
    ↓
人工确认与导出
```

当前项目已经实现了其中的核心闭环：

```text
LLM 生成 build123d 代码
    ↓
本地执行
    ↓
检查 solid_count、体积、包围盒与 is_valid
    ↓
生成 STL 和渲染图
    ↓
将错误与渲染反馈给模型
    ↓
模型继续修改代码
```

这与近期研究中的 Generate -> Execute -> Critique -> Rewrite 模式一致。因此，代码优先和执行反馈本身不是过时的路线。

## 二、当前项目与前沿方法的差距

| 维度 | 当前项目 | 近期方向 |
| --- | --- | --- |
| 中间表示 | 直接生成 `model.py` | DesignSpec、CAD-IR、特征图、装配图 |
| 澄清 | Prompt 驱动的 `question` 工具 | 独立的主动需求审计和澄清阶段 |
| 生成 | 通用 LLM + 文档 prompt | CAD 专门 SFT、RL、primitive-aware tokenization |
| 反馈 | 内核指标 + 单张渲染图 | 可执行 CADTests、多视图、独立 VLM Judge |
| 修复 | 基于源码的整体写入或替换 | 失败定位到特征后的局部 patch |
| 记忆 | 简单经验库和 playbook | RAG、相似零件检索、专家工艺技能 |
| 范围 | 单零件为主 | 多零件、端口、mates、装配约束 |
| 输出 | build123d 后导出 STEP/STL | 代码、FeatureScript、原生 B-Rep、STEP、NURBS 的混合路线 |
| 工程验证 | 有效实体与基础几何指标 | 功能、可制造性、可装配性、物理和公差检查 |

## 三、近期研究趋势

### 1. 显式中间表示

较新的方法不再直接从文字跳到一大段 CAD 代码，而是先生成结构化规格或特征依赖图。例如：

```json
{
  "parameters": {
    "plate_length": 60,
    "plate_width": 30,
    "plate_thickness": 4
  },
  "features": [
    {
      "id": "mounting_holes",
      "type": "through_hole",
      "diameter": 3,
      "positions": "four symmetric corners"
    }
  ],
  "constraints": [
    {"type": "edge_offset", "value": 5},
    {"type": "symmetry", "axis": "x"}
  ]
}
```

代表工作：

- [HierCAD: Hierarchical Text-to-CAD Design via Structure Alignment and Parameter Grounding](https://arxiv.org/abs/2607.11339)：层次结构推理与参数 grounding。
- [ArtisanCAD: An Industrial-Level CAD Agent with Expert-Grounded Knowledge Distillation](https://arxiv.org/abs/2607.05750)：CAD-IR 包含参数、操作、依赖、工具绑定和验证规则。
- [AssemCAD: Production-Ready CAD Assembly Generation from Natural Language](https://arxiv.org/abs/2607.05123)：从零件、端口、mate 和工程公理开始建模装配。

### 2. 主动澄清

用户需求往往缺尺寸、互相矛盾或只描述高层意图。较新的方法将“是否提问”从提示词习惯变成独立策略：先审核需求，再只问会阻塞建模的问题。

- [ProCAD: Clarify Before You Draw](https://arxiv.org/abs/2602.03045)

### 3. 训练与优化

研究型 text-to-CAD 系统开始使用大规模文本-CAD 数据、监督微调和几何奖励优化：

- [Text-to-CadQuery](https://arxiv.org/abs/2505.06507)：直接从文本生成 CadQuery。
- [CAD-Coder](https://arxiv.org/abs/2505.19713)：CadQuery 代码生成、Chain-of-Thought 与几何奖励。
- [ReCAD](https://arxiv.org/abs/2512.06328)：用强化学习提升多模态参数化 CAD 生成。
- [CAD-Tokenizer](https://arxiv.org/abs/2509.21150)：面向 CAD primitive 的 tokenization。
- [ToolCAD](https://arxiv.org/abs/2604.07960)：面向工具调用 CAD Agent 的在线课程强化学习。

### 4. 闭环执行、批评与修复

近期工作强调“执行后反馈”而不是 one-shot 代码生成：

- [CADSmith](https://arxiv.org/abs/2603.26512)：几何验证与独立视觉模型 Judge 的双重反馈。
- [RA-CAD](https://arxiv.org/abs/2608.05714)：将执行后的 critique 作为可学习的策略动作。
- [CADFusion](https://arxiv.org/abs/2501.19054)：结合序列监督和视觉反馈。

### 5. 从可执行转向工程可用

仅仅生成合法实体不代表满足工程需求。新 benchmark 和评估方法开始要求：

```text
代码可执行
→ 几何有效
→ 尺寸与拓扑正确
→ 设计意图满足
→ 可制造
→ 可装配
→ 功能合理
```

代表工作：

- [CADTests / CADTestBench](https://arxiv.org/abs/2605.07807)：将自然语言要求转化为可执行几何和拓扑测试。
- [MUSE](https://arxiv.org/abs/2605.28579)：评估可制造性、功能性和可装配性。
- [Text2CAD-Bench](https://arxiv.org/abs/2605.18430)：覆盖从基本几何到复杂拓扑和实际应用的多级 benchmark。

### 6. 表示形式的分化

当前主要存在三条路线：

| 表示 | 优点 | 局限 |
| --- | --- | --- |
| CAD 代码 | 可读、易调试、易版本控制，适合 Agent | 依赖具体 CAD 后端 |
| 操作序列 / FeatureScript | 更接近原生特征树 | 数据和工具链门槛较高 |
| STEP / B-Rep / NURBS | 面向制造交换，几何表达强 | 结构复杂，生成和局部编辑更难 |

相关探索包括：

- [STEP-LLM](https://arxiv.org/abs/2601.12641)：自然语言到 STEP。
- [NURBGen](https://arxiv.org/abs/2511.06194)：生成 NURBS 表示。
- [DreamCAD](https://arxiv.org/abs/2603.05607)：多模态可编辑 B-Rep 生成。
- [CADFS](https://arxiv.org/abs/2605.01925)：以 FeatureScript 和大规模 CAD 数据扩展建模操作空间。

直接生成 B-Rep 不必然优于代码生成。对于本地、可审计、可修改的 CAD Agent，代码优先仍是很有价值的工程选择。

### 7. 商业和开源实践方向

实际系统越来越重视“可编辑的源码或原生特征树”而不是一次性网格。Zoo 的 [KCL 文档](https://zoo.dev/docs/kcl) 体现了这一趋势：KCL 是模型的 source of truth，模型可作为普通文本编辑、参数化和版本控制。

另一个明显趋势是通过 MCP、脚本或原生 API 驱动已有 CAD 软件，而不是重新造一个 CAD 内核。这有利于保留现有企业的特征树、装配和制造工作流。

## 四、对当前项目的判断

### 仍然正确的部分

- 代码优先的参数化建模。
- build123d / OpenCASCADE 的本地真实执行。
- 沙箱化运行不可信模型代码。
- 构建后检查实体有效性、体积和尺寸。
- 版本、回滚和用户固定参数/特征。
- 浏览器成功加载 STL 后才视为完成。
- 人工审查和最终导出分离。

### 优先补齐的部分

1. 在代码生成前增加结构化 `DesignSpec`。
2. 将主动澄清变成明确阶段，而非仅依赖 prompt。
3. 从用户需求自动生成 CAD 验收测试。
4. 用特征 ID 将失败测试映射到源码区域。
5. 增加多视图与截面视图，视觉模型只做语义补充。
6. 检索相似 CAD、API 示例和已验证技能。
7. 后续再考虑装配、制造性和原生 B-Rep。

## 五、面向 CCF C 的论文方案

### 推荐定位

不必追求训练新的 CAD 基础模型，也不需要直接生成 STEP/B-Rep 或完整装配系统。较务实的论文定位是：

> 面向可靠参数化建模的自然语言 CAD 智能体框架。

推荐题目：

> **ContractCAD: Executable Specification and Localized Repair for Reliable Text-to-Parametric CAD**

中文可表述为：

> 面向可靠参数化建模的可执行需求约束自然语言 CAD 智能体。

### 问题定义

现有 text-to-CAD 系统即使生成了可执行代码，也可能因为需求不完整、参数关系隐含、反馈过于粗糙而得到“合法但不符合意图”的模型。发生错误后，模型往往需要重写整个源码，修复效率低且容易引入新错误。

### 核心主张

> 让 DesignSpec 同时约束 CAD 代码生成和可执行测试生成，并将失败测试映射到具体 CAD 特征，可以提高设计意图满足率，同时减少修复轮数和代码重写量。

这应是论文唯一的主贡献。RAG、VLM、版本管理和主动澄清都是支撑该主张的系统组件，而不是平行的创新点。

## 六、推荐方法：Specification-Test 双向契约

```text
自然语言 / 参考图片
        ↓
主动澄清关键尺寸
        ↓
生成结构化 DesignSpec
        ↓
生成特征图与 build123d 程序
        ↓
由同一份 DesignSpec 生成 CADTests
        ↓
CAD 内核执行
        ↓
几何测试 + 多视图视觉检查
        ↓
定位到具体特征
        ↓
局部 patch 修复
```

### 1. DesignSpec

DesignSpec 记录：

- 参数和单位。
- 主体几何。
- 特征类型，例如孔、槽、圆角、阵列。
- 几何关系，例如对称、同轴、等距、平行。
- 用户固定的约束。
- 最终验收条件。

### 2. 主动澄清

在生成代码之前审计规格：

```text
检查缺失尺寸
检查冲突约束
判断是否可建模
只询问真正阻塞的问题
```

用户回答被写回 DesignSpec，而不是只作为一段对话文本。

### 3. 代码和测试协同生成

同一份规格同时生成：

```text
model.py
test_model.py
```

例如用户要求“四个对称 M3 通孔，距边 5 mm”，测试可以检查：

```text
孔数量是否为 4
孔径是否为 3 mm
孔是否贯穿
孔是否关于指定轴对称
孔中心到边缘距离是否为 5 mm
```

### 4. 特征级局部修复

将每个 CAD 特征表示为：

```text
feature_id
参数
父特征
负责的测试
源码区域
```

例如：

```text
base_plate
└── mounting_holes
    └── edge_fillet
```

如果失败信息为：

```text
mounting_holes.hole_3.position_failed
```

修复器优先修改 `mounting_holes` 对应源码区域，而不是重写整个 `model.py`。

### 5. RAG 和视觉评审的角色

RAG 负责检索 build123d API、相似零件、已验证代码模板和历史修复经验。

视觉模型只负责整体形态、参考图相似度和明显缺失特征；精确尺寸、拓扑和制造规则仍由程序化 CADTests 负责。

## 七、当前项目可直接复用的能力

当前仓库已有：

- `question` 工具。
- `model.py` 生成和编辑流程。
- `cad_build_and_verify`。
- build123d 沙箱执行。
- `render.png` 与 STL 预览。
- revision history。
- feature markers 与 constraints。
- quality store。

最小新增内容应为：

1. `DesignSpec` schema。
2. 规格审计和主动澄清模块。
3. 自动 CADTests 生成与运行器。
4. feature-to-test 映射。
5. 局部 patch repair 策略。
6. 用于实验的统一日志和统计指标。

## 八、不建议第一篇论文同时做的内容

以下方向可作为 future work，不应同时作为第一篇论文的主要贡献：

- 直接生成 STEP/B-Rep。
- 多零件装配、端口和 mate。
- 物理仿真或结构优化。
- SFT、RL、GRPO 同时训练。
- 多个并行 Agent。
- 打印、CNC、注塑等全部制造验证。
- 同时支持 build123d、CadQuery、KCL、FeatureScript 等多个后端。

避免以下叙事：

```text
主动澄清
+ RAG
+ 多 Agent
+ VLM
+ RL
+ 装配
+ STEP
+ 仿真
```

这会让论文显得是工程拼装，且难以通过消融说明具体收益来自哪里。

## 九、最小实验设计

### 数据集和任务

可以构造 60 到 120 个可复现任务，按难度划分为：

- 基本体。
- 孔、槽、阵列等特征零件。
- 有歧义、需要用户澄清的任务。
- 带参考图片的任务。
- 后续文本编辑任务。

也可以结合公开数据集或 benchmark，但必须确保最终评价可复现且需求可执行。

### 比较基线

| 方法 | 说明 |
| --- | --- |
| One-shot LLM | 一次生成 CAD 代码，不修复 |
| Code + execution repair | 生成代码并利用 CAD 执行错误修复 |
| Code + visual feedback | 加入渲染图或视觉评审 |
| Proposed | DesignSpec、CADTests 与局部修复 |

### 核心指标

- 代码执行成功率。
- 有效实体成功率。
- 尺寸误差。
- 特征满足率。
- DesignSpec / design-intent pass rate。
- 平均修复轮数。
- 平均 Token 消耗。
- 用户澄清次数。
- 源码改动行数或局部 patch 比例。

### 必做消融

```text
去掉 DesignSpec
去掉自动 CADTests
去掉 feature-level localization
去掉视觉评审
```

实验应主要验证两项主张：

1. DesignSpec 能减少歧义并提高需求满足率。
2. CADTests 与局部修复能降低失败重试和代码改动量。

## 十、发表可行性判断

如果只有：

```text
Flask + LLM API + build123d + 网页界面
```

它更像工程项目，缺少论文创新。

如果形成：

```text
明确的问题定义
+ DesignSpec 表示
+ 自动验收测试
+ 闭环修复
+ 基线对比
+ 消融实验
```

那么作为 CCF C 级别的应用型或系统型论文，存在现实可行性。

不需要宣称“提出了新的 CAD 大模型”。更合适的表述是：

> 提出一种面向可靠参数化 CAD 生成的需求约束智能体框架，并通过可执行几何测试和特征级修复实现迭代生成。

## 十一、最终建议

整篇论文应只围绕两条 claim：

**Claim 1：** 结构化 DesignSpec 能减少自然语言歧义，提高 CAD 需求满足率。

**Claim 2：** 由 DesignSpec 自动生成的 CADTests，结合特征级局部修复，能减少失败重试次数和代码修改量。

一句话总结：

> 对 CCF C，不必追赶所有最新技术；将当前项目发展为“DesignSpec + CAD 验收测试 + Agent 闭环局部修复”的完整方法，并通过可靠基线和消融证明它有效，是最务实且最有论文形状的路线。

## 资料说明

本文调研主要基于截至 2026-08-08 的公开 arXiv 论文、Zoo/KCL 文档和开源项目资料。部分近期论文属于预印本，代表研究趋势，不等同于已经成熟的商业产品；具体投稿前还应核对目标会议当年的征稿范围与最新 CCF 推荐目录。
