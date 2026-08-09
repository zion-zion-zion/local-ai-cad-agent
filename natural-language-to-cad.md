# 自然语言如何生成 CAD

这个项目的核心可以理解为一条完整的流水线：

> 大模型负责把自然语言“翻译”为参数化 `build123d` 程序；本地 CAD 内核负责判断这个程序是否真的生成了有效实体；模型再根据构建结果和渲染图进行修正。

它不是一个“文本直接生成网格”的系统，也不是一个专门训练过的 CAD 模型。真正的建模过程是一个带工具调用的代码生成与验证循环。

## 一次建模任务的主循环

以用户输入：

> 创建一个 60 × 30 × 4 mm 的安装板，四角各有一个 M3 通孔，孔中心距离边缘 5 mm。

为例，内部大致会经过下面这些阶段：

```text
自然语言请求
    ↓
模型理解设计意图
    ↓
决定参数、坐标系和建模操作
    ↓
生成 model.py
    ↓
静态检查 model.py
    ↓
执行 build123d
    ↓
检查实体有效性、体积和尺寸
    ↓
生成 preview.stl 和 render.png
    ↓
模型查看指标和渲染结果
    ↓
必要时修改 model.py
    ↓
再次构建
```

整个智能体循环在 [AgentRunner._run()](/mnt/data_44T/ytk/local-ai-cad-agent/agent/core.py:250) 中实现。

## 1. 模型如何理解自然语言

模型收到的上下文不只是用户的一句话，还包括一个 CAD 系统提示词和 build123d 使用手册。

系统提示词主要规定：

- 所有尺寸使用毫米。
- 所有参数要写在 `model.py` 顶部。
- 参数必须有类型标注。
- 最终形状必须叫 `result`。
- 修改代码后必须构建验证。
- 不能凭经验猜 build123d 的 API 参数。
- 布尔运算、倒角、圆角之后不能盲目复用旧的边索引。
- 只有用户明确需要时才询问尺寸。
- 最终导出由 UI 的 Finalize 操作完成。

这些规则定义在 [prompt.py](/mnt/data_44T/ytk/local-ai-cad-agent/agent/prompt.py:95)，具体 API 和 build123d 0.11.1 的用法在 [build123d_cli_playbook.md](/mnt/data_44T/ytk/local-ai-cad-agent/agent/resources/build123d_cli_playbook.md:1)。

模型需要自行完成几项推理：

1. 这是什么类型的零件？
2. 哪些尺寸是明确给出的？
3. 哪些尺寸必须询问？
4. 应该选择哪些几何原语？
5. 应该使用 Builder 模式还是 Algebra 模式？
6. 哪些特征应该做成独立参数？
7. 如何放置孔、槽、倒角、圆角或重复阵列？
8. 最后生成的实体是否符合原始意图？

这里没有一个独立的“自然语言尺寸解析器”。尺寸和设计意图主要由 LLM 推理完成，然后由 CAD 执行结果进行验证。

## 2. 信息不足时，模型会先提问

模型不是遇到任何模糊点都暂停，而是只询问会阻止建模的问题。

例如：

> 创建一个带孔的安装支架。

模型可能会认为孔直径、板厚或孔位置是关键未知量，于是调用 `question` 工具：

```json
{
  "questions": [
    {
      "id": "hole_diameter",
      "question": "孔径应该是多少？",
      "input_type": "number"
    }
  ]
}
```

系统会暂停当前任务，把问题保存到：

```text
<project>/.agent_state.json
```

用户回答 `6 mm` 后，系统会将它重新组织成模型上下文：

```text
User answers:
- 孔径应该是多少？: 6 mm
```

然后重新启动模型循环。

问题类型包括普通文本、数字、单选和多选。数字问题支持 `6`、`6 mm`、`0.25 inch` 等形式。相关实现位于 [question_tool.py](/mnt/data_44T/ytk/local-ai-cad-agent/agent/tools/question_tool.py:12) 和 [question_validator.py](/mnt/data_44T/ytk/local-ai-cad-agent/agent/tools/question_validator.py:1)。

## 3. 模型把设计转成参数化代码

对于上面的安装板，模型可能生成类似这样的代码：

