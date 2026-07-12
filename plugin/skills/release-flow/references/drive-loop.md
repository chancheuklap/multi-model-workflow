# Drive Loop · 出包自愈机械驱动合同

> SKILL 路由到这时，manifest 已登记，且已 `release init` 或有可恢复的 `release-state.json`。这份 reference 是唯一的 AFK 驱动方法：连续问状态、执行状态给出的机械动作、如实写回，再问；直到安装包就绪或引擎 surface。
>
> **引擎持有 loop，你是它的手。** 进度、下一步、修复次数、完成与否全由 `release-state.json` 计算。不从会话记忆续跑、不自行选择下一 stage、不另记一份已试账。

## 状态表：`where` 的输出决定唯一动作

每次先运行 `bash "$MMW" release where`。只处理当前输出，不预跑下一步：

| `where` 回显 | 机械动作 | 轮次处理 | 是否交回判断层 |
|---|---|---|---|
| `STAGE:<name> RUN:<display>` | `release stage run --stage <name>`(引擎展开占位符、路由 remote-build、跑 diagnose、写 done\|failed 并记 findings);失败据 `where` 为 `RETRY-STAGE` 则 `dispatch --stage <name>` | 线性全绿不推进；只有 dispatch 后引擎仍要求重跑才 `round next` | 否 |
| `RETRY-STAGE:<name> RUN:<display>` | 与 `STAGE` 相同，`stage run` 重跑该 stage(失败重跑、transient 重试、进程中断后的 running 恢复都长这样) | dispatch 后已推进的一轮不再额外推进 | 否 |
| `SUCCESS:all stages done` | `exit-check` 必须为 `DONE`，随后 `close` | 不适用 | 否；`exit-check` 非 `DONE` 是引擎错误，不报告成功 |
| `PAUSED:needs-context` | **驱动 Agent 自主处置**(见「PAUSED 自主处置」节)，不是直接交人 | 不推进 | 自主处置连续 2 次无效才交负责人 |
| `PAUSED:needs-redirection` | 读取 `receipt`，原样交负责人——P0 保护路径、熔断、预算越界是保命闸，Agent 不得自行 resume | 不推进 | 是 |
| `CORRUPT:` / `FAILED-STAGE:` / `NO-STAGES:` | 不执行 stage argv、不调用 `resume`；读取 `receipt` 或引擎错误 | 不推进 | 是 |
| 其他输出或命令错误 | 不猜测 state、不重新 `init` | 不推进 | 是，带原始输出 |

`RUN:<display>` 只供人阅读；**stage argv 由引擎 `stage run` 从 `release-state.json` 读取并展开，驱动器不自行读取 argv、更不把展示字符串 shell-split。**

## 连续驱动一轮

以下命令是 `STAGE` / `RETRY-STAGE` 分支的一轮。成功执行完一轮后立刻重新运行 `release where`，直到状态表给出终态；不要每个 shell turn 人工停顿。

```bash
state="$(bash "$MMW" release where)"

case "$state" in
  STAGE:*|RETRY-STAGE:*)
    stage="${state#*:}"
    stage="${stage%% RUN:*}"
    # 引擎的 stage run 是唯一执行器:它按 state 读取 stage argv、展开 ${RELEASE_STAGE_DIR} /
    # ${RELEASE_PLUGIN_DIR}、把 build stage 的 mmw-release-remote-build 路由到远程 harness、
    # 跑 manifest.diagnose、按退出码写 done|failed 并把 findings 记进 attempt ledger。
    # 驱动器不自建第二执行器,也不 shell-split 展示串 RUN:<display>。
    bash "$MMW" release stage run --stage "$stage"
    post="$(bash "$MMW" release where)"
    case "$post" in
      RETRY-STAGE:*)
        # 本 stage 失败并已分级。P0 / 同 fingerprint 熔断 / 预算熔断会被引擎写成 PAUSED(不是
        # RETRY-STAGE),不会走到这。派一次修复:findings 由引擎从最近 attempt 的 artifact_refs 读回,
        # 驱动器无须自持 findings 文件。
        bash "$MMW" release dispatch --stage "$stage"
        post_dispatch="$(bash "$MMW" release where)"
        case "$post_dispatch" in
          STAGE:*|RETRY-STAGE:*) bash "$MMW" release round next ;;
        esac
        ;;
    esac
    ;;
  SUCCESS:*)
    [ "$(bash "$MMW" release exit-check)" = "DONE" ] || exit 1
    bash "$MMW" release close
    ;;
  PAUSED:*|CORRUPT:*|FAILED-STAGE:*|NO-STAGES:*)
    bash "$MMW" release receipt
    exit 0
    ;;
esac
```

