# 界面 QA

这个 Context 定义 `/mmw-ui-qa` 使用的语言。它检查界面本身，不是六道审的任何一道。无标签默认是 `this-change`。用户可挂的标签是 `this-task` 与 `full`。

## Language

**UI QA**：
agent 依据已经谈定的判据自动检查界面，产出 violation 与 finding。「QA」是质量保证（Quality Assurance）。
_Avoid_: 走查、UI 审、界面审、自动验收、界面 QA

**check**：
UI QA 每次运行都要跑的一种检查。两类九种：A 类四种由确定性检查判定，B 类五种由模型判断产出。它是要跑的东西，不是跑出来的结果——结果按类分别叫 violation 和 finding。
_Avoid_: 判拒、规则、错误码、检查项

**violation**：
确定性检查直接判定成立的界面问题。它不是候选，不需要用户裁决，由技能直接修改。
_Avoid_: finding、已确认缺陷、bug、违规项

**finding**：
(authoritative: [finding](./review.md))

**处置**：
(authoritative: [处置](./review.md))

**criterion self-check**：
对设计系统文件跑格式校验得到的结果。它说的是判据有问题，不是界面有问题，因此不进九种 check，也不进用户裁决。
_Avoid_: violation、finding、界面问题、判据自检结果

**screen map**：
界面、每个界面的状态与界面之间跳转的集合。它在进程内构建，不落文件，每次运行重建。
_Avoid_: 路由表、站点地图、界面清单、界面全图

**coverage report**：
本次运行到不了的状态清单，逐条写明状态名与到不了的原因。它不驱动修改，也不进用户裁决。
_Avoid_: 覆盖率、遗漏项、跳过清单、覆盖报告

**范围**：
一次 UI QA 检查哪些界面。无标签默认 `this-change`，用最新一次提交的 diff。用户可挂的标签只有 `this-task`（当前任务分支相对父分支的 diff）与 `full`（screen map 里每一个界面）。`this-change` 不是用户标签。
_Avoid_: 三档标签、把 this-change 写成要挂的标签

**路径形状**：
(authoritative: [路径形状](./artifact-location.md))
