# Prototype 迭代闭环设计

## 目标

prototype 继续属于 design 阶段，不增加顶层 phase。引擎必须让零上下文 agent 在冷启动后默认续作已有原型，逐轮记录反馈、改动和验证结果，并且只把用户确认的最终产物交给计划与落地工人。

验收结果：任意 agent 进入在管 worktree 后只运行一次 `mmw where`，即可知道当前验证问题、轮次、现有产物、运行命令和唯一下一步；已有原型不能被静默重建，未收敛原型不能越过设计确认。

## 范围

- 三个单宿主镜像同步实现同一业务合同：`plugin/`、`pi-plugin/`、`droid-plugin/`。
- 增加轻量 prototype 运行状态、两个 CLI 动作、断点恢复投影、设计确认门和下游选中产物传递。
- prototype 源码原地演进，Git 保存源码历史；仓库内只追加迭代记录和每轮必要证据。
- evidence campaign 的原始探测数据退出 prototype 目录。
- Droid 保留现有宿主状态目录、派发后端和设计文档布局；本次只统一 prototype 行为与材料传递。

## 不变量

1. `task.json` 仍是当前运行状态的唯一真相源，进度板只作可重建投影。
2. design 的唯一出口仍是用户显式运行 `/approve-design`；prototype 不增加第二个人闸。
3. 状态更新必须原子、失败可见，不得用默认值掩盖损坏或缺失。
4. prototype、mockup 仍是随设计提交的正式资产。
5. plan/build 工人材料由脚本确定，不让主线程或工人自行搜索和猜测权威版本。
6. 三宿主只共享业务合同；状态目录、工具名、派发后端和宿主接线保持独立。

## 状态合同

新任务的 `task.json.prototype` 初始化为 `null`。旧任务缺少该字段时按 `null` 读取，但已有 prototype/mockup 文件必须先显式接管，不允许静默兼容。

```json
{
  "prototype": {
    "status": "active",
    "kind": "logic",
    "question": "待验证的单一设计问题",
    "iteration": 2,
    "run_command": "python docs/design/<slug>/prototype/demo.py",
    "artifacts": ["docs/design/<slug>/prototype/demo.py"],
    "selected": [],
    "log": "docs/design/<slug>/prototype/README.md",
    "updated_at": "<UTC ISO>"
  }
}
```

| 字段 | 合同 |
| --- | --- |
| `status` | `active`、`accepted`、`superseded` |
| `kind` | `logic`、`ui`、`mixed` |
| `question` | 当前原型要回答的单一设计问题，单行非空 |
| `iteration` | 当前轮次，从 1 开始 |
| `run_command` | 用户验证现有原型的单行命令，只记录、不执行 |
| `artifacts` | 当前持续演进的原型与 mockup 路径 |
| `selected` | accepted 后交给审批和下游的权威产物，可多项 |
| `log` | 固定为设计目录内 `prototype/README.md` |
| `updated_at` | prototype 状态最近更新时间 |

状态转换：

| 当前状态 | 动作 | 下一状态 | 结果 |
| --- | --- | --- | --- |
| `null` | `start` | `active` | 创建日志，进入第 1 轮 |
| `null` 且已有文件 | `start --adopt` | `active` | 原地登记已有产物，不复制、不覆盖 |
| `active` | `checkpoint --verdict continue` | `active` | 关闭当前轮并记录结果，轮次加一 |
| `active` | `checkpoint --verdict accepted` | `accepted` | 记录通过结论并钉住 selected |
| `active` | `checkpoint --verdict superseded` | `superseded` | 记录方向失效，回执要求退回 propose |
| `accepted` | `checkpoint --verdict continue` | `active` | 收到新反馈后重新打开，进入下一轮并清空 selected |
| `superseded` | `start` | `active` | 在同一日志追加新的验证问题，重新从第 1 轮开始 |

active 状态重复 `start` 必须非零退出并打印已有状态与续作指令。accepted 状态重复 `start` 必须要求用 `checkpoint --verdict continue` 重新打开。

## CLI 合同

统一入口只增加一个命令组、两个动作：

