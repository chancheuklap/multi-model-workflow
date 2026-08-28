# 按机制用途检查改造计划：哪些步骤该交给脚本、哪些该交给 hook

落地 spec #60 的十一节已经定了改什么。本文用一张「机制—用途」表逐步检查 #60 与 `12-decisions.md`，找出用错机制或没用上机制的地方，给出可以落地、边际情况少、不需要大基建的改法。本文只调查、只提议，不定案。参考快照在 `docs/research/code-landing-refs/`（下称 `refs/`），行号来自 `cat -n`。

## 检查用的表

| 机制 | 用它的理由 | 不该用它做的事 |
| --- | --- | --- |
| 技能 | 内容要被多个 agent 复用，或主 agent 要做多项任务 | 描述一串固定操作让模型逐步照做 |
| agent 配置文件（subagent 定义） | 自定义模型与思考强度；调用时自动加载固定上下文 | 把禁令、汇报格式放进派发 prompt |
| Herdr 派发外部会话 | 要用搭载不同模型的 agent | — |
| hook | 强制执行与判断 | 注入长段指令（Grok 的被动事件忽略 stdout） |
| 脚本 | 固定操作脚本化：不出错、不跳步、省 token | 做需要判断的事 |
| 文档 + 指针 | 一份事实服务多个流程；已写下的内容不再抄进 prompt | — |

## 六份参考的核在哪

六份参考里有五份的核是同一个原则：**模型写草稿，脚本判定并执行状态转移**（关票、换标签、入队），其中三份还用 hook 把「必须经过脚本」变成强制。

| 参考 | 它靠代码做的核 | #60 拿到的 | 仍留给模型的 |
| --- | --- | --- | --- |
| unlazy | 一份 parser 被 checker、lint、Stop hook 共用（`refs/unlazy/scripts/lib/gates.mjs` L79-242）；`exit 0 ∧ EXPECT` 由脚本判、EVIDENCE 由脚本写（`scripts/gate-check.mjs` L589-600、L759-765）；`--reverify` 把旧勾改回 `- [ ]`（L796-797）；Stop hook 在 ledger 未清时阻止会话结束（`scripts/stop-hook.mjs` L122-128 分类、L168-173 输出 block）；总结行 `ALL MET` / `UNMET` / `HANDOFF REQUIRED` 与退出码由脚本算（L841-894） | parser、判定、写回、`--reverify`、lint——vendor 进 `verify-ticket`（#60 第 2 节） | 收尾评论首行与 `Counts:`（#60 第 9 节第 4–5 步）；Stop hook |
| pstack | `check-plan.mjs` 只查计划文件形状、有问题 exit 1（`refs/pstack/skills/poteto-mode/scripts/check-plan.mjs` L110-186）；`ledger check <pr> <sha>` 查不到裁决打印 `NOT-VERIFIED`（`skills/poteto-mode/scripts/orch/store.ts` L1358-1372；exit 2 在 `orch.ts` L544-551）；`watch-pr` 把 PR 状态分四级阻塞和退出码（`skills/poteto-mode/scripts/watch-pr/policy.ts` L137-178 定义、L219-224 定顺序、L307-325 退出码）；`skills/poteto-mode/playbooks/orchestrate.md` L17「The CLI never spawns, waits, or wakes anything」 | `VERDICT` 五级词汇（B4） | 关票前没有任何东西查「最后一条 VERDICT 的 commit 是不是 HEAD」 |
| swarm-forge | 出站前一串机器拒绝：草稿位置、字段、commit 可达 HEAD 且是 base 后代、`git diff --name-only` 非空、无重复在途（`refs/swarm-forge/swarmforge/scripts/swarm_handoff.bb` L286-288、L598-735、L851-870）；接活时 `in_process` 多于一个即 exit 2（`ready_for_next_task.bb` L122-125）；状态转移全由脚本执行，agent 只写四行草稿（`git_handoff` 草稿模板 L19-22）；启动器按宿主拼权限参数（`swarmforge.bb` L473-500） | 宿主启动命令进 `models.md`（E1）；二次调用审计明确不做（0.3） | 开工守卫；关票前的 git 核对；启动命令由主 agent 手抄 |
| grok-bundled | `validate-plan.py` 校验 DAG 无环、无悬空、算层级（`refs/grok-bundled/execute-plan/scripts/validate-plan.py` L145-292）——但被它自己的 SKILL.md 绕过，整个快照里没有任何 `.md` 引用它 | 无（code-review 方法论里的 grok 部分登记 F15 后补，`12-decisions.md` B7） | `Blocked by` 边没有任何东西查环和悬空 |
| ponytail | 三个 hook 在会话与子代理启动时注入、压缩后重注入（`refs/ponytail/hooks/claude-codex-hooks.json` L5 matcher 含 `compact`）；benchmark 带自检门「自检不过拒绝花钱」（`benchmarks/agentic/run.py` L183-203、L419-420） | 五句规则文本（C1） | 无待补：注入型 hook 在我们这里由技能承担；对照实验按 C1 不做 |
| mattpocock | 无脚本。四个技能目录只有 `SKILL.md` + `agents/openai.yaml` | 起点 | — |

