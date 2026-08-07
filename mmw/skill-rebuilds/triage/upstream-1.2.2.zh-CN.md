# `triage` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/SKILL.md:1-5 -->

```yaml
---
name: triage
description: 让 issue 和外部 PR 经过由分诊角色组成的状态机：分类、验证、需要时 grilling，并编写可供 agent 使用的 agent brief。
disable-model-invocation: true
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/SKILL.md:7-23 -->

# Triage

让项目 issue tracker 上的 issue 经过一个由分诊角色组成的小型状态机。

如果本仓库把外部 pull request 当作请求入口，参见 issue tracker 配置，triage 也会处理它们：**PR 是一张附带代码的 issue**。它使用相同的角色、相同的状态和相同的状态机；少数差异会在下方标为“对于 PR”。根据 tracker 配置，把单独的 `#42` 解析为 issue 或 PR。

Triage 期间发布到 issue tracker 的每条评论或 issue 都**必须**以下方免责声明开头：

```
> *本内容由 AI 在 triage 期间生成。*
```

## Reference 文档

- [AGENT-BRIEF.md](AGENT-BRIEF.md)——如何编写持久的 agent brief
- [OUT-OF-SCOPE.md](OUT-OF-SCOPE.md)——`.out-of-scope/` 知识库如何运行

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/SKILL.md:24-45 -->

## 角色

两种**类别角色**：

- `bug`——某项内容损坏
- `enhancement`——新功能或改进

五种**状态角色**：

- `needs-triage`——维护者需要评估
- `needs-info`——等待报告者提供更多信息
- `ready-for-agent`——已经完全明确，可交给 AFK agent
- `ready-for-human`——需要人工实现
- `wontfix`——不会执行

对于 PR，相同状态要结合附带的代码来解读：`ready-for-agent` 表示已经附上 agent brief，agent 应该继续处理该 diff；`ready-for-human` 表示已经可以由人类合并。

每张已分诊的 issue 都应该恰好带一种类别角色和一种状态角色。如果状态角色冲突，标记问题，并在执行其他任何操作前询问维护者。

这些是规范角色名；issue tracker 实际使用的标签字符串可能不同。映射应该已经提供给你；如果没有，运行 `/setup-matt-pocock-skills`。

状态转换：没有标签的 issue 通常先进入 `needs-triage`；随后进入 `needs-info`、`ready-for-agent`、`ready-for-human` 或 `wontfix`。报告者回复后，`needs-info` 返回 `needs-triage`。维护者可以随时覆盖状态；标记看起来异常的转换，并在继续前询问。

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/SKILL.md:47-66 -->

## 调用方式

维护者调用 `/triage`，并用自然语言说明需求。解释请求并执行。例子：

- “向我展示任何需要我关注的内容”
- “我们看看 #42”，可以是 issue 或 PR
- “把 #42 移到 ready-for-agent”
- “有哪些内容已经可以供 agent 认领？”

## 展示需要关注的内容

查询 issue tracker，并按最旧在前的顺序展示三个分组：

1. **没有标签**——从未分诊。
2. **`needs-triage`**——正在评估。
3. **`needs-info`，而且报告者在上一份 triage note 后有新活动**——需要重新评估。

PR 在范围内时，把外部 PR 加入这些分组，并为每一行加上 `[PR]` 或 `[issue]` 标记。发现阶段只呈现**外部** PR；tracker 配置定义谁算外部。协作者正在进行的 PR 不属于分诊工作。该筛选只用于发现；无论作者是谁，明确点名的 PR 始终要分诊。

展示数量，并为每项写一行摘要。让维护者选择。

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/SKILL.md:68-90 -->

## Triage 指定 issue 或 PR

1. **收集上下文。** 读取完整 issue 或 PR，包括正文、评论、标签、作者、日期；对于 PR 还要读取 diff。解析任何先前的分诊记录，避免再次询问已经解决的问题。使用项目领域术语表探索代码库，并遵守相关区域的 ADR。针对代码库运行两项检查：(a) **重复性**——按照领域概念搜索请求行为的现有实现，不能只按请求原话搜索，并报告查找位置。如果已经存在，就按第 5 步处理为“已经实现”的 `wontfix`。(b) **先前否决**——读取 `.out-of-scope/*.md`，并呈现与当前请求相似的项目。

