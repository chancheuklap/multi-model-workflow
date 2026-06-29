# Loop Engineering · 落地规格

> **OVERVIEW = 设计文档**(为什么、什么形态);**本文 = 落地文档**(具体建什么:载体 / 数据 / 命令 / hook / 退出 / 空跑)。
> 冲突时以 OVERVIEW + `routes.json` + 进度记录 schema + 代码为准。具体字段名以骨架空跑时定死为准,本文是建表蓝本。

---

## 1. 范围:两类内层 loop,一台机器

| loop | 干什么 | 载体写 | "一步" | Claude 验吃 |
|---|---|---|---|---|
| **落地 loop**(execution) | 自驱写代码 | **Codex** 在 worktree | 一个 pack:写测试→实现→提交 | 跑测试/读 diff 坐实 acceptance |
| **审核 loop ×4**(①设计②计划③落地④final) | 自驱查证 | **Codex** 出审查 | 一个维度 / 一条 finding | grep/读/跑去坐实 finding 真假 |

**统一规律:Codex 是苦力(落地写码 / 审出审查),Claude 是对齐了设计的验收脑。** 同一台机器、同一套退出三件套(§6),载体和数据不同。**small-change 不进 loop**:主线程就地做,不派 Codex。**③落地审**不开判断 loop,降成机器合同门(§2)。

### 落地 loop 机制(序列):Codex 写 + Claude 验

```mermaid
sequenceDiagram
    participant H as 你
    participant C as 主线程(Claude 协调+验收)
    participant X as Codex(worktree 内写码)
    participant L as 进度记录(steps/pause)

    C->>L: steps expand(从计划展开 Pack)
    C->>X: codex-worker dispatch(开 worktree + 固定 prompt 严防过度设计;并行 plan 并行派)
    X->>X: 自驱 TDD,每 Pack 一提交(Pack N.M)
    X-->>C: 返回最后消息(逐 Pack done/blocked + acceptance + 改了啥)
    C->>C: 验收:跑测试/读 diff 坐实(不信 Codex 自述)
    alt 没过 / 要修
        C->>X: codex exec resume(发回修·context 原封)
    else 过
        C->>L: 记 step done
    end
    alt Codex 停下说缺输入/方向疑
        C->>H: 在场→AskUserQuestion;afk→软停自决留痕 / 冒泡停
    end
    C->>L: 全 plan 验过 → exit-check DONE → ③合同门 → 合并 → 结论词
    Note over H,C: merge/deploy 时 PreToolUse 拦·要你批(红线)
```

审核 loop 同构:Codex 出审查(`codex exec --sandbox read-only` + 我们的提示词),Claude 协调帮手亲验 + cover 清单;续接 `codex exec resume`。**防过早完工:落地/审都靠 Claude 按清单 verify + exit-check 机器核(Codex 不吃 SubagentStop)**;审协调帮手是 Claude subagent,才受 SubagentStop 看守。

---

## 2. 载体分配(落地必须照这个调,角色不混)

| loop | 写者载体 | 派发 | 续接 | 防过早完工 |
|---|---|---|---|---|
| 落地 worker | **Codex** | `codex-worker dispatch`(`codex exec -C <wt> --sandbox workspace-write` + 固定 prompt) | `codex exec resume` | 主线程按 plan 验收清单 verify + `exit-check`(Codex 不吃 SubagentStop) |
| 审 ①②④ | **Codex 出审查** + Claude 协调帮手验 | `review.sh start` → 协调帮手 `codex exec --sandbox read-only` 喂 `quartet`+阶段 angle | `codex exec resume`(Codex)/ `SendMessage`(协调帮手) | `SubagentStop` 看守协调帮手 + `exit-check` 清单 |
| 审 ③(合同门) | **脚本**(无模型) | 机器核:全 pack committed + 声明的跨 plan 合同存在 | — | — |

**铁律**(§5b):审/落地都用 `codex exec`,**不用 `codex review`**;续接两套别混(Codex=exec resume,Claude subagent=SendMessage);只有主线程能问用户,Codex/帮手都抛回主线程。

> review 提示词已迁到 `plugin2/skills/orchestrate/references/review/`(`quartet.md` + 四阶段 angle),`review.sh` 配好喂给 codex exec。

---

## 3. 数据结构(进度记录新增字段 · 建表蓝本)

**落地 loop**(写进 task.json 或并列执行档):
```
steps:       [ { id, desc, status: pending|done|blocked, commit } ]   # 主线程从计划展开
attendance:  attended | afk                                           # 在场开关
pause:       { at_step, kind: soft|surface, question } | null         # soft=有默认的判断;surface=缺输入/方向疑
decisions:   [ { at_step, chose, why, at } ]                          # afk 软停留痕,不偷跳
```

**审核 loop**(每轮审):
```
checklist:   [ { item, source, status: open|covered, evidence } ]    # 主线程从设计/issue 文档抽
findings:    [ { severity, confidence, locator, evidence, impact, remediation } ]  # quartet 字段
verdict:     pass | needs-repair | needs-redirection | needs-context | blocked
# 收敛轮由协调帮手自管,不落 loop-state;routes.json caps 是外层重派兜底上限
```

**merge/deploy 红线**:不在进度记录,是 PreToolUse hook 的判定 + 一条 `release_approval`(用户批准令牌)。

> 删净(已否定):续派信封 / resume_from_step / 红线路径表 / context 计数 —— 都不要。

---

## 4. 命令(实际落在 `loop.sh` / `review.sh`,统一经 `mmw` 调)