各参考的逐项细节（脚本文件、行号、协议）见本文末尾附录。

## 五个宿主的 hook 能力（2026-08-29 核实）

之前各文档写「无 hook」的理由是 `10-previous-attempt-postmortem.md` §3.a.1（注入型 hook 送到了错的会话）和 §3.a.3（Stop hook 依赖状态文件镜像）。两条都是针对**注入**和**镜像文件**，不是针对 hook 本身；下面两种 gate 不注入、不建镜像文件，两条理由都不适用。

| 宿主 | hook 配置文件 | 拒绝一次 shell 命令 | 阻止会话结束 | 输入里的 cwd / 命令文本 |
| --- | --- | --- | --- | --- |
| Claude Code | `~/.claude/settings.json` `hooks` 段（本机已有 Herdr 的 `SessionStart` 等五段） | `PreToolUse` matcher `Bash`：stdout `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"…"}}` 或 exit 2 + stderr | `Stop`：stdout `{"decision":"block","reason":"…"}`，reason 回给模型；`stop_hook_active` 防死循环 | `cwd`、`tool_input.command` |
| Grok Build | `~/.grok/hooks/*.json`（本机 `~/.grok/config.toml` L31、L39 把 `[compat.claude]`/`[compat.cursor]` 的 `hooks` 关了，所以不读 Claude/Cursor 的文件） | `PreToolUse` matcher `Bash`（自动别名到 `run_terminal_command`）：stdout `{"decision":"deny","reason":"…"}` 或 exit 2（`~/.grok/docs/user-guide/10-hooks.md` L92、L255、L265） | `Stop`：stdout `{"decision":"block","reason":"…"}`，一 turn 内最多 8 次续跑，600 秒默认超时（L96、L274、L281-283） | 驼峰：`cwd`、`toolInput.command`（L235-248） |
| Codex | `~/.codex/hooks.json`（本机 `config.toml` L18 `hooks = true`，`[hooks.state]` L625、L634 记录用过 `pre_tool_use`、`stop`） | `PreToolUse`：同 Claude 的 `permissionDecision:"deny"` | `Stop`：`{"decision":"block","reason":"…"}`，带 `stop_hook_active` | `cwd`、`tool_input.command` |
| Cursor CLI | `~/.cursor/hooks.json`（本机只有 `sessionStart`） | `beforeShellExecution`：stdout `{"permission":"deny","user_message":"…"}` 或 exit 2；`failClosed: true` 让 hook 失败也拒绝 | `stop` 不能硬阻止；stdout `{"followup_message":"…"}` 自动当下一条用户消息提交，`loop_limit` 默认 5。Claude 格式的 `{"decision":"block"}` 会被翻译成 `followup_message`。社区报告过 CLI 只发 shell 两个事件的 bug，上线前要实测 | `cwd`、`command` |
| pi | TypeScript 扩展 `~/.pi/agent/extensions/*.ts`（本机已有 Herdr 的） | `tool_call` handler return `{ block: true, reason }` | 没有 stop 事件；`agent_end` 里 `pi.sendUserMessage(reason)` 可续一轮 | 进程内对象 `ctx.cwd`、`event.input.command` |

结论：「worker 想结束时查票、票没关也没 HANDOFF 就顶回去」与「`gh issue close` 前跑校验、非零就拒绝」两件事五个宿主都做得到；Cursor 与 pi 是软阻止。Herdr 在五个宿主各装了一个 `SessionStart` hook（`09-herdr-dispatch-model.md` §1 表），安装方式可以照抄。上次尝试的 Grok hook 残留在 `~/.grok/hooks/mmw-discipline.json.bak-*`，已停用。

