# 怎么写 agent brief

agent brief 是一张 issue 或 PR 转到 `ready-for-agent` 时贴上去的一条结构化评论。它是无人值守的 agent 干活时依据的权威规格。原始正文和讨论是背景，agent brief 才是合同。

brief 说的是**这个 agent 该做什么**。两个面都适用：对一张 issue，那是从零把改动做出来；对一个 PR，那是*在已有的 diff 上*还剩什么要做——补完、堵住缺口、回应审查意见。原则一样，下面的 PR 例子展示差别在哪。

## 原则

### 经得起放置，比写得精确重要

这张 issue 可能在 `ready-for-agent` 上停几天甚至几周，其间代码库会变。brief 要写成即使文件被改名、被挪走、被重构，它依然有用。

- **要**描述接口、类型和行为合同
- **要**点出 agent 该去找、该去改的具体类型、函数签名或配置形状
- **不要**引用文件路径——它们会过期
- **不要**引用行号
- **不要**假定当前的实现结构还会是那样

### 说行为，不说步骤

描述系统**应该做到什么**，不是**怎么实现**。agent 会重新探索代码库，自己做实现决定。

- **好**：「`SkillConfig` 类型应当接受一个可选的 `schedule` 字段，类型是 `CronExpression`」
- **坏**：「打开 src/types/skill.ts，在第 42 行加一个 schedule 字段」
- **好**：「用户不带参数跑 `/mmw-triage` 时，应当看到一份需要处理的 issue 摘要」
- **坏**：「在主处理函数里加一个 switch」

### 验收标准要完整

agent 需要知道什么时候算做完。每一份 agent brief 都必须有具体的、可测的验收标准，每一条都能独立验证。

- **好**：「跑 `gh issue list --label needs-triage` 返回的是已经过初步分类的 issue」
- **坏**：「分诊应当正常工作」

### 范围边界要明说

写清楚什么不在范围内。这挡住 agent 镀金，也挡住它对相邻功能做假设。

### 点名测试 seam

工人没有人可以商量 seam，所以由 brief 自己点名：回归测试坐在哪一层，断言什么行为。用行为描述——「一个穿过公开分诊命令的集成测试，断言写进 tracker 的那个标签」——不要写成文件路径。

点不出一个正确的 seam 时，在 brief 里说明，并把这张 issue 改判 `ready-for-human`。seam 不写明，工人就会自己发明一个，而一个发明出来的 seam 上的测试给的是虚假信心。

## 模板

字段名保持英文，它们是结构键，工人按名字找；内容用中文写。

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

### 好的 agent brief（bug）

```markdown
## Agent Brief

**Category:** bug
**Summary:** 技能描述截断时从词中间断开，输出是坏的

**Current behavior:**
技能描述超过 1024 个字符时，不管词边界在哪，一律在第 1024 个字符处截断。
截出来的描述会停在半个词上（例如「Use when the user wants to confi」）。

**Desired behavior:**
截断应当断在 1024 字符之前的最后一个词边界上，并追加「...」表示被截断了。

**Key interfaces:**
- `SkillMetadata` 类型的 `description` 字段 —— 类型不用改，
  但填充它的那段校验与处理逻辑要尊重词边界
- 任何读取 SKILL.md frontmatter 并取出 description 的函数

**Test seam:**
一个直接测截断函数本身的单元测试，对刚好不到、正好等于、远超上限的三种
描述断言返回的字符串。

**Acceptance criteria:**
- [ ] 不到 1024 字符的描述原样不动
- [ ] 超过 1024 字符的描述断在 1024 之前的最后一个词边界上
- [ ] 被截断的描述以「...」结尾
- [ ] 含「...」在内的总长度不超过 1024

**Out of scope:**
- 改动 1024 这个上限本身
- 支持多行描述
```

### 好的 agent brief（enhancement）

