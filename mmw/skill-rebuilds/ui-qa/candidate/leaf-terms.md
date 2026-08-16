# ui-qa.md 本轮要改的术语

发布 `/mmw-ui-qa` 英文候选时，替换 `docs/context/ui-qa.md` 里这些条目的英文名。含义不动。范围标签用 `this-task` 与 `full`，不再用 `本任务` 与 `全量`。

**UI QA**（现用名 `界面 QA`）：
agent 依据已经谈定的判据自动检查界面，产出违规项与 finding。「QA」是质量保证（Quality Assurance）。
_Avoid_: 走查、UI 审、界面审、自动验收

**check**（现用名 `检查项`）：
界面 QA 每次运行都要跑的一种检查。两类九种：A 类四种由确定性检查判定，B 类五种由模型判断产出。它是要跑的东西，不是跑出来的结果——结果按类分别叫 violation 和 finding。
_Avoid_: 判拒、规则、错误码

**violation**（现用名 `违规项`）：
确定性检查直接判定成立的界面问题。它不是候选，不需要用户裁决，由技能直接修改。
_Avoid_: finding、已确认缺陷、bug

**finding**：
(authoritative: [finding](./review.md))

**disposition**（现用名 `处置`）：
(authoritative: [处置](./review.md))

**criterion self-check**（现用名 `判据自检结果`）：
对设计系统文件跑格式校验得到的结果。它说的是判据有问题，不是界面有问题，因此不进九种检查项，也不进用户裁决。
_Avoid_: 违规项、finding、界面问题

**screen map**（现用名 `界面全图`）：
界面、每个界面的状态与界面之间跳转的集合。它在进程内构建，不落文件，每次运行重建。
_Avoid_: 路由表、站点地图、界面清单

**coverage report**（现用名 `覆盖报告`）：
本次运行到不了的状态清单，逐条写明状态名与到不了的原因。它不驱动修改，也不进用户裁决。
_Avoid_: 覆盖率、遗漏项、跳过清单

**path shape**（现用名 `路径形状`）：
(authoritative: [路径形状](./artifact-location.md))