## 对 #60 的逐步检查

按 #60 的十一节顺序，只列有改法的。

### 第 2 节 `verify-ticket`：技能正文写的是一串固定操作，应是一个脚本

#60 第 2 节 `SKILL.md` 三种用法都写成「`gh issue view` 取 AC 段 → 写临时账本 → 跑 `gate-check.mjs` → 算 `Outside Owns` → `gh issue comment`」。这五步没有一步需要判断，按表是脚本。

改法：`scripts/verify-ticket.py <n> [--reverify|--lint]`（python3 标准库，调 `gh`、`node gate-check.mjs`、git）；`SKILL.md` 只剩一句「run `python3 <skill-dir>/scripts/verify-ticket.py …`」和三种用法的含义。同一脚本再多两个子命令：

- `--closeout <评论草稿>`：核收尾评论首行是 `ALL MET` 或 `HANDOFF REQUIRED: <n> abandoned (<kinds>), <m> unmet, <k> met of <total>`；任一 `ABANDON:` 或未过 → 不得 `ALL MET`；`ABANDON` 的 kind 属四个之一且指向已知 AC；勾了但 EVIDENCE 为 pending → unmet；`Counts:` 重算；最后一条 `VERDICT` 的 commit == `git rev-parse HEAD`（不等 = 修后没再验）；`git status --porcelain` 空；`git merge-base --is-ancestor main HEAD`；`git diff --name-only $(git merge-base main HEAD)..HEAD` 非空；票 OPEN 且 assignee 是我。全过 → 脚本贴评论并 `gh issue close --reason completed`；否则贴评论并 `--remove-label ready-for-agent --add-label ready-for-human`。参照 unlazy `gate-check.mjs` L841-894 的总结行、swarm-forge `swarm_handoff.bb` 的拒绝条件表、pstack `ledger check`。
- `--preflight`：分支名 == `issue-<n>`、`git status --porcelain` 空、票 OPEN 且带 `ready-for-agent` 且 `blockedBy` 全 CLOSED、assignee 为空 → 才 `gh issue edit --add-assignee @me`；否则 `NOT_READY: <原因>` exit 2。参照 swarm-forge `ready_for_next_task.bb` L118-142。
- `--lint` 多做一件事：`gh issue list --json number,blockedBy` 取本批票，查环、悬空引用、算启动层级；有环或悬空 exit 1。grok `validate-plan.py` `validate_dag` L145-229 原样复用。

边际情况：收尾评论格式已在 #60 第 9 节第 5 步定死；`VERDICT` 行要求写完整 SHA（第 5 节 `body.md` 加一句）；`main` 分支名写死。不持有状态文件（`10` §3.a.3、`05` §10）：每次从 `gh` 读，只往评论输出。

### 第 5 节 verifier：`body.md` 只剩动作，AC 明细由脚本给

`body.md` 现在要写「每条 AC 一行（id、退出码、匹配与否、输出前 200 字）」。这就是 `verify-ticket.py --reverify` 的输出；verifier 只补 `VERDICT <完整 SHA> <level> by <model> — 一句话`，level 是它唯一要判的事。

### 第 7 节与第 9 节：两个 gate 用 hook 强制

现状：第 7 节开工核对、第 9 节第 6 步关票/换标签，都是 worker 读正文自己做；跑不跑 `verify-ticket` 也由它决定。#60 Out of Scope 把「票不动而 agent 已 idle」的处置留给以后，早上靠第 13 步第三条查询发现会话死了。

两个 hook，一个脚本文件 `mmw-v2/skills/verify-ticket/scripts/hook.py`，按 `$1` 分两种：

1. **Stop gate**（`hook.py stop`）：读 stdin JSON 取 `cwd`；`git branch --show-current` 匹配 `issue-<n>` 且 `HERDR_ENV=1` 才动作（这就是自定位：主 agent 会话、用户日常会话、reviewer 会话 `issue-<n>-review` 都不匹配，§3.a.1 的错位不会发生）；`gh issue view <n> --json state,comments` → 票 CLOSED 或最后一条评论首行是 `HANDOFF REQUIRED` → 允许；否则输出 `{"decision":"block","reason":"#<n> is still open with no closing comment. Run verify-ticket.py <n> --closeout or write the HANDOFF REQUIRED comment."}`。`stop_hook_active` / `stopHookActive` 为真且票状态没变 → 允许（宿主本身还有 8 次/5 次上限）。`gh` 失败 → 允许（宿主 fail-open，与文档一致）。
2. **关票 gate**（`hook.py pretool`）：读 stdin 取命令文本；正则命中 `gh issue (close|edit .*--(add-label ready-for-human|remove-label ready-for-agent))` 才动作；跑 `verify-ticket.py <n> --closeout --check-only`（只核不贴）；非零 → deny 并把脚本 stderr 第一行当 reason；其余命令一律 allow。分支名不匹配 `issue-<n>` → allow。

