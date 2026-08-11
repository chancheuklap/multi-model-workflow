# 产物落点

这个 Context 定义 MMW 产物在仓库中的位置由哪几段构成。它定义构成方式和每类产物的类别根，不列出每一类产物的完整落点。

## Language

**路径形状**：
一件产物在仓库中的位置规则，由四段构成：`<类别根>/<名字段>/[<范围段>/]<类别内细分>`。
_Avoid_: 落点合同、目录结构、路径模板

**类别根**：
路径形状的第一段，由产物类别决定。一个类别根只放一类产物。
_Avoid_: 顶层目录、产物根

**固定类别根**：
由 MMW 规定、目标仓库不可改的类别根。
_Avoid_: 默认路径、内置路径

**工作目录根**：
取值由目标仓库自己决定的类别根，取值在 `.mmw.json` 的 `paths`。
_Avoid_: 临时目录、本地目录

**名字段**：
路径形状中承载 effort 名字的那一段。全部产物只有这一个名字位置。
_Avoid_: 任务目录、slug 段

**范围段**：
路径形状中标识 Wayfinder decision ticket 的那一段，值是 `issue-<编号>`。只有 decision ticket 有这一段。
_Avoid_: 子目录、任务段

**类别内细分**：
类别根之下由产物类别自己规定的目录结构。它一律使用目录，不使用文件名前缀。
_Avoid_: 文件名前缀、扁平命名

**安全路径段**：
首字符是字母或数字，其余只能是字母、数字、点、下划线、连字符，不含斜杠，一律小写的单个路径段。名字段、范围段和类别内细分的每一段都是安全路径段。
_Avoid_: slug、目录名

**effort**：
(authoritative: [effort](./wayfinding.md))

## 类别根

| 产物 | 类别根 |
| --- | --- |
| spec | `docs/specs/` |
| plan | `docs/plans/` |
| prototype 资产 | `docs/prototypes/` |
| research | `docs/research/` |
| ADR | `docs/adr/` |
| leaf | `docs/context/` |
| 否决记录 | `.out-of-scope/` |
| 过程材料 | scratch 根 |
| 审查记录 | reviews 根 |

ADR、leaf 和否决记录是仓库级产物，没有名字段。

表中前七项是固定类别根，目标仓库不可改。scratch 根与 reviews 根是工作目录根，取值读目标仓库配置。

## 不使用路径形状的产物

三类产物不使用路径形状。

出包状态、出包阶段产物、交付记录、结构图谱和任务 worktree 跨任务存在，身份由产品名、attempt 序号或分支名决定，不由 effort 名决定。

map、decision ticket、结论评论、spec issue、tracer bullet ticket 和 agent brief 落在 issue tracker 上，不占仓库路径。

能在提示词或标准输入里传完的内容不写文件，因此没有落点。判据见 [不落盘判据](#不落盘判据)。

## 不落盘判据

能在提示词或标准输入里传完的，一律不写文件。必须落盘才能被读到、被执行、被事后诊断的，写进 scratch 根，任务结束时清理。