```markdown
## Agent Brief

**Category:** enhancement
**Summary:** 加上 `.out-of-scope/` 目录，用来记住被否掉的功能需求

**Current behavior:**
一个功能需求被否掉时，那张 issue 打上 `wontfix` 标签、留一条评论就关了。
这个决定和它的理由没有留下持久记录。以后再来相似的需求，维护者只能凭
记忆或者去翻当初的讨论。

**Desired behavior:**
被否掉的功能需求应当记进 `.out-of-scope/<概念>.md`，写下决定、理由，以及
所有提过这个需求的 issue 链接。分诊新 issue 时要查这些文件有没有匹配上的。

**Key interfaces:**
- `.out-of-scope/` 下的 Markdown 格式 —— 每份文件有一个 `# 概念名` 标题、
  一行 `**Decision:**`、一行 `**Reason:**`，以及一份带 issue 链接的
  `**Prior requests:**` 清单
- 分诊流程应当在早期就读完所有 `.out-of-scope/*.md`，按概念相似度
  跟进来的 issue 比对

**Test seam:**
一个走 wontfix 路径的集成测试，对着一个临时目录：关掉一个功能需求，
然后断言产生的那份 `.out-of-scope/` 文件。只测文件写入函数的单元测试
会漏掉「追加还是新建」这个分支。

**Acceptance criteria:**
- [ ] 以 wontfix 关掉一个功能需求会新建或更新 `.out-of-scope/` 下的文件
- [ ] 那份文件含决定、理由，以及指向这张已关闭 issue 的链接
- [ ] 已经存在匹配的 `.out-of-scope/` 文件时，新 issue 追加进它的
      「Prior requests」清单，而不是新建一份重复的
- [ ] 分诊过程中，已有的 `.out-of-scope/` 文件会被查阅；新 issue 跟
      某次否决匹配上时把它呈现出来

**Out of scope:**
- 自动匹配（由人确认匹配）
- 重开先前被否掉的功能
- bug 报告（只有 enhancement 的否决才进 `.out-of-scope/`）
```

### 好的 agent brief（PR）

对一个 PR，「Current behavior」描述的是这份 diff 现在的状态，brief 要求 agent 把它补完或修好，不是从零做起。

```markdown
## Agent Brief

**Category:** enhancement
**Summary:** 把贡献者提交的 `triage list --json` 输出选项补完

**Current behavior:**
这个 PR 加了一个 `--json` 选项，把 issue 清单序列化成 JSON。顺利路径能跑，
diff 也符合项目的命令结构。还差两处：错误仍然按人读的文本打印（不是 JSON），
以及这个新选项没有任何测试覆盖。

**Desired behavior:**
带 `--json` 时，所有输出——包括错误——都是 stdout 上格式良好的 JSON，
命令的退出码不变。不带这个选项时，原有的人读输出原样不动。

**Key interfaces:**
- 带 `--json` 时，命令的错误路径应当输出 `{ "error": string }`，
  而不是纯文本错误
- 复用这个 PR 已经加进来的那个序列化器，不要再引入第二个

**Test seam:**
一个命令行层面的测试，对着一个打了桩的 tracker 调 `triage list --json`，
断言解析后的 stdout 和退出码——成功和失败各测一次。

**Acceptance criteria:**
- [ ] `triage list --json` 在成功和失败两种情形下都输出合法 JSON
- [ ] 退出码与不带 `--json` 时一致
- [ ] 有测试覆盖 `--json` 的成功输出和一种错误情形
- [ ] 默认（不带 `--json`）的输出逐字节不变

**Out of scope:**
- 给别的命令加 `--json`
- 改动这个 PR 已经定下的成功响应的 JSON 形状
```

### 坏的 agent brief

```markdown
## Agent Brief

**Summary:** 修一下分诊的 bug

**What to do:**
分诊那块坏了。看一下主文件把它修好。
150 行附近那个函数有问题。

**Files to change:**
- src/mmw-triage/handler.ts（第 150 行）
- src/types.ts（第 42 行）
```

它坏在这几处：

- 没有 category
- 描述含糊（「分诊那块坏了」）
- 引用了会过期的文件路径和行号
- 没有验收标准
- 没有范围边界
- 没有描述现状与目标状态
- 没有测试 seam，无头工人只能自己发明一个
