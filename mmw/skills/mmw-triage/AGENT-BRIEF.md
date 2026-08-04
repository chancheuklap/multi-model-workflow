# 怎么写 agent brief

agent brief 是一张 issue 或 PR 转到 `ready-for-agent` 时贴上去的一条结构化评论。它是 `worker` 实现这张 issue 或补完这份 PR 时，行为合同的唯一事实来源。原始正文和讨论只提供背景。

agent brief 说的是**这个 agent 该做什么**。两个面都适用：对一张 issue，那是从零把改动做出来；对一个 PR，那是*在已有的 diff 上*还剩什么要做——补完、堵住缺口、回应审查意见。原则一样，下面的 PR 例子展示差别在哪。

## 原则

### 经得起放置，比写得精确重要

一张 issue 可能在 `ready-for-agent` 里放上几天甚至几周，期间代码会继续变化。agent brief 要写成即使文件被改名、被挪走、被重构，它依然有用。

- **要**描述接口、类型和行为合同
- **要**点出 agent 该去找、该去改的具体类型、函数签名或配置形状
- **不要**引用文件路径——它们会过期
- **不要**引用行号
- **不要**假定当前的实现结构还会是那样

### 说行为，不说步骤

描述系统**应该做到什么**，不是**怎么实现**。

`worker` 会从当时的最新代码重新探索，并自行决定可逆的实现细节。agent brief 负责钉住行为合同，不替它写实施步骤。

- **好**：「`SkillConfig` 类型应当接受一个可选的 `schedule` 字段，类型是 `CronExpression`」
- **坏**：「打开 src/types/skill.ts，在第 42 行加一个 schedule 字段」
- **好**：「用户不带参数跑 `/mmw-triage` 时，应当看到一份需要处理的 issue 摘要」
- **坏**：「在主处理函数里加一个 switch」

### 验收标准要完整

agent 需要知道什么时候算做完。每一份 agent brief 都必须有具体的、可测的验收标准，每一条都能独立验证。

- **好**：「跑 `gh issue list --label needs-triage` 返回的是已经过初步分类的 issue」
- **坏**：「分诊应当正常工作」

### 范围边界要明说

写清楚什么不在范围内，防止 agent 扩大需求，或者替相邻功能补上未经确认的假设。

### 点名测试 seam

agent brief 自己点名：回归测试坐在哪一层，断言什么行为。用行为描述——「一个穿过公开分诊命令的集成测试，断言写进 tracker 的那个标签」——不要写成文件路径。

点不出一个正确的 seam 时，在 agent brief 里说明，并把这张 issue 改判 `ready-for-human`。

## 模板

字段名保持英文，它们是结构键，`worker` 按名字找；内容用中文写。

```markdown
## Agent Brief

**Category:** bug / enhancement
**Summary:** 一句话说清要发生什么

**Current behavior:**
描述现在会发生什么。对 bug 来说，这是坏掉的那个行为。
对 enhancement 来说，这是这个功能要长在上面的现状。

**Desired behavior:**
描述 agent 做完之后应当发生什么。
边界情形和错误情形要写具体。

**Key interfaces:**
- `TypeName` —— 要改什么、为什么
- `functionName()` 的返回类型 —— 现在返回什么，应该返回什么
- 配置形状 —— 需要哪些新的配置项

**Test seam:**
测试坐在哪一层、断言什么，用行为描述。

**Acceptance criteria:**
- [ ] 具体、可测的第 1 条
- [ ] 具体、可测的第 2 条
- [ ] 具体、可测的第 3 条

**Out of scope:**
- 这次**不该**改、不该碰的东西
- 看起来相关、其实是另一件事的相邻功能
```

## 例子

三份写得好的（bug、enhancement、PR）和一份写坏的，在 [examples.md](examples.md)。写之前照着你手上这一类看一份。