| 命令 | 谁调 | 干什么 |
|---|---|---|
| `mmw loop init --kind <execution\|review\|contract-gate>` | 主线程 | 起一台内层 loop |
| `mmw loop step add` | 主线程 | 从计划逐项展开 `steps[]` |
| `mmw loop step done` | 主线程 verify 后 / record-step hook(仅 Claude 经 Bash 的提交) | 记 `status=done` + commit |
| `mmw loop checklist add` | 主线程 | 从设计/issue 文档抽覆盖清单(审核 loop) |
| `mmw loop checklist cover` | 协调帮手 | 亲验坐实一个维度,记 evidence |
| `mmw loop finding add` | 协调帮手 | 收 Codex 亲验后的真 finding 落 `findings` |
| `mmw loop softstop` / `surface` | 主线程 / 协调帮手 | 软停(有默认)/ 冒泡(缺输入/方向疑)yield 回主线程 |
| `mmw loop exit-check` | 看守 hook / 主线程 | 核退出三件套(§6):完成判据 + 熔断 + 第三态 |
| `mmw review start --stage <...> --source <...>` | 主线程 | 一条命令 init 审 loop + 配审题 + 出协调帮手 brief |

续接走载体原语(SendMessage / codex exec resume),不另造命令。审者派 Codex 由协调帮手用 Bash 跑 `codex exec`,无专用脚本。

---

## 5. Hooks 新增

| hook | 事件 | 逻辑 |
|---|---|---|
| **看守** | `SubagentStop`(仅 Claude subagent:审协调 / Claude 直修) | 核 `steps`/`checklist`:没全绿且没到该停 → `exit 2` + `additionalContext` 顶回去续 |
| **红线** | `PreToolUse` | 命中 merge 回主分支 / push / 部署命令 且无 `release_approval` → deny,要主线程拿用户批准 |
| **记进度** | `PostToolUse`(commit) | 抽 `Pack N.M` 调 `step done`——**仅对 Claude 经 Bash 的提交生效**(small-change / Claude 直修) |

> **Codex 落地 + Codex 审都是外部进程,不吃 SubagentStop / PostToolUse**:Codex 在 worktree 自提交不触发 record-step;build 的 `step done` 由**主线程 verify 通过后手记**,防过早完工靠主线程按 plan 验收清单 verify + `exit-check`(不靠 hook)。SubagentStop 现只看守 Claude subagent(审协调 / Claude 直修)。

---

## 6. 退出三件套(每个 loop 落地怎么核)

| 件 | 怎么落 |
|---|---|
| **完成判据** | 覆盖清单全绿(客观项机器核:落地=steps 全 done;审=checklist 全 covered)+ 无开口 Critical/Important + 收敛(无新高置信 finding) |
| **熔断** | 修复轮上限(数据持有,见下),到顶转第三态 |
| **第三态** | `needs-redirection`(方向)/ `needs-context`(缺输入)/ `blocked`(卡死或超限)→ 抛主线程交人 |

**轮上限矩阵**(放 routes.json caps):①设计=2 · ②计划=2 · ③合同门=不开 loop · ④final=1–2 + 超限转根因调查。

**per-review 退出判据**:

| 审 | 完成判据(覆盖 + 怎么验) | 第三态 |
|---|---|---|
| ①设计 | 两轴过 + 方向级五问明答 + 无 Critical;验=grep 仓库 | 方向疑 / 缺输入 |
| ②计划 | 两轴过 + issue↔plan 全覆盖 + 引用符号 grep 得到 + 无 Critical | 方向疑 / blocked |
| ③落地 | 全 pack committed + 跨 plan 合同兑现(机器核) | 合同根上错→升级 |
| ④final | 意图清单逐条坐实 + 跨 plan 合同真接上 + 两基线过 + 无 Critical;验=真跑测试/读大 diff | 回流落地(上限1)/ 发布风险→人 |

**防过早完工**:覆盖清单客观项由看守/脚本机器核,没全绿不让出 pass;语义项每条 finding 引 `file:line` 原文,引不出=降置信。

---

## 7. 骨架空跑断言(先空跑,再装真内容)

**落地 loop**(`codex-worker dispatch` 用 **fake codex** stub,见 `test_codex_worker.sh`):
- dispatch 组对 prompt 铁律(严防过度设计 / TDD / Pack N.M / 禁改 docs)+ codex 参数(`-C <wt>` / `--sandbox workspace-write` / `--add-dir`)+ 抓 session;`resume` 走 `codex exec resume`。
- 主线程 verify 后 `mmw loop step done`;`exit-check` steps 全 done 才放行(防过早完工)。
- 软停随 attendance 变(attended 停问 / afk 自决+留 decisions);冒泡停下抛主线程。
- merge/deploy 被 PreToolUse 拦,要 `release_approval` 才放。
- small-change 路径:主线程就地做,不派 Codex。

**审核 loop**:
- 主线程 / 协调帮手抽覆盖清单;`checklist` 没全 covered 不让出 pass。
- `review.sh start` 按阶段映射 kind + angle、init loop、出协调帮手 brief(断言见 `test_review.sh`)。
- 轮上限到顶→转第三态。
- ③合同门:全 pack committed + 合同存在 → 过;缺→回落地。

---

## 8. 落地依据(设计取舍出处)

载体能力(Codex `codex exec`/`exec resume`/`--output-schema`/sandbox、Claude subagent SendMessage/SubagentStop/不能问用户)均为实测/官方文档核实;退出三件套、副作用隔离(每步一提交→续接不重做)、风险分级、防过早完工 取自业界成熟做法 + 旧 plugin 实测取舍。详见 OVERVIEW §10。
