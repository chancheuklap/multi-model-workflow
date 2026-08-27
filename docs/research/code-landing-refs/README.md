# code-landing-refs

代码落地前 / 中 / 后三阶段设计的外部参考资料，完整快照，供反复查阅。只读：不改、不安装、不运行里面的脚本。

丢弃了图片与二进制文件（logo、guide 插图），其余文件按原目录结构原样保留。

| 目录 | 来源 | 快照 | 一句话 |
| --- | --- | --- | --- |
| `mattpocock-implement-spec/` | mattpocock/skills `skills/in-progress/implement-spec/` | 6654f6b6 | frontier + worktree 实现者子代理 + merger 的 9 步骨架 |
| `ponytail/` | github.com/DietrichGebert/ponytail | 2ed6c52c | 注入 worker 的 YAGNI 规则梯子；规则正文在 `.openclaw/skills/ponytail/SKILL.md` 与 `AGENTS.md` |
| `unlazy/` | github.com/Leonxlnx/unlazy | da0b00a3 | 机器可检的验收账本 `GATES.md`（`CHECK:`/`EXPECT:`/`EVIDENCE:`）、`--reverify`、Stop hook；规范在 `references/gates.md`，模板在 `templates/` |
| `swarm-forge/` | github.com/unclebob/swarm-forge | 60e9280c | tmux 多角色流水线与文件收件箱交接；协议在 `swarmforge/handoff-protocol.md`，规则在 `swarmforge/constitution/articles/` |
| `pstack/` | github.com/cursor/plugins `pstack/` | 799151d9 | `skills/architect`、`skills/interrogate`、`skills/create-verification-skill`、`skills/poteto-mode/playbooks/`（brief 模板、验证阶梯、overnight 契约）；入门在 `docs/guide/` |
| `grok-bundled/` | 本机 Grok Build 1.0.5 内置技能 `~/.grok/bundled/skills/` 中与代码落地相关的 8 个 | grok 1.0.5 (5115b46b) | `design` → `execute-plan` → `pr-babysit` 流水线，`implement` 的实现-评审循环，`shared/personas/` 里的角色提示 |
