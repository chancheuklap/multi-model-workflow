# codex-skills

给 **Codex Worker** 用的 skill 源(Codex 读不到 Claude 的 `plugin/`,所以落地纪律得自包含在这里)。

plugin 在 build 阶段派 Codex 时,prompt 只给三文档路径 + 指向 `worktree-build` skill;铁律本体在 skill 里渐进加载(开工前不占 Codex context)。

## 安装(软链到 Codex skill 目录)

```bash
ln -s "$(pwd)/codex-skills/worktree-build" <Codex skill 目录>/worktree-build
```

装好后 Codex 侧 `worktree-build` 可用,与已装的 `/tdd` 配合。

## worktree-build

- `SKILL.md` — 落地总纲(5 步循环 + 必读三文档 + 收工回执契约 + 边界)。
- `references/discipline.md` — 防过度设计/兜底、契约类型、登记+迁移(开工读一次)。
- `references/tests.md` — 测试对标仓库治理文档、测公开行为/mock/权威层(写测试前读)。
- `references/when-stuck.md` — 3-strike / 计划冲突 / 缺输入(卡住才读)。