2. **提出建议。** 告诉维护者你建议的类别和状态及理由，再附上与请求相关的简短代码库摘要，包括是否已经实现。等待指示。

3. **验证主张。** 任何 grilling 前，检查主张是否成立。对于 bug，按照报告者步骤复现。对于 PR，确认 diff 实现了它声称的内容：checkout，并运行相关测试或命令。报告结果：已确认并附代码路径、失败，或细节不足；细节不足是强烈的 `needs-info` 信号。经过确认的验证会产生强得多的 agent brief。

4. **Grill，如果需要。** 如果请求需要进一步明确，同时运行 `/grilling` 和 `/domain-modeling` 技能；每轮提出一组问题，使请求形成明确形态，同时明确领域术语，并在决定落定时就地更新 `CONTEXT.md` 或 ADR。

5. **应用结果：**
   - `ready-for-agent`——发布一条 agent brief 评论，参见 [AGENT-BRIEF.md](AGENT-BRIEF.md)。
   - `ready-for-human`——使用与 agent brief 相同的结构，但说明为何无法委托，例如判断、外部访问、设计决定或手动测试。
   - `needs-info`——发布 triage note，使用下方模板。
   - `wontfix`——关闭；评论根据**原因**决定：
     - **已经实现**——改动已存在于代码库。指出所在位置；**不要**写入 `.out-of-scope/`，该知识库用于被**否决**的请求，不用于已构建的请求。
     - **否决 bug**——礼貌说明，然后关闭。
     - **否决 enhancement**——写入 `.out-of-scope/`，从评论链接到该文件，然后关闭，参见 [OUT-OF-SCOPE.md](OUT-OF-SCOPE.md)。
   - `needs-triage`——应用该角色。如果已经有部分进展，可以选择发布评论。

## 快速覆盖状态

如果维护者说“把 #42 移到 ready-for-agent”，信任维护者，并直接应用该角色。确认即将执行的内容，包括角色改动、评论和是否关闭，然后执行。跳过 grilling。如果没有经过 grilling session 就移到 `ready-for-agent`，询问是否要编写 agent brief。

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/SKILL.md:92-112 -->

## Needs-info 模板

```markdown
## Triage Notes

**目前已经确定的内容：**

- 要点 1
- 要点 2

**仍然需要你提供的内容（@reporter）：**

- 问题 1
- 问题 2
```

把 grilling 期间解决的全部内容记录在“目前已经确定的内容”下，避免工作丢失。问题必须具体且可以执行，不能只写“请提供更多信息”。

## 恢复先前 session

如果 issue 或 PR 上存在先前 triage note，读取它们，检查报告者是否回答了任何未决问题，并在继续前展示更新后的情况。不要再次询问已经解决的问题。

## `AGENT-BRIEF.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/AGENT-BRIEF.md:1-39 -->

# 编写 Agent Brief

Agent brief 是 issue 或 PR 移到 `ready-for-agent` 时发布在 GitHub 上的一条结构化评论。它是 AFK agent 据此工作的权威 spec。原始正文和讨论属于上下文；agent brief 才是合同。

Agent brief 说明**agent 应该做什么**，并覆盖两种入口：对于 issue，是从零构建改动；对于 PR，是说明在**现有 diff**上还要完成什么，例如完成它、填补缺口、处理审查意见。两种情况使用相同原则；下方 PR 示例会展示差异。

## 原则

### 持久性优先于精确定位

Issue 可能在 `ready-for-agent` 停留数天或数周。期间代码库会改变。编写 agent brief 时，即使文件被重命名、移动或重构，它仍然有用。

- **要**描述接口、类型和行为合同
- **要**指出 agent 应寻找或修改的具体类型、函数签名或配置结构
- **不要**引用文件路径，因为会过期
- **不要**引用行号
- **不要**假定当前实现结构保持不变