```python
from build123d import Align, Box, Cylinder, Pos

# Parameters, all dimensions in mm
length: float = 60.0
width: float = 30.0
thickness: float = 4.0
hole_diameter: float = 3.0
edge_offset: float = 5.0

base = Box(
    length,
    width,
    thickness,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)

result = base

hole_positions = [
    (-length / 2 + edge_offset, -width / 2 + edge_offset),
    ( length / 2 - edge_offset, -width / 2 + edge_offset),
    (-length / 2 + edge_offset,  width / 2 - edge_offset),
    ( length / 2 - edge_offset,  width / 2 - edge_offset),
]

for x, y in hole_positions:
    cutter = Pos(x, y, 0) * Cylinder(
        hole_diameter / 2,
        thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    result = result - cutter
```

这里有几个关键特征：

- 用户说的尺寸被转换成明确参数。
- 参数集中在源码顶部。
- 孔位置由参数计算，而不是写死最终坐标。
- 修改 `length` 或 `edge_offset` 可以自动改变整个模型。
- 最终实体被赋值给 `result`。

生成的不是一次性的三角网格，而是一个可以继续修改的参数化程序。

模型可以选择两种 build123d 风格。

### Algebra 模式

适合简单布尔运算：

```python
base = Box(...)
hole = Cylinder(...)
result = base - hole
```

### Builder 模式

适合包含多个连续特征的复杂零件：

```python
with BuildPart() as model:
    Box(...)
    Cylinder(..., mode=Mode.SUBTRACT)

result = model.part
```

## 4. `file_write` 不是普通文件写入

模型不能直接操作宿主文件系统，而是调用 `file_write(filename="model.py", content="...")`。

工具定义在 [tool_schemas.py](/mnt/data_44T/ytk/local-ai-cad-agent/agent/tool_schemas.py:10)，具体实现位于 [file_tool.py](/mnt/data_44T/ytk/local-ai-cad-agent/agent/tools/file_tool.py:289)。

写入前会做静态预检。

### 禁止危险导入

例如 `os`、`subprocess`、`socket`、`pathlib` 等导入会被拒绝。

### 禁止危险函数

例如 `open`、`eval`、`exec`、`compile` 等调用会被拒绝。

### 检查典型 build123d 错误

代码还会检查：

- `RadiusArc` 的半径小于端点弦长的一半。
- `Ellipse` 使用了错误的关键字参数。
- 圆角或倒角之后仍然使用固定边索引。
- 特征标记格式错误。
- 保护参数被删除或改名。

只有通过 AST 检查后，源码才会写入项目并生成一个新版本。

## 5. 每次修改都会形成一个 CAD 版本

假设第一次生成：

```python
thickness: float = 4.0
```

用户后来要求：

> 板子厚一点，改成 6 mm。

智能体通常会：

1. 读取当前 `model.py`。
2. 修改 `thickness`。
3. 提交新源码。
4. 生成新的 revision。
5. 重新构建。

版本系统会保存当前源码、旧版本源码、父版本关系、源码摘要、修改来源以及构建成功/失败记录。恢复旧版本不会倒退 head，而是创建一个新的恢复版本。

版本实现位于 [revisions.py](/mnt/data_44T/ytk/local-ai-cad-agent/agent/revisions.py:152)。

## 6. 修改源码后，模型必须调用 CAD 构建工具

模型生成 `model.py` 后，必须调用：

```text
cad_build_and_verify
```

这不是简单的 `python model.py`。 [CadTool](/mnt/data_44T/ytk/local-ai-cad-agent/agent/tools/cad_tool.py:70) 会：

1. 读取当前 `model.py`。
2. 再次执行源码验证。
3. 创建临时工作目录。
4. 把 `model.py` 复制到临时目录。
5. 放入受信任的 runner 和 renderer。
6. 在 Bubblewrap 沙箱中运行。
7. 读取构建结果。
8. 将产物原子复制回项目目录。

模型代码只在临时环境中执行，不直接在 Flask 进程中执行。

## 7. CAD runner 如何判断模型是否有效

runner 会寻找模型源码暴露的顶层变量：

```python
shape = namespace.get("result")
```

随后计算：

```python
shape.bounding_box()
shape.solids()
shape.volume
shape.is_valid
```

成功后得到类似结构化指标：

```json
{
  "solid_count": 1,
  "is_valid": true,
  "volume_mm3": 6540.0,
  "dimensions_mm": {
    "x": 60.0,
    "y": 30.0,
    "z": 4.0
  }
}
```

如果没有 `result`、实体为空、体积不为正、几何无效、尺寸非有限，或者 build123d API 调用失败，构建都会失败。错误会包装成工具结果，再送回模型作为下一轮上下文。