输入键名差异（Claude/Codex 蛇形、Grok 驼峰、Cursor 自有字段）在 `hook.py` 里一处兼容；输出按宿主：Claude/Codex `hookSpecificOutput.permissionDecision`，Grok `decision`，Cursor `permission` / `followup_message`。宿主由 `$2` 传入，配置项里写死。

效果：第 9 节第 6 步的关票动作从「worker 照做」变成「不经 `--closeout` 做不了」；夜间 worker 停在半路的情况由 Stop gate 顶回去，早上第三条查询只剩真正死掉的会话。

### 安装：`install.sh` 多装一层 hook

这是唯一的基建。四个宿主各写一条 JSON、pi 一个 `.ts`，都指向 `~/.agents/skills/verify-ticket/scripts/hook.py`（技能已软链到那里）：

- Claude：`~/.claude/settings.json` 的 `hooks.Stop` 与 `hooks.PreToolUse`（matcher `Bash`）各加一条，python3 读—改—写 JSON，按 `command` 字符串去重，不动别人的条目。
- Grok：新文件 `~/.grok/hooks/mmw-verify-ticket.json`（`Stop`、`PreToolUse` matcher `Bash`），不改 `config.toml`。
- Codex：`~/.codex/hooks.json` 同 Claude 的合并法。
- Cursor：`~/.cursor/hooks.json` 加 `stop` 与 `beforeShellExecution`。
- pi：`~/.pi/agent/extensions/mmw-verify-ticket.ts`，`tool_call` 与 `agent_end` 两个 handler 调同一个 `hook.py`。

`--check` 顺带核对五处存在。约 150 行，一次性；Herdr 的安装脚本是现成模板。

### 第 4 节 `models.md` 与第 9 节第 3 步：派发是固定操作，应是脚本

主 agent 晚上每张票重复「读 `models.md` 抄 worker 行 → `herdr pane split` → `agent start … --kind …` → 等 idle → `agent prompt "implement #<n>"`」；worker 起 reviewer 会话是同一串。按表是脚本：`dispatch.sh <n> <role>`，从 `docs/agents/models.md` 的表里按角色取命令列（表保持「角色 | 宿主 | 完整启动命令」三列，脚本只读第三列，用户照旧只改表）。再加 `dispatch.sh wait <n> <首行前缀> [秒]`：每 30 秒 `gh issue view` 看最后一条评论首行，出现即 exit 0 打印评论，超时 exit 1——第 9 节第 3 步「轮询 `gh issue view`」和第 10 步等 VERDICT 都用它。放 `mmw-v2/skills/implement/`？不行，它在上游 subtree；放 `verify-ticket/scripts/` 与其余脚本同处。

边际情况：`09` §7 实测过 `agent start` 约 4 秒返回、`--wait` 是稳定态；Herdr 名 `issue-<n>` 与 `issue-<n>-review` 已定（E1）。

### 第 3 节 Read back：加 DAG 核对

已并入上面 `--lint`。

### 第 6 节 code-review：按表核对，形态不变

B7 定的「`SKILL.md` 路由 + 三个 reference，prompt 只给起点 commit 与票号」符合「文档 + 指针」；两个 reviewer 子代理跟随 opus 会话的模型，没有各自定模型的需要。不改。

### 不提的

二次调用审计门（0.3 不做）；对照实验 harness（C1 不做）；跨票记忆（消费端是提示词，`10` §5 第 4 条）；merge-note 与正文的一致性 canary（「关键句」没有可机械判定的定义，边际情况太多）。

## 若采纳，落在 #60 哪里

