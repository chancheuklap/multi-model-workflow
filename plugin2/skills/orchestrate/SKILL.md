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
| 新想法/功能(清晰或模糊),要一起设计 | `new-design` | 想方案 → 拆计划 → 落地 → 验收 → 收尾 |
| 反馈/真机发现要优化,要先查清现状 | `optimize` | 查清 → 想方案 → 拆计划 → 落地 → 验收 → 收尾 |
| bug/报错/regression,根因不明 | `bug` | 查清 → 落地(修) → 验收 → 收尾 |
| 多个并行 worktree 要合并 | (merge,不开 worktree) | 见下 merge |

新设计和优化是同一主干,只是优化默认多开"查清"。判不准就问一句收窄(一次只问一个)。概念/事实问题直接答,不进 orchestrate。

## Step 2 · 准备(机器一条命令)

### small-change / new-design / optimize / bug —— 建 worktree

1. **起名**:从对话主题提一个人类可读、切题的 slug,格式 `YYYY-MM-DD-<theme>`(kebab,如 `2026-06-28-phone-login`)。这个名贯穿 worktree / 分支 / docs 目录,你要在 VSCode 里认得出。**向用户确认一次**(可同时让他改名)。

2. **一条命令建好**(从本地最新 HEAD 分叉,scaffold docs,写 manifest):
   ```bash
   bash "${SCRIPTS}/prepare.sh" new --scenario <small-change|new-design|optimize|bug> --slug <slug> --title "<人类可读标题>"
   ```
   回执给出 `worktree_path`。prepare 据预设把开着的阶段序列固化进进度记录(`phases`)。

3. **进 worktree**(只有这步能切会话 cwd,脚本切不了):
   ```
   EnterWorktree({ path: "<回执里的 worktree_path>" })
   ```

4. 进入对应场景的第一阶段(见上表)。产出文档按 write-design-doc 布局:设计 `docs/design/<slug>.md`、issue `docs/issues/<slug>/`、领域文档项目级 `docs/context/`+CONTEXT-MAP(跨任务共享);全是交付物,提交进分支。临时状态落 `.claude/multi-model-workflow/`(随 worktree 删除消失)。

### merge —— 不开 worktree

`git worktree list` 列全队 → 逐个读 `<wt>/.claude/multi-model-workflow/task.json` 拿各任务身份与状态 → 进 merge 流程(待建)。

## 阶段内容(从旧/独立系统逐步忠实搬运)

进到某阶段,按该阶段方法论干活。已搬:

- **想方案 / design** → `Skill({ skill: "write-design-doc" })` —— 主线程跑(跟用户讨论、写设计文档),做完按下方 handoff 交还。

其余阶段(查清 / 拆计划 / 落地 / 验收 / 收尾)内容待搬。

## Step 3 · 推进(进 worktree 之后的自循环)

进入某场景后,每个阶段(或派出去的帮手)干完,**只调一条命令交接 + 推进**:

```bash
bash "${SCRIPTS}/flow.sh" handoff --conclusion <结论词> [--produced <产出文件>]...
```

- **结论词**是统一一套(`pass` / `needs-repair` / `needs-redirection` / `needs-context` / `blocked`),选哪个是你的判断(灵活);选完命令查 `routes.json` 算出下一步、写进度档、回执 `NEXT_ACTION` / `NEXT_PHASE` / `STATUS`。你照回执走,**不自己猜下一步、不手写状态**。
- 缺结论或词非法 → 命令当场拦(fail-closed),不让带残缺往下走。
- 调查中挖到 bug / 旁路优化,别 out-of-scope,登记成关联子任务,主流程继续:
  ```bash
  bash "${SCRIPTS}/flow.sh" spinoff --tag <bug|optimize|out-of-scope|needs-evaluation> --finding "<一句话>"
  ```
- 返工/掉头有次数上限,命令计数强制,到顶自动转 `blocked` 上报,绝不无限往返。
- `STATUS=ready-to-close` → 末阶段过,回主仓库 `prepare.sh cleanup --slug <slug>` 收尾。

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
