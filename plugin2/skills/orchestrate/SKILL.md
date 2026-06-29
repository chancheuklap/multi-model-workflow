---
name: orchestrate
description: "开发工作流主入口。用户给出想法/功能/改造、报 bug、要优化、或要合并多个并行 worktree 时主动使用。入口只做两件事:断点恢复 + 选预设路由(LLM 当场判),随后把机械准备交给 prepare.sh。"
---

# Orchestrate · 入口

主线程入口。**只做两件事:断点恢复、路由。** 路由是 LLM 语义判断,不跑脚本、不读关键词表。机械准备(建 worktree、scaffold、写状态)全交给 `prepare.sh`,一条命令做完。

`${SKILL_DIR}` = 本 skill 目录;`${SCRIPTS}` = `${CLAUDE_PLUGIN_ROOT}/scripts`。

---

## Step 0 · 先试断点恢复

无脑先跑一次(无论在哪):

```bash
bash "${SCRIPTS}/prepare.sh" resume
```

- 输出 `MANAGED` + 一段 JSON → **当前 worktree 是个在管任务**。再跑一次 `bash "${SCRIPTS}/flow.sh" where` 拿精确位置(阶段/下标/计数/待办数),一句话告诉用户"你在 `<title>`,场景 `<scenario>`,阶段 `<phase>`",直接进该 phase 继续。**跳过 Step 1。**
- 输出 `UNMANAGED` → 当前不是在管任务(在主仓库,或 worktree 里没 manifest)→ 进 Step 1。

## Step 1 · 路由(LLM 判,零脚本)

只有一条主干流程:`查清 → 想方案 → 拆计划 → 落地 → 验收 → 收尾`(investigate / design / plan / build / verify / closing)。开口的差别**不是走不同流程,是默认开主干里的哪几个前置**。看对话判这是哪种开口,选一个预设:

| 你怎么开口 | 预设 `scenario` | 默认走的阶段(前置可中途翻开关) |
| --- | --- | --- |
| 明确的小改 | `small-change` | 落地 → 验收 → 收尾 |
| 新想法/功能 或 要优化改进(要设计) | `develop` | 查清 → 想方案 → 拆计划 → 落地 → 验收 → 收尾 |
| bug/报错/regression,根因不明 | `bug` | 查清 → 落地(修) → 验收 → 收尾 |
| 多个并行 worktree 要合并 | (merge,不开 worktree) | 见下 merge |

新想法和优化是同一条完整主干(`develop`),不分两个预设。判不准就问一句收窄(一次只问一个)。概念/事实问题直接答,不进 orchestrate。

## Step 2 · 准备(机器一条命令)

### small-change / develop / bug —— 建 worktree

1. **起名**:从对话主题提一个人类可读、切题的 slug,格式 `YYYY-MM-DD-<theme>`(kebab,如 `2026-06-28-phone-login`)。这个名贯穿 worktree / 分支 / docs 目录,你要在 VSCode 里认得出。**向用户确认一次**(可同时让他改名)。

2. **一条命令建好**(从本地最新 HEAD 分叉,scaffold docs,写 manifest):
   ```bash
   bash "${SCRIPTS}/prepare.sh" new --scenario <small-change|develop|bug> --slug <slug> --title "<人类可读标题>"
   ```
   回执给出 `worktree_path`。prepare 据预设把开着的阶段序列固化进进度记录(`phases`)。

3. **进 worktree**(只有这步能切会话 cwd,脚本切不了):
   ```
   EnterWorktree({ path: "<回执里的 worktree_path>" })
   ```

4. 进 worktree 后,按下面**阶段运行契约**逐阶段推进(第一阶段见路由表)。文档产出提交进分支(设计 `docs/design/`、issue `docs/issues/`、领域 `docs/context/`);临时状态落 `.claude/multi-model-workflow/`(随 worktree 删)。

### merge —— 不开 worktree

`git worktree list` 列全队 → 逐个读 `<wt>/.claude/multi-model-workflow/task.json` 拿各任务身份与状态 → 进 merge 流程(待建)。

## 阶段运行契约(进 worktree 后的主循环)

**进 worktree 后,你对每个阶段都做同样 4 个动作。** 阶段之间唯一变的是「干」用哪套方法论;进 / 钉 / 交完全一样。这是整条 run 的骨架——别给某个阶段另搞一套流程。