### 描述行为，不描述步骤

描述系统应该**做什么**，不要描述**如何**实现。Agent 会重新探索代码库，并自己作出实现决定。

- **好：** “`SkillConfig` 类型应接受一个可选的 `schedule` 字段，类型为 `CronExpression`”
- **差：** “打开 `src/types/skill.ts`，在第 42 行增加 `schedule` 字段”
- **好：** “用户不带参数运行 `/triage` 时，应该看到需要关注的 issue 摘要”
- **差：** “在主 handler 函数中增加 switch 语句”

### 完整的验收判据

Agent 需要知道何时完成。每份 agent brief 都必须提供具体、可测试的验收判据。每项判据都应该能够独立验证。

- **好：** “运行 `gh issue list --label needs-triage` 会返回已经完成初始分类的 issue”
- **差：** “Triage 应该正确运行”

### 明确的范围边界

说明哪些内容不在范围内。这能防止 agent 过度打磨，或对相邻功能作出假设。

## 模板

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/AGENT-BRIEF.md:41-68 -->

```markdown
## Agent Brief

**Category:** bug / enhancement
**Summary:** 用一行说明需要发生什么

**Current behavior:**
说明当前会发生什么。对于 bug，这是损坏的行为。
对于 enhancement，这是功能建立其上的现状。

**Desired behavior:**
说明 agent 完成工作后应该发生什么。
具体说明边界情况和错误条件。

**Key interfaces:**
- `TypeName`——需要改变什么，以及原因
- `functionName()` 返回类型——当前返回什么，应该返回什么
- 配置结构——需要的任何新配置选项

**Acceptance criteria:**
- [ ] 具体且可测试的判据 1
- [ ] 具体且可测试的判据 2
- [ ] 具体且可测试的判据 3

**Out of scope:**
- 本 issue 不应改变或处理的内容
- 可能看起来相关，但实际独立的相邻功能
```

## 示例

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/AGENT-BRIEF.md:72-105 -->

### 良好 agent brief：bug

```markdown
## Agent Brief

**Category:** bug
**Summary:** 技能描述截断会在单词中间切断，产生损坏的输出

**Current behavior:**
技能描述超过 1024 个字符时，无论单词边界如何，都会在
第 1024 个字符处准确截断。这会产生从单词中间结束的描述，
例如 “Use when the user wants to confi”。

**Desired behavior:**
截断应该在第 1024 个字符前的最后一个单词边界处发生，
并追加 “...”，表明内容被截断。

**Key interfaces:**
- `SkillMetadata` 类型的 `description` 字段——不需要改变类型，
  但填充该字段的验证或处理逻辑需要尊重
  单词边界
- 读取 SKILL.md frontmatter 并提取描述的任何函数

**Acceptance criteria:**
- [ ] 少于 1024 个字符的描述保持不变
- [ ] 超过 1024 个字符的描述在第 1024 个字符前的最后一个
      单词边界处截断
- [ ] 截断后的描述以 “...” 结尾
- [ ] 包括 “...” 在内的总长度不超过 1024 个字符

**Out of scope:**
- 改变 1024 个字符的限制本身
- 支持多行描述
```

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/AGENT-BRIEF.md:107-146 -->

### 良好 agent brief：enhancement

```markdown
## Agent Brief

**Category:** enhancement
**Summary:** 增加 `.out-of-scope/` 目录支持，用于跟踪被否决的功能请求

**Current behavior:**
功能请求被否决时，issue 会带 `wontfix` 标签关闭，
并附上一条评论。没有持久记录保存该决定或理由。
未来出现相似请求时，维护者必须回忆或搜索
先前讨论。

**Desired behavior:**
被否决的功能请求应记录在 `.out-of-scope/<concept>.md`
文件中，保存决定、理由和所有请求该功能的 issue 链接。
triage 新 issue 时，应该检查这些文件
是否匹配。

**Key interfaces:**
- `.out-of-scope/` 中的 Markdown 文件格式——每份文件都应该有
  `# Concept Name` 标题、`**Decision:**` 行、`**Reason:**` 行，
  以及带 issue 链接的 `**Prior requests:**` 清单
