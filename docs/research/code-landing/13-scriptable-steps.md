# 六份参考的核在哪、我们拿了什么、还有哪些步骤能交给脚本

落地 spec #60 的十一节已经定了改什么。本文回头核对六份参考资料里**由代码而不是提示词完成**的部分（快照在 `docs/research/code-landing-refs/`，下称 `refs/`，行号来自 `cat -n`），对照 #60 与 `12-decisions.md` 的定案，找出 #60 里仍由模型自己判、而参考项目交给脚本判的步骤。本文只调查、只提议，不定案。

## 一句话结论

六份参考里有五份的核是同一个原则：**模型写草稿，脚本判定并执行状态转移**（关票、换标签、入队）。#60 把「判定」交给了 vendor 的 `gate-check.mjs`（`12-decisions.md` B8），这是对的；但「执行状态转移」——关票、换标签、收尾评论的首行与计数、开工认领——仍由 worker 自己做（#60 第 9 节第 4–6 步、第 7 节）。`00-synthesis.md`「三份报告一致指出的根因」第 4 行「自报、自评、自勾、自关票」里，「自评」已由 gate-check 与 verifier 接走，「自关票」还在。

| 参考 | 它靠代码做的核 | #60 拿到的 | 仍留给模型的 |
| --- | --- | --- | --- |
| unlazy | 一份 parser 被 checker、lint、Stop hook 共用（`refs/unlazy/scripts/lib/gates.mjs` L79-242）；`exit 0 ∧ EXPECT` 由脚本判、EVIDENCE 由脚本写（`scripts/gate-check.mjs` L589-600、L759-765）；`--reverify` 把旧勾改回 `- [ ]`（L796-797）；Stop hook 在 ledger 未清时阻止会话结束（`scripts/stop-hook.mjs` L122-128 分类、L168-173 输出 block）；总结行 `ALL MET` / `UNMET` / `HANDOFF REQUIRED` 与退出码由脚本算（L841-894） | parser、判定、写回、`--reverify`、lint——vendor 进 `verify-ticket`（#60 第 2 节） | 收尾评论首行与 `Counts:`（#60 第 9 节第 4–5 步「Audit … 重数」）；Stop hook 按 `10` §6 hook 层行不要 |
| pstack | `check-plan.mjs` 只查计划文件形状、有问题 exit 1（`refs/pstack/skills/poteto-mode/scripts/check-plan.mjs` L110-186）；`ledger check <pr> <sha>` 查不到裁决打印 `NOT-VERIFIED`（`skills/poteto-mode/scripts/orch/store.ts` L1358-1372；exit 2 在 `orch.ts` L544-551）；`watch-pr` 把 PR 状态分四级阻塞和退出码（`skills/poteto-mode/scripts/watch-pr/policy.ts` L137-178 定义、L219-224 定顺序、L307-325 退出码）；`skills/poteto-mode/playbooks/orchestrate.md` L17「The CLI never spawns, waits, or wakes anything」 | `VERDICT` 五级词汇（B4） | 关票前没有任何东西查「最后一条 VERDICT 的 commit 是不是 HEAD」 |
| swarm-forge | 出站前一串机器拒绝：草稿位置、字段、commit 可达 HEAD 且是 base 后代、`git diff --name-only` 非空、无重复在途（`refs/swarm-forge/swarmforge/scripts/swarm_handoff.bb` L286-288、L598-735、L851-870）；接活时 `in_process` 多于一个即 exit 2（`ready_for_next_task.bb` L122-125）；状态转移全由脚本执行，agent 只写四行草稿（`git_handoff` 草稿模板 L19-22）；启动器按宿主拼权限参数（`swarmforge.bb` L473-500） | 宿主启动命令进 `models.md`（E1）；二次调用审计明确不做（0.3） | 开工守卫（分支名、工作区干净、票 OPEN 且 blocker 全关）；关票前的 git 核对 |
| grok-bundled | `validate-plan.py` 校验 DAG 无环、无悬空、算层级（`refs/grok-bundled/execute-plan/scripts/validate-plan.py` L145-292）——但被它自己的 SKILL.md 绕过，整个快照里没有任何 `.md` 引用它；`memory.py` 跨运行记忆带锁（`implement/scripts/memory.py` L340-351、L800-823） | 无（code-review 方法论里的 grok 部分登记 F15 后补，`12-decisions.md` B7） | `Blocked by` 边没有任何东西查环和悬空（#60 第 3 节 Read back 只核 Owns） |
| ponytail | 三个 hook 在会话与子代理启动时注入、压缩后重注入（`refs/ponytail/hooks/claude-codex-hooks.json` L5 matcher 含 `compact`）；benchmark 带自检门「自检不过拒绝花钱」（`benchmarks/agentic/run.py` L183-203、L419-420）；规则副本 canary 九条短语两处逐字一致（`scripts/check-rule-copies.js` L44-69）；结果文件记录八次改规则文本都没推动那一项数字（`benchmarks/results/2026-06-16-robustness-audit.md` L94-102） | 五句规则文本（C1，用真实的票跑一遍验证） | 无待补：常驻注入按 `10` §6 hook 层行不要，对照实验按 C1 不做；merge-note 与正文的一致性没有 canary |
| mattpocock | 无脚本。`implement`、`to-tickets`、`to-spec`、`code-review` 四个目录只有 `SKILL.md` + `agents/openai.yaml`（`find … -name '*.sh' -o -name '*.py'` 零命中） | 起点 | — |

