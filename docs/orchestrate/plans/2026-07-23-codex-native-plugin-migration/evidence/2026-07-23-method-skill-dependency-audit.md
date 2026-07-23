# 三镜像与外部 Skill 边界核验

## 范围

- 日期：2026-07-23。
- 基线：`main`
  `2efefbe1668cf108ab63a85cd639da067c3c76dd`。
- 只读当前 `plugin/`、`droid-plugin/`、`pi-plugin/` 源码与 references。
- 不使用历史迁移文档判断现状。

## 三份 Plugin 自带 Skill 数量

实际目录：

```text
plugin/skills/
droid-plugin/skills/
pi-plugin/skills/
```

三份都只有同样五个 MMW skills：

```text
orchestrate
release-flow
worktree-build
worktree-plan
worktree-review
```

三份都没有把 `tdd`、`codebase-design`、`diagnosing-bugs`、
`domain-modeling`、`prototype`、`grilling` 或 `to-tickets` 放入自己的
`skills/`。

## 外部依赖是当前正式设计

三份 `flow.sh` 都有同一个 `mmw_warn_ext_skills`：

| 镜像 | 主线程 skill 根 | 工人 skill 根 |
| --- | --- | --- |
| Claude | `~/.claude/skills` | `~/.agents/skills` |
| Droid | `~/.factory/skills` | `~/.factory/skills` |
| pi | `~/.agents/skills` | `~/.agents/skills` |

三份主线程集合相同：

```text
tdd
codebase-design
diagnosing-bugs
domain-modeling
prototype
grilling
to-tickets
triage
improve-codebase-architecture
```

三份工人集合相同：

```text
tdd
codebase-design
to-tickets
```

检查是 warning，不是 vendoring 或自动安装。缺装时打印缺失名字和现有
`npx skills@latest add mattpocock/skills` 提示；具体 reference 再决定当前路径是
停下报告还是允许跳过。

## References 的职责边界

当前 references 一致采用以下模式：

- MMW reference 决定在什么阶段调用哪个外部 skill。
- 外部 skill 保存自己的通用方法。
- MMW reference 只规定 MMW 需要的输入、产物落点、handoff 和适配。

例子：

- `to-issue-skeleton.md` 明确写“委托外部 `to-tickets` skill，方法论单源，不在此
  复制”。
- `prototype-mockup.md` 调用外部 `prototype`，然后规定 MMW 的产物要放进设计
  目录并作为下游输入。
- `worktree-build` 调用已装 `tdd`，同时由 MMW 自己规定 Pack、commit 和 docs
  边界。
- investigate topic 的 `skill` 字段让工人先读对应外部 skill，再执行当前 topic。

这说明“外部方法 + MMW 编排适配”就是现有设计，不是迁移缺口。

## Codex 的对应实现

Codex 官方 skill 搜索目录包含 `~/.agents/skills`。因此 Codex 镜像直接沿用 pi 的
依赖根：

```text
main_dir="$HOME/.agents/skills"
worker_dir="$HOME/.agents/skills"
```

Codex plugin 只分发自己的五个 MMW skills 和为了替代 command/prompt surface 的
11 个薄控制 wrappers。

不实施：

- vendor 外部 skills。
- 复制外部 skill 正文到 MMW references。
- 修改外部 skill 行为以适配 MMW。
- 锁定或接管外部 skill 版本。
- 建立 method-contract 子系统。
- 把外部 skills 伪装成 MMW 自带能力。

Codex 安装验收要同时证明两件事：

1. MMW plugin 自己能被正确安装和加载。
2. `mmw where` 能准确报告外部 skill preflight；依赖齐全时沿现有 references
   正常调用。