| 改法 | #60 位置 |
| --- | --- |
| `verify-ticket.py` 三用法 + `--closeout` + `--preflight` + `--lint` 加 DAG | 第 2 节（技能正文改为一句命令）；第 3 节 Read back；第 7 节第一步改为跑 `--preflight`；第 9 节第 5–6 步改为跑 `--closeout` |
| `hook.py stop` / `hook.py pretool` | 第 2 节多一个脚本；新增一节「hook 安装」或并入第 2 节；第 1 节的虚构票多一条检查：故意在票没关时让 worker 会话结束，看它被顶回 |
| `dispatch.sh <n> <role>` / `wait` | 第 4 节 `models.md` 表定三列；第 9 节第 3 步改为跑 `dispatch.sh` |
| `install.sh` 装 hook | Testing Decisions「结构核对」加 `--check` 核对五处 hook |
| verifier `body.md` 只补 VERDICT 行；VERDICT 写完整 SHA | 第 5 节 |

都不改 `12-decisions.md` 的任何定案；hook 这一条与 `10` §6 表「hook 层 … 不做」相抵，理由已在上文「五个宿主的 hook 能力」首段说明，需要你定。

## 附录：各参考的核，逐项

### unlazy

- **parser 唯一**：`refs/unlazy/scripts/lib/gates.mjs` L79-242 `parseGates`：gate 行格式、id 唯一、CHECK/EXPECT 成对、`ABANDON:` 指向已知 id、fenced code 内忽略，任一不满足 exit 2；`gate-check.mjs`、`gate-lint.mjs`、`stop-hook.mjs` 三方共用。
- **三态**：`gates.mjs` L254-260 `gateState`：有 ABANDON → abandoned；没勾 → unmet；勾了但 EVIDENCE 空或 `pending` → unmet-no-evidence；否则 met。
- **判定与写回**：`gate-check.mjs` L589-600 `ok = !error && exitCode === 0 && matched`；超时、输出超 1 MiB、spawn 失败都算 error；`refs/unlazy/tests/hardening-tests.mjs` L242-252 专门防「exit 7 但输出含 token」。写回前在文件锁下重读，CHECK/EXPECT/CWD/shell 签名变了就丢弃结果打印 `STALE`（L778-805）。
- **`--reverify`**：已 met 的 gate 也重跑（L682），不过就改回 `- [ ]` 与 `EVIDENCE: pending`（L796-797）；没跑 reverify 的 met gate 计入 unmet `(reverify not run)`（L860-866）。
- **总结与退出码**：L841-894 算 `ALL MET`（exit 0）/ `UNMET` 或 `HANDOFF REQUIRED`（exit 1）；有 abandoned 永远不是 `ALL MET`。
- **Stop hook**：`stop-hook.mjs` L122-128 分出 unmet，L168-173 输出 `{"decision":"block"}`；同一语义状态连续 block 超过 6 次放行（L12、L161-165）；abandoned 放行但附 `HANDOFF REQUIRED`（L133-134）。它读本地 ledger 文件——我们的 Stop gate 读 `gh`，没有这份文件。
- **只是散文的**：Depth Tree、四遍打磨、「Audit the final report」（`refs/unlazy/SKILL.md` L80-82）。

### pstack

- 下列路径都在 `refs/pstack/skills/poteto-mode/` 下。
- **`scripts/check-plan.mjs`**：每个 PR 节 9 个子块名字与顺序一致（L8-18、L118-121）、`Depends on.` 非空（L126-127）、Verify 块以固定句开头（L132-135）；stderr 每条 `file:line: message`，有问题 exit 1（L186）。服务于 `playbooks/multi-phase-plan.md` L10 第 6 步「fix every line it prints」。
- **`scripts/orch/store.ts`**：`ledger record <pr> <sha> <verdict>` 只接受五个词（L21-26、L286-294），按 `pr+sha` upsert（L1346-1355）；`ledger check` 查不到抛 `NotFoundError`（L1358-1372），`orch.ts` L544-551 转成 exit 2；`unit set --state` 不校验转移（L1270），五个状态词在 `playbooks/orchestrate.md` L75 散文里。
- **`scripts/watch-pr/policy.ts`**：四级阻塞定义在 L137-178，固定顺序在 L219-224，退出码 2/3/4/6 在 L307-325；反应本身在 `playbooks/babysit.md` L13-14 散文。
- architect 偏离上报（`refs/pstack/skills/architect/SKILL.md` L57）和 visual-parity（`playbooks/visual-parity.md` L5-8）在 pstack 里本来就是散文。

### swarm-forge