- triage 工作流应该尽早读取所有 `.out-of-scope/*.md` 文件，
  并按照概念相似性匹配传入 issue

**Acceptance criteria:**
- [ ] 以 wontfix 关闭功能时，在 `.out-of-scope/` 创建或更新文件
- [ ] 文件包含决定、理由和已关闭 issue 的链接
- [ ] 如果匹配的 `.out-of-scope/` 文件已经存在，就把新 issue
      追加到它的 “Prior requests” 清单，不创建重复文件
- [ ] triage 期间检查现有 `.out-of-scope/` 文件，并在新 issue
      匹配先前否决时呈现

**Out of scope:**
- 自动匹配，由人类确认匹配
- 重新开启先前否决的功能
- Bug 报告，只有被否决的 enhancement 写入 `.out-of-scope/`
```

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/AGENT-BRIEF.md:148-183 -->

### 良好 agent brief：PR

对于 PR，“Current behavior”描述 diff 的状态；agent brief 要求 agent 完成或修复它，不是从零构建。

```markdown
## Agent Brief

**Category:** enhancement
**Summary:** 完成贡献者为 `triage list` 增加的 `--json` 输出标志位

**Current behavior:**
PR 增加了一个 `--json` 标志位，把 issue 清单序列化为 JSON。正常路径
能够运行，而且 diff 符合项目命令结构。仍有两个缺口：
错误仍然以人类文本打印，不是 JSON；新标志位
没有测试覆盖。

**Desired behavior:**
使用 `--json` 时，全部输出，包括错误，都应该成为 stdout 上格式正确的 JSON；
命令的退出码保持不变。没有该标志位时，现有的人类可读输出
保持不变。

**Key interfaces:**
- 命令的错误路径在 `--json` 下应该发出 `{ "error": string }`，
  不再发出纯文本错误
- 复用 PR 已经增加的序列化器；不要引入第二份

**Acceptance criteria:**
- [ ] `triage list --json` 在成功和错误两种情况都发出有效 JSON
- [ ] 退出码与非 JSON 命令相同
- [ ] 一项测试覆盖 `--json` 成功输出和一种错误情况
- [ ] 默认的非 JSON 输出逐字节保持不变

**Out of scope:**
- 为其他命令增加 `--json`
- 改变 PR 已经定义的成功载荷的 JSON 结构
```

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/AGENT-BRIEF.md:185-207 -->

### 不良 agent brief

```markdown
## Agent Brief

**Summary:** 修复 triage bug

**What to do:**
triage 的某项内容坏了。查看主文件并修复。
第 150 行附近的函数有问题。

**Files to change:**
- src/triage/handler.ts（第 150 行）
- src/types.ts（第 42 行）
```

这份 agent brief 不良，因为：
- 没有 category
- 描述含混，例如“triage 的某项内容坏了”
- 引用会过期的文件路径和行号
- 没有验收判据
- 没有范围边界
- 没有说明当前行为与目标行为

## `OUT-OF-SCOPE.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/OUT-OF-SCOPE.md:1-21 -->

# Out-of-Scope 知识库

仓库中的 `.out-of-scope/` 目录保存被否决功能请求的持久记录。它有两个目的：

1. **组织记忆**——记录一项功能被否决的原因，使 issue 关闭后不会丢失推理
2. **去重**——新 issue 与先前否决匹配时，本技能可以呈现先前决定，不必重新争论

## 目录结构

```
.out-of-scope/
├── dark-mode.md
├── plugin-system.md
└── graphql-api.md
```

每个**概念**一个文件，不是每张 issue 一个文件。请求同一内容的多张 issue 归入一个文件。

## 文件格式

文件应该使用轻松、易读的风格，更像一份简短设计文档，不像一条数据库记录。使用段落、代码样例和示例，使第一次接触该决定的人也能清楚理解推理，并觉得有用。

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/OUT-OF-SCOPE.md:23-54 -->