## 每份参考的核，逐项

### unlazy

- **parser 唯一**：`refs/unlazy/scripts/lib/gates.mjs` L79-242 `parseGates`：gate 行格式、id 唯一、CHECK/EXPECT 成对、`ABANDON:` 指向已知 id、fenced code 内忽略，任一不满足 exit 2；`gate-check.mjs`、`gate-lint.mjs`、`stop-hook.mjs` 三方共用。
- **三态**：`gates.mjs` L254-260 `gateState`：有 ABANDON → abandoned；没勾 → unmet；勾了但 EVIDENCE 空或 `pending` → unmet-no-evidence；否则 met。
- **判定与写回**：`gate-check.mjs` L589-600 `ok = !error && exitCode === 0 && matched`；超时、输出超 1 MiB、spawn 失败都算 error；`refs/unlazy/tests/hardening-tests.mjs` L242-252 专门防「exit 7 但输出含 token」。写回前在文件锁下重读，CHECK/EXPECT/CWD/shell 签名变了就丢弃结果打印 `STALE`（L778-805）。
- **`--reverify`**：已 met 的 gate 也重跑（L682），不过就改回 `- [ ]` 与 `EVIDENCE: pending`（L796-797）；没跑 reverify 的 met gate 计入 unmet `(reverify not run)`（L860-866）。
- **总结与退出码**：L841-894 算 `ALL MET`（exit 0）/ `UNMET` 或 `HANDOFF REQUIRED`（exit 1）；有 abandoned 永远不是 `ALL MET`。
- **Stop hook**：`stop-hook.mjs` L122-128 分出 unmet，L168-173 输出 `{"decision":"block"}`；同一语义状态连续 block 超过 6 次放行（L12、L161-165）；abandoned 放行但附 `HANDOFF REQUIRED`（L133-134）。
- **只是散文的**：Depth Tree、四遍打磨、「Audit the final report」（`refs/unlazy/SKILL.md` L80-82）、PLAN 的 contract inventory。

对照 #60：第 2 节 vendor 了 parser、判定、写回、`--reverify`、lint，账本每次从票派生（`05` §10）。没拿的是 L841-894 那段总结行——#60 第 9 节第 4–5 步让 worker「重数 Counts」再手写首行，而 `gate-check.mjs` 跑完已经算过一次，只是 `verify-ticket` 把它的输出贴回票时没有把这行当收尾评论的依据。

### pstack

- 下列路径都在 `refs/pstack/skills/poteto-mode/` 下。
- **`scripts/check-plan.mjs`**：不读语义，只查形状——每个 PR 节 9 个子块名字与顺序一致（L8-18、L118-121）、`Depends on.` 非空（L126-127）、Verify 块以固定句开头（L132-135）；stderr 每条 `file:line: message`，有问题 exit 1（L186）。服务于 `playbooks/multi-phase-plan.md` L10 第 6 步「fix every line it prints」。
- **`orch/store.ts`**：`ledger record <pr> <sha> <verdict>` 只接受五个词（L21-26、L286-294），按 `pr+sha` upsert（L1346-1355）；`ledger check` 查不到抛 `NotFoundError`（L1358-1372），`orch.ts` L544-551 转成 exit 2；`unit set --state` 不校验转移（L1270），五个状态词在 `playbooks/orchestrate.md` L75 散文里。
- **`watch-pr/policy.ts`**：四级阻塞定义在 L137-178，固定顺序 `merge-conflicts → review-threads → failing-checks → merge-gate` 在 L219-224，退出码 2/3/4/6 在 L307-325；反应本身在 `playbooks/babysit.md` L13-14 散文。
- 我们从它拿的 architect 偏离上报（`refs/pstack/skills/architect/SKILL.md` L57）和 visual-parity（`playbooks/visual-parity.md` L5-8）在 pstack 里本来就是散文，不是核。

