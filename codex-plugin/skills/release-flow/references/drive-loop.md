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
| `NATIVE-REPAIR-PENDING:<name>` | 读取第二行 `prompt=` 的全文；当前 task 已有同一修复子代理就等待，没有就用 `spawn_agent(task_name="release_repair_<name>", fork_turns="none")` 派 GPT 子代理 | 不推进 | 否 |
| `NATIVE-REPAIR-VERIFY:<name>` | 等修复子代理结束，再运行 `release repair verify --stage <name> --worker-ref <子代理名>`；引擎验路径、提交、跑修后门禁并推进本轮 | 验收成功由引擎推进 | 否 |
| `SUCCESS:all stages done` | `exit-check` 必须为 `DONE`，随后 `close` | 不适用 | 否；`exit-check` 非 `DONE` 是引擎错误，不报告成功 |
| `PAUSED:needs-context` | **驱动 Agent 自主处置**(见「PAUSED 自主处置」节)，不是直接交人。`where` 第二行 `question=` 是根因处置句（必读）；`receipt` 的「根因摘要」从 findings 抽出 name/fp/remediation | 不推进 | 自主处置连续 2 次无效才交负责人 |
| `PAUSED:needs-redirection` | 读取 `receipt`，原样交负责人——P0 保护路径、熔断、预算越界是保命闸，Agent 不得自行 resume | 不推进 | 是 |
| `CORRUPT:` / `FAILED-STAGE:` / `NO-STAGES:` | 不执行 stage argv、不调用 `resume`；读取 `receipt` 或引擎错误 | 不推进 | 是 |
| 其他输出或命令错误 | 不猜测 state、不重新 `init` | 不推进 | 是，带原始输出 |

`RUN:<display>` 只供人阅读；**stage argv 由引擎 `stage run` 从 `release-state.json` 读取并展开，驱动器不自行读取 argv、更不把展示字符串 shell-split。**

## 连续驱动一轮

以下命令是 `STAGE` / `RETRY-STAGE` 分支的一轮。成功执行完一轮后立刻重新运行 `release where`，直到状态表给出终态；不要每个 shell turn 人工停顿。