```markdown
# 深色模式

本项目不支持深色模式或面向用户的主题功能。

## 为什么不在范围内

渲染管线假定只有一套在
`ThemeConfig` 中定义的调色板。支持多套主题需要：

- 包裹整个组件树的主题 context provider
- 每个组件各自执行感知主题的样式解析
- 保存用户主题偏好的持久化层

这是一项重大的架构改动，与项目专注于内容创作的方向不符。
主题功能应该由嵌入或重新分发输出的下游
使用方处理。

```ts
// 当前 ThemeConfig interface 并非为运行时切换而设计：
interface ThemeConfig {
  colors: ColorPalette; // 单一调色板，在构建时解析
  fonts: FontStack;
}
```

## 先前请求

- #42 — “增加深色模式支持”
- #87 — “为可访问性提供夜间主题”
- #134 — “深色主题选项”
```

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/OUT-OF-SCOPE.md:56-68 -->

### 文件命名

为概念使用简短、有描述力的 kebab-case 名称，例如 `dark-mode.md`、`plugin-system.md`、`graphql-api.md`。名称应该足够容易辨认，使浏览目录的人无需打开文件就能理解被否决的内容。

### 编写理由

理由必须实质充分；不能只写“我们不想要”，而要说明原因。良好理由会引用：

- 项目范围或理念，例如“本项目专注于 X；主题功能属于下游关注事项”
- 技术约束，例如“支持这项内容需要 Y，而 Y 与我们的 Z 架构冲突”
- 战略决定，例如“我们选择 A 而不是 B，因为……”

理由应该持久。避免引用临时情况，例如“我们现在太忙”；这种情况不是真正否决，而是延期。

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/OUT-OF-SCOPE.md:70-88 -->

## 何时检查 `.out-of-scope/`

Triage 期间，也就是第 1 步“收集上下文”，读取 `.out-of-scope/` 中的全部文件。评估新 issue 时：

- 检查请求是否匹配现有 out-of-scope 概念
- 按概念相似性匹配，不按关键词；`night theme` 与 `dark-mode.md` 匹配
- 如果匹配，向维护者呈现：“这与 `.out-of-scope/dark-mode.md` 相似；我们以前因为 [理由] 否决了它。你现在仍然持相同看法吗？”

维护者可以：

- **确认**——把新 issue 加入现有文件的“先前请求”清单，然后关闭
- **重新考虑**——删除或更新 out-of-scope 文件，issue 进入正常 triage
- **不同意**——issue 相互关联但并不相同，继续正常 triage

## 何时写入 `.out-of-scope/`

只有一项 **enhancement**，不是 bug，被否决为 `wontfix` 时才写入。enhancement PR 与 issue 完全相同；被否决的 PR 记录在这里，使同一请求不会以新代码形式再次出现。

某项内容因为**已经实现**而以 `wontfix` 关闭时，**不要**写入。那是已经构建的功能，不是被否决的功能；记录在这里会用错误否决污染去重检查。关闭评论应改为指向该功能已经存在的位置。

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/OUT-OF-SCOPE.md:90-105 -->

流程如下：

1. 维护者决定一项功能请求不在范围内
2. 检查是否已经存在匹配的 `.out-of-scope/` 文件
3. 如果有，把新 issue 追加到“先前请求”清单
4. 如果没有，使用概念名称、决定、理由和第一项先前请求创建新文件
5. 在 issue 上发布评论，说明决定并提到 `.out-of-scope/` 文件
6. 带 `wontfix` 标签关闭 issue

## 更新或移除 out-of-scope 文件

如果维护者对先前否决的概念改变想法：

- 删除 `.out-of-scope/` 文件
- 本技能不需要重新开启旧 issue；它们是历史记录
- 触发重新考虑的新 issue 进入正常 triage

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/triage/agents/openai.yaml:1-5 -->

```yaml
interface:
  display_name: "Triage"
  short_description: "让 issue 经过 triage role"
policy:
  allow_implicit_invocation: false
```