对照 #60：`VERDICT <commit> <level> by <model>` 只是评论一行（第 5 节）；「换 SHA 作废」是约定，关票前没有 `ledger check` 那种查一次的门。

### swarm-forge

- **出站门 `swarm_handoff.bb`**：`git_handoff` 草稿只有四行（模板 L19-22；`allowed-fields` L33 共七个可用字段），commit 由脚本取 sender HEAD 覆盖（`fill-commit` L466-469）。拒绝条件：草稿不在 `tmp/`（L286-288）、字段非法（L598-651）、`task_id` 与 `in_process` 不符（L507-525）、commit 不是 HEAD 祖先或不是 `task_base_commit` 后代（L851-853、L582-591）、`git diff --name-only <base> <sha>` 为空（L303-310、L868-870）、同 from/to/task/commit 已在途（L527-580）。通过后脚本自己入队并调 `done_with_current.sh` 完成当前入站项（L189-197）。
- **二次调用审计**：`invocation-fingerprint`（L386-396）= sender + task + recipients + commit + 草稿 sha256，`audit-candidate`（L407-419）再加 artifacts 列表；第一次写 pending 并打印 `AUDIT_REQUIRED`（L421-437、L456-461）退出；第二次指纹相等才入队（L398-405、L447-461）。
- **接活守卫 `ready_for_next_task.bb`**：`in_process` 是 batch 目录或多于一个文件 → exit 2（L118-125）；为零是正常接活路径（L130-144）；接活时写死 `task_base_commit`（L136-142）。
- **弱于名字的两件**：`commit-msg-hook.bb` 只追加 `By <role>.` 永远 exit 0（L47-61）；watchdog 只看终端窗口不看 agent（`swarm-window-watchdog.bb` L8、L65-72）。
- **启动器 `swarmforge.bb`** 按宿主拼权限参数：claude `--permission-mode bypassPermissions` + `CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1`，codex `--no-alt-screen --yolo` 并写 `~/.codex/config.toml` trust（flag 字面量 L451-471，拼装 L473-500，trust L515-525）。

对照 #60：E1 把启动命令写进 `models.md`，与启动器同一思路；`12-decisions.md` 0.3 明确不做二次调用审计。没拿的是「状态转移由脚本执行」——第 9 节第 6 步 worker 自己 `gh issue close` / 换标签；第 7 节 `--add-assignee @me` 前没有守卫。

### grok-bundled

- **`validate-plan.py`**：`validate_dag` L145-172 查 id 唯一、依赖存在、Kahn 算法查环并回溯环路径（L175-229）；`compute_levels` L250-280、`linearize` L283-292。`execute-plan/SKILL.md` L278-371 让 orchestrator 自己按散文解析分层，脚本从未被调用。
- **`memory.py`**：`$HOME/.grok/implement-memory/<workspace-id>.md`，workspace-id = `<可读名>-<sha256 前 12 位>`，来源优先 canonical 化的 `remote.origin.url`，其次 `--git-common-dir`、再次 cwd（L278-321）；temp + rename 原子写（L800-823）加 `fcntl.flock`（L849、L867）。
- **实现-评审循环终止条件**：`implement/SKILL.md` L758-762「The only exit condition is all reviewers reporting 0 issues… There is no iteration cap」；判定方式是 orchestrator 读文件数 `Status: open`（L579、L994）。
- **文档与脚本镜像的漂移测试**：`implement/tests/test_memory.py` L824 要求 SKILL.md 里的格式样例与 `memory.py` L134-139 `DEFAULT_HEADER` 逐字一致。