`stage run` 内部分开保存 stage 退出码与 diagnose 结果:stage 非零而 diagnose 没有 fail finding 时，引擎以 `needs-context` PAUSE，绝不把构建失败伪装成 `stage done`。空 findings、非法 JSON、非法 Finding 同样由引擎 surface，驱动器不自行补默认 finding、不自行重试。

## 何时推进修复轮次

`round next` 代表一次已处置的修复/派生重试，不是“跑过一个 stage”的计数器。

- `stage run` 成功（diagnose 无 fail）：引擎写 `stage done`，立即重新 `where`。多阶段 no-op loop 因此可以直接到 `SUCCESS`，不消耗 round。
- `stage run` 失败：引擎已在其内部跑完 diagnose 并 `stage fail` 分级。若引擎已 surface（`where` 为 `PAUSED`），读取 receipt，不 dispatch。
- 引擎尚未 surface（`where` 为 `RETRY-STAGE`）：`dispatch --stage <name>` 让引擎按 P2/P1/P0 和收敛护栏裁决（findings 从 attempt ledger 读回）。只有 dispatch 后 `where` 仍为 `STAGE` / `RETRY-STAGE`，才调用一次 `round next`，随后重新 `where` 由 `stage run` 重跑同一失败 stage。
- P0、同 fingerprint 熔断、attempt / round / wall-clock 预算熔断都由引擎写成 `PAUSED`。不再调用 `round next`，不继续跑 stage。

你不判 P0/P1/P2，不改工作树，不绕 path-gate、post-fix gate 或 dispatch，也不自建第二执行器。stage 执行、真相源派生、P1 的修复提交和 P0 的人工门禁都属于引擎；驱动器只连续问 `where`、调 `stage run` / `dispatch` / `round next` 并如实推进。

## PAUSED 自主处置（needs-context 专用）

无人值守出包的第一原则是**能自己修的不等人**。`PAUSED:needs-context` 表示引擎缺信息无法机械分级（diagnose 产不出合规 finding、动作无改动、清理失败等），这类暂停由驱动 Agent 亲自补上"判断层"，流程：

1. `release receipt` 读已试账目；从最近 attempt 的 `log_refs` / `artifact_refs` 读引擎日志、回传的远端构建日志(`build-run.log`)和 findings 原文。
2. 亲自诊断根因。判断依据必须能引用日志原文，不猜。
3. 能处置的直接处置：修仓库代码/钥匙/配置照常提交到功能分支（你就是主 Agent，path-gate 只约束引擎派的自动修复，不约束你的正常开发提交）；环境瞬态问题（网络、构建机忙）等待或修好环境。
4. 处置完 `release resume` 续跑（HEAD 变了引擎自动全量重验）。
5. **同一根因自主处置 2 次仍未解决，或根因涉及计费/合同/保护路径/需要负责人拍板的业务决策 → 停下写清楚交负责人**。不无限打转。

`PAUSED:needs-redirection` 不适用本节：那是 P0 硬约束和熔断护栏，必须交负责人。

## 终态、回执和恢复

- `SUCCESS` 不是口头成功。只有 `release exit-check` 返回 `DONE` 才能说“安装包就绪”，随后执行 `release close` 收束 state。`DONE` 不代表安装后的用户测试已经完成。
- 安装包路径只能来自刚完成 stage 的 execution output 或 artifact reference。若回执没有记录路径，诚实报告“安装包路径未被 stage 回执记录”，不按约定目录猜测。
- `CORRUPT`、`FAILED-STAGE`、`NO-STAGES` 都不执行下一 stage，也不自动 `resume`。读取 `release receipt`；其 `attempt_ledger` 是唯一的“已试什么”来源，原样交负责人判断。
- `needs-redirection` 暂停由负责人处置后显式 `release resume`；`needs-context` 暂停按上节由驱动 Agent 自主处置后 `release resume`。新的驱动器从 `release where` 重新读取 `release-state.json`，不重复 `init`，不丢弃已有 ledger。