```bash
mmw prototype start \
  --kind <logic|ui|mixed> \
  --question "<待验证问题>" \
  --run "<运行命令>"

mmw prototype start --adopt \
  --kind <logic|ui|mixed> \
  --question "<待验证问题>" \
  --run "<运行命令>" \
  --artifact <已有路径> [--artifact <已有路径> ...]

mmw prototype checkpoint \
  --feedback "<本轮反馈或假设>" \
  --change "<实际改动>" \
  --result "<验证方式和结果>" \
  [--artifact <当前产物> ...] \
  [--evidence <本轮证据> ...] \
  --verdict <continue|accepted|superseded> \
  [--selected <最终产物> ...]
```

规则：

- `start` 和 `checkpoint` 只允许在 develop 的 design 阶段执行。
- fresh start 发现 `prototype/` 或 `mockup/` 已有文件时拒绝，回执给出 `--adopt` 指令。
- `--adopt` 必须显式列出现有产物。
- active checkpoint 必须填写反馈、改动和结果；accepted 必须至少一个 selected；superseded 必须在结果中说明方向失效原因。
- accepted 重新打开时，`checkpoint --verdict continue` 只登记新反馈并进入下一轮；之后再完成该轮 checkpoint。
- checkpoint 未传 `--artifact` 时沿用当前 artifacts；传入时以本次列表替换。
- selected 必须真实存在，且自动并入 artifacts。
- 每条回执都打印状态、轮次、日志、产物和一条唯一 `NEXT=` 指令。

## 路径与安全合同

- 日志固定为 `<docs.design>/prototype/README.md`。
- 原型产物只允许位于 `<docs.design>/prototype/` 或 `<docs.design>/mockup/`。
- prototype 走查证据只允许位于 `<docs.design>/prototype/runs/<三位轮次>/`。
- 拒绝绝对路径、`..`、换行、软链，以及目录内部包含软链的产物。
- 所有传入路径必须是 worktree 相对路径并真实存在。
- fresh start 只创建日志和 `runs/`，不替 agent 创建语言或框架骨架。

仓库形态：

```text
docs/design/<slug>/
├── <slug>.md
├── prototype/
│   ├── README.md
│   ├── <持续原地演进的可运行产物>
│   └── runs/
│       ├── 001/
│       └── 002/
└── mockup/
    └── <持续原地演进的 UI 产物>
```

## 迭代日志合同

`README.md` 由命令维护，agent 不手写流程状态。文件先记录验证问题、类型和运行命令，随后按轮次追加：

- 用户反馈或待验证假设；
- 本轮实际改动；
- 验证方式与结果；
- 证据路径；
- verdict 与 selected。

每轮使用不可重复标记 `<!-- mmw-prototype-round:<N> -->`。checkpoint 先幂等追加日志，再原子更新 manifest；若日志已写而 manifest 更新失败，原命令重跑只能补齐状态，不能重复写轮次。

源码不按轮次复制。每个有意义 checkpoint 将源码、证据和日志作为同一 Git 提交，历史源码由 Git 保存。

## `mmw where` 与冷启动

prototype 仅改变 design 阶段的内部指路，不改 `phase` 或 `phase_index`。

active 时，`where` 必须输出：

```text
inner_loop=prototype
prototype_status=active
prototype_iteration=<N>
prototype_question=<...>
prototype_log=<...>
prototype_artifacts=<JSON>
prototype_run=<...>
load=references/design/prototype-mockup.md
do=先读日志和全部现有产物，运行现有原型，在原产物上修改
then=<一条完整 checkpoint 模板>
```

accepted 时，`where` 明确要求把选中原型的结论回填主设计文档，再走自检、设计预审和 `/approve-design`。

superseded 时，`where` 只给出退回 propose 的完整 handoff 命令。

状态为空但磁盘已有 prototype/mockup 文件时，`where` 输出 `prototype_untracked`、真实文件清单和完整 `start --adopt` 模板；不得继续成文或审批。

同时修正 design 当前通用 `then=` 的误导：正常 design 的出口显示 pin 主设计文档、设计预审、请用户 `/approve-design`，不得显示普通 `handoff pass`。

会话分诊直接显示 active/accepted/superseded、轮次和日志；进度板从 task.json 投影同一状态，不另存真相。

## 设计确认

`mmw approve` 增加以下机器检查：