对照 #60：`## Blocked by` + `gh --blocked-by` 只存边；第 3 节 Read back 核 Owns 重叠，不查环与悬空。

### ponytail

- **三个 hook**：`SessionStart`（matcher 含 `compact`）注入按当前 mode 过滤后的 SKILL 正文（去 frontmatter、去其他 mode 的表行与示例，`hooks/ponytail-instructions.js` L11-41、L77-92；调用在 `hooks/ponytail-activate.js` L41-42、L92-94）；`SubagentStart` 再注入一次，因为 SessionStart context 不传给子代理（`hooks/ponytail-subagent.js` L3-6）；`UserPromptSubmit` 解析 `/ponytail <mode>`（`hooks/ponytail-mode-tracker.js` L23-56）。
- **benchmark `benchmarks/agentic/run.py`**：每 cell 独立目录 + `git init` 基线（L155-160、L285-298）；`claude -p … --output-format json --disallowedTools Bash`（L310-320）；自检门 good 必过、bad 必被抓，不过拒绝花钱（L183-203、L419-420）；工作区保留可 `--rescore`（L382-396）；聚合 `safe_rate`、`correct_rate`、LOC 中位数、成本（L341-367）。
- **judge `judge.py`**：`claude-sonnet-4-6` 温度 0（L26、L66），0-3 分只判 over-engineering（L28-39），先自检排序否则拒判（L120-137）。
- **规则副本 canary**：`scripts/check-rule-copies.js` L44-69。
- **证据**：`benchmarks/results/2026-06-22-issue-245-217-comprehension.md` L40-52，第一句在 Sonnet/Opus 上 1/6→6/6，散文版 0/3；`2026-06-16-robustness-audit.md` L94-102 针对 OpenAI 上一个邮箱校验陷阱八次改文本都没推动数字；`2026-06-17-cost-verification.md` L12-15 规则段在 `gpt-5.4-mini` / `gpt-5.5` 上更贵 26-39%，在 Claude 上反而便宜 42-75%（L9-11）。
- `07-overbuild-discipline.md` §8 的对照实验（P1、P2、P2′、P3、P4）里，P1 与 P4 在 `benchmarks/agentic/tasks.py` L699-755（`trace-transfer`）、L70-106（`safe-path`）已有现成件；C1 定了不做对照实验，真票跑出问题再针对那一句做，届时可直接复用。

对照 #60：按定案只收句子。定案的高级 worker 模型 grok-4.6 xhigh 不在 ponytail 测过的模型里，规则段对它的成本影响没测过，属待核事实。

### mattpocock 上游技能

四个技能全部是模型读提示词执行；`code-review/SKILL.md` L17-23 三条 git 命令是模型跑的。本仓已有的脚本能力与调用写法：`mmw-v2/install.sh`（只软链技能目录与 subagent 成品）、`mmw-v2/agents/assemble.py`、`mmw-v2/skills/ui-qa/scripts/`、`mmw-v2/skills/exe-release/scripts/release-flow.sh`（`SKILL.md` L14-17「Resolve its absolute path once」）。#60 第 2 节的 `verify-ticket` 沿用这一形态。

## #60 之外还能交给脚本的步骤

放置：都放 `mmw-v2/skills/verify-ticket/scripts/`，与 gate-check 同一技能（D4 的理由同样适用：worker 与 verifier 都用、不碰上游 subtree）。硬约束沿用 `10-previous-attempt-postmortem.md` §3.a.3 与 `05` §10：**不持有状态文件**，每次从 `gh issue view` 读票、只往评论输出。

