# Drive Loop · 出包自愈机械驱动合同

> SKILL 路由到这时，manifest 已登记，且已 `release init` 或有可恢复的 `release-state.json`。这份 reference 是唯一的 AFK 驱动方法：连续问状态、执行状态给出的机械动作、如实写回，再问；直到安装包就绪或引擎 surface。
>
> **引擎持有 loop，你是它的手。** 进度、下一步、修复次数、完成与否全由 `release-state.json` 计算。不从会话记忆续跑、不自行选择下一 stage、不另记一份已试账。

## 状态表：`where` 的输出决定唯一动作

每次先运行 `bash "$MMW" release where`。只处理当前输出，不预跑下一步：

| `where` 回显 | 机械动作 | 轮次处理 | 是否交回判断层 |
|---|---|---|---|
| `STAGE:<name> RUN:<display>` | 从 state 读取该 stage 的 argv，运行 stage，再运行 diagnose；全绿则 `stage done`，否则 `stage fail` 后按 state 决定是否 dispatch | 线性全绿不推进；只有 dispatch 后引擎仍要求重跑才 `round next` | 否 |
| `RETRY-STAGE:<name> RUN:<display>` | 与 `STAGE` 相同，重跑该失败 stage | dispatch 后已推进的一轮不再额外推进 | 否 |
| `SUCCESS:all stages done` | `exit-check` 必须为 `DONE`，随后 `close` | 不适用 | 否；`exit-check` 非 `DONE` 是引擎错误，不报告成功 |
| `PAUSED:<reason>` | 读取 `receipt`，原样交回判断层 | 不推进 | 是 |
| `CORRUPT:` / `FAILED-STAGE:` / `NO-STAGES:` | 不执行 stage argv、不调用 `resume`；读取 `receipt` 或引擎错误 | 不推进 | 是 |
| 其他输出或命令错误 | 不猜测 state、不重新 `init` | 不推进 | 是，带原始输出 |

`RUN:<display>` 只供人阅读；**stage argv 必须从 `release-state.json` 的数组读取，禁止把展示字符串 shell-split。**

## 连续驱动一轮

以下命令是 `STAGE` / `RETRY-STAGE` 分支的一轮。成功执行完一轮后立刻重新运行 `release where`，直到状态表给出终态；不要每个 shell turn 人工停顿。

```bash
PLUGIN_SCRIPTS="$(cd "$(dirname "$MMW")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"
. "$PLUGIN_SCRIPTS/lib/host.sh"
STATE_FILE="$REPO_ROOT/$(mmw_resolve_state_subdir "$REPO_ROOT")/release-state.json"
state="$(bash "$MMW" release where)"

case "$state" in
  STAGE:*|RETRY-STAGE:*)
    stage="${state#*:}"
    stage="${stage%% RUN:*}"
    findings="$(mktemp)"
    manifest="$(jq -r '.manifest_path' "$STATE_FILE")"
    STAGE_ARGV=()
    while IFS= read -r arg; do STAGE_ARGV+=("$arg"); done < <(
      jq -r --arg stage "$stage" '.stages[] | select(.name == $stage) | .run[]' "$STATE_FILE"
    )
    DIAGNOSE_ARGV=()
    while IFS= read -r arg; do DIAGNOSE_ARGV+=("$arg"); done < <(
      jq -r '.diagnose[]' "$manifest"
    )

    set +e
    (cd "$REPO_ROOT" && "${STAGE_ARGV[@]}")
    stage_rc=$?
    (cd "$REPO_ROOT" && "${DIAGNOSE_ARGV[@]}") >"$findings"
    diagnose_rc=$?
    set -e

    if [ "$stage_rc" -eq 0 ] && [ "$diagnose_rc" -eq 0 ] \
      && jq -e '.findings | type == "array" and all(.[]; .status != "fail")' "$findings" >/dev/null; then
      bash "$MMW" release stage done --stage "$stage"
    else
      bash "$MMW" release stage fail --stage "$stage" --findings "$findings"
      post_fail="$(bash "$MMW" release where)"
      case "$post_fail" in
        PAUSED:*|CORRUPT:*|FAILED-STAGE:*|NO-STAGES:*) ;;
        *)
          bash "$MMW" release dispatch --stage "$stage" --findings "$findings"
          post_dispatch="$(bash "$MMW" release where)"
          case "$post_dispatch" in
            STAGE:*|RETRY-STAGE:*) bash "$MMW" release round next ;;
            PAUSED:*|CORRUPT:*|FAILED-STAGE:*|NO-STAGES:*|SUCCESS:*) ;;
          esac
          ;;
      esac
    fi
    rm -f "$findings"
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

`stage_rc` 与 `diagnose_rc` 必须分开保存。stage 非零而 diagnose 没有 fail finding 时，仍把 diagnostics 交给 `stage fail`；引擎会以 `needs-context` PAUSE，绝不能把构建失败伪装成 `stage done`。空 findings、非法 JSON、非法 Finding 同样由 `stage fail` surface，驱动器不自行补默认 finding 或重试。

## 何时推进修复轮次

`round next` 代表一次已处置的修复/派生重试，不是“跑过一个 stage”的计数器。

- stage argv 成功且 diagnose 无 fail：只 `stage done`，立即重新 `where`。多阶段 no-op loop 因此可以直接到 `SUCCESS`，不消耗 round。
- stage 失败或 diagnose 有 fail：先以同一份 findings `stage fail`。若引擎已 surface，读取 receipt，不 dispatch。
- 引擎尚未 surface：`dispatch` 让引擎按 P2/P1/P0 和收敛护栏裁决。只有 dispatch 后 `where` 仍为 `STAGE` / `RETRY-STAGE`，才调用一次 `round next`，随后重新 `where` 重跑同一失败 stage。
- P0、同 fingerprint 熔断、attempt / round / wall-clock 预算熔断都由引擎写成 `PAUSED`。不再调用 `round next`，不继续跑 stage。

你不判 P0/P1/P2，不改工作树，不绕 path-gate、post-fix gate 或 dispatch。P2 的真相源派生、P1 的修复提交和 P0 的人工门禁都属于引擎；驱动器只提供原始 stage 结果与同一份 diagnose findings。

## 终态、回执和恢复

- `SUCCESS` 不是口头成功。只有 `release exit-check` 返回 `DONE` 才能说“安装包就绪”，随后执行 `release close` 收束 state。`DONE` 不代表安装后的用户测试已经完成。
- 安装包路径只能来自刚完成 stage 的 execution output 或 artifact reference。若回执没有记录路径，诚实报告“安装包路径未被 stage 回执记录”，不按约定目录猜测。
- `PAUSED`、`CORRUPT`、`FAILED-STAGE`、`NO-STAGES` 都不执行下一 stage，也不自动 `resume`。读取 `release receipt`；其 `attempt_ledger` 是唯一的“已试什么”来源，原样交负责人判断。
- 负责人完成必要处置后，才可由人显式 `release resume`。新的驱动器从 `release where` 重新读取 `release-state.json`，不重复 `init`，不丢弃已有 ledger。