- active：拒绝，返回当前轮次和 checkpoint 指令。
- superseded：拒绝，返回退回 propose 的 handoff 指令。
- prototype 状态为空但磁盘已有 prototype/mockup 文件：拒绝，要求 `start --adopt`。
- accepted：验证 log 与全部 selected 存在，并自动加入 approval reports 后计算指纹。
- 未触发 prototype 且磁盘无相关文件：保持现有审批流程。

approval 只自动覆盖 prototype 日志和 selected。淘汰产物、未选中候选和运行证据不进入指纹。selected 在确认后变化时，现有 `approval_stale` 机制必须阻止后续推进。

## 下游材料

worker 不再机械传递整个 `prototype/` 和 `mockup/` 目录。

- accepted：传递主设计文档、prototype README、selected、direction、investigating 和 evidence 结论。
- active、superseded、null：不传 prototype/mockup；正常流程下 active/superseded 已被 approve 阻止。
- plan worker 继续把材料复制进隔离 sandbox；build worker继续按各宿主现有方式引用材料。
- selected 路径由脚本从 task manifest 解析，协调者不传额外旗标。

Droid 删除 plan-dispatch 的手工 `--mockup` 接口，改为和另外两镜像相同的 manifest 选中材料推导；Droid exec、模型和 sandbox 接线保持原实现。

## Evidence 目录

外部方案、API、并发和性能取证的计划、原始结果改放：

```text
docs/design/<slug>/evidence/
├── <campaign>-plan.md
├── <campaign>-result.md
└── runs/<campaign>/
```

prototype/runs 只保存 prototype 用户走查产生的截图和输出。设计正文继续只引用 evidence 结论，不内联长输出。

## 三宿主接入

共同行为以实体文件分别落入三个镜像，禁止软链。公共 prototype 状态 helper、CLI 行为、reference 方法和测试断言保持一致；以下内容宿主化：

| 宿主 | 保持独立 |
| --- | --- |
| Claude Code | `.claude` 状态面、Codex worker、Claude hooks/commands |
| Pi | `.pi` 状态面、pi-subagents、TypeScript extension、prompts |
| Droid | `.factory` 状态面、droid exec、Factory hooks/commands |

本次不迁移 Droid 已存在的 investigating/direction 布局。所有新路径从 `task.json.docs.design` 推导，不硬编码 Claude/Pi 的目录形态。

## 落地文件

| 模块 | 改动 |
| --- | --- |
| `scripts/lib/prototype-state.sh` | 三宿主共同行为：状态目录适配、路径安全、未登记文件、selected 材料解析 |
| `scripts/prototype.sh` | start/checkpoint 与幂等日志 |
| `scripts/mmw.sh` | 命令分发和 help |
| `state-schema/task-manifest.schema.json` | nullable prototype 合同 |
| `scripts/prepare.sh` | 新任务初始化 `prototype:null` |
| `scripts/flow.sh` | active/accepted/superseded/untracked 导航与 design 出口 |
| `scripts/note.sh` | approve 前置门与 selected 指纹 |
| `scripts/progress.sh`、会话分诊 hook | prototype 投影 |
| `scripts/worker.sh` | 只传 accepted log + selected；Droid 自动推导 |
| `prototype-mockup.md` | 完整迭代运行指南，通用 prototype skill 只提供制作方法 |
| `evidence-campaign.md` | 原始探测数据迁出 prototype |
| tests | 命令、恢复、审批、下游、E2E、三镜像一致性 |

## 验证

专项测试必须覆盖：

1. fresh start、重复 start 拒绝且不覆盖、旧产物 adopt。
2. 路径越界、`..`、绝对路径、换行和软链全部 fail-closed。
3. continue 追加且轮次增加；重复执行不重复日志；accepted 必须 selected；accepted 可重新打开；superseded 给出唯一回退指令。
4. 冷启动 active/accepted/superseded/untracked 均返回唯一正确下一步。
5. active、superseded、untracked 均不能 approve；accepted 自动指纹覆盖 selected；selected 修改触发 stale。
6. plan/build 只接收 accepted README 与 selected，不接收整个 prototype/mockup。
7. 完整 develop E2E 在 prototype accepted 后正常通过唯一人闸并进入流水线。
8. session/progress 投影可从 task.json 重建。
9. 三宿主专项与全量 shell 测试、build check/build test、release Python tests、JSON 解析全部通过。
10. 三镜像共同行为文件无漂移，版本号及 marketplace 同步更新。