| # | 蓝图步 / #60 节 | 现在谁判 | 脚本做什么 | 参照 | 代价 |
| --- | --- | --- | --- | --- | --- |
| S1 `closeout` | 步 11–12 / 第 9 节第 4–6 步 | worker 重数 `Counts:`、手写首行、自己 `gh issue close` 或换标签 | 读收尾评论草稿：首行是 `ALL MET` 或 `HANDOFF REQUIRED: <n> abandoned (<kinds>), <m> unmet, <k> met of <total>`；任一 `ABANDON:` 或未过 → 不得 `ALL MET`；`ABANDON` 的 kind 属四个之一且指向已知 AC；勾了但 EVIDENCE 为 pending → unmet；`Counts:` 重算核对。核 git：`git status --porcelain` 空、`git merge-base --is-ancestor main HEAD`（分支从 main 开，A2 的前提）、`git diff --name-only $(git merge-base main HEAD)..HEAD` 非空。核票：OPEN、assignee 是我、最后一条 `VERDICT` 的 commit == HEAD（不等 → 修后没再验，拒）。全过 → **脚本**贴评论并 `gh issue close --reason completed`；否则贴评论并 `--remove-label ready-for-agent --add-label ready-for-human` | unlazy `gate-check.mjs` L841-894 总结行；swarm-forge `swarm_handoff.bb` 拒绝条件表；pstack `ledger check` | python3 标准库 ~250 行；把「自关票」从 worker 手里拿走 |
| S2 `--lint` 加 DAG 核对 | 步 4 / 第 3 节 Read back | 模型看 Blocked by「都能解析」 | `verify-ticket --lint` 多做一件事：`gh issue list --json number,blockedBy` 取本批票，查环、悬空引用、算启动层级并打印；有环或悬空 exit 1 | grok `validate-plan.py` `validate_dag` L145-229 原样复用，输入换成 issue 列表 | ~120 行；填第 3 节没覆盖的一项 |
| S3 `preflight` | 步 6 / 第 7 节开工 | 模型核对 frontier 后自己 `--add-assignee` | 分支名 == `issue-<n>`、`git status --porcelain` 空、票 OPEN 且带 `ready-for-agent` 且 `blockedBy` 全 CLOSED、assignee 为空 → 才 `gh issue edit --add-assignee @me`；否则 `NOT_READY: <原因>` exit 2 | swarm-forge `ready_for_next_task.bb` L118-142 | ~40 行 bash |
| S4 review 完成轮询 | 步 8 / 第 9 节第 3 步 | 模型自己轮询 `gh issue view` | `wait-comment.sh <n> <前缀> [超时]`：每 30 秒查最后一条评论首行是否以给定前缀开头（reviewer 报告、`VERDICT`），到则 exit 0 打印评论，超时 exit 1 | pstack `watch-pr` 的轮询退避（`policy.ts` L262-265） | ~30 行；第 9 节第 3 步已写明「轮询」，脚本只是把它固定 |
| S5 merge-note canary | 落地纪律 / #60 卷首「merge-note」 | 人眼 | 关键句（ponytail 五句、Owns 两档）必须同时逐字出现在 `implement/SKILL.md` 与 `mmw-v2/merge-notes/implement.md`；不一致 exit 1 | ponytail `check-rule-copies.js` L44-69 | ~20 行 python3；防 `10` §3.a.2「同一份纪律放在两个家」再犯 |

优先级 S1 → S3 → S2 → S4 → S5。S1 直接对应根因表第 4 行剩下的「自关票」。

明确不提的（已有定案或与定案相抵）：二次调用审计门（0.3 不做）；对照实验 harness（C1 不做）；Stop hook 与常驻注入（`10` §6 hook 层行：工人不是编排会话的子代理，SessionStart / SubagentStart 送不到工人）；派发脚本（E1 已把完整命令放 `models.md`，主 agent 抄一行即可）；跨票记忆（消费端是提示词，`10` §5 第 4 条「抄机制先列消费者」）。

## 脚本改不了的一件事

没有 hook，所以**跑不跑脚本仍由模型决定**。gate-check 把判定拿走了，S1 把关票动作拿走了，「是否执行」留在 worker 手里。verifier 也是 worker 派的，它用 `--reverify` 重跑防的是「worker 跑了但报错了」，防不了「worker 整步跳过」；后者只有 S1 关票前查「最后一条 VERDICT 的 commit == HEAD」这一道。unlazy 的 Stop hook、ponytail 的压缩后重注入、swarm-forge 的 daemon 投递，都是「模型想停也停不下来」的机制，本轮全部没有对应物；夜间 worker 停在半路，靠早上第三条查询（`08` §5.4「认领了却没收尾评论」）发现。

## 若采纳，落在 #60 哪里

- S1、S3、S4 归第 2 节 `verify-ticket`（多三个脚本），第 9 节第 5–6 步改为「跑 `closeout`」，第 7 节第一步改为「跑 `preflight`」。
- S2 归第 2 节 `--lint` 用法与第 3 节 Read back。
- S5 归 Testing Decisions「提交前跑」一行。
- 都不改 `12-decisions.md` 的任何定案。
