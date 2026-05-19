# codex/skills/ agents.overrides.md

## 目录职责

`codex/skills/` 只维护 Codex Orchestrate skills 的安装入口。真实 skill source 在 `.agents/skills/orchestrate-*`，真实 user-level runtime 在 `/Users/cheuklapchan/.agents/skills/orchestrate-*`。

## 编辑规则

- `install-orchestrate-runtime.sh` 是当前完整安装入口，必须覆盖六个 phase skills。
- 安装脚本只做复制、校验和 dry-run/apply 控制，不写 workflow phase logic。
- 不要从旧 Claude plugin 或归档 Codex V1 推导安装范围；以 `.agents/skills/orchestrate-*` 为 source 真相。
- 修改本目录后运行 `bash codex/skills/install-orchestrate-runtime.sh --user --apply`，并对比 `/Users/cheuklapchan/.agents/skills/` runtime。