- **出站门 `swarm_handoff.bb`**：`git_handoff` 草稿只有四行（模板 L19-22；`allowed-fields` L33 共七个可用字段），commit 由脚本取 sender HEAD 覆盖（`fill-commit` L466-469）。拒绝条件：草稿不在 `tmp/`（L286-288）、字段非法（L598-651）、`task_id` 与 `in_process` 不符（L507-525）、commit 不是 HEAD 祖先或不是 `task_base_commit` 后代（L851-853、L582-591）、`git diff --name-only <base> <sha>` 为空（L303-310、L868-870）、同 from/to/task/commit 已在途（L527-580）。通过后脚本自己入队并调 `done_with_current.sh`（L189-197）。
- **二次调用审计**：`invocation-fingerprint`（L386-396）= sender + task + recipients + commit + 草稿 sha256，`audit-candidate`（L407-419）再加 artifacts 列表；第一次写 pending 并打印 `AUDIT_REQUIRED`（L421-437、L456-461）退出；第二次指纹相等才入队（L398-405、L447-461）。
- **接活守卫 `ready_for_next_task.bb`**：`in_process` 是 batch 目录或多于一个文件 → exit 2（L118-125）；为零是正常接活路径（L130-144）；接活时写死 `task_base_commit`（L136-142）。
- **弱于名字的两件**：`commit-msg-hook.bb` 只追加 `By <role>.` 永远 exit 0（L47-61）；watchdog 只看终端窗口不看 agent（`swarm-window-watchdog.bb` L8、L65-72）。
- **启动器 `swarmforge.bb`**：claude `--permission-mode bypassPermissions` + `CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1`，codex `--no-alt-screen --yolo` 并写 `~/.codex/config.toml` trust（flag 字面量 L451-471，拼装 L473-500，trust L515-525）。

### grok-bundled

- **`validate-plan.py`**：`validate_dag` L145-172 查 id 唯一、依赖存在、Kahn 算法查环并回溯环路径（L175-229）；`compute_levels` L250-280、`linearize` L283-292。`execute-plan/SKILL.md` L278-371 让 orchestrator 自己按散文解析分层，脚本从未被调用。
- **`memory.py`**：`$HOME/.grok/implement-memory/<workspace-id>.md`，workspace-id = `<可读名>-<sha256 前 12 位>`（L278-321）；temp + rename 原子写（L800-823）加 `fcntl.flock`（L849、L867）。
- **实现-评审循环终止条件**：`implement/SKILL.md` L758-762「The only exit condition is all reviewers reporting 0 issues… There is no iteration cap」；判定方式是 orchestrator 读文件数 `Status: open`（L579、L994）。

### ponytail

- **三个 hook**：`SessionStart`（matcher 含 `compact`）注入按当前 mode 过滤后的 SKILL 正文（`hooks/ponytail-instructions.js` L11-41、L77-92；调用在 `hooks/ponytail-activate.js` L41-42、L92-94）；`SubagentStart` 再注入一次，因为 SessionStart context 不传给子代理（`hooks/ponytail-subagent.js` L3-6）；`UserPromptSubmit` 解析 `/ponytail <mode>`（`hooks/ponytail-mode-tracker.js` L23-56）。
- **benchmark `benchmarks/agentic/run.py`**：每 cell 独立目录 + `git init` 基线（L155-160、L285-298）；自检门（L183-203、L419-420）；`--rescore`（L382-396）；聚合（L341-367）。judge `judge.py` 温度 0（L26、L66），先自检排序否则拒判（L120-137）。规则副本 canary `scripts/check-rule-copies.js` L44-69。
- **证据**：`benchmarks/results/2026-06-22-issue-245-217-comprehension.md` L40-52，第一句在 Sonnet/Opus 上 1/6→6/6，散文版 0/3；`2026-06-17-cost-verification.md` L12-15 规则段在 `gpt-5.4-mini` / `gpt-5.5` 上更贵 26-39%，在 Claude 上便宜 42-75%（L9-11）；定案的高级 worker 模型 grok-4.6 xhigh 不在测过的模型里。

### mattpocock 上游技能

四个技能全部是模型读提示词执行；`code-review/SKILL.md` L17-23 三条 git 命令是模型跑的。本仓已有的脚本能力与调用写法：`mmw-v2/install.sh`（软链技能目录与 subagent 成品、跑 `assemble.py`）、`mmw-v2/skills/exe-release/scripts/release-flow.sh`（`SKILL.md` L14-17「Resolve its absolute path once」）。