| 动作 | 做什么 | 命令 / 机制 |
|---|---|---|
| **① 进** | `where` 告诉你在哪阶段、在不在审闸、上阶段钉了什么产出(`prev_outputs` 照单读,不自己找);按当前阶段查下表加载该阶段指南 | `bash "${SCRIPTS}/flow.sh" where` |
| **② 干** | 跑该阶段方法论(唯一因阶段而异)。读 `prev_outputs` 当输入 | 见下「阶段 → 加载」表 |
| **③ 钉** | 把本阶段产出钉进接力单,下阶段照单读 | handoff 的 `--produced` |
| **④ 交** | 给一个结论词,引擎算下一步、写进度、回执;你照回执走,**不自己猜下一步、不手写状态** | `bash "${SCRIPTS}/flow.sh" handoff` |

**② 干 —— 阶段 → 加载该阶段指南:**

| 阶段 | 加载 | 谁跑 |
|---|---|---|
| investigate(查清) | `${SKILL_DIR}/references/investigate.md` | 主线程跑自建 Workflow |
| design(想方案) | `Skill({ skill: "write-design-doc" })` | 主线程跟用户讨论 |
| plan(拆计划) | `Skill({ skill: "write-plan-doc" })` | 主线程编排 + 派 plan-writer |
| build(落地) | `${SKILL_DIR}/references/build.md` | 主线程派帮手跑落地 loop |
| verify(验收=④终审) | `${SKILL_DIR}/references/review.md`(final) | 主线程起终审 loop |
| 审闸(`NEXT_ACTION=review`) | `${SKILL_DIR}/references/review.md` | 主线程起审 loop + 派 Codex 协调帮手 |

> build / plan / verify / merge 待接满,接法照本契约(进/钉/交不变,只填各自的「干」)。

**③ 钉 + ④ 交 —— 一条 handoff:**

```bash
bash "${SCRIPTS}/flow.sh" handoff --conclusion <结论词> [--produced <本阶段产出路径>]...
```

- **结论词**统一五选一(`pass` / `needs-repair` / `needs-redirection` / `needs-context` / `blocked`),选哪个是你的判断;选完引擎查 `routes.json` 算 `NEXT_ACTION` / `NEXT_PHASE` / `STATUS`。缺结论或词非法当场拦(fail-closed)。
- **`--produced` 必带本阶段的承重产出**(investigate→现状报告;design→设计文档;plan→plan 目录;build→提交范围;verify→终审报告)——它钉进接力单,下阶段靠它接,不靠"自己找"。
- **回执 `NEXT_ACTION=review`**(design/plan 产物过 → 进审闸,见 `REVIEW_STAGE`):别 advance,先按 `references/review.md` 跑该阶段审 loop,审完再 handoff verdict——`pass` 才进下一阶段,`needs-repair` 回本阶段返工。
- 中途挖到 bug / 旁路优化 → 登记关联子任务,主流程不动:`bash "${SCRIPTS}/flow.sh" spinoff --tag <bug|optimize|out-of-scope|needs-evaluation> --finding "<一句话>"`。
- 返工/掉头有上限,命令计数强制,到顶自动转 `blocked`,绝不无限往返。
- `STATUS=ready-to-close` → 末阶段过,回主仓库 cleanup 收尾。

**断点续传**:任何时候 `flow.sh where` + 接力单就够你接着跑——进度、游标、各阶段产出全在 manifest,不靠会话记忆。

## 收尾 · 合并后删干净

任务分支已 merge 进主线后,worktree 连同里面的临时状态一起删:

```bash
bash "${SCRIPTS}/prepare.sh" cleanup --slug <slug>   # 回主仓库执行
```

worktree 在**使用期**持久(可跨天,别中途删);**合并后**才 cleanup,worktree + 分支 + `.claude/` 临时状态一并清除。

---

## 边界

- 入口不写设计/计划/代码、不派 worker、不做 review —— 那些是各 phase 的活。
- 路由是 LLM 判断,不要把它脚本化。准备是机器活,不要让模型手搓 JSON / markdown。
- worktree 一律从本地最新 HEAD 建;建完必 `EnterWorktree`;命名必人类可读切题。