## 8. 模型如何自动修复 CAD 错误

典型过程是：

```text
模型写入 model.py
    ↓
CAD 构建失败
    ↓
返回 RadiusArc 半径过小等错误
    ↓
模型理解错误原因
    ↓
修改 radius，或改用 ThreePointArc
    ↓
再次调用 cad_build_and_verify
```

例如，模型使用了错误的固定边索引时，系统提示它改为基于几何属性重新选择：

```python
edges = (
    model.edges()
    .filter_by(GeomType.CIRCLE)
    .filter_by_position(Axis.Z, 9.9, 10.1)
)
```

或者使用 Builder 模式中的：

```python
model.edges(Select.LAST)
```

因此，系统并不是期望模型第一次生成就正确，而是让模型通过错误信息不断修正源码。

## 9. 渲染图片用于视觉自检

CAD 构建成功后，系统还会将实体三角化，生成 `render.png`，然后把它再次作为图片提供给模型。

模型需要检查：

- 是否生成了用户要求的主体。
- 孔的位置是否合理。
- 形状比例是否明显错误。
- 是否出现断开的实体。
- 是否存在意外的多余结构。
- 渲染结果是否和参考图片相符。

如果几何指标正确但视觉上仍然不符合要求，模型会继续修改源码并重建。

所以系统同时进行两类检查：

### 几何检查

由本地程序完成：

```text
solid_count
is_valid
volume
bounding box
```

### 语义和视觉检查

由模型完成：

```text
是否符合用户意图
是否缺少特征
比例是否合理
参考图形态是否匹配
```

## 10. 参考图片如何影响建模

参考图不会先经过单独的轮廓提取模块。当前实现是：

```text
图片 → PNG 规范化 → Base64 → 作为多模态消息发给模型
```

模型自己从图片中判断：

- 外形比例。
- 大致轮廓。
- 孔、槽、凸台等特征。
- 对称性。
- 哪些尺寸需要用户确认。
- 哪些尺寸可以合理估计。

系统提示词要求模型：

- 用参考图估计比例。
- 非关键尺寸可以估计。
- 关键公差、孔径和装配尺寸必须提问。
- 不要为了视觉效果擅自放大结构。

如果配置的端点不接受图片，客户端会自动去掉图片重新请求，但此时模型只能依靠文字和已有源码继续工作。

## 11. 用户提出后续修改时发生什么

例如用户继续说：

> 把四个孔改成沉头孔，并把板厚增加到 6 mm。

智能体不会从零开始，而是：

1. 读取现有 `model.py`。
2. 读取已有对话和工具结果。
3. 读取当前约束。
4. 找到对应参数和孔特征。
5. 只修改相关代码。
6. 生成新的 revision。
7. 重新构建和渲染。
8. 再次等待预览检查。

如果用户固定了：

```python
thickness: float = 4.0
```

模型尝试改成 `6.0` 时，写入会被约束系统拒绝，并返回类似：

```text
Protected constraint(s) violated:
parameter 'thickness' value was changed
```

模型只能修改没有被保护的部分。

## 12. 什么时候才算完成

模型说“完成”并不等于任务真的完成。至少需要满足：

1. `model.py` 存在。
2. `result` 存在。
3. build123d 成功执行。
4. 几何有效。
5. 体积为正。
6. 生成 STL 预览。
7. 生成渲染图。
8. 模型完成视觉检查。
9. 浏览器成功加载当前 STL。

只有模型已经成功构建、浏览器也确认预览加载完成，AgentRunner 才会发布最终完成消息。相关状态管理在 [core.py](/mnt/data_44T/ytk/local-ai-cad-agent/agent/core.py:1236)。

## 总结

这个项目的自然语言 CAD 能力由四部分共同组成：

```text
1. LLM：
   把自然语言转换成建模计划和 build123d 代码。

2. build123d：
   真正执行实体建模和布尔运算。

3. 静态/动态验证：
   阻止危险代码，检查几何是否有效。

4. 迭代反馈：
   把 CAD 错误、几何指标和渲染图再次交给模型修正。
```

因此它的实际工作方式更接近：

> 让语言模型编写 CAD 程序，并给它一个可以运行、报错、测量和渲染的 CAD 环境，让它通过多轮工具调用把程序修到可用。

而不是：

> 把一句话直接转换成一个三维网格文件。
