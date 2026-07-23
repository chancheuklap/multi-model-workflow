# Codex 方法 Skill 依赖审计

## 审计范围

- 日期：2026-07-23
- 当前仓库基线：`main`
  `2efefbe1668cf108ab63a85cd639da067c3c76dd`
- 真相源：当前 `plugin/skills/**`、Codex 官方
  [Build plugins](https://learn.chatgpt.com/docs/build-plugins) 与
  [Build skills](https://learn.chatgpt.com/docs/build-skills)
- 不使用历史迁移文档判断现状。

## 当前源码事实

当前 Claude plugin 把通用方法 skill 当作阶段内部动作调用，并没有把它们当作
独立业务能力：

| 调用位置 | 当前外部依赖 | MMW 已经写明的真实行为 |
| --- | --- | --- |
| `plugin/skills/orchestrate/references/investigate.md:13` | `codebase-design`、`diagnosing-bugs` | 查模块边界、数据流、seam 或根因；一 topic 一工人；主线程亲验 `file:line` |
| `plugin/skills/orchestrate/references/scenario/bug.md:7` | `diagnosing-bugs` | 复现、隔离、定位根因，窄问题由主线程直接查 |
| `plugin/skills/orchestrate/references/wayfind.md:22` | `grilling` | 沿 frontier 一次解决一个决策，每问附推荐，决策不下放 |
| `plugin/skills/orchestrate/references/propose.md:33` | `grilling` | 沿依赖顺序拆开收费、数据归属、上下架等业务决策 |
| `plugin/skills/orchestrate/references/design/discussion.md:31-117` | `domain-modeling`、`grilling`、`diagnosing-bugs`、`codebase-design` | 领域文档落点、访谈纪律、bug 澄清、模块边界和 Domain Alignment 已在同一 reference 中定义 |
| `plugin/skills/orchestrate/references/design/prototype-mockup.md:7-19` | `prototype` | 状态模型必须可运行并覆盖成功、失败、空、并发和回滚；代码作为正式实现种子随设计提交 |
| `plugin/skills/orchestrate/references/design/to-issue-skeleton.md:7-17` | `to-tickets` | tracer-bullet 垂直切片，宽重构走 expand–migrate–contract，并使用 MMW issue 模板 |
| `plugin/skills/worktree-plan/SKILL.md:31-32` | `codebase-design`、`to-tickets` | 亲验真实路径/类型/函数，按当前大 issue 拆可独立验证的 Small issues |
| `plugin/skills/worktree-build/SKILL.md:29` | `tdd` | 失败测试、确认失败、最小实现、确认通过、每 Pack 提交 |

`prototype-mockup.md` 还明确覆盖上游 prototype 的 throwaway 默认，把原型改成要进
Git 的实现种子。完整 vendoring 上游 skill 会让同一个阶段同时存在两套相反语义。

当前 references 还调用 `triage`、`improve-codebase-architecture`、
`frontend-design` 和 `impeccable`。它们同样是阶段方法或质量检查，不应成为 Codex
核心路径的个人 skill/plugin 依赖。真实浏览器、图片生成、远程构建和产品 API
属于工具或环境能力，保留按路径 preflight。

## Codex 官方能力边界

Codex plugin manifest 可以分发本 plugin 自己的 skills、hooks、apps 和 MCP
配置。官方 `Build skills` 文档说明：

- plugin 可以包含一个或多个 skills；
- skill 通过描述被显式或隐式激活，会占用初始 skill 列表预算；
- `agents/openai.yaml` 的 `dependencies` 当前只声明工具依赖；
- 官方没有提供“本 plugin 安装时再解析并安装另一组 method skills”的依赖合同。

因此可行路径只有三类：依赖用户个人目录、把通用方法 skills 一并公开分发，或让
MMW 自己的阶段 reference 闭合行为。前两类都会增加安装面或公开入口；第三类直接
对应现有 workflow 的真实职责。

## 采用的迁移结构

Codex plugin 只暴露：

- `orchestrate`
- `release-flow`
- `worktree-plan`
- `worktree-build`
- `worktree-review`
- 11 个保持用户控制习惯的 command-equivalent skills

方法行为按以下方式进入这些现有入口：

| 行为 | 写入位置 | 验收 |
| --- | --- | --- |
| 仓库边界和根因取证 | investigate reference、bug scenario | 多 topic 调查返回真实 locator；主线程亲验；bug E2E 产出回归测试 |
| 决策访谈 | wayfind、propose、design references | 一次只问一个 blocking decision，每问给推荐，业务取舍由用户确认 |
| 领域对齐 | design discussion | 每个确认术语、对象、状态和跨 context 关系写入规定落点 |
| 状态原型 | prototype/mockup reference | 原型可运行，非法转移被拒，产物进入设计目录并被 plan/build 消费 |
| 垂直切片 | to-issue 与 worktree-plan | issue 可端到端独立验收；宽重构形成 expand、migrate、contract 依赖链 |
| TDD | build coordinator、worktree-build、tests reference | RED 命令确实失败，GREEN 命令确实通过，随后按 Pack 提交 |

相同文字确实要进入两份以上完整 references 时，沿用
`codex-plugin/build/fragments/*.md` 在构建期注入，不新增 method 子系统。运行时
不让 agent 跳读 fragment；每条阶段路径仍只读一份完整 reference。角色不同的行为
直接写进该角色 reference，不再造七个同义 reference。

## 删除的实现

- 不 vendor 七个通用方法 skills。
- 不锁上游 method commit。
- 不为未复制的上游正文增加第三方声明。
- 不做 method skill bootstrap、依赖安装器或个人目录探测。
- 不用“七个 skills 可发现”代替功能验收。
- 不允许 Codex 核心 references 指令 agent 调用 ambient method skill/plugin。

清洁 profile 的验收对象改为真实用户行为：根因调查、决策访谈、领域更新、状态
原型、垂直切片和 RED/GREEN TDD 均能只靠 MMW plugin 完成。