```bash
raw="$(bash "$MMW" release where)"
# where 暂停时第二行是 question=…；token 永远只取首行
state="${raw%%$'\n'*}"

case "$state" in
  STAGE:*|RETRY-STAGE:*)
    stage="${state#*:}"
    stage="${stage%% RUN:*}"
    # 引擎的 stage run 是唯一执行器:它按 state 读取 stage argv、展开 ${RELEASE_STAGE_DIR} /
    # ${RELEASE_PLUGIN_DIR}、把 build stage 的 mmw-release-remote-build 路由到远程 harness、
    # 跑 manifest.diagnose、按退出码写 done|failed 并把 findings 记进 attempt ledger。
    # 驱动器不自建第二执行器,也不 shell-split 展示串 RUN:<display>。
    bash "$MMW" release stage run --stage "$stage"
    post_raw="$(bash "$MMW" release where)"
    post="${post_raw%%$'\n'*}"
    case "$post" in
      RETRY-STAGE:*)
        # 本 stage 失败并已分级。P0 / 同 fingerprint 熔断 / 预算熔断会被引擎写成 PAUSED(不是
        # RETRY-STAGE),不会走到这。派一次修复:findings 由引擎从最近 attempt 的 artifact_refs 读回,
        # 驱动器无须自持 findings 文件。
        bash "$MMW" release dispatch --stage "$stage"
        post_dispatch_raw="$(bash "$MMW" release where)"
        post_dispatch="${post_dispatch_raw%%$'\n'*}"
        case "$post_dispatch" in
          STAGE:*|RETRY-STAGE:*) bash "$MMW" release round next ;;
        esac
        ;;
    esac
    ;;
  NATIVE-REPAIR-PENDING:*)
    # 这一步不能 shell 化。读取 raw 第二行的 prompt 绝对路径，把文件全文作为 message，
    # 从当前 Codex task 调 spawn_agent(fork_turns="none")。已有同一修复子代理就等待，
    # 不重复派；子代理只改当前 App worktree，不 commit。
    ;;
  NATIVE-REPAIR-VERIFY:*)
    stage="${state#*:}"
    # 先确认子代理已经结束，再让引擎验收磁盘上的真实改动。
    bash "$MMW" release repair verify --stage "$stage" --worker-ref codex-native-subagent
    ;;
  SUCCESS:*)
    [ "$(bash "$MMW" release exit-check)" = "DONE" ] || exit 1
    bash "$MMW" release close
    ;;
  PAUSED:needs-context*)
    # 不是终点:读 receipt 后进入「PAUSED 自主处置」节的判断流程(亲诊根因→能处置就处置→
    # release resume 续跑)。这一支无法纯 shell 化——它就是驱动 Agent 要补的判断层。
    # raw 第二行 question= 已是处置句，优先照做。
    bash "$MMW" release receipt
    ;;
  PAUSED:*|CORRUPT:*|FAILED-STAGE:*|NO-STAGES:*)
    # needs-redirection(P0/熔断)与 state 损坏:读 receipt 原样交负责人,不 resume。
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
- P0、同 fingerprint 熔断、fix-round / wall-clock 预算熔断都由引擎写成 `PAUSED`。不再调用 `round next`，不继续跑 stage。(`attempts` 只是全动作审计计数，不参与预算判断；熔断预算只看 `fix_rounds` 与墙钟。)

你不判 P0/P1/P2，不绕 path-gate、post-fix gate 或 dispatch，也不自建第二执行器。stage 执行、真相源派生、P1 的边界冻结/验收/提交和 P0 的人工门禁都属于引擎；Codex 原生 GPT 子代理只在冻结边界内改当前 App worktree。驱动器连续问 `where`，按状态调用 `stage run` / `dispatch` / 原生子代理 / `repair verify`。

## PAUSED 自主处置（needs-context 专用）

无人值守出包的第一原则是**能自己修的不等人**。`PAUSED:needs-context` 表示引擎缺信息无法机械分级，或失败被标成 **环境类 `env:` 指纹**（见下）。这类暂停由驱动 Agent 亲自补上"判断层"，流程：

1. `release where`：读第二行 `question=`（引擎已写清处置句时优先照做，例如「先停 PC 上 hedgehog 开发版再 resume」）。
2. `release receipt`：读「根因摘要」与 attempt 的 `log_refs` / `artifact_refs`；需要原文时再打开 build-run.log。
3. 亲自诊断根因。判断依据必须能引用日志或 findings 原文，不猜。
4. 能处置的直接处置：
   - **`env:active_product_process:*`**：停 Win-PC 上该产品开发版/安装版（`pc-*-dev --action stop` 或等价），确认无 electron-vite/backend 残留后再 `release resume`。
   - **`env:missing_RELEASE_REMOTE_HOST` / `env:missing_RELEASE_REMOTE_ROOT`**：在驱动 shell 导出后 resume（典型 `RELEASE_REMOTE_HOST=pc`、`RELEASE_REMOTE_ROOT=D:/agentflow-release-input`）。
   - **其它 `env:*`**：按 remediation 改构建机/本机环境后 resume，**不要**派代码 fix executor。
   - 仓库代码/钥匙/配置问题照常提交到功能分支后 resume。
5. 处置完 `release resume` 续跑（HEAD 变了引擎自动全量重验）。
6. **同一根因自主处置 2 次仍未解决，或根因涉及计费/合同/保护路径/需要负责人拍板的业务决策 → 停下写清楚交负责人**。不无限打转。

`PAUSED:needs-redirection` 不适用本节：那是 P0 硬约束和熔断护栏，必须交负责人。

## 终态、回执和恢复

- `SUCCESS` 不是口头成功。只有 `release exit-check` 返回 `DONE` 才能说“安装包就绪”，随后执行 `release close` 收束 state。`DONE` 不代表安装后的用户测试已经完成。
- 安装包路径只能来自刚完成 stage 的 execution output 或 artifact reference。若回执没有记录路径，诚实报告“安装包路径未被 stage 回执记录”，不按约定目录猜测。
- `CORRUPT`、`FAILED-STAGE`、`NO-STAGES` 都不执行下一 stage，也不自动 `resume`。读取 `release receipt`；其 `attempt_ledger` 是唯一的“已试什么”来源，原样交负责人判断。
- `needs-redirection` 暂停由负责人处置后显式 `release resume`；`needs-context` 暂停按上节由驱动 Agent 自主处置后 `release resume`。新的驱动器从 `release where` 重新读取 `release-state.json`，不重复 `init`，不丢弃已有 ledger。
- `NATIVE-REPAIR-PENDING` 恢复时，先看当前 Codex task 是否仍有同一修复子代理；有就等待，没有就复用原 prompt 重派。`NATIVE-REPAIR-VERIFY` 表示磁盘已有候选改动，等子代理结束后直接验收，不重派。状态不保存 agent id，跨压缩只认现有 release state、prompt、Git HEAD 和工作树。
